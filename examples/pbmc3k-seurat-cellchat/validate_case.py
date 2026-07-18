#!/usr/bin/env python3
"""Validate the portable evidence committed with the PBMC3K teaching case."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_REVIEWS = {
    "umap-clean": "umap_clean.png",
    "umap-arrow": "umap_arrow.png",
    "umap-dark-nebula": "umap_dark_nebula.png",
    "umap-multistyle": "umap_multistyle.png",
    "marker-dotplot": "marker_dotplot.png",
    "cellchat-circle": "cellchat_circle.png",
    "cellchat-chord": "cellchat_chord_top35.png",
    "cellchat-bubble": "cellchat_bubble_top30.png",
    "cellchat-heatmap": "cellchat_heatmap.png",
}
EXPECTED_PACKAGES = {
    "Seurat": "5.4.0",
    "SeuratObject": "5.4.0",
    "CellChat": "2.2.0.9001",
    "ggplot2": "4.0.3",
    "ComplexHeatmap": "2.26.1",
    "circlize": "0.4.18",
}
EXPECTED_STAGES = {
    "00_preflight",
    "01_seurat_pbmc3k",
    "02_skill_visualizations",
    "03_cellchat_pbmc3k",
    "04_cellchat_visualizations",
}


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    json_files = sorted(ROOT.rglob("*.json"))
    for path in json_files:
        try:
            load_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON: {path.relative_to(ROOT)} ({exc})")

    lock = load_json(ROOT / "renv.lock")
    if not isinstance(lock, dict) or (lock.get("R") or {}).get("Version") != "4.5.3":
        errors.append("renv.lock does not pin R 4.5.3")
    packages = lock.get("Packages", {}) if isinstance(lock, dict) else {}
    for package, expected in EXPECTED_PACKAGES.items():
        actual = (packages.get(package) or {}).get("Version")
        if actual != expected:
            errors.append(f"renv.lock: {package} expected {expected}, found {actual!r}")

    review_dir = ROOT / "artifacts" / "review"
    figure_root = ROOT / "artifacts" / "figures"
    for review_name, figure_name in EXPECTED_REVIEWS.items():
        review_path = review_dir / f"{review_name}.review.json"
        if not review_path.is_file():
            errors.append(f"missing review: {review_path.relative_to(ROOT)}")
            continue
        review = load_json(review_path)
        if not isinstance(review, dict):
            errors.append(f"review is not an object: {review_path.relative_to(ROOT)}")
            continue
        if review.get("decision") != "keep":
            errors.append(f"review is not terminal keep: {review_name}")
        if review.get("original_size_reviewed") is not True:
            errors.append(f"original size was not reviewed: {review_name}")
        if review.get("final_size_reviewed") is not True:
            errors.append(f"final size was not reviewed: {review_name}")
        expected_hashes = {
            "original": digest(figure_root / "original" / figure_name),
            "final": digest(figure_root / "final" / figure_name),
        }
        if review.get("image_hashes_seen") != expected_hashes:
            errors.append(f"review/image hash mismatch: {review_name}")

    marker_files = sorted((ROOT / "artifacts" / "logs").glob("*.complete.json"))
    stages = {load_json(path).get("stage") for path in marker_files}
    missing_stages = sorted(EXPECTED_STAGES - stages)
    if missing_stages:
        errors.append("missing completion stages: " + ", ".join(missing_stages))

    seurat_manifest = load_json(ROOT / "artifacts" / "manifests" / "run_manifest_seurat.json")
    archive_hash = ((seurat_manifest or {}).get("dataset") or {}).get("archive_sha256")
    if archive_hash != "847d6ebd9a1ec9a768f2be7e40ca42cbfe75ebeb6d76a4c24167041699dc28b5":
        errors.append("official PBMC3K archive checksum is missing or changed")

    report = {
        "pass": not errors,
        "json_files": len(json_files),
        "reviews": len(EXPECTED_REVIEWS),
        "completion_stages": len(stages),
        "pinned_packages_checked": len(EXPECTED_PACKAGES),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
