from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "plot_library.py"
SPEC = importlib.util.spec_from_file_location("plot_library", MODULE_PATH)
assert SPEC and SPEC.loader
plot_library = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plot_library)


class PlotIntentTests(unittest.TestCase):
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
