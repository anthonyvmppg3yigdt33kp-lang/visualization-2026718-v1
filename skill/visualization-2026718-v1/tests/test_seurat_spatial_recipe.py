from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import subprocess
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "plot_library.py"
SPEC = importlib.util.spec_from_file_location("plot_library_spatial_tests", MODULE_PATH)
assert SPEC and SPEC.loader
plot_library = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plot_library)

RECIPE_DIR = SKILL_ROOT / "assets" / "recipes" / "seurat-spatial-overlay-r-v1"
METADATA_PATH = RECIPE_DIR / "recipe.json"
FIXTURE_PATH = SKILL_ROOT / "assets" / "fixtures" / "seurat_spatial_contract.R"
PREVIEW_DIR = SKILL_ROOT / "assets" / "previews-rendered"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SeuratSpatialRecipeTests(unittest.TestCase):
    def test_recipe_schema_safety_and_r_syntax(self) -> None:
        recipe_ids = {
            json.loads(path.read_text(encoding="utf-8"))["id"]
            for path in (SKILL_ROOT / "assets" / "recipes").glob("*/recipe.json")
        }
        errors, _warnings = plot_library.validate_recipe(
            METADATA_PATH,
            run_r_parse=True,
            catalog_by_id=None,
            recipe_ids=recipe_ids,
        )
        self.assertEqual(errors, [])

        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(metadata["entrypoint"], "plot_seurat_spatial_overlay")
        self.assertEqual(metadata["validation"]["tier"], "verified")
        self.assertEqual(
            metadata["validation"]["checks"]["fixture"],
            "pass_seurat_5.5.0_guarded",
        )
        self.assertEqual(metadata["validation"]["checks"]["render"], "pass_real_visium_2695")
        self.assertEqual(
            metadata["validation"]["checks"]["visual"],
            "pass",
        )
        self.assertTrue(metadata["visual_fingerprint"]["reviewed"])

        evidence = json.loads(
            (RECIPE_DIR / "validation-evidence.json").read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["status"], "verified")
        self.assertEqual(evidence["validation_scope"]["evidence_set"], "v6-output2")
        self.assertEqual(
            evidence["validation_scope"]["executed_component"],
            "independent upstream Seurat spatial Recipe harness",
        )
        self.assertEqual(
            evidence["runtime"]["renv_lock_sha256"],
            "b8450521054cd750e93a27fab0b44757519361bd8b694ffbae35636de508cf5b",
        )
        self.assertEqual(evidence["formal_preflight"]["status"], "pass")
        self.assertEqual(evidence["formal_preflight"]["missing_dependencies"], [])
        self.assertEqual(
            evidence["formal_preflight"]["entrypoint"],
            "plot_seurat_spatial_overlay",
        )
        self.assertTrue(
            evidence["formal_preflight"]["processor_architecture_restored_for_child"]
        )
        self.assertFalse(evidence["formal_preflight"]["parent_environment_modified"])
        self.assertEqual(
            evidence["real_visium_execution"]["analysis_object_sha256"],
            "e549e9003f6ca12181a728f024ccb711c1d171ab57f3960f37156a53d858be51",
        )
        self.assertEqual(
            evidence["real_visium_execution"]["barcode_reconciliation"]["set_differences"],
            {
                "assay_minus_image": 0,
                "image_minus_assay": 0,
                "assay_minus_coordinates": 0,
                "coordinates_minus_assay": 0,
                "image_minus_coordinates": 0,
                "coordinates_minus_image": 0,
            },
        )
        self.assertEqual(
            {
                key: evidence["real_visium_execution"]["barcode_reconciliation"][key]
                for key in ("assay", "image", "coordinates")
            },
            {"assay": 2695, "image": 2695, "coordinates": 2695},
        )
        self.assertEqual(evidence["native_process_evidence"]["native_returncode"], 0)
        self.assertEqual(evidence["native_process_evidence"]["forbidden_matches"], [])
        self.assertEqual(
            evidence["native_process_evidence"]["execution_marker_sha256"],
            "a2404517b54e5fd07dcf2b77640829f4c29923e93f3044e0ba9160063bc00128",
        )
        self.assertEqual(
            evidence["native_process_evidence"]["process_evidence_sha256"],
            "2d1dc6fec31cb8c9d2ae4ce633ebb4f6d9cc665ef9bcbc1a99e83b5c41bc859e",
        )
        marker_path = RECIPE_DIR / evidence["native_process_evidence"]["execution_marker_file"]
        process_path = RECIPE_DIR / evidence["native_process_evidence"]["process_evidence_file"]
        self.assertEqual(
            sha256(marker_path), evidence["native_process_evidence"]["execution_marker_sha256"]
        )
        self.assertEqual(
            sha256(process_path), evidence["native_process_evidence"]["process_evidence_sha256"]
        )
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        process = json.loads(process_path.read_text(encoding="utf-8"))
        self.assertEqual(marker["status"], "pass")
        self.assertEqual(marker["analysis_object_sha256"], evidence["real_visium_execution"]["analysis_object_sha256"])
        self.assertEqual(marker["recipe_sha256"], evidence["code_binding"]["recipe_sha256"])
        self.assertEqual(marker["barcode_reconciliation"], evidence["real_visium_execution"]["barcode_reconciliation"])
        self.assertEqual(marker["scale_factors"], evidence["real_visium_execution"]["scale_factors"])
        self.assertTrue(marker["caller_default_assay_unchanged"])
        self.assertEqual(process["status"], "passed")
        self.assertTrue(process["native_exit_zero"])
        self.assertEqual(process["native_returncode"], 0)
        self.assertEqual(process["forbidden_matches"], [])
        self.assertFalse(process["absolute_paths_included"])
        self.assertEqual(
            set(evidence["native_visual_review"]["decisions"].values()),
            {"KEEP"},
        )
        self.assertEqual(
            [pair["decision"] for pair in evidence["native_visual_review"]["pairs"]],
            ["keep", "keep"],
        )
        self.assertTrue(
            all(not pair["blockers"] and not pair["major_findings"]
                for pair in evidence["native_visual_review"]["pairs"])
        )
        self.assertFalse(evidence["visual_adjustment"]["scientific_parameters_changed"])
        self.assertEqual(
            evidence["excluded_attempt"]["status"],
            "excluded_from_success_evidence",
        )

        expected_outputs = {
            "seurat-spatial-overlay-r.png": (3600, 2400, 3023362, "747488f45c6a1e03bff9cde683b3241080dc3f14689929620d648abd22bb4abd"),
            "seurat-spatial-overlay-r-final.png": (2130, 1425, 1459059, "0f35e3714c2c6f980481205654b760ec0e8bbda0c745bf94c1fc5299f0a5ac8a"),
            "seurat-spatial-feature-r.png": (3600, 2400, 2743981, "3205ea00d3ceee73c28b63230c403d1d4b4f35d8aacd00e7b386ba8ea1c21dd6"),
            "seurat-spatial-feature-r-final.png": (2130, 1425, 1332529, "f2d95dd59baf7d70ec3297670cd765a3e12a76ed85935f8185613dacc6781a1b"),
        }
        for item in evidence["rendered_outputs"]:
            name = Path(item["path"]).name
            width, height, size_bytes, expected_hash = expected_outputs[name]
            self.assertEqual((item["width_px"], item["height_px"]), (width, height))
            self.assertEqual(item["size_bytes"], size_bytes)
            self.assertEqual(item["sha256"], expected_hash)
            preview = PREVIEW_DIR / name
            self.assertEqual(preview.stat().st_size, size_bytes)
            self.assertEqual(sha256(preview), expected_hash)

        process_outputs = {
            item["name"]: (
                item["width_px"], item["height_px"], item["size_bytes"], item["sha256"]
            )
            for item in process["outputs"]
        }
        self.assertEqual(process_outputs, expected_outputs)

        self.assertEqual(
            sha256(RECIPE_DIR / "recipe.R"), evidence["code_binding"]["recipe_sha256"]
        )
        self.assertEqual(
            sha256(FIXTURE_PATH), evidence["code_binding"]["fixture_sha256"]
        )
        for audit_path in (
            RECIPE_DIR / "validation-evidence.json",
            marker_path,
            process_path,
        ):
            audit_text = audit_path.read_text(encoding="utf-8")
            self.assertNotIn("C:\\\\Users", audit_text)
            self.assertNotIn("file://", audit_text.casefold())
        evidence_text = (RECIPE_DIR / "validation-evidence.json").read_text(encoding="utf-8")
        self.assertNotIn("v6-output\"", evidence_text)

        code = (RECIPE_DIR / "recipe.R").read_text(encoding="utf-8")
        for public_api in (
            "Seurat::Images",
            "Seurat::ScaleFactors",
            "Seurat::GetTissueCoordinates",
            "Seurat::SpatialDimPlot",
            "Seurat::SpatialFeaturePlot",
            "SeuratObject::Layers",
        ):
            self.assertIn(public_api, code)
        self.assertNotIn("@images", code)
        self.assertNotIn("slot(object", code)

    def test_spatial_spot_scheme_maps_to_formal_r_recipe(self) -> None:
        record = next(
            row
            for row in plot_library.load_scheme_records()
            if row.get("scheme_id")
            == "scheme-3792985494804332545-006-spatial_spot_overlay-v1"
        )
        intent = plot_library.query_intent(
            "R Seurat Visium：运行 SpatialDimPlot 组织图像 spot overlay",
            backend="r",
        )
        plan = plot_library.scheme_execution_plan(record, intent)
        self.assertEqual(plan["status"], "executable")
        self.assertEqual(plan["base_recipe_id"], "seurat-spatial-overlay-r-v1")
        self.assertIsNone(plan["adapter_id"])
        self.assertEqual(plan["mapping_level"], "formal_subtype")
        self.assertEqual(plan["parameter_bindings"]["assay"], "Spatial")
        self.assertEqual(plan["blockers"], [])

    def test_contract_fixture_and_barcode_mismatch_guard(self) -> None:
        if os.name == "nt":
            self.skipTest(
                "raw Windows R subprocess shutdown is not accepted as success; "
                "use the hash-bound guarded Seurat 5.5.0 fixture evidence"
            )
        rscript = plot_library.locate_rscript()
        if not rscript:
            self.skipTest("Rscript is unavailable")
        script = r"""
args <- commandArgs(trailingOnly = TRUE)
dependencies <- c("Seurat", "SeuratObject", "Matrix")
if (!all(vapply(dependencies, requireNamespace, logical(1), quietly = TRUE))) {
  quit(status = 42L)
}
source(args[[1]], encoding = "UTF-8")
source(args[[2]], encoding = "UTF-8")
object <- make_seurat_spatial_contract_fixture()
object <- Seurat::NormalizeData(object, verbose = FALSE)
object[["RNA"]] <- SeuratObject::CreateAssayObject(
  counts = SeuratObject::LayerData(object[["Spatial"]], layer = "counts")
)
SeuratObject::DefaultAssay(object) <- "RNA"
object <- Seurat::NormalizeData(object, verbose = FALSE)
default_before <- SeuratObject::DefaultAssay(object)

identity_plot <- plot_seurat_spatial_overlay(
  object,
  mode = "identity",
  assay = "Spatial",
  image = "slice1",
  group_by = "cluster"
)
feature_plot <- plot_seurat_spatial_overlay(
  object,
  mode = "feature",
  assay = "Spatial",
  feature_assay = "RNA",
  image = "slice1",
  features = c("Hpca", "Ttr")
)
stopifnot(inherits(identity_plot, c("gg", "ggplot", "patchwork")))
stopifnot(inherits(feature_plot, c("gg", "ggplot", "patchwork")))
stopifnot(identical(SeuratObject::DefaultAssay(object), default_before))

bad_object <- object
bad_image <- bad_object[["slice1"]]
bad_coordinates <- methods::slot(bad_image, "coordinates")[-1, , drop = FALSE]
methods::slot(bad_image, "coordinates") <- bad_coordinates
bad_images <- methods::slot(bad_object, "images")
bad_images[["slice1"]] <- bad_image
methods::slot(bad_object, "images") <- bad_images
barcode_error <- tryCatch(
  {
    plot_seurat_spatial_overlay(
      bad_object,
      mode = "identity",
      assay = "Spatial",
      image = "slice1",
      group_by = "cluster"
    )
    NULL
  },
  error = identity
)
stopifnot(inherits(barcode_error, "error"))
stopifnot(grepl("barcode-coordinate reconciliation failed", conditionMessage(barcode_error), fixed = TRUE))
cat("SEURAT_SPATIAL_CONTRACT_OK\n")
"""
        completed = subprocess.run(
            [rscript, "-e", script, str(FIXTURE_PATH), str(RECIPE_DIR / "recipe.R")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if completed.returncode == 42:
            self.skipTest("Seurat contract-fixture dependencies are unavailable")
        self.assertEqual(
            completed.returncode,
            0,
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
