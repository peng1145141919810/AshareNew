from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .config_utils import ensure_dir, load_config
from .constraint_brain import evaluate as brain_evaluate, apply_to_config as brain_apply
from .execution_llm_review import review_execution_plan
from .execution_bridge_runner import execution_policy, run_execution_bridge
from .market_state import load_latest_market_state
from .portfolio_release import load_latest_release, load_release_by_id, record_release_execution
from .safety_guard import (
    assess_system_safety,
    load_system_safety_state,
    record_incident,
    save_system_safety_state,
)
from .sql_store import mirror_runtime_json_artifact
from .trading_clock import clock_now, current_execution_window, is_trading_day, market_stage


def _trade_clock_root(config: Dict[str, Any]) -> Path:
    return ensure_dir(Path(str(config.get("paths", {}).get("trade_clock_root", "") or "")).resolve())


def _mirror_json_to_sql(config: Dict[str, Any], path: Path, payload: Dict[str, Any]) -> None:
    mirror_runtime_json_artifact(config, path, payload)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_iso(text: str) -> datetime | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return None


def _latest_t_audit_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    audit_cfg = dict(config.get("t_audit", {}) or {})
    root = Path(str(audit_cfg.get("artifact_root", "") or "")).resolve()
    path = root / "latest" / "latest_t_audit.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_release(config: Dict[str, Any], release_id: str = "") -> Dict[str, Any]:
    from . import portfolio_release as _release_mod

    _release_mod._load_json._active_config = config
    if str(release_id).strip():
        return load_release_by_id(config=config, release_id=str(release_id).strip())
    return load_latest_release(config=config)


def _load_portfolio_summary(release_doc: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = dict(release_doc.get("artifacts", {}) or {})
    summary_path = Path(str(artifacts.get("portfolio_summary_path", "") or "")).resolve() if str(artifacts.get("portfolio_summary_path", "") or "").strip() else Path()
    if not summary_path.exists():
        return {}
    return _load_json(summary_path)


def _market_state_runtime(release_doc: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(release_doc.get("market_state", {}) or {})
    if payload:
        return payload
    return dict(load_latest_market_state(config=config, allow_build=False) or {})




def _account_snapshot_from_safety(safety: Dict[str, Any]) -> Dict[str, Any]:
    latest = dict(safety.get("latest_account_health", {}) or {})
    account_state = dict(latest.get("account_state", {}) or {})
    return {
        "account_id": str(account_state.get("account_id") or latest.get("account_id") or ""),
        "cash": float(account_state.get("cash", latest.get("cash", 0.0)) or 0.0),
        "nav": float(account_state.get("nav", latest.get("total_asset", 0.0)) or 0.0),
        "positions_count": int(latest.get("positions_count", len(list(account_state.get("positions", []) or []))) or 0),
    }


def _load_intraday_phase_state(config: Dict[str, Any]) -> Dict[str, Any]:
    return _load_json(_trade_clock_root(config) / "intraday_state" / "latest" / "intraday_phase_state.json")


def assess_execution_gate(
    config: Dict[str, Any],
    release_id: str = "",
    ignore_window: bool = False,
    now: datetime | None = None,
) -> Dict[str, Any]:
    current_dt = now or clock_now(str(config.get("trade_clock", {}).get("timezone", "Asia/Shanghai") or "Asia/Shanghai"))
    policy = execution_policy(config)
    account_mode = str(policy.get("account_mode", "simulation"))
    precision_trade_enabled = bool(policy.get("precision_trade_enabled", False))
    gate: Dict[str, Any] = {
        "now": current_dt.isoformat(timespec="seconds"),
        "market_stage": market_stage(current_dt),
        "ignore_window": bool(ignore_window),
        "account_mode": account_mode,
        "precision_trade_enabled": precision_trade_enabled,
    }
    try:
        release_doc = _load_release(config=config, release_id=release_id)
    except Exception as exc:
        gate.update({
            "ok": False,
            "should_execute": False,
            "reason": f"release_unavailable: {exc}",
            "release": None,
        })
        return gate

    trading_day_info = is_trading_day(config=config, target_date=current_dt.date())
    window = current_execution_window(config=config, now=current_dt)
    valid_after = _parse_iso(str(release_doc.get("valid_after", "") or ""))
    expires_at = _parse_iso(str(release_doc.get("expires_at", "") or ""))
    release_trade_date = str(release_doc.get("trade_date", "") or "")
    simulation_ready = bool(release_doc.get("simulation_ready", True))
    if account_mode == "simulation":
        time_window_ok = True
        valid_after_ok = True
        not_expired = True
        trade_date_ok = True
        calendar_ok = True
        should_execute = bool(simulation_ready)
        reason = "simulation_ready" if should_execute else "simulation_ready_false"
    else:
        time_window_ok = bool(ignore_window or window is not None)
        valid_after_ok = bool(ignore_window or valid_after is None or current_dt >= valid_after)
        not_expired = bool(expires_at is None or current_dt <= expires_at)
        trade_date_ok = bool(release_trade_date == current_dt.date().isoformat())
        calendar_ok = bool(trading_day_info.get("ok", False) and trading_day_info.get("is_trading_day", False))
        should_execute = all([
            precision_trade_enabled,
            calendar_ok,
            trade_date_ok,
            simulation_ready,
            time_window_ok,
            valid_after_ok,
            not_expired,
        ])
        if not precision_trade_enabled:
            reason = "precision_trade_disabled"
        else:
            reason = "eligible" if should_execute else "gate_blocked"
    gate.update(
        {
            "ok": True,
            "should_execute": bool(should_execute),
            "calendar_ok": calendar_ok,
            "release_trade_date": release_trade_date,
            "trade_date_ok": trade_date_ok,
            "simulation_ready": simulation_ready,
            "time_window_ok": time_window_ok,
            "valid_after_ok": valid_after_ok,
            "not_expired": not_expired,
            "active_execution_window": {
                "label": window.label,
                "start": window.start.strftime("%H:%M:%S"),
                "end": window.end.strftime("%H:%M:%S"),
            } if window else None,
            "release": {
                "release_id": str(release_doc.get("release_id", "") or ""),
                "trade_date": release_trade_date,
                "manifest_path": str(release_doc.get("artifacts", {}).get("manifest_path", "") or ""),
                "target_positions_path": str(release_doc.get("artifacts", {}).get("target_positions_path", "") or ""),
                "profile": str(release_doc.get("profile", "") or ""),
                "source_mode": str(release_doc.get("source_mode", "") or ""),
            },
            "reason": reason,
        }
    )
    return gate


def run_execution_only(
    config_path: Path,
    release_id: str = "",
    ignore_window: bool = False,
    gate_only: bool = False,
    trigger_label: str = "manual",
    trigger_source: str = "manual",
    intent_source: str = "release",
    intraday_tactical_orders_path: str = "",
) -> Dict[str, Any]:
    config = load_config(config_path)
    tac_path = str(intraday_tactical_orders_path or "").strip()
    if tac_path:
        config = dict(config)
        config["intraday_tactical_orders_path"] = tac_path
    project_root = config_path.resolve().parent.parent
    policy = execution_policy(config)
    namespace = str(policy.get("namespace", "main") or "main").strip() or "main"
    shadow_run = bool(policy.get("shadow_run", False))
    gate = assess_execution_gate(config=config, release_id=release_id, ignore_window=ignore_window)
    safety = assess_system_safety(
        config=config,
        gate=gate,
        project_root=project_root,
        service_name="execution_only",
        current_mode="execution_only",
        force_account_refresh=bool(not gate_only),
    )
    if gate_only:
        return {
            "ok": bool(gate.get("ok", False)),
            "status": "gate_only",
            "gate": gate,
            "safety": safety,
            "execution_namespace": namespace,
            "allow_unfinished_orders_reconcile": bool(config.get("execution_policy", {}).get("allow_unfinished_orders_reconcile", False)),
            "shadow_run": shadow_run,
            "market_state": _market_state_runtime(release_doc=_load_release(config=config, release_id=release_id), config=config) if bool(gate.get("ok", False)) else {},
        }
    tactical_continue = str(intent_source or "") == "intraday_tactical" and bool(tac_path)
    if not bool(gate.get("should_execute", False)) and not shadow_run and not tactical_continue:
        release_doc = _load_release(config=config, release_id=release_id) if bool(gate.get("ok", False)) else {}
        return {
            "ok": bool(gate.get("ok", False)),
            "status": "skipped",
            "gate": gate,
            "safety": safety,
            "execution_namespace": namespace,
            "allow_unfinished_orders_reconcile": bool(config.get("execution_policy", {}).get("allow_unfinished_orders_reconcile", False)),
            "shadow_run": shadow_run,
            "market_state": _market_state_runtime(release_doc=release_doc, config=config) if release_doc else {},
        }
    if not bool(safety.get("allow_execution", False)) and not shadow_run:
        release_doc = _load_release(config=config, release_id=release_id) if bool(gate.get("ok", False)) else {}
        return {
            "ok": False,
            "status": "safety_blocked",
            "gate": gate,
            "safety": safety,
            "execution_namespace": namespace,
            "allow_unfinished_orders_reconcile": bool(config.get("execution_policy", {}).get("allow_unfinished_orders_reconcile", False)),
            "shadow_run": shadow_run,
            "market_state": _market_state_runtime(release_doc=release_doc, config=config) if release_doc else {},
        }

    release_doc = _load_release(config=config, release_id=release_id)
    portfolio_summary = _load_portfolio_summary(release_doc)
    market_state = _market_state_runtime(release_doc=release_doc, config=config)
    account_snapshot = _account_snapshot_from_safety(safety)

    # LLM review — runs before constraint brain so brain can consume its output
    llm_review = review_execution_plan(
        config=config,
        release_doc=release_doc,
        market_state=market_state,
        account_state=account_snapshot,
        safety=safety,
    )

    # ConstraintBrain: 收所有信号，一次性决策，产出合并好的 config_overrides
    brain_decision = brain_evaluate(
        config=config,
        safety=safety,
        market_state=market_state,
        llm_review=llm_review,
        account_snapshot=account_snapshot,
        intraday_state=_load_intraday_phase_state(config),
        clock_snapshot=_load_json(_trade_clock_root(config) / "clock_account_snapshot.json"),
        trade_discipline=dict(portfolio_summary.get("trade_discipline", {}) or {}),
    )
    execution_config = brain_apply(config, brain_decision)

    release_context = {
        "release_id": str(release_doc.get("release_id", "") or ""),
        "trade_date": str(release_doc.get("trade_date", "") or ""),
        "profile": str(release_doc.get("profile", "") or ""),
        "source_mode": str(release_doc.get("source_mode", "") or ""),
        "manifest_path": str(release_doc.get("artifacts", {}).get("manifest_path", "") or ""),
        "trigger_label": str(trigger_label or "manual"),
        "trigger_source": str(trigger_source or "manual"),
        "system_mode": str(safety.get("system_mode", "") or ""),
        "market_safety_regime": str(safety.get("market_safety_regime", "") or ""),
        "market_regime": str(market_state.get("market_regime", "") or ""),
        "style_bias": str(market_state.get("style_bias", "") or ""),
        "mechanism_bias": str(market_state.get("mechanism_bias", "") or ""),
        "new_position_policy": str(market_state.get("new_position_policy", "") or ""),
        "execution_namespace": namespace,
        "shadow_run": shadow_run,
        "shadow_reason": "shadow_run_bypass" if shadow_run and (not bool(gate.get("should_execute", False)) or not bool(safety.get("allow_execution", False))) else "",
        "intent_source": str(intent_source or "release"),
        "intraday_tactical_orders_path": str(tac_path or ""),
        "constraint_brain": brain_decision.to_audit_dict(),
        "llm_execution_review": {
            "enabled": bool(llm_review.get("enabled", False)),
            "applied": bool(llm_review.get("applied", False)),
            "provider": str(llm_review.get("provider", "") or ""),
            "model": str(llm_review.get("model", "") or ""),
            "artifact_path": str(llm_review.get("artifact_path", "") or ""),
            "review_summary": str((llm_review.get("review") or {}).get("review_summary", "") or ""),
            "risk_level": str((llm_review.get("review") or {}).get("risk_level", "") or ""),
            "candidate_pool_assessment": dict((llm_review.get("review") or {}).get("candidate_pool_assessment", {}) or {}),
        },
        "trade_discipline": dict(portfolio_summary.get("trade_discipline", {}) or {}),
    }
    latest_t_audit = _latest_t_audit_summary(config)
    if bool(latest_t_audit.get("available", False)):
        top_suited_mechanism = str(latest_t_audit.get("top_suited_mechanism", "") or "").strip()
        if top_suited_mechanism and top_suited_mechanism not in {"unknown", "unlabeled"}:
            release_context["preferred_t_mechanism"] = top_suited_mechanism
            release_context["preferred_t_mechanism_source"] = "latest_t_audit"
        release_context["t_audit_top_reject_reason"] = str(latest_t_audit.get("top_reject_reason", "") or "")
        release_context["t_audit_policy_change_suggestions"] = list(latest_t_audit.get("policy_change_suggestions", []) or [])[:3]

    if tac_path:
        execution_config = dict(execution_config)
        execution_config["intraday_tactical_orders_path"] = tac_path
    try:
        report = run_execution_bridge(
            config=execution_config,
            project_root=project_root,
            explicit_portfolio_path=str(release_doc.get("artifacts", {}).get("target_positions_path", "") or ""),
            release_context=release_context,
            intraday_tactical_orders_path=str(config.get("intraday_tactical_orders_path", "") or ""),
        )
    except Exception as exc:
        state = load_system_safety_state(config)
        state["updated_at"] = datetime.now().isoformat(timespec="seconds")
        state["system_mode"] = "HALT"
        state["halt_reason"] = "execution_bridge_error"
        state["last_incident_level"] = "error"
        state["last_incident_type"] = "execution_bridge_error"
        save_system_safety_state(config=config, state=state)
        record_incident(
            config=config,
            incident_type="execution_bridge_error",
            severity="error",
            component="execution_manager",
            reason=str(exc),
            action_taken="execution_stopped",
            requires_human_action=True,
            before_system_mode=str(safety.get("system_mode", "") or ""),
            after_system_mode="HALT",
            before_market_regime=str(safety.get("market_safety_regime", "") or ""),
            after_market_regime=str(safety.get("market_safety_regime", "") or ""),
            context_snapshot_ref=str(_trade_clock_root(config) / "system_safety_state.json"),
        )
        return {
            "ok": False,
            "status": "execution_error",
            "gate": gate,
            "safety": safety,
            "execution_namespace": namespace,
            "allow_unfinished_orders_reconcile": bool(config.get("execution_policy", {}).get("allow_unfinished_orders_reconcile", False)),
            "shadow_run": shadow_run,
            "error": str(exc),
        }
    if not bool(report.get("ok", False)):
        return {
            "ok": False,
            "status": "execution_error",
            "gate": gate,
            "safety": safety,
            "execution_namespace": namespace,
            "allow_unfinished_orders_reconcile": bool(config.get("execution_policy", {}).get("allow_unfinished_orders_reconcile", False)),
            "shadow_run": shadow_run,
            "market_state": market_state,
            "release": release_context,
            "error": str(report.get("parse_error", "") or report.get("error", "") or "execution_bridge_report_not_ok"),
            "execution_report": report,
        }
    dispatch_root = ensure_dir(_trade_clock_root(config) / "dispatches" / namespace / datetime.now().strftime("%Y%m%d_%H%M%S"))
    dispatch_path = dispatch_root / "execution_dispatch.json"
    dispatch_doc = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "trigger_label": str(trigger_label or "manual"),
        "trigger_source": str(trigger_source or "manual"),
        "gate": gate,
        "safety": safety,
        "release": release_context,
        "llm_execution_review": llm_review,
        "execution_report": report,
        "allow_unfinished_orders_reconcile": bool(config.get("execution_policy", {}).get("allow_unfinished_orders_reconcile", False)),
    }
    dispatch_path.write_text(json.dumps(dispatch_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    _mirror_json_to_sql(config, dispatch_path, dispatch_doc)
    latest_path = _trade_clock_root(config) / "latest_execution_dispatch.json"
    if namespace != "main":
        latest_path = _trade_clock_root(config) / f"latest_execution_dispatch.{namespace}.json"
    latest_path.write_text(json.dumps(dispatch_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    _mirror_json_to_sql(config, latest_path, dispatch_doc)
    history_paths: Dict[str, Any] = {}
    if not shadow_run:
        record_release_execution._active_config = config
        history_paths = record_release_execution(
            release_doc=release_doc,
            execution_record={
                "timestamp": dispatch_doc["timestamp"],
                "trigger_label": str(trigger_label or "manual"),
                "trigger_source": str(trigger_source or "manual"),
                "execution_report_path": str(report.get("execution_report_path", "") or ""),
                "dispatch_path": str(dispatch_path),
                "n_orders": int(report.get("n_orders", 0) or 0),
                "n_fills": int(report.get("n_fills", 0) or 0),
            },
        )
    return {
        "ok": True,
        "status": "shadow_executed" if shadow_run else "executed",
        "gate": gate,
        "safety": safety,
        "execution_namespace": namespace,
        "shadow_run": shadow_run,
        "market_state": market_state,
        "release": release_context,
        "dispatch_path": str(dispatch_path),
        "latest_dispatch_path": str(latest_path),
        "release_execution_paths": history_paths,
        "execution_report": report,
    }
