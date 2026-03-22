from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Iterable, List, Mapping, Sequence

LIQUIDITY_BUCKET_BASE_SCORE = {'A': 0.38, 'B': 0.25, 'C': 0.12}
LIQUIDITY_BUCKET_RISK_PENALTY = {'A': 0.02, 'B': 0.05, 'C': 0.10}
LIQUIDITY_BUCKET_PROFILE_SCORE = {'A': 1.0, 'B': 0.72, 'C': 0.45}
LIQUIDITY_RANK = {'A': 0, 'B': 1, 'C': 2}

LOW_MID_HIGH = {'low': 0.2, 'mid': 0.55, 'high': 0.9}
ELASTICITY_BUCKET = {'low': 0.2, 'mid': 0.5, 'high': 0.75, 'extreme': 1.0}
PASS_THROUGH_BUCKET = {'weak': 0.2, 'mid': 0.55, 'strong': 0.9}
DIRECT_RESOURCE_BUCKET = {'theme_only': 0.1, 'indirect_beneficiary': 0.35, 'midstream_material': 0.65, 'direct_resource': 0.95}
DEFENSIVE_BUCKET = {'defensive': 0.85, 'balanced': 0.55, 'offensive': 0.2}
GLOBAL_EXPOSURE_BUCKET = {'domestic_dominant': 0.35, 'dual_engine': 0.68, 'global_dominant': 0.92}
BENEFIT_MODE_BUCKET = {'theme_only': 0.12, 'valuation_link': 0.32, 'capacity_pull': 0.58, 'spec_upgrade': 0.74, 'direct_order': 0.92}
CUSTOMER_ANCHOR_BUCKET = {
    'other': 0.3,
    'terminal_brand': 0.45,
    'equipment_vendor': 0.52,
    'foundry': 0.6,
    'operator': 0.66,
    'domestic_cloud': 0.76,
    'global_cloud': 0.9,
}
STYLE_BUCKET = {'value': 0.62, 'growth': 0.55, 'dividend': 0.88, 'financial': 0.8, 'cyclical': 0.45, 'policy_sensitive': 0.52}


def safe_text(value: Any) -> str:
    return str(value or '').strip()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def safe_json_text(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except Exception:
        return '{}'


def normalize_symbol(value: Any) -> str:
    text = safe_text(value).upper()
    if not text:
        return ''
    if '.' in text:
        code, suffix = text.split('.', 1)
        return f"{code.zfill(6)}.{suffix.upper()}"
    if text.isdigit():
        suffix = 'SH' if text.startswith(('5', '6', '9')) else 'SZ'
        return f"{text.zfill(6)}.{suffix}"
    return text


def symbol_to_code(symbol: Any) -> str:
    text = normalize_symbol(symbol)
    if not text:
        return ''
    return text.split('.', 1)[0]


def parse_date(value: Any) -> str:
    text = safe_text(value)
    if not text:
        return ''
    return text[:10]


def normalize_date(text: Any) -> str:
    raw = safe_text(text)
    if not raw:
        return ''
    if '年' in raw:
        raw = raw.replace('年', '-').replace('月', '-').replace('日', '')
    raw = raw.replace('/', '-')
    parts = raw.split('-')
    if len(parts) >= 3:
        try:
            return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        except Exception:
            return raw[:10]
    return raw[:10]


def parse_confidence(value: Any) -> float:
    text = safe_text(value).lower()
    if text in {'high', 'very_high'}:
        return 0.9
    if text == 'medium':
        return 0.7
    if text == 'low':
        return 0.4
    num = safe_float(value, -1.0)
    if num >= 0:
        return max(0.0, min(1.0, num if num <= 1.0 else num / 100.0))
    return 0.65


def normalize_importance(value: Any) -> float:
    num = safe_float(value, 0.0)
    if num <= 0:
        return 0.0
    if num <= 1.0:
        return num
    if num <= 10.0:
        return min(1.0, num / 10.0)
    return min(1.0, num / 100.0)


def split_exposures(value: Any) -> List[str]:
    text = safe_text(value)
    if not text:
        return []
    parts = [item.strip() for item in text.replace(',', '|').split('|')]
    return [item for item in parts if item]


def signed_direction(direction: Any) -> int:
    text = safe_text(direction).lower()
    if text in {'positive', 'up', 'bullish', '利好'}:
        return 1
    if text in {'negative', 'down', 'bearish', '利空'}:
        return -1
    return 0


def liquidity_base_score(bucket: Any) -> float:
    return LIQUIDITY_BUCKET_BASE_SCORE.get(safe_text(bucket).upper(), 0.18)


def liquidity_risk_penalty(bucket: Any) -> float:
    return LIQUIDITY_BUCKET_RISK_PENALTY.get(safe_text(bucket).upper(), 0.06)


def liquidity_profile_score(bucket: Any) -> float:
    return LIQUIDITY_BUCKET_PROFILE_SCORE.get(safe_text(bucket).upper(), 0.58)


def clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def map_bucket_score(value: Any, mapping: Mapping[str, float], default: float = 0.5) -> float:
    return clip(mapping.get(safe_text(value).lower(), default), 0.0, 1.0)


def classify_regime(score: float, heat: float) -> str:
    state = clip(score, -1.0, 1.0)
    heat_v = clip(heat, 0.0, 1.0)
    if state >= 0.45 and heat_v >= 0.35:
        return 'expansion'
    if state <= -0.45 and heat_v >= 0.35:
        return 'contraction'
    if abs(state) <= 0.12 and heat_v <= 0.18:
        return 'idle'
    if state > 0:
        return 'improving'
    if state < 0:
        return 'weakening'
    return 'neutral'


def freshness_weight(publish_date: str, as_of_date: str) -> float:
    pub = normalize_date(publish_date)
    ref = normalize_date(as_of_date)
    if not pub or not ref:
        return 0.45
    try:
        days = (datetime.strptime(ref, '%Y-%m-%d').date() - datetime.strptime(pub, '%Y-%m-%d').date()).days
    except Exception:
        return 0.45
    if days <= 45:
        return 1.0
    if days <= 120:
        return 0.75
    if days <= 240:
        return 0.45
    return 0.25


def dominant_strings(values: Iterable[str], limit: int = 2) -> List[str]:
    seen: List[str] = []
    for item in values:
        text = safe_text(item)
        if text and text not in seen:
            seen.append(text)
        if len(seen) >= limit:
            break
    return seen


def exposure_overlap_score(exposures: Sequence[str], keywords: Sequence[str]) -> float:
    if not exposures or not keywords:
        return 0.0
    tokens = {safe_text(x).lower() for x in exposures if safe_text(x)}
    refs = {safe_text(x).lower() for x in keywords if safe_text(x)}
    if not tokens or not refs:
        return 0.0
    hits = sum(1 for token in tokens if any(token in ref or ref in token for ref in refs))
    return clip(hits / max(len(tokens), 1), 0.0, 1.0)


def sign_consensus(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    positives = sum(1 for item in values if item > 0)
    negatives = sum(1 for item in values if item < 0)
    total = max(len(values), 1)
    return round(abs(positives - negatives) / total, 4)


def mean_or_zero(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(sum(float(x) for x in values) / max(len(values), 1))
