#!/usr/bin/env python3
"""Remove credential-shaped payloads from a copied source snapshot without touching its origin."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PEM_PRIVATE_KEY = re.compile(
    r"(?ms)^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s*$.*?^-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s*$"
)
REPLACEMENT = "# [REDACTED: embedded private key removed by plot-code-retriever safety policy]"
TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".py", ".r"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path: Path, text: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=path.parent) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def update_checksum_table(root: Path, changed_paths: list[Path]) -> None:
    table = root / "SHA256SUMS.csv"
    if not table.exists() or not changed_paths:
        return
    with table.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or ["path", "bytes", "sha256"]
    changed = {path.relative_to(root).as_posix(): path for path in changed_paths}
    for row in rows:
        target = changed.get(row.get("path", ""))
        if target:
            row["bytes"] = str(target.stat().st_size)
            row["sha256"] = sha256(target)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=table.parent) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    temporary.replace(table)


def sanitize(root: Path, apply: bool) -> dict:
    findings = []
    changed_paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or ".state" in path.parts or "_tools" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        matches = list(PEM_PRIVATE_KEY.finditer(text))
        if not matches:
            continue
        before = sha256(path)
        sanitized = PEM_PRIVATE_KEY.sub(REPLACEMENT, text)
        finding = {
            "path": path.relative_to(root).as_posix(),
            "rule": "embedded_private_key",
            "occurrences": len(matches),
            "before_sha256": before,
            "action": "would_redact" if not apply else "redacted",
        }
        if apply:
            atomic_write(path, sanitized)
            finding["after_sha256"] = sha256(path)
            changed_paths.append(path)
        findings.append(finding)
    if apply:
        update_checksum_table(root, changed_paths)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "root": root.name,
        "applied": apply,
        "findings": findings,
        "changed_files": len(changed_paths),
        "raw_secret_material_in_report": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"snapshot root does not exist: {root}")
    result = sanitize(root, apply=args.apply)
    if args.report:
        report = Path(args.report).resolve()
        report.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(report, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.apply or not result["findings"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
