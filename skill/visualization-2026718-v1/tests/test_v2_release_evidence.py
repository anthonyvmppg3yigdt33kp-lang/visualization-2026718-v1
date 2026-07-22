import hashlib
import json
import re
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RECIPES = SKILL_ROOT / "assets" / "recipes"
PREVIEWS = SKILL_ROOT / "assets" / "previews-rendered"

BASES = {
    "umap-dataframe-r-v2": {
        "adapter": "seurat-embedding-adapter-r-v2",
        "preview": "pbmc3k-umap-r-v2.png",
    },
    "marker-dotplot-r-v2": {
        "adapter": "seurat-marker-summary-adapter-r-v2",
        "preview": "pbmc3k-marker-dotplot-r-v2.png",
    },
    "seurat-spatial-overlay-r-v2": {
        "adapter": None,
        "preview": "visium-spatial-identity-r-v2.png",
    },
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v2_release_metadata_and_public_runtime_versions_match():
    active_manifest = (SKILL_ROOT / "manifest.yaml").read_text(encoding="utf-8")
    assert "version: 1.2.0" in active_manifest
    public_overlay = SKILL_ROOT / "manifest.public-runtime.yaml"
    if public_overlay.is_file():
        assert "version: 1.2.0" in public_overlay.read_text(encoding="utf-8")
    else:
        assert "profile: biomedical-public-runtime-v1" in active_manifest
    assert (SKILL_ROOT / "agents" / "openai.yaml").is_file()

    for recipe_id, expected in BASES.items():
        recipe = load_json(RECIPES / recipe_id / "recipe.json")
        assert recipe["validation"]["tier"] == "verified"
        assert all(
            recipe["validation"]["checks"][name] == "pass"
            for name in ("schema", "syntax", "safety", "fixture", "render", "visual", "semantic", "provenance")
        )
        assert recipe["visual_fingerprint"]["reviewed"] is True
        assert recipe["visual_fingerprint"]["evidence_level"] == "image_code_data"
        assert recipe["files"]["preview"].endswith(expected["preview"])
        preview = (RECIPES / recipe_id / recipe["files"]["preview"]).resolve()
        final = preview.with_name(f"{preview.stem}-final{preview.suffix}")
        assert preview.is_file()
        assert final.is_file()
        assert (RECIPES / recipe_id / recipe["files"]["validation_evidence"]).resolve().is_file()


def test_v2_evidence_binds_current_code_and_promoted_preview_hashes():
    for recipe_id, expected in BASES.items():
        evidence_path = RECIPES / recipe_id / "validation-evidence.json"
        evidence = load_json(evidence_path)
        assert evidence["recipe_id"] == recipe_id
        assert evidence["status"] == "verified"
        assert evidence["code_binding"]["base_recipe_sha256"] == sha256(
            RECIPES / recipe_id / "recipe.R"
        )
        assert evidence["code_binding"]["plot_library_sha256"] == sha256(
            SKILL_ROOT / "scripts" / "plot_library.py"
        )
        assert evidence["code_binding"]["recipe_runtime_sha256"] == sha256(
            SKILL_ROOT / "scripts" / "recipe_runtime.py"
        )

        adapter = expected["adapter"]
        if adapter:
            assert evidence["validation_scope"]["executed_chain"] == [adapter, recipe_id]
            assert evidence["code_binding"]["adapter_recipe_sha256"] == sha256(
                RECIPES / adapter / "recipe.R"
            )

        for artifact in evidence["rendered_outputs"]:
            asset = (evidence_path.parent / artifact["path"]).resolve()
            assert asset.is_relative_to(SKILL_ROOT)
            assert asset.is_file()
            assert asset.stat().st_size == artifact["size_bytes"]
            assert sha256(asset) == artifact["sha256"]

        serialized = evidence_path.read_text(encoding="utf-8")
        assert not re.search(r"(^|[\"\s])[A-Za-z]:[\\/]", serialized, flags=re.MULTILINE)
        assert all(item["successful_artifacts_reused"] is False for item in evidence["excluded_attempts"])


def test_v2_adapters_link_to_their_real_chain_evidence_without_claiming_visual_review():
    links = {
        "seurat-embedding-adapter-r-v2": "umap-dataframe-r-v2",
        "seurat-marker-summary-adapter-r-v2": "marker-dotplot-r-v2",
    }
    for adapter_id, base_id in links.items():
        recipe_path = RECIPES / adapter_id / "recipe.json"
        recipe = load_json(recipe_path)
        assert recipe["kind"] == "adapter"
        assert recipe["validation"]["checks"]["fixture"] == "pass"
        assert recipe["validation"]["checks"]["visual"] == "not_applicable"
        assert recipe["visual_fingerprint"]["reviewed"] is False
        evidence_path = (recipe_path.parent / recipe["files"]["validation_evidence"]).resolve()
        evidence = load_json(evidence_path)
        assert evidence["recipe_id"] == base_id
        assert evidence["validation_scope"]["executed_chain"] == [adapter_id, base_id]


def test_v2_exact_render_reviews_are_terminal_and_hash_consistent():
    reviews = {}
    for line in (SKILL_ROOT / "references" / "exact-render-review.jsonl").read_text(
        encoding="utf-8"
    ).splitlines():
        row = json.loads(line)
        reviews[row["recipe_id"]] = row

    for recipe_id in BASES:
        row = reviews[recipe_id]
        assert row["decision"] == "keep"
        assert row["evidence_level"] == "image_code_data"
        assert {"original", "final"}.issubset(row["native_views_opened"])
        assert row["blockers"] == []
        assert row["major_findings"] == []
        evidence = load_json(RECIPES / recipe_id / "validation-evidence.json")
        promoted = {artifact["sha256"] for artifact in evidence["rendered_outputs"]}
        assert set(row["opened_hashes"].values()).issubset(promoted)

    marker = reviews["marker-dotplot-r-v2"]
    assert marker["resolved_findings"] == ["axis_label_clipped"]
    assert marker["visual_only_revision"]["scientific_parameters_changed"] is False


def test_spatial_v2_evidence_covers_identity_and_feature_pairs():
    evidence = load_json(RECIPES / "seurat-spatial-overlay-r-v2" / "validation-evidence.json")
    assert {item["role"] for item in evidence["rendered_outputs"]} == {
        "identity_original",
        "identity_final",
        "feature_original",
        "feature_final",
    }
    assert evidence["data_binding"]["spots"] == 2695
    assert evidence["data_binding"]["barcode_reconciliation"]["all_six_set_differences"] == 0
    assert [pair["decision"] for pair in evidence["native_visual_review"]["pairs"]] == [
        "keep",
        "keep",
    ]
