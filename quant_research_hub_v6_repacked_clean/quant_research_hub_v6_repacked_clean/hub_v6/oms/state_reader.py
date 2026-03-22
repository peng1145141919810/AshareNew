from __future__ import annotations

import json
from typing import Any, Dict

from .paths import build_oms_paths


def load_latest_oms_actual_state(config: Dict[str, Any]) -> Dict[str, Any]:
    path = build_oms_paths(config)["latest_actual_portfolio_state"]
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_latest_oms_control_feedback(config: Dict[str, Any]) -> Dict[str, Any]:
    path = build_oms_paths(config)["control_feedback_latest"]
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
