from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "visual_review_controller.py"
SPEC = importlib.util.spec_from_file_location("visual_review_controller", MODULE_PATH)
assert SPEC and SPEC.loader
vrc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vrc)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def write_png(path: Path, width: int = 40, height: int = 30, dpi: int = 300) -> None:
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixels_per_metre = round(dpi / 0.0254)
    phys = struct.pack(">IIB", pixels_per_metre, pixels_per_metre, 1)
    scanline = b"\x00" + (b"\xff\xff\xff" * width)
    payload = signature
    payload += png_chunk(b"IHDR", ihdr)
    payload += png_chunk(b"pHYs", phys)
    payload += png_chunk(b"IDAT", zlib.compress(scanline * height))
    payload += png_chunk(b"IEND", b"")
    path.write_bytes(payload)


class VisualReviewControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data = self.root / "data.csv"
        self.code = self.root / "plot.py"
        self.input = self.root / "intent.json"
        self.data.write_text("x,y\n1,2\n", encoding="utf-8")
        self.code.write_text("STYLE = {'font_size': 6}\n", encoding="utf-8")
        self.input.write_text(json.dumps({"question": "compare"}), encoding="utf-8")
        self.state = vrc.initialize_state(
            review_id="test-review",
            backend="python",
            data_source=self.data,
            code_source=self.code,
            input_source=self.input,
            scheme_id="scheme-test-v1",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def artifacts(self, round_number: int) -> tuple[Path, Path]:
        original = self.root / f"round-{round_number}-original.png"
        final = self.root / f"round-{round_number}-final.png"
        write_png(original, 120, 90)
        write_png(final, 60, 45)
        return original, final

    def review(
        self,
        state: dict,
        *,
        decision: str,
        findings: list[dict] | None = None,
        evidence_level: str = "pixels_only",
    ) -> dict:
        template = vrc.native_review_template(state)
        template["reviewer"] = {
            "method": "native_local_image_view",
            "tool": "codex.view_image",
            "completed": True,
        }
        template["original_size_reviewed"] = True
        template["final_size_reviewed"] = True
        template["evidence_level"] = evidence_level
        template["visible"] = ["labels are visible"]
        template["interpretable"] = []
        template["confirmed"] = []
        template["cannot_assert"] = ["no statistical claim from pixels"]
        template["findings"] = findings or []
        template["decision"] = decision
        template["recommendation"] = "bounded visual revision"
        return template

    @staticmethod
    def finding(code: str, status: str = "open", severity: str = "major") -> dict:
        return {
            "issue_code": code,
            "severity": severity,
            "status": status,
            "evidence": "visible at final physical size",
            "source_view": "final",
        }

    def test_safe_two_round_revision_reaches_delivery_ready(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        state = vrc.ingest_native_review(
            state,
            self.review(state, decision="revise", findings=[self.finding("label_overlap")]),
        )
        self.assertEqual(state["status"], "revise")

        # A visual-only code edit is allowed, but it must be declared in the
        # issue-bound parameter diff and the data hash must remain unchanged.
        self.code.write_text("STYLE = {'font_size': 6, 'repel': True}\n", encoding="utf-8")
        original, final = self.artifacts(2)
        state = vrc.register_render(
            state,
            round_number=2,
            original_path=original,
            final_path=final,
            parameter_diff=[
                {
                    "path": "labels.repel",
                    "issue_code": "label_overlap",
                    "before": False,
                    "after": True,
                }
            ],
        )
        resolved = self.finding("label_overlap", status="resolved")
        state = vrc.ingest_native_review(
            state, self.review(state, decision="keep", findings=[resolved])
        )
        result = vrc.validate_state(state, require_terminal=True)
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["ready_for_delivery"], result)
        self.assertEqual(result["unresolved_blocker_major"], 0)
        self.assertNotEqual(
            state["rounds"][0]["code_sha256"], state["rounds"][1]["code_sha256"]
        )
        self.assertIsNotNone(state["rounds"][0]["artifacts"]["final"]["physical_width_in"])

    def test_wrong_midpoint_requires_explicit_confirmation(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        with self.assertRaisesRegex(vrc.VisualReviewError, "requires at least image_metadata"):
            vrc.ingest_native_review(
                state,
                self.review(
                    state,
                    decision="revise",
                    findings=[self.finding("wrong_midpoint")],
                    evidence_level="pixels_only",
                ),
            )
        state = vrc.ingest_native_review(
            state,
            self.review(
                state,
                decision="revise",
                findings=[self.finding("wrong_midpoint")],
                evidence_level="image_metadata",
            ),
        )
        self.assertEqual(state["status"], "awaiting_confirmation")
        original, final = self.artifacts(2)
        diff = [
            {
                "path": "scale.midpoint",
                "issue_code": "wrong_midpoint",
                "before": 0.5,
                "after": 0.0,
            }
        ]
        with self.assertRaisesRegex(vrc.VisualReviewError, "requires explicit confirmation"):
            vrc.register_render(
                state,
                round_number=2,
                original_path=original,
                final_path=final,
                parameter_diff=diff,
            )
        state = vrc.record_confirmation(
            state,
            round_number=2,
            issue_code="wrong_midpoint",
            parameter_paths=["scale.midpoint"],
            approved_by="scientist",
            rationale="zero is the scientifically defined null value",
        )
        state = vrc.register_render(
            state,
            round_number=2,
            original_path=original,
            final_path=final,
            parameter_diff=diff,
        )
        self.assertTrue(state["rounds"][1]["parameter_diff"][0]["requires_confirmation"])

    def test_data_and_filter_changes_are_blocked(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        state = vrc.ingest_native_review(
            state,
            self.review(state, decision="revise", findings=[self.finding("label_overlap")]),
        )
        original, final = self.artifacts(2)
        with self.assertRaisesRegex(vrc.VisualReviewError, "forbidden"):
            vrc.register_render(
                state,
                round_number=2,
                original_path=original,
                final_path=final,
                parameter_diff=[
                    {
                        "path": "filter.minimum_count",
                        "issue_code": "label_overlap",
                        "before": 1,
                        "after": 5,
                    }
                ],
            )
        self.data.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")
        with self.assertRaisesRegex(vrc.VisualReviewError, "data hash changed"):
            vrc.register_render(
                state,
                round_number=2,
                original_path=original,
                final_path=final,
                parameter_diff=[
                    {
                        "path": "labels.repel",
                        "issue_code": "label_overlap",
                        "before": False,
                        "after": True,
                    }
                ],
            )
        validation = vrc.validate_state(state)
        self.assertFalse(validation["ok"])
        self.assertTrue(
            any(item["code"] == "data_integrity" for item in validation["errors"]),
            validation,
        )

    def test_statistical_change_is_never_automatic(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        state = vrc.ingest_native_review(
            state,
            self.review(
                state,
                decision="revise",
                findings=[self.finding("statistical_semantics_change", severity="blocker")],
                evidence_level="image_code_data",
            ),
        )
        self.assertEqual(state["status"], "awaiting_confirmation")
        original, final = self.artifacts(2)
        diff = [
            {
                "path": "statistics.test",
                "issue_code": "statistical_semantics_change",
                "before": "unpaired",
                "after": "paired",
            }
        ]
        with self.assertRaisesRegex(vrc.VisualReviewError, "requires explicit confirmation"):
            vrc.register_render(
                state,
                round_number=2,
                original_path=original,
                final_path=final,
                parameter_diff=diff,
            )
        state = vrc.record_confirmation(
            state,
            round_number=2,
            issue_code="statistical_semantics_change",
            parameter_paths=["statistics.test"],
            approved_by="analyst",
            rationale="paired samples were verified from the study design",
        )
        state = vrc.register_render(
            state,
            round_number=2,
            original_path=original,
            final_path=final,
            parameter_diff=diff,
        )
        self.assertFalse(state["rounds"][1]["parameter_diff"][0]["automatic_visual_only"])

    def test_native_review_hashes_must_match_render(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        review = self.review(state, decision="keep")
        review["image_hashes_seen"]["final"] = "sha256:" + ("0" * 64)
        with self.assertRaisesRegex(vrc.VisualReviewError, "hashes do not match"):
            vrc.ingest_native_review(state, review)

    def test_artifact_cannot_change_between_render_and_native_review(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        review = self.review(state, decision="keep")
        write_png(final, 61, 45)
        with self.assertRaisesRegex(vrc.VisualReviewError, "changed before native review"):
            vrc.ingest_native_review(state, review)

    def test_third_revision_request_becomes_blocked(self) -> None:
        state = self.state
        for round_number in (1, 2, 3):
            original, final = self.artifacts(round_number)
            diff = []
            if round_number > 1:
                diff = [
                    {
                        "path": "labels.force",
                        "issue_code": "label_overlap",
                        "before": round_number - 1,
                        "after": round_number,
                    }
                ]
            state = vrc.register_render(
                state,
                round_number=round_number,
                original_path=original,
                final_path=final,
                parameter_diff=diff,
            )
            state = vrc.ingest_native_review(
                state,
                self.review(state, decision="revise", findings=[self.finding("label_overlap")]),
            )
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["decision"], "blocked")
        result = vrc.validate_state(state, require_terminal=True)
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["ready_for_delivery"])

    def test_keep_cannot_hide_prior_unresolved_major(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        state = vrc.ingest_native_review(
            state,
            self.review(state, decision="revise", findings=[self.finding("legend_clipped")]),
        )
        original, final = self.artifacts(2)
        state = vrc.register_render(
            state,
            round_number=2,
            original_path=original,
            final_path=final,
            parameter_diff=[
                {
                    "path": "layout.width",
                    "issue_code": "legend_clipped",
                    "before": 4,
                    "after": 5,
                }
            ],
        )
        with self.assertRaisesRegex(vrc.VisualReviewError, "remain open"):
            vrc.ingest_native_review(state, self.review(state, decision="keep", findings=[]))

    def test_required_issue_registry_entries_exist(self) -> None:
        registry = vrc.load_registry()
        required = {
            "label_overlap",
            "legend_clipped",
            "font_too_small",
            "cross_panel_color_inconsistent",
            "red_green_only",
            "missing_colorbar",
            "wrong_midpoint",
        }
        self.assertTrue(required.issubset(registry["issues"]))
        self.assertTrue(registry["issues"]["wrong_midpoint"]["requires_confirmation"])
        self.assertFalse(registry["issues"]["wrong_midpoint"]["safe_auto"])

    def test_unknown_issue_cannot_authorize_automatic_revision(self) -> None:
        original, final = self.artifacts(1)
        state = vrc.register_render(
            self.state, round_number=1, original_path=original, final_path=final
        )
        state = vrc.ingest_native_review(
            state,
            self.review(state, decision="revise", findings=[self.finding("novel_visual_defect")]),
        )
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["decision"], "blocked")
        self.assertEqual(state["rounds"][0]["decision"], "blocked")


if __name__ == "__main__":
    unittest.main()
