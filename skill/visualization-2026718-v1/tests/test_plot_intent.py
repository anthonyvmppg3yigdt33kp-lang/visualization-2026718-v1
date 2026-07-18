from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "plot_library.py"
SPEC = importlib.util.spec_from_file_location("plot_library", MODULE_PATH)
assert SPEC and SPEC.loader
plot_library = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plot_library)


class PlotIntentTests(unittest.TestCase):
    def test_catalog_fingerprint_is_portable_across_clone_mtimes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_root = Path(directory)
            checksum_index = source_root / "SHA256SUMS.csv"
            payload = source_root / "example.txt"
            checksum_index.write_text(
                "path,bytes,sha256\nexample.txt,1,unused-by-this-unit-test\n",
                encoding="utf-8",
            )
            payload.write_bytes(b"x")
            first = plot_library.catalog_input_fingerprint(source_root)
            stat = payload.stat()
            os.utime(
                payload,
                ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000_000),
            )
            second = plot_library.catalog_input_fingerprint(source_root)
            self.assertEqual(first, second)
            self.assertEqual(first["algorithm"], "sha256-v2-portable")

            payload.write_bytes(b"xx")
            third = plot_library.catalog_input_fingerprint(source_root)
            self.assertNotEqual(first["sha256"], third["sha256"])

    def test_execute_then_review_keeps_executable_gate(self) -> None:
        intent = plot_library.query_intent(
            "执行代码，复核并解释结果图",
            backend="python",
        )
        self.assertEqual(intent["action_intent"], "execute")
        self.assertTrue(intent["requires_executable"])
        self.assertTrue(intent["review_requested"])
        self.assertTrue(intent["review_after_execution"])
        self.assertEqual(intent["action_intents"], ["execute", "review"])

    def test_render_then_review_keeps_both_actions(self) -> None:
        intent = plot_library.query_intent(
            "Python：调用代码运行生成结果图，并看图解释结果",
        )
        self.assertEqual(intent["backend"], "python")
        self.assertEqual(intent["action_intent"], "render")
        self.assertTrue(intent["requires_executable"])
        self.assertTrue(intent["review_requested"])
        self.assertIn("render", intent["action_intents"])
        self.assertIn("review", intent["action_intents"])

    def test_chinese_punctuation_r_backend_is_explicit(self) -> None:
        intent = plot_library.query_intent(
            "使用 visualization-2026718-v1。R：数据列为 pathway、GeneRatio、Count 和 p.adjust，请运行富集玫瑰图。"
        )
        self.assertEqual(intent["backend"], "r")
        self.assertFalse(intent["requires_backend_choice"])
        self.assertEqual(intent["analysis_method"], "ora")
        self.assertEqual(intent["core_question"], "pathway_enrichment")
        self.assertEqual(intent["retrieval_family"], "gsea")

    def test_final_explain_result_is_post_execution_review(self) -> None:
        intent = plot_library.query_intent(
            "R：请调用富集玫瑰图代码并运行，最后解释结果图。"
        )
        self.assertEqual(intent["action_intent"], "execute")
        self.assertTrue(intent["requires_executable"])
        self.assertTrue(intent["review_after_execution"])
        self.assertIn("review", intent["action_intents"])

    def test_composition_control_group_is_not_binary_outcome(self) -> None:
        intent = plot_library.query_intent(
            "Python/AnnData：比较处理组与对照组的 cluster 结构和每个样本的细胞比例，匹配代码并运行。"
        )
        self.assertNotIn("binary_outcome", intent["variables"])
        self.assertEqual(intent["core_question"], "sample_level_composition")

    def test_post_render_review_without_repeating_figure_is_detected(self) -> None:
        intent = plot_library.query_intent(
            "R Seurat PBMC3K：对各个细胞簇做高级感 UMAP，可直接运行并在生成后复核"
        )
        self.assertTrue(intent["review_requested"])
        self.assertTrue(intent["review_after_execution"])

    def test_marker_size_and_average_colour_is_not_composition(self) -> None:
        intent = plot_library.query_intent(
            "R Seurat PBMC3K：展示每个亚群的特征 marker，使用点大小表示表达比例、颜色表示平均表达，可直接运行并复核结果图"
        )
        self.assertEqual(intent["retrieval_family"], "dotplot")
        self.assertEqual(intent["backend"], "r")
        self.assertIn("Seurat", intent["input_objects"])
        self.assertTrue(intent["review_requested"])

    def test_cellchat_multiview_preserves_requested_panel_order(self) -> None:
        query = "R CellChat PBMC3K：分析各细胞簇配体受体通讯，运行并生成圈图、弦图、气泡图与热图，之后复核解释"
        intent, decisions, _appearance, _rejected, clarification = plot_library.search_scheme_records(
            plot_library.load_scheme_records(), query, top_k=3
        )
        self.assertEqual(intent["retrieval_family"], "cellchat_chord")
        self.assertEqual(
            intent["geometry_subtypes"][:4],
            ["cellchat_circle_network", "cellchat_chord", "cellchat_bubble", "cellchat_heatmap"],
        )
        self.assertTrue(intent["review_requested"])
        self.assertTrue(intent["review_after_execution"])
        self.assertIsNone(clarification)
        self.assertEqual(
            [row["geometry_subtype"] for row in decisions[:4]],
            ["cellchat_circle_network", "cellchat_chord", "cellchat_bubble", "cellchat_heatmap"],
        )
        self.assertEqual(
            [row["executable_plan"]["base_recipe_id"] for row in decisions[:4]],
            [
                "cellchat-circle-r-v1",
                "cellchat-chord-r-v1",
                "cellchat-bubble-r-v1",
                "cellchat-heatmap-r-v1",
            ],
        )
        self.assertEqual(
            [row["executable_plan"]["adapter_id"] for row in decisions[:4]],
            [
                "cellchat-matrix-adapter-r-v1",
                "cellchat-matrix-adapter-r-v1",
                "cellchat-lr-adapter-r-v1",
                "cellchat-matrix-adapter-r-v1",
            ],
        )

    def test_any_regular_python_runtime_failure_is_structured(self) -> None:
        for operation in (
            lambda: 1 / 0,
            lambda: (_ for _ in ()).throw(FileNotFoundError("fixture missing")),
        ):
            result = plot_library.run_render_safely(operation, "python")
            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["stage"], "runtime")
            self.assertEqual(result["partial_artifacts"], [])

    def test_system_exit_is_not_swallowed(self) -> None:
        with self.assertRaises(SystemExit):
            plot_library.run_render_safely(
                lambda: (_ for _ in ()).throw(SystemExit(9)),
                "python",
            )


if __name__ == "__main__":
    unittest.main()
