# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _read_csv_positions(path: Path, limit: int = 20) -> list[dict[str, str]]:
    if not path.exists():
        return []
    import csv
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as handle:
            rows = []
            for idx, row in enumerate(csv.DictReader(handle)):
                rows.append({str(k): str(v or '') for k, v in row.items()})
                if idx + 1 >= limit:
                    break
            return rows
    except Exception:
        return []


def _filter_live_positions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            shares = float(row.get('actual_shares') or row.get('shares') or row.get('volume') or 0.0)
        except Exception:
            shares = 0.0
        try:
            weight = float(row.get('actual_weight') or row.get('weight') or 0.0)
        except Exception:
            weight = 0.0
        try:
            market_value = float(row.get('market_value') or row.get('amount') or 0.0)
        except Exception:
            market_value = 0.0
        if abs(shares) > 1e-9 or abs(weight) > 1e-12 or abs(market_value) > 1e-6:
            out.append(row)
    return out


def _filter_gap_rows_for_release(rows: list[dict[str, str]], release_id: str) -> list[dict[str, str]]:
    normalized = str(release_id or '').strip()
    if not normalized:
        return rows
    filtered = [row for row in rows if str(row.get('release_id') or '').strip() == normalized]
    if filtered:
        return filtered
    if any(str(row.get('release_id') or '').strip() for row in rows):
        return []
    return rows


def load_operator_docs(repo_root: Path) -> dict[str, str]:
    docs_root = repo_root / 'docs' / 'ai_operator'
    names = ['system_overview.md', 'operator_rules.md', 'intent_schema.md']
    out: dict[str, str] = {}
    for name in names:
        path = docs_root / name
        try:
            out[name] = path.read_text(encoding='utf-8')
        except Exception:
            out[name] = ''
    return out


def _published_runtime_context() -> dict[str, Any]:
    raw = str(os.environ.get('OPERATOR_RUNTIME_CONTEXT_PATH', '') or '').strip()
    if not raw:
        return {}
    path = Path(raw)
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else {}


def _active_namespace(repo_root: Path, latest_release: dict[str, Any], clock: dict[str, Any]) -> str:
    account_mode = str(
        clock.get('account_mode')
        or (clock.get('gate') or {}).get('account_mode')
        or clock.get('mode')
        or ''
    ).strip().lower()
    if account_mode in {'precision', 'simulation'}:
        return account_mode
    manifest_path = Path(str(latest_release.get('manifest_path', '') or '').strip())
    if manifest_path.exists():
        latest_execution = _read_json(manifest_path.parent / 'latest_execution.json')
        execution_report_path = Path(str(latest_execution.get('execution_report_path', '') or '').strip())
        if execution_report_path.exists():
            execution_report = _read_json(execution_report_path)
            namespace = str(
                execution_report.get('execution_namespace')
                or (execution_report.get('execution_policy') or {}).get('namespace')
                or ''
            ).strip().lower()
            if namespace:
                return namespace
    return 'main'


def build_runtime_context(repo_root: Path) -> dict[str, Any]:
    published = _published_runtime_context()
    if published:
        published.setdefault('notes', [])
        notes = list(published.get('notes') or [])
        notes.append(f'当前回答基于已发布的运行时上下文快照：{os.environ.get("OPERATOR_RUNTIME_CONTEXT_PATH", "").strip()}')
        published['notes'] = notes
        return published

    latest_release = _read_json(repo_root / 'data' / 'trade_release_v1' / 'latest_release.json')
    manifest_path = Path(str(latest_release.get('manifest_path', '') or '').strip())
    manifest = _read_json(manifest_path) if str(manifest_path).strip() else {}
    portfolio_summary_path = Path(str((manifest.get('artifacts') or {}).get('portfolio_summary_path', '') or '').strip())
    portfolio_summary = _read_json(portfolio_summary_path) if portfolio_summary_path.exists() else {}
    clock = _read_json(repo_root / 'data' / 'trade_clock' / 'clock_state.json')
    safety = _read_json(repo_root / 'data' / 'trade_clock' / 'system_safety_state.json')
    health = _read_json(repo_root / 'data' / 'trade_clock' / 'latest_account_health.json')
    market = _read_json(repo_root / 'data' / 'market_state_v6' / 'latest_market_state.json')
    strategy = _read_json(repo_root / 'data' / 'event_lake_v6' / 'research' / 'integrated_thesis' / 'integrated_thesis_state.json')
    intraday = _read_json(repo_root / 'data' / 'trade_clock' / 'intraday_state' / 'latest' / 'intraday_phase_state.json')
    intraday_proxy = _read_json(repo_root / 'data' / 'trade_clock' / 'intraday_proxy' / 'latest' / 'intraday_proxy_manifest.json')
    external_research = _read_json(repo_root / 'data' / 'external_research_feeds' / 'latest' / 'external_research_refresh_manifest.json')
    namespace = _active_namespace(repo_root, latest_release, clock)
    oms_root = repo_root / 'data' / 'live_execution_bridge' / 'oms_v1'
    if namespace != 'main':
        oms_root = oms_root / namespace
    oms = _read_json(oms_root / 'snapshots' / 'latest_actual_portfolio_state.json')
    gap_rows = _read_csv_positions(oms_root / 'snapshots' / 'desired_vs_actual_gap.csv', limit=64)
    gap_rows = _filter_gap_rows_for_release(gap_rows, str(latest_release.get('release_id') or '').strip())[:10]
    positions = _filter_live_positions(list(oms.get('positions') or []))[:12]
    account = dict(oms.get('account') or {})
    account_truth = _read_json(repo_root / 'data' / 'trade_clock' / 'intraday_proxy' / 'latest' / 'account_truth_snapshot.json')
    if latest_release:
        account['release_id'] = latest_release.get('release_id') or account.get('release_id') or '-'
        account['trade_date'] = latest_release.get('trade_date') or account.get('trade_date') or '-'
    if account_truth:
        account['available_cash'] = account_truth.get('available_cash', account.get('available_cash'))
        account['frozen_cash'] = account_truth.get('frozen_cash', account.get('frozen_cash'))
        account['market_value'] = account_truth.get('market_value', account.get('market_value'))
        account['pending_orders_count'] = account_truth.get('pending_orders_count')
        account['t1_locked_positions_count'] = account_truth.get('t1_locked_positions_count')
    notes = []
    if not positions:
        notes.append('当前账户快照中没有持仓列表，回答需要保守。')
    if not latest_release:
        notes.append('当前没有 latest_release.json，发布信息缺失。')
    return {
        'trade_date': latest_release.get('trade_date') or clock.get('trade_date') or '-',
        'clock_phase': clock.get('current_phase') or clock.get('phase') or intraday.get('current_phase') or '-',
        'clock_mode': clock.get('mode') or '-',
        'heartbeat_at': clock.get('last_heartbeat_at') or '-',
        'release_id': latest_release.get('release_id') or '-',
        'run_id': manifest.get('run_id') or '-',
        'execution_namespace': namespace,
        'account': account,
        'positions': positions,
        'gap_rows': gap_rows,
        'safety': safety,
        'health': health,
        'market_state': {
            'market_regime': market.get('market_regime'),
            'style_bias': market.get('style_bias'),
            'mechanism_bias': market.get('mechanism_bias'),
            'risk_budget_multiplier': market.get('risk_budget_multiplier'),
        },
        'integrated_thesis_summary': strategy.get('summary') or {},
        'integrated_thesis_portfolio_construction': strategy.get('portfolio_construction') or {},
        'alpha_lifecycle': portfolio_summary.get('alpha_lifecycle') or {},
        'trade_discipline': portfolio_summary.get('trade_discipline') or {},
        'llm_operating_brain': portfolio_summary.get('llm_operating_brain') or {},
        'intraday_proxy': intraday_proxy,
        'external_research_refresh': external_research,
        'notes': notes,
    }
