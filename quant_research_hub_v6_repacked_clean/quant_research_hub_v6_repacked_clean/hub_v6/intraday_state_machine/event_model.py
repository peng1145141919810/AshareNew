from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd


EVENT_TYPES = [
    "phase_entered",
    "phase_exited",
    "release_loaded",
    "market_state_refreshed",
    "safety_changed",
    "account_health_stale",
    "account_health_restored",
    "intent_admitted",
    "order_submitted",
    "order_acknowledged",
    "partial_fill_detected",
    "fill_completed",
    "stale_pending_detected",
    "replace_required_detected",
    "cancel_requested",
    "cancel_confirmed",
    "manual_override_applied",
    "midday_plan_published",
    "close_reconcile_started",
    "archive_completed",
]


def build_intraday_events(
    *,
    trade_date: str,
    release_id: str,
    namespace: str,
    phase_state: Dict[str, Any],
    safety_state: Dict[str, Any],
    intent_frame: pd.DataFrame,
    symbol_frame: pd.DataFrame,
    now_ts: datetime,
) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    def add(event_type: str, timestamp: str, stock_code: str = "", payload: Dict[str, Any] | None = None) -> None:
        events.append(
            {
                "event_type": event_type,
                "timestamp": str(timestamp or now_ts.isoformat(timespec="seconds")),
                "trade_date": str(trade_date or ""),
                "release_id": str(release_id or ""),
                "namespace": str(namespace or "main"),
                "stock_code": str(stock_code or ""),
                "payload": dict(payload or {}),
            }
        )

    current_phase = str(phase_state.get("current_phase", "") or "")
    previous_phase = str(phase_state.get("previous_phase", "") or "")
    if current_phase:
        add("phase_entered", str(phase_state.get("updated_at", "") or now_ts.isoformat(timespec="seconds")), payload={"phase": current_phase})
    if previous_phase:
        add("phase_exited", str(phase_state.get("updated_at", "") or now_ts.isoformat(timespec="seconds")), payload={"phase": previous_phase})
    if release_id:
        add("release_loaded", str(phase_state.get("updated_at", "") or now_ts.isoformat(timespec="seconds")), payload={"release_id": release_id})
    add(
        "safety_changed",
        str(phase_state.get("updated_at", "") or now_ts.isoformat(timespec="seconds")),
        payload={
            "safety_mode": str(phase_state.get("safety_mode", "") or ""),
            "system_mode": str(safety_state.get("system_mode", "") or ""),
            "market_regime": str(safety_state.get("market_safety_regime", "") or ""),
        },
    )
    if str(safety_state.get("account_snapshot_health", "") or "").lower() == "stale":
        add("account_health_stale", now_ts.isoformat(timespec="seconds"))
    else:
        add("account_health_restored", now_ts.isoformat(timespec="seconds"))
    if str(phase_state.get("midday_decision", "") or "").strip():
        add("midday_plan_published", str(phase_state.get("updated_at", "") or now_ts.isoformat(timespec="seconds")), payload={"decision": str(phase_state.get("midday_decision", "") or "")})

    if intent_frame is not None and not intent_frame.empty:
        for _, row in intent_frame.iterrows():
            stock_code = str(row.get("stock_code", "") or "")
            ts = str(row.get("updated_at", "") or now_ts.isoformat(timespec="seconds"))
            state = str(row.get("intent_state", "") or "")
            if state == "admitted":
                add("intent_admitted", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or "")})
            elif state == "submitted":
                add("order_submitted", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "order_id": str(row.get("order_id", "") or "")})
            elif state == "acknowledged":
                add("order_acknowledged", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "order_id": str(row.get("order_id", "") or "")})
            elif state == "partial_fill":
                add("partial_fill_detected", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "fill_ratio": row.get("fill_ratio", 0.0)})
            elif state == "filled":
                add("fill_completed", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "fill_ratio": row.get("fill_ratio", 1.0)})
            elif state == "stale_pending":
                add("stale_pending_detected", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "stale_reason": str(row.get("stale_reason", "") or "")})
            elif state == "replace_required":
                add("replace_required_detected", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "parent_intent_id": str(row.get("parent_intent_id", "") or "")})
            elif state == "cancel_requested":
                add("cancel_requested", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "order_id": str(row.get("order_id", "") or "")})
            elif state == "cancelled":
                add("cancel_confirmed", ts, stock_code, {"intent_id": str(row.get("intent_id", "") or ""), "order_id": str(row.get("order_id", "") or "")})

    if symbol_frame is not None and not symbol_frame.empty:
        for _, row in symbol_frame.iterrows():
            if str(row.get("freeze_reason", "") or "").strip():
                add("manual_override_applied", str(row.get("updated_at", "") or now_ts.isoformat(timespec="seconds")), str(row.get("stock_code", "") or ""), {"freeze_reason": str(row.get("freeze_reason", "") or ""), "symbol_state": str(row.get("symbol_state", "") or "")})
    if current_phase == "close_reconcile":
        add("close_reconcile_started", str(phase_state.get("updated_at", "") or now_ts.isoformat(timespec="seconds")))
    if current_phase == "postclose_archive":
        add("archive_completed", str(phase_state.get("updated_at", "") or now_ts.isoformat(timespec="seconds")))
    return events
