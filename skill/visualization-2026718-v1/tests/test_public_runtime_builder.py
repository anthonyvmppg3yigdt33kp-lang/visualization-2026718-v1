import json
import subprocess
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUILDER = SKILL_ROOT / "scripts" / "build_public_runtime.py"


def run_builder(*args: str):
    return subprocess.run(
        [sys.executable, str(BUILDER), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_public_runtime_build_verify_and_refuse_overwrite(tmp_path):
    if not (SKILL_ROOT / "SKILL.public-runtime.md").is_file():
        pytest.skip("source-only builder test; public runtime retains verify mode only")
    runtime = tmp_path / "visualization-2026718-v1"
    built = run_builder("build", "--output", str(runtime))
    assert built.returncode == 0, built.stderr or built.stdout
    summary = json.loads(built.stdout)
    assert summary["ok"] is True
    assert summary["skill_version"] == "1.2.0"

    verified = run_builder("verify", "--runtime-root", str(runtime))
    assert verified.returncode == 0, verified.stderr or verified.stdout
    verification = json.loads(verified.stdout)
    assert verification["ok"] is True
    assert verification["content_sha256"] == summary["content_sha256"]

    # Import/test caches are runtime-local ephemera and must not invalidate the
    # immutable install payload after users execute the bundled test suite.
    (runtime / "tests" / "__pycache__").mkdir()
    (runtime / "tests" / "__pycache__" / "test_cache.pyc").write_bytes(b"cache")
    (runtime / ".pytest_cache").mkdir()
    (runtime / ".pytest_cache" / "README.md").write_text("cache\n", encoding="utf-8")
    verified_after_cache = run_builder("verify", "--runtime-root", str(runtime))
    assert verified_after_cache.returncode == 0, (
        verified_after_cache.stderr or verified_after_cache.stdout
    )
    cache_verification = json.loads(verified_after_cache.stdout)
    assert cache_verification["ok"] is True
    assert cache_verification["content_sha256"] == summary["content_sha256"]

    assert not (runtime / "assets" / "source_archive").exists()
    assert not (runtime / "assets" / "scheme-candidates").exists()
    assert not (runtime / "assets" / "previews-curated").exists()
    assert not (runtime / "references" / "catalog.jsonl").exists()
    assert not (runtime / "SKILL.public-runtime.md").exists()
    assert not (runtime / "manifest.public-runtime.yaml").exists()
    assert "public formal-Recipe runtime（V1.2.0）" in (runtime / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "version: 1.2.0" in (runtime / "manifest.yaml").read_text(encoding="utf-8")
    assert (runtime / "agents" / "openai.yaml").is_file()
    for rel in (
        "assets/recipes/umap-dataframe-r-v2/validation-evidence.json",
        "assets/recipes/marker-dotplot-r-v2/validation-evidence.json",
        "assets/recipes/seurat-spatial-overlay-r-v2/validation-evidence.json",
        "assets/previews-rendered/pbmc3k-umap-r-v2-final.png",
        "assets/previews-rendered/pbmc3k-marker-dotplot-r-v2-final.png",
        "assets/previews-rendered/visium-spatial-identity-r-v2-final.png",
        "assets/previews-rendered/visium-spatial-feature-r-v2-final.png",
    ):
        assert (runtime / rel).is_file()

    refused = run_builder("build", "--output", str(runtime))
    assert refused.returncode == 2
    assert "refusing to overwrite" in refused.stdout
