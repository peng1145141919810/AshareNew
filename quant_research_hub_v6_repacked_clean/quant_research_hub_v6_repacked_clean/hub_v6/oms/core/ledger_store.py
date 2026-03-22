from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def _safe_read_csv(path: Path, columns: List[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = pd.NA
    return df[columns].copy()


def load_ledger_frame(path: Path, columns: List[str]) -> pd.DataFrame:
    return _safe_read_csv(path, columns=columns)


def write_latest_ledger(path: Path, frame: pd.DataFrame, columns: List[str], key_cols: List[str] | None = None) -> Path:
    out = frame.copy() if frame is not None else pd.DataFrame(columns=columns)
    for col in columns:
        if col not in out.columns:
            out[col] = pd.NA
    out = out[columns].copy()
    if key_cols:
        out = out.drop_duplicates(subset=key_cols, keep="last")
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def append_actual_state_daily(path: Path, frame: pd.DataFrame, columns: List[str]) -> Path:
    existing = _safe_read_csv(path, columns=columns)
    incoming = frame.copy() if frame is not None else pd.DataFrame(columns=columns)
    for col in columns:
        if col not in incoming.columns:
            incoming[col] = pd.NA
    if existing.empty:
        merged = incoming[columns].copy()
    elif incoming.empty:
        merged = existing.copy()
    else:
        merged = pd.concat([existing, incoming[columns]], ignore_index=True)
    merged["date"] = merged["date"].astype(str).str.slice(0, 19)
    merged["symbol"] = merged["symbol"].astype(str)
    merged = merged.drop_duplicates(subset=["date", "symbol"], keep="last")
    path.parent.mkdir(parents=True, exist_ok=True)
    merged[columns].to_csv(path, index=False, encoding="utf-8-sig")
    return path


def append_frame_rows(path: Path, frame: pd.DataFrame, columns: List[str], dedupe_cols: List[str] | None = None) -> Path:
    existing = _safe_read_csv(path, columns=columns)
    incoming = frame.copy() if frame is not None else pd.DataFrame(columns=columns)
    for col in columns:
        if col not in incoming.columns:
            incoming[col] = pd.NA
    if existing.empty:
        merged = incoming[columns].copy()
    elif incoming.empty:
        merged = existing.copy()
    else:
        merged = pd.concat([existing, incoming[columns]], ignore_index=True)
    if dedupe_cols:
        merged = merged.drop_duplicates(subset=dedupe_cols, keep="last")
    path.parent.mkdir(parents=True, exist_ok=True)
    merged[columns].to_csv(path, index=False, encoding="utf-8-sig")
    return path


def write_json_artifact(path: Path, payload: Dict[str, Any]) -> Path:
    def _json_default(value: Any):
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if value is pd.NA:
            return None
        return str(value)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return path


def timestamp_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
