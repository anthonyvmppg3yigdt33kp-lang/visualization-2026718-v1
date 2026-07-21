from __future__ import annotations

import importlib.util
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
        self.assertEqual(metadata["validation"]["tier"], "parse-verified")
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
        self.assertEqual(
            evidence["real_visium_execution"]["barcode_reconciliation"],
            {
                "assay": 2695,
                "image": 2695,
                "coordinates": 2695,
                "all_pairwise_set_differences": 0,
            },
        )
        self.assertEqual(
            set(evidence["native_visual_review"]["decisions"].values()),
            {"KEEP"},
        )

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
