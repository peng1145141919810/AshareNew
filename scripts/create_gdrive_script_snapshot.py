from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


DEFAULT_BACKUP_ROOT = Path(r"H:\我的云端硬盘\AshareCSharp_backups")
EXCLUDED_DIR_NAMES = {
    ".git",
    ".idea",
    ".venv",
    "venvs",
    "__pycache__",
    "data",
    "outputs",
}
EXCLUDED_FILE_NAMES = {
    "local_settings.py",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def slugify_label(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(text or "").strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "manual"


def next_version_parts(script_versions_dir: Path) -> tuple[str, int]:
    today = datetime.now().strftime("%Y%m%d")
    max_revision = 0
    pattern = re.compile(rf"^AshareCSharp_script_{today}_r(\d{{3}})(?:_|$)", re.IGNORECASE)
    if script_versions_dir.exists():
        for child in script_versions_dir.iterdir():
            if not child.is_dir():
                continue
            match = pattern.match(child.name)
            if match:
                max_revision = max(max_revision, int(match.group(1)))
    return today, max_revision + 1


def should_skip(path: Path, repo_root: Path) -> bool:
    relative = path.relative_to(repo_root)
    for part in relative.parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.name.startswith("hub_config.v6.runtime.") and path.suffix.lower() == ".json":
        return True
    if path.name == "gmtrade_runtime_config.autogen.json":
        return True
    return False


def copy_repo_scripts(repo_root: Path, destination_root: Path) -> int:
    copied = 0
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path=path, repo_root=repo_root):
            continue
        relative = path.relative_to(repo_root)
        target = destination_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def run_git(args: list[str], repo_root: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_catalog(
    catalog_path: Path,
    version_id: str,
    snapshot_dir: Path,
    label: str,
    head_commit: str,
    branch: str,
    copied_files: int,
) -> None:
    if not catalog_path.exists():
        write_text(
            catalog_path,
            "# AshareCSharp Version Catalog\n\n"
            "| Version ID | Timestamp | Label | Branch | Head | Snapshot Path | Files |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n",
        )
    row = (
        f"| {version_id} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"{label} | {branch or '-'} | {head_commit[:12] or '-'} | {snapshot_dir} | {copied_files} |\n"
    )
    with catalog_path.open("a", encoding="utf-8") as handle:
        handle.write(row)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Google Drive snapshot of the current AshareC# script workspace.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT)
    parser.add_argument("--label", type=str, default="manual")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    backup_root = args.backup_root.resolve()
    label_slug = slugify_label(args.label)
    script_versions_dir = backup_root / "script_versions"
    date_text, revision = next_version_parts(script_versions_dir=script_versions_dir)
    version_id = f"SCRIPT-{date_text}-R{revision:03d}"
    snapshot_dir = script_versions_dir / f"AshareCSharp_script_{date_text}_r{revision:03d}_{label_slug}"
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    copied_files = copy_repo_scripts(repo_root=repo_root, destination_root=snapshot_dir)
    head_commit = run_git(["rev-parse", "HEAD"], repo_root).strip()
    branch = run_git(["branch", "--show-current"], repo_root).strip()

    manifest = {
        "version_id": version_id,
        "label": args.label,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repo_root": str(repo_root),
        "snapshot_dir": str(snapshot_dir),
        "head_commit": head_commit,
        "branch": branch,
        "copied_files": copied_files,
    }
    write_text(snapshot_dir / "snapshot_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    append_catalog(
        catalog_path=backup_root / "VERSION_CATALOG.md",
        version_id=version_id,
        snapshot_dir=snapshot_dir,
        label=args.label,
        head_commit=head_commit,
        branch=branch,
        copied_files=copied_files,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
