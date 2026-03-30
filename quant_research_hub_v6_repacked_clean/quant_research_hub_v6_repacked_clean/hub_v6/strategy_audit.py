from __future__ import annotations

import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .config_utils import ensure_dir


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


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _candidate_funnel(summary: Dict[str, Any]) -> Dict[str, Any]:
    filt = dict(summary.get("execution_candidate_filter", {}) or {})
    tech = dict(summary.get("technical_confirmation", {}) or {})
    v2a = dict(summary.get("portfolio_v2a", {}) or {})
    kept = _safe_int(filt.get("kept_rows", 0))
    dropped = _safe_int(filt.get("dropped_rows", 0))
    allow_count = _safe_int(tech.get("allow_count", 0))
    reject_count = _safe_int(tech.get("reject_count", 0))
    selected_count = _safe_int(summary.get("n_names", 0))
    return {
        "candidate_source": _safe_text(summary.get("candidate_source")),
        "kept_rows": kept,
        "dropped_rows": dropped,
        "allow_count": allow_count,
        "reject_count": reject_count,
        "selected_count": selected_count,
        "filter_drop_ratio": round(dropped / max(kept + dropped, 1), 4),
        "technical_reject_ratio": round(reject_count / max(allow_count + reject_count, 1), 4),
        "selection_ratio_after_technical": round(selected_count / max(allow_count, 1), 4) if allow_count else 0.0,
        "v2a_state_counts": dict(v2a.get("state_counts", {}) or {}),
        "v2a_action_counts": dict(v2a.get("action_counts", {}) or {}),
    }


def _portfolio_budget(summary: Dict[str, Any], release_doc: Dict[str, Any]) -> Dict[str, Any]:
    limits = dict(summary.get("portfolio_limits", {}) or release_doc.get("constraints", {}) or {})
    weight_totals = dict(summary.get("portfolio_weight_totals", {}) or {})
    final_total = _safe_float(weight_totals.get("final_total_weight", 0.0))
    cap = _safe_float(limits.get("total_exposure_cap", 0.0))
    return {
        "total_exposure_cap": cap,
        "single_name_cap": _safe_float(limits.get("single_name_cap", 0.0)),
        "max_names": _safe_int(limits.get("max_names", 0)),
        "final_total_weight": final_total,
        "fill_ratio": round(final_total / max(cap, 1e-9), 4) if cap > 0 else 0.0,
        "target_fill": _safe_float(weight_totals.get("target_fill", 0.0)),
        "reweight_before": _safe_float(weight_totals.get("reweight_before", 0.0)),
        "reweight_after": _safe_float(weight_totals.get("reweight_after", 0.0)),
    }


def _positions_breakdown(target_df: pd.DataFrame) -> Dict[str, Any]:
    if target_df.empty:
        return {"available": False}
    frame = target_df.copy()
    if "portfolio_weight" in frame.columns:
        frame["portfolio_weight"] = pd.to_numeric(frame["portfolio_weight"], errors="coerce").fillna(0.0)
    elif "final_target_weight_v2a" in frame.columns:
        frame["portfolio_weight"] = pd.to_numeric(frame["final_target_weight_v2a"], errors="coerce").fillna(0.0)
    else:
        frame["portfolio_weight"] = 0.0
    if "industry" in frame.columns:
        top_industries = (
            frame.assign(industry=frame["industry"].fillna("unknown").astype(str))
            .groupby("industry")["portfolio_weight"]
            .sum()
            .sort_values(ascending=False)
            .head(8)
            .reset_index()
            .rename(columns={"industry": "bucket"})
            .to_dict(orient="records")
        )
    else:
        top_industries = []
    action_counts = (
        frame["position_action_intent"].astype(str).value_counts().to_dict()
        if "position_action_intent" in frame.columns
        else {}
    )
    gate_counts = (
        frame["tech_gate_reason"].astype(str).value_counts().head(10).to_dict()
        if "tech_gate_reason" in frame.columns
        else {}
    )
    return {
        "available": True,
        "n_positions": int(len(frame.index)),
        "top_industries_by_weight": top_industries,
        "action_intent_counts": action_counts,
        "tech_gate_reason_counts": gate_counts,
    }


def _strategy_exposure(summary: Dict[str, Any], target_df: pd.DataFrame) -> Dict[str, Any]:
    state = dict(summary.get("three_strategy_state", {}) or {})
    strategies = dict(state.get("strategies", {}) or {})
    allocations = dict(state.get("strategy_allocations", {}) or {})
    output = {
        "formal_strategy_framework": _safe_text(
            summary.get("formal_strategy_framework")
            or state.get("formal_strategy_framework")
            or "three_long_term_strategies"
        ),
        "primary_strategy_key": _safe_text(summary.get("primary_strategy_key") or state.get("primary_strategy_key")),
        "strategy_allocations": allocations,
        "strategy_readiness": {
            key: round(_safe_float(dict(value).get("readiness_score", 0.0)), 4)
            for key, value in strategies.items()
            if isinstance(value, dict)
        },
    }
    if not target_df.empty and "mechanism_primary" in target_df.columns:
        frame = target_df.copy()
        if "portfolio_weight" in frame.columns:
            weights = pd.to_numeric(frame["portfolio_weight"], errors="coerce").fillna(0.0)
        elif "final_target_weight_v2a" in frame.columns:
            weights = pd.to_numeric(frame["final_target_weight_v2a"], errors="coerce").fillna(0.0)
        else:
            weights = pd.Series(0.0, index=frame.index)
        frame["portfolio_weight"] = weights
        frame["mechanism_primary"] = frame["mechanism_primary"].fillna("unlabeled").astype(str)
        mechanism_weights = (
            frame.groupby("mechanism_primary")["portfolio_weight"].sum().sort_values(ascending=False).to_dict()
        )
    else:
        mechanism_weights = {}
    output["mechanism_weight_proxy"] = {str(k): round(float(v), 6) for k, v in mechanism_weights.items()}
    return output


def _equity_curve_analysis(summary: Dict[str, Any]) -> Dict[str, Any]:
    feedback = dict(summary.get("performance_feedback", {}) or {})
    raw = _safe_text(feedback.get("source_equity_curve"))
    if not raw:
        return {"available": False, "reason": "missing_equity_curve_path"}
    path = Path(raw)
    frame = _read_csv(path)
    if frame.empty or "nav" not in frame.columns:
        return {"available": False, "reason": f"unavailable:{path}"}
    bucket = frame.copy()
    ts_col = "timestamp" if "timestamp" in bucket.columns else bucket.columns[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        bucket[ts_col] = pd.to_datetime(bucket[ts_col], errors="coerce")
    bucket["nav"] = pd.to_numeric(bucket["nav"], errors="coerce")
    bucket = bucket.dropna(subset=[ts_col, "nav"]).sort_values(ts_col)
    if bucket.empty:
        return {"available": False, "reason": f"empty:{path}"}
    latest_nav = float(bucket["nav"].iloc[-1])
    peak = bucket["nav"].cummax()
    drawdown = bucket["nav"] / peak - 1.0
    result = {
        "available": True,
        "path": str(path),
        "latest_nav": latest_nav,
        "current_drawdown": round(float(drawdown.iloc[-1]), 6),
        "max_drawdown": round(float(drawdown.min()), 6),
    }
    for horizon in (1, 5, 20):
        if len(bucket.index) > horizon:
            prev = float(bucket["nav"].iloc[-1 - horizon])
            result[f"ret_{horizon}d"] = round(latest_nav / prev - 1.0, 6) if prev > 0 else 0.0
        else:
            result[f"ret_{horizon}d"] = 0.0
    result["series"] = [
        {"date": str(bucket[ts_col].iloc[idx])[:10], "nav": round(float(bucket["nav"].iloc[idx]), 6)}
        for idx in range(max(0, len(bucket.index) - 20), len(bucket.index))
    ]
    return result


def _benchmark_comparison(config: Dict[str, Any], equity: Dict[str, Any]) -> Dict[str, Any]:
    market_cfg = dict(config.get("market_pipeline", {}) or {})
    hs300_path = Path(str(market_cfg.get("hs300_path", "") or config.get("hs300_path", "") or "")).resolve()
    if not hs300_path.exists():
        return {"available": False, "reason": f"missing_benchmark:{hs300_path}"}
    frame = _read_csv(hs300_path)
    if frame.empty or "date" not in frame.columns or "close" not in frame.columns:
        return {"available": False, "reason": f"unavailable:{hs300_path}"}
    bench = frame.copy()
    bench["date"] = pd.to_datetime(bench["date"], errors="coerce")
    bench["close"] = pd.to_numeric(bench["close"], errors="coerce")
    bench = bench.dropna(subset=["date", "close"]).sort_values("date")
    if bench.empty:
        return {"available": False, "reason": f"empty:{hs300_path}"}
    result = {
        "available": True,
        "path": str(hs300_path),
        "latest_close": round(float(bench["close"].iloc[-1]), 6),
    }
    for horizon in (1, 5, 20, 60):
        if len(bench.index) > horizon:
            prev = float(bench["close"].iloc[-1 - horizon])
            latest = float(bench["close"].iloc[-1])
            result[f"ret_{horizon}d"] = round(latest / prev - 1.0, 6) if prev > 0 else 0.0
        else:
            result[f"ret_{horizon}d"] = 0.0
    if equity.get("available") and list(equity.get("series", []) or []):
        eq = pd.DataFrame(list(equity.get("series", []) or []))
        if not eq.empty and "date" in eq.columns and "nav" in eq.columns:
            eq["date"] = pd.to_datetime(eq["date"], errors="coerce")
            eq["nav"] = pd.to_numeric(eq["nav"], errors="coerce")
            eq = eq.dropna(subset=["date", "nav"]).sort_values("date")
            overlap = eq.merge(bench[["date", "close"]], on="date", how="inner")
            if not overlap.empty:
                first_nav = float(overlap["nav"].iloc[0])
                first_close = float(overlap["close"].iloc[0])
                if first_nav > 0 and first_close > 0:
                    overlap["system_norm"] = overlap["nav"] / first_nav
                    overlap["benchmark_norm"] = overlap["close"] / first_close
                    result["excess_return_since_overlap_start"] = round(
                        float(overlap["system_norm"].iloc[-1] - overlap["benchmark_norm"].iloc[-1]),
                        6,
                    )
                    result["comparison_series"] = [
                        {
                            "date": str(overlap["date"].iloc[idx])[:10],
                            "system_norm": round(float(overlap["system_norm"].iloc[idx]), 6),
                            "benchmark_norm": round(float(overlap["benchmark_norm"].iloc[idx]), 6),
                        }
                        for idx in range(max(0, len(overlap.index) - 30), len(overlap.index))
                    ]
                    for horizon in (5, 20):
                        eq_key = f"ret_{horizon}d"
                        bench_key = f"ret_{horizon}d"
                        result[f"excess_{horizon}d"] = round(
                            _safe_float(equity.get(eq_key, 0.0)) - _safe_float(result.get(bench_key, 0.0)),
                            6,
                        )
    return result


def _actual_state_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    oms_root = Path(
        str(config.get("paths", {}).get("oms_output_root", "") or config.get("oms", {}).get("output_root", "") or "")
    ).resolve()
    if not str(oms_root).strip():
        return {"available": False, "reason": "missing_oms_root"}
    latest_actual = oms_root / "snapshots" / "latest_actual_portfolio_state.json"
    payload = _load_json(latest_actual)
    if not payload:
        return {"available": False, "reason": f"unavailable:{latest_actual}"}
    positions = list(payload.get("positions", []) or [])
    mechanism_counts: Dict[str, int] = {}
    gap_weight_abs = 0.0
    for row in positions:
        mechanism = _safe_text(dict(row).get("mechanism_primary") or "unlabeled")
        mechanism_counts[mechanism] = mechanism_counts.get(mechanism, 0) + 1
        gap_weight_abs += abs(_safe_float(dict(row).get("gap_weight_abs", 0.0)))
    return {
        "available": True,
        "release_id": _safe_text(payload.get("release_id")),
        "n_positions": len(positions),
        "account_total_asset": _safe_float(dict(payload.get("account", {}) or {}).get("total_asset", 0.0)),
        "account_cash": _safe_float(dict(payload.get("account", {}) or {}).get("cash", 0.0)),
        "actual_state_counts": dict(dict(payload.get("summary", {}) or {}).get("actual_state_counts", {}) or {}),
        "mechanism_counts": mechanism_counts,
        "gap_weight_abs_sum": round(gap_weight_abs, 6),
    }


def _overfit_risk(summary: Dict[str, Any], funnel: Dict[str, Any], budget: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    score = 0
    total_score = _safe_float(summary.get("total_score", 0.0))
    sharpe = _safe_float(summary.get("sharpe", 0.0))
    if "fallback" in _safe_text(funnel.get("candidate_source")).lower():
        score += 1
        reasons.append("portfolio_used_latest_scores_fallback")
    if _safe_float(funnel.get("filter_drop_ratio", 0.0)) >= 0.25:
        score += 1
        reasons.append("candidate_universe_filter_drop_high")
    if _safe_float(funnel.get("technical_reject_ratio", 0.0)) >= 0.70:
        score += 1
        reasons.append("technical_reject_ratio_high")
    if _safe_float(budget.get("fill_ratio", 0.0)) <= 0.75:
        score += 1
        reasons.append("post_filter_fill_ratio_low")
    if total_score >= 35.0 and sharpe >= 1.2 and _safe_float(funnel.get("technical_reject_ratio", 0.0)) >= 0.60:
        score += 1
        reasons.append("paper_metrics_ok_but_live_admission_friction_high")
    level = "low"
    if score >= 4:
        level = "high"
    elif score >= 2:
        level = "medium"
    return {
        "risk_level": level,
        "risk_score": score,
        "reasons": reasons,
        "interpretation": {
            "low": "Current evidence does not show a strong paper-to-live mismatch.",
            "medium": "There are visible signs that candidate quality or live filters are compressing deployable alpha.",
            "high": "Model or candidate quality likely looks better on paper than in live admission or execution conditions.",
        }[level],
    }


def _plain_language(
    summary: Dict[str, Any],
    strategy_exposure: Dict[str, Any],
    funnel: Dict[str, Any],
    overfit: Dict[str, Any],
    equity: Dict[str, Any],
    benchmark: Dict[str, Any],
    actual: Dict[str, Any],
) -> Dict[str, Any]:
    strengths: List[str] = []
    drags: List[str] = []
    primary = _safe_text(strategy_exposure.get("primary_strategy_key"))
    if primary:
        strengths.append(f"Current primary strategy is {primary}.")
    if equity.get("available"):
        ret_5d = _safe_float(equity.get("ret_5d", 0.0))
        if ret_5d > 0:
            strengths.append(f"Recent 5-day NAV trend is positive at {ret_5d:.2%}.")
        elif ret_5d < 0:
            drags.append(f"Recent 5-day NAV trend is negative at {ret_5d:.2%}.")
    if benchmark.get("available") and "excess_20d" in benchmark:
        excess_20d = _safe_float(benchmark.get("excess_20d", 0.0))
        if excess_20d > 0:
            strengths.append(f"System outperformed HS300 by {excess_20d:.2%} over the recent 20-day comparison window.")
        elif excess_20d < 0:
            drags.append(f"System underperformed HS300 by {abs(excess_20d):.2%} over the recent 20-day comparison window.")
    if _safe_float(funnel.get("technical_reject_ratio", 0.0)) > 0.60:
        drags.append("Technical confirmation reject ratio is high, so many candidates never reached the final portfolio.")
    if _safe_float(funnel.get("filter_drop_ratio", 0.0)) > 0.20:
        drags.append("Too much candidate loss happened in the tradable-universe filter, which weakens paper-to-live conversion.")
    if actual.get("available") and _safe_float(actual.get("gap_weight_abs_sum", 0.0)) > 0:
        drags.append("OMS actual positions still show a residual gap versus target positions.")
    if overfit.get("risk_level") in {"medium", "high"}:
        drags.append(f"There is a {overfit.get('risk_level')} overfit or paper-to-live mismatch warning.")
    if not strengths:
        strengths.append("No strong positive driver is available yet because realized PnL attribution history is still incomplete.")
    if not drags:
        drags.append("No major drag is visible in the current proxy-based audit view.")
    return {
        "what_helped": strengths,
        "what_hurt": drags,
    }


def _bar(label: str, value: float, color: str) -> str:
    pct = max(0.0, min(100.0, float(value) * 100.0))
    return (
        f"<div class='bar-row'><div class='bar-label'>{label}</div>"
        f"<div class='bar-track'><div class='bar-fill' style='width:{pct:.1f}%;background:{color};'></div></div>"
        f"<div class='bar-value'>{pct:.1f}%</div></div>"
    )


def _line_chart(series: List[Dict[str, Any]]) -> str:
    if not series:
        return "<div>No time-series comparison available.</div>"
    values: List[float] = []
    for row in series:
        for key in ("nav", "system_norm", "benchmark_norm"):
            if key in row:
                values.append(_safe_float(row.get(key, 0.0)))
    if not values:
        return "<div>No time-series comparison available.</div>"
    min_v = min(values)
    max_v = max(values)
    spread = max(max_v - min_v, 1e-9)

    def build_points(key: str) -> str:
        points: List[str] = []
        for idx, row in enumerate(series):
            x = 20 + (760 * idx / max(len(series) - 1, 1))
            y = 180 - (( _safe_float(row.get(key, 0.0)) - min_v) / spread) * 140
            points.append(f"{x:.1f},{y:.1f}")
        return " ".join(points)

    system_points = build_points("system_norm" if "system_norm" in series[0] else "nav")
    benchmark_points = build_points("benchmark_norm") if "benchmark_norm" in series[0] else ""
    labels = "".join(
        f"<div class='axis-label' style='left:{20 + (760 * idx / max(len(series) - 1, 1)):.1f}px'>{_safe_text(row.get('date'))}</div>"
        for idx, row in enumerate(series[:: max(len(series) // 5, 1)])
    )
    svg = [
        "<div class='chart-wrap'>",
        "<svg viewBox='0 0 800 220' class='line-chart'>",
        "<line x1='20' y1='180' x2='780' y2='180' class='axis' />",
        f"<polyline fill='none' stroke='#2f7f66' stroke-width='3' points='{system_points}' />",
    ]
    if benchmark_points:
        svg.append(f"<polyline fill='none' stroke='#28638b' stroke-width='3' stroke-dasharray='6 4' points='{benchmark_points}' />")
    svg.append("</svg>")
    svg.append(labels)
    svg.append("</div>")
    return "".join(svg)


def _render_html(payload: Dict[str, Any]) -> str:
    strategy_allocations = dict(payload.get("strategy_exposure", {}).get("strategy_allocations", {}) or {})
    funnel = dict(payload.get("candidate_funnel", {}) or {})
    budget = dict(payload.get("portfolio_budget", {}) or {})
    overfit = dict(payload.get("overfit_risk", {}) or {})
    plain = dict(payload.get("plain_language", {}) or {})
    equity = dict(payload.get("equity_curve_analysis", {}) or {})
    benchmark = dict(payload.get("benchmark_comparison", {}) or {})
    actual = dict(payload.get("actual_state_analysis", {}) or {})
    top_industries = list(dict(payload.get("positions_breakdown", {}) or {}).get("top_industries_by_weight", []) or [])
    chart_series = list(benchmark.get("comparison_series", []) or equity.get("series", []) or [])
    html = [
        "<html><head><meta charset='utf-8'><title>Strategy Audit</title>",
        "<style>",
        "body{font-family:Segoe UI,Microsoft YaHei,sans-serif;background:#f4f1ea;color:#1f2a30;margin:0;padding:24px;}",
        ".wrap{max-width:1100px;margin:0 auto;}",
        ".hero{background:linear-gradient(135deg,#fdf8ef,#e5efe9);border:1px solid #d9e4dc;border-radius:18px;padding:24px;}",
        ".grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:18px;}",
        ".grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:18px;}",
        ".card{background:#fffdf8;border:1px solid #e5ddd1;border-radius:16px;padding:18px;box-shadow:0 8px 24px rgba(31,42,48,.05);}",
        ".bar-row{display:grid;grid-template-columns:200px 1fr 70px;gap:10px;align-items:center;margin:8px 0;}",
        ".bar-track{height:12px;background:#ece7dc;border-radius:999px;overflow:hidden;}",
        ".bar-fill{height:100%;border-radius:999px;}",
        ".kv{display:grid;grid-template-columns:180px 1fr;gap:6px 12px;font-size:14px;}",
        ".pill{display:inline-block;padding:4px 10px;border-radius:999px;background:#1f2a30;color:#fff;font-size:12px;}",
        ".metric{font-size:32px;font-weight:700;margin:6px 0;}",
        ".sub{font-size:13px;color:#61717a;}",
        ".line-chart{width:100%;height:220px;display:block;}",
        ".axis{stroke:#c7c0b4;stroke-width:1;}",
        ".chart-wrap{position:relative;padding-bottom:18px;}",
        ".axis-label{position:absolute;bottom:0;transform:translateX(-50%);font-size:11px;color:#7a6f64;white-space:nowrap;}",
        "ul{margin:8px 0 0 18px;padding:0;} table{width:100%;border-collapse:collapse;font-size:14px;} th,td{padding:8px;border-bottom:1px solid #eee5d9;text-align:left;}",
        "@media (max-width: 900px){.grid,.grid-3{grid-template-columns:1fr;}.bar-row{grid-template-columns:120px 1fr 60px;}}",
        "</style></head><body><div class='wrap'>",
        f"<div class='hero'><h1>Strategy Audit</h1><div class='pill'>{_safe_text(payload.get('trade_date'))}</div>",
        f"<p>Primary strategy: <strong>{_safe_text(payload.get('strategy_exposure', {}).get('primary_strategy_key')) or 'unknown'}</strong></p>",
        f"<p>Overfit risk: <strong>{_safe_text(overfit.get('risk_level')).upper()}</strong> | Interpretation: {_safe_text(overfit.get('interpretation'))}</p></div>",
        "<div class='grid-3'>",
        f"<div class='card'><h2>System NAV</h2><div class='metric'>{_safe_float(equity.get('latest_nav', 0.0)):.3f}</div><div class='sub'>Current drawdown {_safe_float(equity.get('current_drawdown', 0.0)):.2%}</div></div>",
        f"<div class='card'><h2>20D Excess vs HS300</h2><div class='metric'>{_safe_float(benchmark.get('excess_20d', 0.0)):.2%}</div><div class='sub'>System 20D {_safe_float(equity.get('ret_20d', 0.0)):.2%} vs HS300 {_safe_float(benchmark.get('ret_20d', 0.0)):.2%}</div></div>",
        f"<div class='card'><h2>Live Account</h2><div class='metric'>{_safe_float(actual.get('account_total_asset', 0.0)):.0f}</div><div class='sub'>Cash {_safe_float(actual.get('account_cash', 0.0)):.0f}</div></div>",
        "</div>",
        "<div class='card' style='margin-top:18px;'><h2>System vs Benchmark</h2>",
        _line_chart(chart_series),
        "</div>",
        "<div class='grid'>",
        "<div class='card'><h2>Strategy Allocation</h2>",
        _bar("Industry Chain", _safe_float(strategy_allocations.get("industry_chain_expectation_gap", 0.0)), "#cf6a32"),
        _bar("Earnings", _safe_float(strategy_allocations.get("earnings_expectation_gap", 0.0)), "#2f7f66"),
        _bar("Asset Allocation", _safe_float(strategy_allocations.get("asset_allocation_risk_parity", 0.0)), "#28638b"),
        "</div>",
        "<div class='card'><h2>Deployment Funnel</h2>",
        _bar("Filter Drop", _safe_float(funnel.get("filter_drop_ratio", 0.0)), "#a94c4c"),
        _bar("Tech Reject", _safe_float(funnel.get("technical_reject_ratio", 0.0)), "#8b6b24"),
        _bar("Fill Ratio", _safe_float(budget.get("fill_ratio", 0.0)), "#4d7f38"),
        "</div>",
        "<div class='card'><h2>What Helped</h2><ul>" + "".join(f"<li>{_safe_text(item)}</li>" for item in list(plain.get("what_helped", []) or [])[:8]) + "</ul></div>",
        "<div class='card'><h2>What Hurt</h2><ul>" + "".join(f"<li>{_safe_text(item)}</li>" for item in list(plain.get("what_hurt", []) or [])[:8]) + "</ul></div>",
        "</div>",
        "<div class='grid'>",
        "<div class='card'><h2>Key Metrics</h2><div class='kv'>",
        f"<div>Candidate source</div><div>{_safe_text(funnel.get('candidate_source'))}</div>",
        f"<div>Kept / Dropped</div><div>{_safe_int(funnel.get('kept_rows'))} / {_safe_int(funnel.get('dropped_rows'))}</div>",
        f"<div>Allow / Reject</div><div>{_safe_int(funnel.get('allow_count'))} / {_safe_int(funnel.get('reject_count'))}</div>",
        f"<div>Final exposure</div><div>{_safe_float(budget.get('final_total_weight')):.2%}</div>",
        f"<div>Exposure cap</div><div>{_safe_float(budget.get('total_exposure_cap')):.2%}</div>",
        f"<div>Overfit reasons</div><div>{', '.join(list(overfit.get('reasons', []) or [])) or 'none'}</div>",
        "</div></div>",
        "<div class='card'><h2>Top Industries</h2><table><thead><tr><th>Industry</th><th>Weight</th></tr></thead><tbody>",
        "".join(
            f"<tr><td>{_safe_text(item.get('industry') or item.get('bucket'))}</td><td>{_safe_float(item.get('portfolio_weight', item.get('weight', 0.0))):.2%}</td></tr>"
            for item in top_industries[:8]
        ),
        "</tbody></table></div>",
        "</div>",
        "</div></body></html>",
    ]
    return "".join(html)


def build_strategy_audit_pack(
    config: Dict[str, Any],
    *,
    trade_date: str,
    release_doc: Dict[str, Any],
    pack_dir: Path,
) -> Dict[str, Any]:
    pack_dir = ensure_dir(pack_dir)
    release_artifacts = dict(release_doc.get("artifacts", {}) or {})
    summary_path = Path(_safe_text(release_artifacts.get("portfolio_summary_path")))
    target_path = Path(_safe_text(release_artifacts.get("target_positions_path")))
    summary = _load_json(summary_path) if summary_path.exists() else {}
    target_df = _read_csv(target_path) if target_path.exists() else pd.DataFrame()

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    funnel = _candidate_funnel(summary)
    budget = _portfolio_budget(summary, release_doc)
    positions = _positions_breakdown(target_df)
    strategy_exposure = _strategy_exposure(summary, target_df)
    equity = _equity_curve_analysis(summary)
    actual = _actual_state_analysis(config)
    benchmark = _benchmark_comparison(config, equity)
    overfit = _overfit_risk(summary, funnel, budget)
    plain = _plain_language(summary, strategy_exposure, funnel, overfit, equity, benchmark, actual)

    payload = {
        "generated_at": generated_at,
        "trade_date": trade_date,
        "release_id": _safe_text(release_doc.get("release_id")),
        "strategy_exposure": strategy_exposure,
        "candidate_funnel": funnel,
        "portfolio_budget": budget,
        "positions_breakdown": positions,
        "equity_curve_analysis": equity,
        "benchmark_comparison": benchmark,
        "actual_state_analysis": actual,
        "overfit_risk": overfit,
        "plain_language": plain,
        "limitations": [
            "realized_pnl_by_strategy_requires_position_level_strategy_tags_plus_historical_nav_or_fill_pnl",
            "current_audit_uses_release_and_execution_proxies_when_full_pnl_ledger_is_missing",
            "industry_vs_earnings_strategy_exposure_is_partial_when_position_rows_do_not_carry_explicit_strategy_tags",
        ],
    }
    json_path = pack_dir / "strategy_audit.json"
    html_path = pack_dir / "strategy_audit.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(_render_html(payload), encoding="utf-8")
    return {
        "generated_at": generated_at,
        "json_path": str(json_path),
        "html_path": str(html_path),
        "payload": payload,
    }
