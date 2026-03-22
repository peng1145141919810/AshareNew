from __future__ import annotations

import json
import re
import ssl
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ...config_utils import ensure_dir
from .common import freshness_weight, normalize_date, safe_float, safe_text

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36'


def strip_html(html_text: str) -> str:
    text = re.sub(r'<script[\s\S]*?</script>', ' ', html_text, flags=re.IGNORECASE)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_title(html_text: str) -> str:
    for pattern in [r'<title[^>]*>(.*?)</title>', r'<h1[^>]*>(.*?)</h1>']:
        match = re.search(pattern, html_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return strip_html(match.group(1))[:180]
    return ''


def extract_date(html_text: str) -> str:
    clean = strip_html(html_text)
    prioritized_patterns = [
        r'(?:发布时间|文章来源|来源|时间)\s*[:：]?\s*(20\d{2}-\d{1,2}-\d{1,2})',
        r'(?:发布时间|文章来源|来源|时间)\s*[:：]?\s*(20\d{2}/\d{1,2}/\d{1,2})',
        r'(?:发布时间|文章来源|来源|时间)\s*[:：]?\s*(20\d{2}年\d{1,2}月\d{1,2}日)',
    ]
    for pattern in prioritized_patterns:
        match = re.search(pattern, clean)
        if not match:
            continue
        text = match.group(1)
        if '年' in text:
            return text.replace('年', '-').replace('月', '-').replace('日', '')
        return text.replace('/', '-')
    patterns = [
        r'(20\d{2}-\d{2}-\d{2})',
        r'(20\d{2}/\d{2}/\d{2})',
        r'(20\d{2}年\d{1,2}月\d{1,2}日)',
    ]
    for pattern in patterns:
        match = re.search(pattern, clean)
        if not match:
            continue
        text = match.group(1)
        if '年' in text:
            return text.replace('年', '-').replace('月', '-').replace('日', '')
        return text.replace('/', '-')
    return ''


def fetch_html(url: str, timeout: int) -> str:
    req = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        ctx = ssl.create_default_context()
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or ''
    except Exception as exc:
        if 'CERTIFICATE_VERIFY_FAILED' not in str(exc).upper():
            raise
        ctx = ssl._create_unverified_context()
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or ''
    tried = []
    for name in [charset, 'utf-8', 'utf-8-sig', 'gb18030', 'gbk']:
        encoding = safe_text(name)
        if not encoding or encoding.lower() in tried:
            continue
        tried.append(encoding.lower())
        try:
            return raw.decode(encoding)
        except Exception:
            continue
    return raw.decode('utf-8', errors='ignore')


def keyword_signal(text: str, positive_keywords: List[str], negative_keywords: List[str]) -> Dict[str, Any]:
    content = safe_text(text)
    pos_hits = [kw for kw in positive_keywords if kw and kw.lower() in content.lower()]
    neg_hits = [kw for kw in negative_keywords if kw and kw.lower() in content.lower()]
    raw_score = 0.14 * len(pos_hits) - 0.14 * len(neg_hits)
    return {
        'score': max(-0.5, min(0.5, round(raw_score, 4))),
        'positive_hits': pos_hits,
        'negative_hits': neg_hits,
    }


def cache_path(snapshot_root: Path, source_id: str) -> Path:
    safe = re.sub(r'[^A-Za-z0-9._-]+', '_', source_id)
    return snapshot_root / f'{safe}.json'


def load_cache(path: Path, cache_hours: int) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    fetched_at = safe_text(payload.get('fetched_at'))
    if not fetched_at:
        return None
    try:
        dt = datetime.fromisoformat(fetched_at)
    except Exception:
        return None
    if datetime.now() - dt > timedelta(hours=cache_hours):
        return None
    return payload


def domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ''


def fetch_source_snapshots(
    config: Dict[str, Any],
    source_contracts: Dict[str, Any],
    output_root: Path,
    as_of_date: str,
) -> Dict[str, Any]:
    source_cfg = dict(config.get('industry_router', {}).get('source_fetch', {}) or {})
    if not bool(source_cfg.get('enabled', False)):
        return {'enabled': False, 'items': [], 'state_rows': [], 'summary': {'status': 'disabled'}}

    timeout = int(source_cfg.get('timeout_seconds', 12) or 12)
    cache_hours = int(source_cfg.get('cache_hours', 12) or 12)
    max_sources = int(source_cfg.get('max_sources_per_run', 12) or 12)
    snapshot_root = ensure_dir(output_root / 'source_snapshots')
    items: List[Dict[str, Any]] = []
    state_rows: List[Dict[str, Any]] = []
    fetched_count = 0

    for mechanism, bucket in dict(source_contracts.get('mechanism_groups', {}) or {}).items():
        for category in ['industry_state_sources', 'macro_context_sources']:
            for entry in list(dict(bucket).get(category, []) or []):
                if not isinstance(entry, dict):
                    continue
                if safe_text(entry.get('mode')) != 'official_page':
                    continue
                if fetched_count >= max_sources:
                    break
                source_id = safe_text(entry.get('source_id')) or safe_text(entry.get('source_name'))
                local_cache_path = cache_path(snapshot_root=snapshot_root, source_id=source_id)
                cached = load_cache(path=local_cache_path, cache_hours=cache_hours)
                if cached is not None:
                    payload = cached
                else:
                    url = safe_text(entry.get('url'))
                    payload = {
                        'source_id': source_id,
                        'source_name': safe_text(entry.get('source_name')),
                        'mechanism_group': mechanism,
                        'category': category,
                        'url': url,
                        'domain': domain_from_url(url),
                        'status': 'error',
                        'fetched_at': datetime.now().isoformat(timespec='seconds'),
                        'publish_date': '',
                        'title': '',
                        'summary': '',
                        'signal_score': 0.0,
                        'confidence': 0.0,
                        'positive_hits': [],
                        'negative_hits': [],
                        'source_weight': 0.0,
                        'category_weight': 0.0,
                        'freshness_weight': 0.0,
                        'error': '',
                    }
                    try:
                        html_text = fetch_html(url=url, timeout=timeout)
                        text = strip_html(html_text)
                        title = extract_title(html_text) or safe_text(entry.get('source_name'))
                        publish_date = extract_date(html_text)
                        summary = text[:360]
                        kw = keyword_signal(
                            text=' '.join([title, summary]),
                            positive_keywords=list(entry.get('positive_keywords', []) or []),
                            negative_keywords=list(entry.get('negative_keywords', []) or []),
                        )
                        fresh = freshness_weight(publish_date=publish_date, as_of_date=as_of_date)
                        source_weight = safe_float(entry.get('source_weight'), 1.0)
                        category_weight = safe_float(entry.get('category_weight'), 1.0 if category == 'industry_state_sources' else 0.85)
                        confidence = round(0.75 * fresh, 4)
                        payload.update(
                            {
                                'status': 'ok',
                                'publish_date': normalize_date(publish_date),
                                'title': title,
                                'summary': summary,
                                'signal_score': round(float(kw['score']) * fresh * source_weight * category_weight, 4),
                                'confidence': confidence,
                                'positive_hits': list(kw['positive_hits']),
                                'negative_hits': list(kw['negative_hits']),
                                'source_weight': round(source_weight, 4),
                                'category_weight': round(category_weight, 4),
                                'freshness_weight': round(fresh, 4),
                                'error': '',
                            }
                        )
                    except Exception as exc:
                        payload['error'] = str(exc)[:300]
                    local_cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
                items.append(payload)
                fetched_count += 1
                if safe_text(payload.get('status')) == 'ok':
                    state_rows.append(
                        {
                            'date': as_of_date,
                            'mechanism_group': mechanism,
                            'source_id': source_id,
                            'source_name': safe_text(payload.get('source_name')),
                            'category': category,
                            'source_signal_score': safe_float(payload.get('signal_score'), 0.0),
                            'confidence': safe_float(payload.get('confidence'), 0.0),
                            'publish_date': safe_text(payload.get('publish_date')),
                            'title': safe_text(payload.get('title')),
                            'summary': safe_text(payload.get('summary')),
                            'url': safe_text(payload.get('url')),
                            'source_weight': safe_float(payload.get('source_weight'), safe_float(entry.get('source_weight'), 1.0)),
                            'category_weight': safe_float(payload.get('category_weight'), safe_float(entry.get('category_weight'), 1.0)),
                            'freshness_weight': safe_float(payload.get('freshness_weight'), 0.45),
                            'positive_hits': '|'.join(list(payload.get('positive_hits', []) or [])),
                            'negative_hits': '|'.join(list(payload.get('negative_hits', []) or [])),
                        }
                    )
            if fetched_count >= max_sources:
                break
        if fetched_count >= max_sources:
            break

    index_path = snapshot_root / 'source_snapshot_index.json'
    items_path = snapshot_root / 'source_snapshot_items.json'
    index_path.write_text(
        json.dumps(
            {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'as_of_date': as_of_date,
                'enabled': True,
                'count': len(items),
                'max_sources_per_run': max_sources,
                'ok_count': sum(1 for item in items if safe_text(item.get('status')) == 'ok'),
                'error_count': sum(1 for item in items if safe_text(item.get('status')) != 'ok'),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    items_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')

    by_mechanism: Dict[str, Dict[str, Any]] = {}
    for mechanism in sorted(set(item['mechanism_group'] for item in state_rows)):
        subset = [item for item in state_rows if item['mechanism_group'] == mechanism]
        by_mechanism[mechanism] = {
            'source_count': len(subset),
            'avg_signal_score': round(sum(safe_float(item.get('source_signal_score')) for item in subset) / max(len(subset), 1), 4),
            'top_sources': [item['source_name'] for item in sorted(subset, key=lambda row: abs(safe_float(row.get('source_signal_score'))), reverse=True)[:3]],
        }

    return {
        'enabled': True,
        'items': items,
        'state_rows': state_rows,
        'summary': {
            'status': 'ok',
            'index_path': str(index_path),
            'items_path': str(items_path),
            'source_state_path': str(output_root / 'source_state_daily.csv'),
            'max_sources_per_run': max_sources,
            'ok_count': sum(1 for item in items if safe_text(item.get('status')) == 'ok'),
            'error_count': sum(1 for item in items if safe_text(item.get('status')) != 'ok'),
            'by_mechanism': by_mechanism,
        },
    }
