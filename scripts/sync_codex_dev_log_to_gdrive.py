from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_POLL_SECONDS = 5.0
DEFAULT_BACKUP_ROOT = Path(r"H:\我的云端硬盘\AshareCSharp_backups")
DEFAULT_MIRROR_DIR = DEFAULT_BACKUP_ROOT / "codex_dev_log_mirror"
WINDOWS_MUTEX_NAME = "Local\\AshareCSharpCodexDevLogSync"
ERROR_ALREADY_EXISTS = 183
IDLE_PRIORITY_CLASS = 0x00000040


class WindowsInstanceGuard:
    def __init__(self, mutex_name: str) -> None:
        self.mutex_name = mutex_name
        self.kernel32 = getattr(ctypes, "windll", None)
        self.handle: Optional[int] = None

    def acquire(self) -> None:
        if self.kernel32 is None:
            return
        self.kernel32.kernel32.SetLastError(0)
        handle = self.kernel32.kernel32.CreateMutexW(None, False, self.mutex_name)
        if not handle:
            raise OSError("failed to create Windows mutex for single-instance guard")
        last_error = self.kernel32.kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            self.kernel32.kernel32.CloseHandle(handle)
            raise RuntimeError(f"another sync watcher is already running: {self.mutex_name}")
        self.handle = handle

    def release(self) -> None:
        if self.kernel32 is None or self.handle is None:
            return
        self.kernel32.kernel32.CloseHandle(self.handle)
        self.handle = None


def lower_process_priority() -> None:
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return
    handle = windll.kernel32.GetCurrentProcess()
    windll.kernel32.SetPriorityClass(handle, IDLE_PRIORITY_CLASS)


@dataclass
class FileSnapshot:
    modified_ns: int
    size: int
    digest: str


def stat_snapshot(path: Path) -> FileSnapshot:
    stat = path.stat()
    return FileSnapshot(modified_ns=stat.st_mtime_ns, size=stat.st_size, digest="")


def finalize_snapshot(path: Path, snapshot: FileSnapshot) -> FileSnapshot:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return FileSnapshot(modified_ns=snapshot.modified_ns, size=snapshot.size, digest=digest)


def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dst.with_suffix(dst.suffix + ".tmp")
    shutil.copy2(src, tmp_path)
    os.replace(tmp_path, dst)


def write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)


def sync_log(source: Path, mirror_dir: Path, snapshot: FileSnapshot, verbose: bool) -> dict:
    latest_path = mirror_dir / "CODEX_DEV_LOG.md"
    archive_dir = mirror_dir / "history"
    archive_name = datetime.now().strftime("CODEX_DEV_LOG_%Y%m%d_%H%M%S.md")
    archive_path = archive_dir / archive_name
    state_path = mirror_dir / "sync_state.json"

    safe_copy(source, latest_path)
    safe_copy(source, archive_path)

    payload = {
        "source_path": str(source),
        "latest_copy_path": str(latest_path),
        "last_archive_path": str(archive_path),
        "last_synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_modified_ns": snapshot.modified_ns,
        "source_size": snapshot.size,
        "source_sha256": snapshot.digest,
    }
    write_state(state_path, payload)

    if verbose:
        print(f"[sync] mirrored {source} -> {latest_path}")
        print(f"[sync] archived copy -> {archive_path}")
        print(f"[sync] state updated -> {state_path}")

    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mirror CODEX_DEV_LOG.md into Google Drive when it changes.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "CODEX_DEV_LOG.md",
        help="Path to the source CODEX_DEV_LOG.md file.",
    )
    parser.add_argument(
        "--mirror-dir",
        type=Path,
        default=DEFAULT_MIRROR_DIR,
        help="Google Drive directory that stores the latest mirror and timestamped history copies.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=DEFAULT_POLL_SECONDS,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Perform one sync pass and exit.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print sync activity.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    source = args.source.resolve()
    mirror_dir = args.mirror_dir.resolve()
    if not source.exists():
        raise FileNotFoundError(f"source file does not exist: {source}")

    lower_process_priority()
    guard = WindowsInstanceGuard(WINDOWS_MUTEX_NAME)
    if not args.once:
        guard.acquire()

    stop_requested = False

    def handle_stop(_signum: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_stop)

    try:
        last_snapshot: Optional[FileSnapshot] = None
        while not stop_requested:
            current_stat = stat_snapshot(source)
            needs_sync = (
                last_snapshot is None
                or current_stat.modified_ns != last_snapshot.modified_ns
                or current_stat.size != last_snapshot.size
            )
            if needs_sync:
                current_snapshot = finalize_snapshot(source, current_stat)
                if last_snapshot is None or current_snapshot.digest != last_snapshot.digest:
                    sync_log(source, mirror_dir, current_snapshot, verbose=args.verbose)
                elif current_snapshot.modified_ns != last_snapshot.modified_ns or current_snapshot.size != last_snapshot.size:
                    sync_log(source, mirror_dir, current_snapshot, verbose=args.verbose)
                last_snapshot = current_snapshot

            if args.once:
                break
            time.sleep(max(args.poll_seconds, 1.0))
    finally:
        guard.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
