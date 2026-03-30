from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

from .config_utils import ensure_dir
from .market_state import load_latest_market_state


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _output_root(config: Dict[str, Any]) -> Path:
    kernel_cfg = dict(config.get("three_strategy_kernel", {}) or {})
    configured = str(kernel_cfg.get("output_root", "") or "").strip()
    if configured:
        return ensure_dir(Path(configured).resolve())
    research_root = Path(str(config.get("paths", {}).get("research_root", "") or "")).resolve()
    return ensure_dir(research_root / "three_strategy_kernel")


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_daily_csv(path: Path, row: Dict[str, Any]) -> None:
    frame = pd.read_csv(path) if path.exists() else pd.DataFrame()
    incoming = pd.DataFrame([row])
    merged = pd.concat([frame, incoming], ignore_index=True)
    merged["trade_date"] = merged["trade_date"].astype(str).str.slice(0, 10)
    merged = merged.drop_duplicates(subset=["trade_date"], keep="last").sort_values("trade_date")
    merged.to_csv(path, index=False, encoding="utf-8-sig")


def _industry_router_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    root = Path(str(config.get("paths", {}).get("industry_router_output_root", "") or "")).resolve()
    return _load_json(root / "industry_router_summary.json")


def _affordable_dataset_stats(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    path = Path(str(config.get("paths", {}).get("affordable_sqlite_path", "") or "")).resolve()
    if not path.exists():
        return {}
    stats: Dict[str, Dict[str, Any]] = {}
    datasets = {
        "forecast": "primary_date",
        "express": "primary_date",
        "daily_basic": "primary_date",
        "moneyflow_hsgt": "primary_date",
        "margin": "primary_date",
        "hk_hold": "primary_date",
        "customs_summary": "primary_date",
    }
    try:
        conn = sqlite3.connect(str(path))
    except Exception:
        return {}
    try:
        for dataset, date_col in datasets.items():
            try:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS row_count,
                        MAX(primary_date) AS latest_primary_date,
                        MAX(updated_at) AS latest_updated_at
                    FROM affordable_dataset_rows
                    WHERE dataset = ?
                    """,
                    (dataset,),
                ).fetchone()
            except Exception:
                row = None
            stats[dataset] = {
                "row_count": _safe_int(row[0] if row else 0),
                "latest_primary_date": _safe_text(row[1] if row else ""),
                "latest_updated_at": _safe_text(row[2] if row else ""),
                "date_field": date_col,
            }
    finally:
        conn.close()
    return stats


def _top_signals(industry_summary: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    payload = dict(industry_summary.get("context_payload", {}) or {})
    rows = list(payload.get("top_stock_signals", []) or [])
    return [dict(item) for item in rows[:limit] if isinstance(item, dict)]


def _industry_chain_strategy(industry_summary: Dict[str, Any]) -> Dict[str, Any]:
    signal_rows = _safe_int(industry_summary.get("signal_rows", 0))
    source_ok = _safe_int(dict(industry_summary.get("source_fetch", {}) or {}).get("ok_count", 0))
    top_signals = _top_signals(industry_summary)
    readiness = _clip(signal_rows / 80.0 * 0.65 + min(source_ok, 6) / 6.0 * 0.35)
    state = "warming_up"
    if readiness >= 0.7:
        state = "active"
    elif readiness < 0.25:
        state = "thin"
    return {
        "strategy_key": "industry_chain_expectation_gap",
        "strategy_name": "Industry Chain Expectation Gap",
        "enabled": True,
        "readiness_score": round(readiness, 4),
        "state": state,
        "evidence_strength": round(_clip(signal_rows / 100.0), 4),
        "signal_rows": signal_rows,
        "source_snapshot_ok_count": source_ok,
        "top_stock_signals": top_signals,
        "data_limitations": [
            "spot_price_inventory_operating_rate_free_coverage_incomplete",
            "customs_only_summary_not_detail",
            "contract_backlog_structured_facts_not_full_universe",
        ],
        "llm_role": "explain_evidence_and_normalize_text_only",
    }


def _earnings_expectation_strategy(affordable_stats: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    forecast_rows = _safe_int(dict(affordable_stats.get("forecast", {}) or {}).get("row_count", 0))
    express_rows = _safe_int(dict(affordable_stats.get("express", {}) or {}).get("row_count", 0))
    daily_basic_rows = _safe_int(dict(affordable_stats.get("daily_basic", {}) or {}).get("row_count", 0))
    evidence_score = min(forecast_rows, 200) / 200.0 * 0.45 + min(express_rows, 200) / 200.0 * 0.35 + min(daily_basic_rows, 5000) / 5000.0 * 0.20
    readiness = _clip(evidence_score)
    state = "warming_up"
    if readiness >= 0.62:
        state = "active"
    elif readiness < 0.20:
        state = "thin"
    return {
        "strategy_key": "earnings_expectation_gap",
        "strategy_name": "Earnings Expectation Gap",
        "enabled": True,
        "readiness_score": round(readiness, 4),
        "state": state,
        "evidence_strength": round(_clip((forecast_rows + express_rows) / 300.0), 4),
        "forecast_rows": forecast_rows,
        "express_rows": express_rows,
        "daily_basic_rows": daily_basic_rows,
        "latest_forecast_date": _safe_text(dict(affordable_stats.get("forecast", {}) or {}).get("latest_primary_date")),
        "latest_express_date": _safe_text(dict(affordable_stats.get("express", {}) or {}).get("latest_primary_date")),
        "data_limitations": [
            "analyst_consensus_revision_missing_under_current_budget",
            "no_broad_eps_revision_panel_yet",
            "financial_indicator_refresh_is_not_full_universe_default",
        ],
        "llm_role": "extract_guidance_direction_and_announcement_structure_only",
    }


def _asset_allocation_strategy(market_state: Dict[str, Any]) -> Dict[str, Any]:
    regime = _safe_text(market_state.get("market_regime") or "neutral")
    risk_budget = _safe_float(market_state.get("risk_budget_multiplier", 1.0), 1.0)
    turnover = _safe_float(market_state.get("turnover_multiplier", 1.0), 1.0)
    readiness = _clip(0.6 + abs(risk_budget - 1.0) * 0.4)
    if regime in {"panic", "risk_off"}:
        target_cash = _clip(1.0 - risk_budget, 0.15, 0.80)
    elif regime == "risk_on":
        target_cash = _clip(1.0 - risk_budget, 0.0, 0.25)
    else:
        target_cash = _clip(1.0 - risk_budget, 0.05, 0.45)
    return {
        "strategy_key": "asset_allocation_risk_parity",
        "strategy_name": "Asset Allocation / Risk Parity",
        "enabled": True,
        "readiness_score": round(readiness, 4),
        "state": regime or "neutral",
        "risk_budget_multiplier": round(risk_budget, 4),
        "turnover_multiplier": round(turnover, 4),
        "target_cash_buffer": round(target_cash, 4),
        "new_position_policy": _safe_text(market_state.get("new_position_policy") or "allow"),
        "de_risk_hint": _safe_text(market_state.get("de_risk_hint") or ""),
        "llm_role": "forbidden_from_overriding_risk_policy",
    }


def _strategy_allocations(
    industry_strategy: Dict[str, Any],
    earnings_strategy: Dict[str, Any],
    allocation_strategy: Dict[str, Any],
) -> Dict[str, float]:
    industry_readiness = _safe_float(industry_strategy.get("readiness_score", 0.0))
    earnings_readiness = _safe_float(earnings_strategy.get("readiness_score", 0.0))
    allocation_readiness = _safe_float(allocation_strategy.get("readiness_score", 0.0))
    alpha_sum = industry_readiness + earnings_readiness
    if alpha_sum <= 1e-9:
        industry_weight = 0.20
        earnings_weight = 0.15
    else:
        industry_weight = 0.60 * industry_readiness / alpha_sum
        earnings_weight = 0.60 * earnings_readiness / alpha_sum
    allocation_weight = max(0.20, 1.0 - industry_weight - earnings_weight)
    if allocation_readiness > 0.8 and _safe_text(allocation_strategy.get("state")) in {"panic", "risk_off"}:
        allocation_weight = max(allocation_weight, 0.40)
        alpha_scale = 1.0 - allocation_weight
        alpha_total = max(industry_weight + earnings_weight, 1e-9)
        industry_weight = alpha_scale * industry_weight / alpha_total
        earnings_weight = alpha_scale * earnings_weight / alpha_total
    return {
        "industry_chain_expectation_gap": round(industry_weight, 4),
        "earnings_expectation_gap": round(earnings_weight, 4),
        "asset_allocation_risk_parity": round(allocation_weight, 4),
    }


def build_three_strategy_artifacts(
    config: Dict[str, Any],
    *,
    industry_router_payload: Dict[str, Any] | None = None,
    market_state_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    kernel_cfg = dict(config.get("three_strategy_kernel", {}) or {})
    output_root = _output_root(config)
    latest_path = output_root / "three_strategy_state.json"
    daily_path = output_root / "three_strategy_daily.csv"

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not bool(kernel_cfg.get("enabled", True)):
        payload = {
            "generated_at": generated_at,
            "trade_date": generated_at[:10],
            "status": "disabled",
            "formal_strategy_framework": "three_long_term_strategies",
            "primary_strategy_key": "",
            "strategy_allocations": {},
            "portfolio_construction": {"alpha_budget_multiplier": 1.0},
            "strategies": {},
            "llm_operating_model": {},
            "data_limitations": {},
            "artifacts": {"latest_path": str(latest_path), "daily_path": str(daily_path)},
        }
        _write_json(latest_path, payload)
        return {"ok": True, "status": "disabled", "latest_path": str(latest_path), "daily_path": str(daily_path), "payload": payload}
    market_state = dict(market_state_payload or {}) or dict(load_latest_market_state(config=config, allow_build=True) or {})
    industry_summary = _industry_router_summary(config)
    if industry_router_payload:
        industry_summary["context_payload"] = dict(industry_router_payload or {})
    affordable_stats = _affordable_dataset_stats(config)

    industry_strategy = _industry_chain_strategy(industry_summary)
    earnings_strategy = _earnings_expectation_strategy(affordable_stats)
    allocation_strategy = _asset_allocation_strategy(market_state)
    allocations = _strategy_allocations(industry_strategy, earnings_strategy, allocation_strategy)

    primary_key = max(allocations.items(), key=lambda item: item[1])[0]
    alpha_budget_multiplier = round(
        _clip(
            0.70
            + _safe_float(industry_strategy.get("readiness_score", 0.0)) * 0.15
            + _safe_float(earnings_strategy.get("readiness_score", 0.0)) * 0.15,
            0.70,
            1.00,
        ),
        4,
    )

    payload = {
        "generated_at": generated_at,
        "trade_date": _safe_text(market_state.get("date") or generated_at[:10]),
        "status": "ok",
        "formal_strategy_framework": "three_long_term_strategies",
        "primary_strategy_key": primary_key,
        "strategy_allocations": allocations,
        "portfolio_construction": {
            "alpha_budget_multiplier": alpha_budget_multiplier,
            "equity_budget_reference": round(_safe_float(allocation_strategy.get("risk_budget_multiplier", 1.0)), 4),
            "target_cash_buffer": round(_safe_float(allocation_strategy.get("target_cash_buffer", 0.0)), 4),
        },
        "strategies": {
            "industry_chain_expectation_gap": industry_strategy,
            "earnings_expectation_gap": earnings_strategy,
            "asset_allocation_risk_parity": allocation_strategy,
        },
        "llm_operating_model": {
            "allowed_roles": [
                "announcement_extraction",
                "evidence_normalization",
                "research_explainer",
                "strategy_state_commentary",
            ],
            "forbidden_roles": [
                "truth_source_substitution",
                "final_risk_budget_override",
                "final_execution_decision_maker",
                "silent_proxy_field_promotion",
            ],
            "policy": "llm_is_an_upstream_interpreter_not_the_constitution_maker",
        },
        "data_limitations": {
            "industry_chain": list(industry_strategy.get("data_limitations", []) or []),
            "earnings": list(earnings_strategy.get("data_limitations", []) or []),
            "asset_allocation": [
                "current_layer_is_equity_posture_first_not_full_cross_asset_engine",
                "true_multi_asset_etf_sleeve_is_not_fully_materialized_yet",
            ],
        },
        "artifacts": {
            "latest_path": str(latest_path),
            "daily_path": str(daily_path),
        },
    }
    _write_json(latest_path, payload)
    _write_daily_csv(
        daily_path,
        {
            "trade_date": payload["trade_date"],
            "generated_at": generated_at,
            "primary_strategy_key": primary_key,
            "industry_readiness": industry_strategy["readiness_score"],
            "earnings_readiness": earnings_strategy["readiness_score"],
            "allocation_readiness": allocation_strategy["readiness_score"],
            "industry_weight": allocations["industry_chain_expectation_gap"],
            "earnings_weight": allocations["earnings_expectation_gap"],
            "allocation_weight": allocations["asset_allocation_risk_parity"],
            "alpha_budget_multiplier": alpha_budget_multiplier,
        },
    )
    return {
        "ok": True,
        "status": "ok",
        "latest_path": str(latest_path),
        "daily_path": str(daily_path),
        "payload": payload,
    }


def load_latest_three_strategy_state(config: Dict[str, Any], allow_build: bool = False) -> Dict[str, Any]:
    latest_path = _output_root(config) / "three_strategy_state.json"
    if latest_path.exists():
        payload = _load_json(latest_path)
        if payload:
            return payload
    if allow_build:
        result = build_three_strategy_artifacts(config=config)
        return dict(result.get("payload", {}) or {})
    return {}
