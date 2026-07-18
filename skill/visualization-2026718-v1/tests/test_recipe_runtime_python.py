from __future__ import annotations

import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "recipe_runtime.py"
SPEC = importlib.util.spec_from_file_location("recipe_runtime_python_tests", MODULE_PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)
SKILL_ROOT = Path(__file__).resolve().parents[1]


def png_dimensions(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("not a PNG")
    return struct.unpack(">II", payload[16:24])


class RecipeRuntimePythonTests(unittest.TestCase):
    def test_final_png_honors_physical_canvas_and_persists_parameters(self) -> None:
        fixture = SKILL_ROOT / "assets" / "fixtures" / "sample_composition_cells.csv"
        with tempfile.TemporaryDirectory() as temporary:
            result = runtime.render_python_recipe(
                "sample-composition-python-v1",
                fixture,
                Path(temporary),
                {"count": "count"},
                width_mm=85.0,
                height_mm=75.0,
                dpi=100,
            )
            width, height = png_dimensions(Path(result["final"]["path"]))
            self.assertLessEqual(abs(width - round(85.0 / 25.4 * 100)), 1)
            self.assertLessEqual(abs(height - round(75.0 / 25.4 * 100)), 1)
            self.assertTrue(Path(result["parameters_path"]).is_file())
            self.assertEqual(result["parameters_sha256"], runtime._sha256(Path(result["parameters_path"])))

    def test_materialized_python_chain_is_persisted_for_review_hashing(self) -> None:
        chain = runtime.build_chain(
            "umap-dataframe-python-v1",
            "python",
            modifier_ids=["label-repel-python-v1", "borderless-python-v1"],
        )
        with tempfile.TemporaryDirectory() as temporary:
            materialized = runtime.materialize_chain(chain, Path(temporary))
            code_path = Path(materialized["code_path"])
            self.assertTrue(code_path.is_file())
            self.assertEqual(materialized["code_sha256"], runtime._sha256(code_path))
            self.assertIn("def build_plot", code_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
