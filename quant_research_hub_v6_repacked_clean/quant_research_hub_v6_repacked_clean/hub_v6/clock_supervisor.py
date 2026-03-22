from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

from .config_utils import ensure_dir, load_config
from .execution_manager import assess_execution_gate, run_execution_only
from .safety_guard import assess_system_safety
from .trading_clock import clock_now, trading_clock_snapshot


def _trade_clock_root(config: Dict[str, Any]) -> Path:
    return ensure_dir(Path(str(config.get("paths", {}).get("trade_clock_root", "") or "")).resolve())


def _state_path(config: Dict[str, Any]) -> Path:
    return _trade_clock_root(config) / "clock_state.json"


def _load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"dispatch_history": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"dispatch_history": {}}


def _save_state(path: Path, state: Dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)
    return path


def _already_dispatched(state: Dict[str, Any], trade_date: str, window_label: str, release_id: str) -> bool:
    history = dict(state.get("dispatch_history", {}) or {})
    day_bucket = dict(history.get(trade_date, {}) or {})
    entry = dict(day_bucket.get(window_label, {}) or {})
    return bool(entry) and str(entry.get("release_id", "") or "") == str(release_id or "")


def _mark_dispatched(state: Dict[str, Any], trade_date: str, window_label: str, release_id: str, dispatch_result: Dict[str, Any]) -> None:
    history = dict(state.get("dispatch_history", {}) or {})
    day_bucket = dict(history.get(trade_date, {}) or {})
    day_bucket[window_label] = {
        "release_id": str(release_id or ""),
        "dispatched_at": str(dispatch_result.get("execution_report", {}).get("timestamp", "") or dispatch_result.get("gate", {}).get("now", "")),
        "dispatch_path": str(dispatch_result.get("dispatch_path", "") or ""),
    }
    history[trade_date] = day_bucket
    state["dispatch_history"] = history


def run_trade_clock(
    config_path: Path,
    profile: str,
    poll_seconds: int | None = None,
    once: bool = False,
) -> Dict[str, Any]:
    config = load_config(config_path)
    project_root = config_path.resolve().parent.parent
    clock_cfg = dict(config.get("trade_clock", {}) or {})
    sleep_seconds = int(poll_seconds if poll_seconds is not None else clock_cfg.get("poll_seconds", 30) or 30)
    state_path = _state_path(config)
    state = _load_state(state_path)
    state["service"] = {
        "profile": str(profile or ""),
        "config_path": str(config_path),
        "poll_seconds": sleep_seconds,
    }

    while True:
        config = load_config(config_path)
        snapshot = trading_clock_snapshot(config=config)
        gate = assess_execution_gate(config=config, release_id="", ignore_window=False)
        safety = assess_system_safety(
            config=config,
            gate=gate,
            project_root=project_root,
            service_name="trade_clock_service",
            current_mode="clock_heartbeat",
            force_account_refresh=False,
        )
        release_info = dict(gate.get("release", {}) or {})
        window = dict(gate.get("active_execution_window", {}) or {})
        release_id = str(release_info.get("release_id", "") or "")
        trade_date = str(release_info.get("trade_date", "") or clock_now().date().isoformat())
        window_label = str(window.get("label", "no_window") or "no_window")
        state.pop("safety", None)
        state.update(
            {
                "last_heartbeat_at": str(snapshot.get("now", "") or clock_now().isoformat(timespec="seconds")),
                "heartbeat_time": str(snapshot.get("now", "") or clock_now().isoformat(timespec="seconds")),
                "market_stage": str(snapshot.get("market_stage", "") or ""),
                "calendar_ok": bool(snapshot.get("calendar_ok", False)),
                "is_trading_day": bool(snapshot.get("is_trading_day", False)),
                "active_execution_window": snapshot.get("active_execution_window"),
                "gate": gate,
                "service_name": "trade_clock_service",
                "service_alive": True,
                "current_mode": "clock_heartbeat",
                "precision_trade_enabled": bool(gate.get("precision_trade_enabled", False)),
                "gate_open": bool(gate.get("should_execute", False)),
                "gate_reason": str(gate.get("reason", "") or ""),
                "system_mode": str(safety.get("system_mode", "") or ""),
                "market_safety_regime": str(safety.get("market_safety_regime", "") or ""),
                "manual_halt": bool(safety.get("manual_halt", False)),
                "manual_reduce_only": bool(safety.get("manual_reduce_only", False)),
                "release_age_seconds": safety.get("state", {}).get("release_age_seconds"),
                "account_state_age_seconds": safety.get("state", {}).get("account_state_age_seconds"),
                "position_sync_age_seconds": safety.get("state", {}).get("position_sync_age_seconds"),
                "system_state_path": str(_trade_clock_root(config) / "system_safety_state.json"),
                "incident_log_path": str(_trade_clock_root(config) / "incident_log.jsonl"),
                "manual_overrides_path": str(_trade_clock_root(config) / "manual_overrides.json"),
            }
        )
        dispatch_result = None
        if bool(gate.get("should_execute", False)) and bool(safety.get("allow_execution", False)) and not _already_dispatched(state, trade_date=trade_date, window_label=window_label, release_id=release_id):
            dispatch_result = run_execution_only(
                config_path=config_path,
                release_id=release_id,
                ignore_window=False,
                gate_only=False,
                trigger_label=window_label,
                trigger_source="clock_supervisor",
            )
            state["last_dispatch"] = dispatch_result
            if str(dispatch_result.get("status", "") or "") == "executed":
                _mark_dispatched(state, trade_date=trade_date, window_label=window_label, release_id=release_id, dispatch_result=dispatch_result)
        elif bool(gate.get("should_execute", False)) and not bool(safety.get("allow_execution", False)):
            state["last_dispatch_skip"] = {
                "reason": "safety_blocked",
                "trade_date": trade_date,
                "window_label": window_label,
                "release_id": release_id,
                "system_mode": str(safety.get("system_mode", "") or ""),
                "market_safety_regime": str(safety.get("market_safety_regime", "") or ""),
            }
        elif bool(gate.get("should_execute", False)):
            state["last_dispatch_skip"] = {
                "reason": "already_dispatched",
                "trade_date": trade_date,
                "window_label": window_label,
                "release_id": release_id,
            }
        _save_state(state_path, state)
        print(
            json.dumps(
                {
                    "heartbeat": state.get("last_heartbeat_at", ""),
                    "market_stage": state.get("market_stage", ""),
                    "window": state.get("active_execution_window"),
                    "release_id": release_id,
                    "should_execute": bool(gate.get("should_execute", False)),
                    "system_mode": str(safety.get("system_mode", "") or ""),
                    "market_regime": str(safety.get("market_safety_regime", "") or ""),
                    "dispatch": str(dispatch_result.get("status", "") if dispatch_result else ""),
                },
                ensure_ascii=False,
            )
        )
        if once:
            return state
        time.sleep(max(sleep_seconds, 10))
