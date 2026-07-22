#!/usr/bin/env python3
"""Build and verify the filtered public formal-Recipe runtime.

The upstream checkout intentionally retains audit-only material.  This tool
applies ``public-install-profile.json`` into a new directory, overlays the
public SKILL/manifest, and writes a deterministic byte inventory.  It never
overwrites an existing destination.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = SKILL_ROOT / "public-install-profile.json"
RUNTIME_MANIFEST = "PUBLIC_RUNTIME_MANIFEST.json"
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_profile() -> dict[str, Any]:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    required = {"schema_version", "profile_id", "excluded_paths", "overlay_files"}
    missing = sorted(required - set(profile))
    if missing:
        raise ValueError(f"public install profile missing fields: {missing}")
    return profile


def safe_relative(value: str, *, label: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe {label}: {value}")
    return path


def parse_manifest_identity(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    name = re.search(r"(?m)^name:\s*([^\s#]+)\s*$", text)
    version = re.search(r"(?m)^version:\s*([^\s#]+)\s*$", text)
    if not name or not version:
        raise ValueError(f"cannot read name/version from {path.name}")
    return name.group(1), version.group(1)


def is_ignored(rel: PurePosixPath, excluded: tuple[PurePosixPath, ...]) -> bool:
    if any(part in IGNORED_DIRS for part in rel.parts):
        return True
    if Path(rel.name).suffix.lower() in IGNORED_SUFFIXES:
        return True
    return any(rel == item or rel.is_relative_to(item) for item in excluded)


def iter_source_files(
    excluded: tuple[PurePosixPath, ...], overlay_sources: set[PurePosixPath]
):
    for source in sorted(path for path in SKILL_ROOT.rglob("*") if path.is_file()):
        rel = PurePosixPath(source.relative_to(SKILL_ROOT).as_posix())
        if rel in overlay_sources or is_ignored(rel, excluded):
            continue
        yield source, rel


def inventory(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = PurePosixPath(path.relative_to(root).as_posix())
        if rel.as_posix() == RUNTIME_MANIFEST or is_ignored(rel, ()):
            continue
        rows.append(
            {
                "path": rel.as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def inventory_fingerprint(rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(
            f"{row['path']}\0{row['size_bytes']}\0{row['sha256']}\n".encode("utf-8")
        )
    return digest.hexdigest()


def validate_destination(output: Path) -> Path:
    resolved = output.expanduser().resolve()
    source = SKILL_ROOT.resolve()
    if resolved.exists():
        raise FileExistsError(f"destination already exists; refusing to overwrite: {resolved}")
    if resolved == source or resolved.is_relative_to(source) or source.is_relative_to(resolved):
        raise ValueError("destination must be outside the source Skill tree and cannot contain it")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def build(output: Path) -> dict[str, Any]:
    destination = validate_destination(output)
    profile = load_profile()
    excluded = tuple(
        safe_relative(value, label="excluded path") for value in profile["excluded_paths"]
    )
    overlays = {
        safe_relative(source, label="overlay source"): safe_relative(target, label="overlay target")
        for source, target in profile["overlay_files"].items()
    }
    for rel in (*excluded, *overlays):
        if not (SKILL_ROOT / Path(*rel.parts)).exists():
            raise FileNotFoundError(f"profile path is missing: {rel.as_posix()}")
    for target in overlays.values():
        if len(target.parts) != 1:
            raise ValueError(f"overlay target must be a root filename: {target.as_posix()}")

    staging = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent)
    )
    try:
        for source, rel in iter_source_files(excluded, set(overlays)):
            target = staging / Path(*rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for source_rel, target_rel in overlays.items():
            shutil.copy2(
                SKILL_ROOT / Path(*source_rel.parts), staging / Path(*target_rel.parts)
            )

        for rel in excluded:
            if (staging / Path(*rel.parts)).exists():
                raise RuntimeError(f"excluded path leaked into runtime: {rel.as_posix()}")

        skill_name, skill_version = parse_manifest_identity(staging / "manifest.yaml")
        rows = inventory(staging)
        manifest = {
            "schema_version": "1.0.0",
            "profile_id": profile["profile_id"],
            "skill_name": skill_name,
            "skill_version": skill_version,
            "content_fingerprint": {
                "algorithm": "sha256-relative-path-size-content-v1",
                "sha256": inventory_fingerprint(rows),
            },
            "excluded_paths_enforced": [item.as_posix() for item in excluded],
            "overlay_files_applied": {
                source.as_posix(): target.as_posix() for source, target in overlays.items()
            },
            "file_count": len(rows),
            "files": rows,
        }
        (staging / RUNTIME_MANIFEST).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return {
        "ok": True,
        "output": str(destination),
        "profile_id": profile["profile_id"],
        "skill_name": skill_name,
        "skill_version": skill_version,
        "file_count": len(rows),
        "content_sha256": manifest["content_fingerprint"]["sha256"],
    }


def verify(runtime_root: Path) -> dict[str, Any]:
    root = runtime_root.expanduser().resolve()
    manifest_path = root / RUNTIME_MANIFEST
    if not root.is_dir() or not manifest_path.is_file():
        raise FileNotFoundError(f"public runtime or manifest is missing: {root}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = load_profile()
    errors: list[str] = []
    for value in profile["excluded_paths"]:
        rel = safe_relative(value, label="excluded path")
        if (root / Path(*rel.parts)).exists():
            errors.append(f"excluded path present: {rel.as_posix()}")
    for source in profile["overlay_files"]:
        rel = safe_relative(source, label="overlay source")
        if (root / Path(*rel.parts)).exists():
            errors.append(f"overlay source retained: {rel.as_posix()}")

    current = inventory(root)
    recorded = manifest.get("files") or []
    if current != recorded:
        errors.append("runtime file inventory differs from PUBLIC_RUNTIME_MANIFEST.json")
    fingerprint = inventory_fingerprint(current)
    expected = (manifest.get("content_fingerprint") or {}).get("sha256")
    if fingerprint != expected:
        errors.append("runtime content fingerprint mismatch")
    name, version = parse_manifest_identity(root / "manifest.yaml")
    if name != manifest.get("skill_name") or version != manifest.get("skill_version"):
        errors.append("runtime manifest identity differs from recorded identity")
    return {
        "ok": not errors,
        "runtime_root": str(root),
        "skill_name": name,
        "skill_version": version,
        "file_count": len(current),
        "content_sha256": fingerprint,
        "errors": errors,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Build or verify the filtered visualization public runtime"
    )
    sub = result.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--output", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--runtime-root", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = build(args.output) if args.command == "build" else verify(args.runtime_root)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
