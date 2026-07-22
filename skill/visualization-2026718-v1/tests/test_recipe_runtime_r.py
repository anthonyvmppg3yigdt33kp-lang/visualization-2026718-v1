from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "recipe_runtime.py"
SPEC = importlib.util.spec_from_file_location("recipe_runtime", MODULE_PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def write_png(path: Path, width: int = 8, height: int = 6) -> None:
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + (b"\xff\xff\xff" * width)
    value = b"\x89PNG\r\n\x1a\n"
    value += _png_chunk(b"IHDR", header)
    value += _png_chunk(b"IDAT", zlib.compress(row * height))
    value += _png_chunk(b"IEND", b"")
    path.write_bytes(value)


def runner_paths(command: list[str]) -> tuple[Path, Path, Path]:
    runner = Path(command[-1])
    source = runner.read_text(encoding="utf-8")

    def value(name: str) -> Path:
        match = re.search(rf"(?m)^{re.escape(name)} <- (.+)$", source)
        assert match, (name, source[:500])
        return Path(json.loads(match.group(1)))

    return value("original_path"), value("final_path"), value("status_path")


def fake_r_success(command, **kwargs):
    original, final, status = runner_paths(command)
    write_png(original)
    write_png(final)
    status.write_text(
        "STATUS\tOK\nOBJECT_CLASS\tggplot,gg\nRENDERER\tggplot2_ggsave\n"
        "ENTRYPOINT\tbuild_plot\nNATIVE_REVIEW\tpending_native_review\n",
        encoding="utf-8",
    )
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def fake_r_crash_after_artifacts(command, **kwargs):
    process = fake_r_success(command, **kwargs)
    return subprocess.CompletedProcess(command, 3221225477, stdout=process.stdout, stderr="")


def fake_r_unsupported_object(command, **kwargs):
    _, _, status = runner_paths(command)
    status.write_text(
        "STATUS\tBLOCKED\nERROR_CLASS\tsimpleError,error,condition\n"
        "ERROR_MESSAGE\tUnsupported R plot object contract: data.frame.\n"
        "ENTRYPOINT\tbuild_plot\nNATIVE_REVIEW\tnot_started\n",
        encoding="utf-8",
    )
    return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


class RecipeRuntimeRTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data = self.root / "data.csv"
        self.code = self.root / "plot.R"
        self.data.write_text("x,y\n1,2\n", encoding="utf-8")
        self.code.write_text("build_plot <- function(data) data\n", encoding="utf-8")
        self.preflight = {
            "ok": True,
            "backend": "r",
            "runtime": {"backend": "r", "executable": "Rscript"},
            "missing_dependencies": [],
            "code_checks": [],
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_low_level(self, process_side_effect) -> dict:
        with mock.patch.object(runtime.subprocess, "run", side_effect=process_side_effect):
            return runtime._run_r_render(
                input_path=self.data,
                code_path=self.code,
                entrypoint="build_plot",
                parameters={},
                output_dir=self.root / "output",
                artifact_stem="test-r",
                preflight=self.preflight,
                identity={"recipe_id": "test-r-v1"},
                composition=False,
                side_effect=False,
                matrix_input=False,
                width_mm=85.0,
                height_mm=70.0,
                dpi=300,
                timeout_seconds=10.0,
            )

    def test_success_returns_hashes_and_pending_native_review(self) -> None:
        result = self.run_low_level(fake_r_success)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["status"], "rendered_pending_native_review")
        self.assertEqual(result["native_review_status"], "pending_native_review")
        self.assertEqual(result["r_process"]["returncode"], 0)
        for key in ("input_sha256", "data_sha256", "code_sha256", "runner_sha256"):
            self.assertRegex(result[key], r"^[0-9a-f]{64}$")
        for view in ("original", "final"):
            self.assertTrue(Path(result[view]["path"]).is_file())
            self.assertRegex(result[view]["sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(result["visual_review_completed"])

    def test_nonzero_r_exit_rejects_even_status_ok_artifacts(self) -> None:
        result = self.run_low_level(fake_r_crash_after_artifacts)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["r_process"]["returncode"], 3221225477)
        self.assertEqual(result["r_status"]["STATUS"], "OK")
        self.assertNotIn("original", result)
        self.assertEqual(len(result["partial_artifacts"]), 2)
        self.assertTrue(all(item["usable"] is False for item in result["partial_artifacts"]))

    def test_unsupported_r_object_is_explicit_object_contract_blocker(self) -> None:
        result = self.run_low_level(fake_r_unsupported_object)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["stage"], "object_contract")
        self.assertIn("Unsupported R plot object", result["reason"])
        self.assertEqual(result["partial_artifacts"], [])

    def test_materialized_r_composition_reaches_real_runner_path(self) -> None:
        chain = runtime.build_chain(
            "marker-dotplot-r-v1", "r", modifier_ids=["borderless-r-v1"]
        )
        fixture = runtime.SKILL_ROOT / "assets" / "fixtures" / "marker_dot.csv"
        with mock.patch.object(runtime, "preflight_chain", return_value=self.preflight), mock.patch.object(
            runtime.subprocess, "run", side_effect=fake_r_success
        ):
            result = runtime.render_r_chain(
                chain,
                fixture,
                self.root / "composition",
                component_kwargs={"borderless-r-v1": {"keep_labels": True}},
            )
        self.assertTrue(result["ok"], result)
        self.assertEqual(
            result["composition_order"], ["marker-dotplot-r-v1", "borderless-r-v1"]
        )
        self.assertEqual(result["entrypoint"], "build_plot")
        self.assertEqual(
            result["component_kwargs"]["borderless-r-v1"]["keep_labels"], True
        )
        candidate_code = Path(result["code_path"]).read_text(encoding="utf-8")
        self.assertIn("build_plot <- function", candidate_code)

    def test_formal_r_recipe_uses_declared_entrypoint_and_runner(self) -> None:
        fixture = runtime.SKILL_ROOT / "assets" / "fixtures" / "marker_dot.csv"
        with mock.patch.object(runtime, "preflight_chain", return_value=self.preflight), mock.patch.object(
            runtime.subprocess, "run", side_effect=fake_r_success
        ):
            result = runtime.render_r_recipe(
                "marker-dotplot-r-v1",
                fixture,
                self.root / "formal-recipe",
                parameters={"size_breaks": [0, 25, 100]},
            )
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["recipe_id"], "marker-dotplot-r-v1")
        self.assertEqual(result["entrypoint"], "plot_marker_dotplot")
        self.assertEqual(result["parameters"]["size_breaks"], [0, 25, 100])
        runner = Path(result["runner_path"]).read_text(encoding="utf-8")
        self.assertIn("runtime_parameters <-", runner)
        self.assertIn("c(0, 25, 100)", runner)

    def test_matrix_side_effect_and_supported_object_contracts_are_declared(self) -> None:
        heatmap = runtime.load_recipe("complex-heatmap-r-v1")
        chord = runtime.load_recipe("cellchat-chord-r-v1")
        marker = runtime.load_recipe("marker-dotplot-r-v1")
        self.assertTrue(runtime._r_expected_matrix(heatmap))
        self.assertTrue(runtime._r_expected_matrix(chord))
        self.assertFalse(runtime._r_expected_matrix(marker))
        self.assertTrue(runtime._r_expected_side_effect(chord))
        source = runtime._r_runner_source(
            code_path=self.code,
            input_path=self.data,
            entrypoint="build_plot",
            parameters={},
            composition=False,
            side_effect=True,
            matrix_input=True,
            original_path=self.root / "o.png",
            final_path=self.root / "f.png",
            status_path=self.root / "status.tsv",
            original_width_mm=160.0,
            original_height_mm=120.0,
            width_mm=85.0,
            height_mm=70.0,
            dpi=300,
        )
        self.assertIn("jsonlite::fromJSON", source)
        self.assertIn("matrix_input_mode <- TRUE", source)
        self.assertIn("base_graphics_side_effect", source)
        self.assertIn("ComplexHeatmap::draw", source)
        self.assertIn("grid::grid.draw", source)
        self.assertIn("grDevices::replayPlot", source)

    def test_r_dependency_probe_nonzero_is_not_preflight_success(self) -> None:
        recipe = runtime.load_recipe("marker-dotplot-r-v1")
        crashed = subprocess.CompletedProcess(["Rscript"], 3221225477, stdout="", stderr="")
        with mock.patch.object(runtime, "locate_rscript", return_value="Rscript"), mock.patch.object(
            runtime.subprocess, "run", return_value=crashed
        ):
            result = runtime.preflight_chain([recipe])
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["runtime"]["probe_returncode"], 3221225477)
        self.assertIn("exited non-zero", result["runtime"]["probe_error"])

    def test_r_child_environment_restores_native_windows_architecture_without_parent_mutation(self) -> None:
        with mock.patch.object(runtime.os, "name", "nt"), mock.patch.object(
            runtime.sys, "maxsize", 2**63 - 1
        ), mock.patch.dict(runtime.os.environ, {}, clear=True):
            child, architecture = runtime._r_child_environment()
            self.assertNotIn("PROCESSOR_ARCHITECTURE", runtime.os.environ)
        self.assertEqual(child["PROCESSOR_ARCHITECTURE"], "AMD64")
        self.assertEqual(architecture["native_architecture"], "X64")
        self.assertTrue(architecture["processor_architecture_restored"])
        self.assertFalse(architecture["parent_environment_modified"])

    def test_r_child_environment_rejects_conflicting_architecture(self) -> None:
        with mock.patch.object(runtime.os, "name", "nt"), mock.patch.object(
            runtime.sys, "maxsize", 2**63 - 1
        ), mock.patch.dict(
            runtime.os.environ, {"PROCESSOR_ARCHITECTURE": "ARM64"}, clear=True
        ):
            with self.assertRaisesRegex(RuntimeError, "PROCESSOR_ARCHITECTURE conflicts"):
                runtime._r_child_environment()

    def test_r_literal_keeps_parameter_strings_inert(self) -> None:
        payload = {'marker-box-r-v1': {'colour': '\"); system("whoami"); #'}}
        encoded = runtime._r_literal(payload)
        self.assertIn("stats::setNames", encoded)
        self.assertIn(r'\"); system(\"whoami\"); #', encoded)
        self.assertNotIn("NA_real_", encoded)
        with self.assertRaisesRegex(ValueError, "NaN or infinity"):
            runtime._r_literal(float("nan"))

    def test_cli_render_and_composition_dispatch_to_r_runtime(self) -> None:
        fixture = runtime.SKILL_ROOT / "assets" / "fixtures" / "marker_dot.csv"
        direct_result = {"ok": True, "status": "rendered_pending_native_review"}
        with mock.patch.object(runtime, "render_r_recipe", return_value=direct_result) as direct:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = runtime.main(
                    [
                        "render",
                        "--recipe-id",
                        "marker-dotplot-r-v1",
                        "--input",
                        str(fixture),
                        "--output-dir",
                        str(self.root / "cli-direct"),
                    ]
                )
        self.assertEqual(exit_code, 0)
        direct.assert_called_once()
        self.assertEqual(json.loads(output.getvalue())["status"], "rendered_pending_native_review")

        with mock.patch.object(runtime, "render_r_chain", return_value=direct_result) as composed:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = runtime.main(
                    [
                        "render-composition",
                        "--backend",
                        "r",
                        "--base-id",
                        "marker-dotplot-r-v1",
                        "--modifier",
                        "borderless-r-v1",
                        "--input",
                        str(fixture),
                        "--output-dir",
                        str(self.root / "cli-composition"),
                    ]
                )
        self.assertEqual(exit_code, 0)
        composed.assert_called_once()
        self.assertEqual(json.loads(output.getvalue())["status"], "rendered_pending_native_review")


if __name__ == "__main__":
    unittest.main()
