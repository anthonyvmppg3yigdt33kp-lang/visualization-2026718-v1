import json
from pathlib import Path, PurePosixPath


SKILL_ROOT = Path(__file__).resolve().parents[1]
PROFILE = SKILL_ROOT / "public-install-profile.json"


def test_public_install_profile_has_exact_rights_boundary_and_exclusions():
    payload = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert payload == {
        "schema_version": "1.0.0",
        "profile_id": "biomedical-public-runtime-v1",
        "purpose": (
            "Task-local formal-Recipe runtime distribution without upstream audit snapshots, "
            "raw extracted source code, reference-only candidates, or third-party curated "
            "reference images of unresolved redistribution status."
        ),
        "capability_scope": [
            "formal_recipe_adaptation",
            "formal_recipe_composition",
            "formal_recipe_preflight",
            "formal_recipe_rendering",
            "native_visual_review",
        ],
        "overlay_files": {
            "SKILL.public-runtime.md": "SKILL.md",
            "manifest.public-runtime.yaml": "manifest.yaml",
        },
        "included_rights_boundary": {
            "original_code_license": "MIT",
            "third_party_rights_status": "mixed-original-and-third-party-not-relicensed",
            "notice_file": "NOTICE.md",
        },
        "excluded_paths": [
            "assets/previews-curated",
            "assets/scheme-candidates",
            "assets/source_archive",
            "references/catalog.jsonl",
        ],
        "exclusion_reasons": {
            "assets/previews-curated": (
                "Third-party curated reference images are retained only in the upstream audit "
                "checkout and are not installed by the public runtime profile."
            ),
            "assets/scheme-candidates": (
                "Reference-only candidates distilled from source blocks are retained only in "
                "the upstream audit checkout and are not installed by the public formal-Recipe "
                "runtime profile."
            ),
            "assets/source_archive": (
                "Article snapshots and source/reference images with unresolved redistribution "
                "rights are retained only in the upstream audit checkout and are not installed "
                "by the public runtime profile."
            ),
            "references/catalog.jsonl": (
                "The full source catalog contains extracted source code and article search "
                "text; it is retained only in the upstream audit checkout and is not installed "
                "by the public formal-Recipe runtime profile."
            ),
        },
        "raw_third_party_data_included": False,
        "raw_extracted_source_code_included": False,
    }


def test_public_install_profile_paths_are_safe_and_notice_is_local():
    payload = json.loads(PROFILE.read_text(encoding="utf-8"))
    for value in payload["excluded_paths"]:
        path = PurePosixPath(value)
        assert not path.is_absolute()
        assert ".." not in path.parts
        assert (SKILL_ROOT / Path(*path.parts)).exists()

    notice = (SKILL_ROOT / "NOTICE.md").read_text(encoding="utf-8")
    license_text = (SKILL_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "not relicensed under MIT" in notice
    assert "CC BY 4.0" in notice
    assert "10x Genomics" in notice
    assert "MIT License" in license_text

    for source, target in payload["overlay_files"].items():
        assert (SKILL_ROOT / source).is_file()
        assert PurePosixPath(target).name == target


def test_public_runtime_manifest_references_only_present_nonexcluded_paths():
    payload = json.loads(PROFILE.read_text(encoding="utf-8"))
    excluded = tuple(f"{path}/" for path in payload["excluded_paths"] if "." not in Path(path).name)
    manifest = (SKILL_ROOT / "manifest.public-runtime.yaml").read_text(encoding="utf-8")
    for forbidden in (*excluded, "references/catalog.jsonl", "assets/previews-curated"):
        assert forbidden not in manifest
    for required in (
        "assets/recipes",
        "assets/previews-rendered",
        "assets/fixtures",
        "references/recipe-schema.md",
        "references/qa-contract.md",
        "references/visual-review-protocol.md",
    ):
        assert required in manifest
        assert (SKILL_ROOT / required).exists()
