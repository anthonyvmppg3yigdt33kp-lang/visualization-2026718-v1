#!/usr/bin/env python3
"""Deterministic state controller for native scientific-figure review.

This module intentionally has no image-semantic model.  It records render
artifacts, accepts a review produced after Codex (or another declared native
viewer) actually opens both images, maps issue codes to bounded actions, and
validates a maximum-three-round review trail.

The public functions are CLI-friendly and may also be imported by
``plot_library.py`` without shelling out:

``initialize_state`` -> ``register_render`` -> ``ingest_native_review`` ->
(``record_confirmation`` -> ``register_render`` -> ...) -> ``validate_state``.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import hashlib
import json
import os
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_ROOT.parent
DEFAULT_REGISTRY_PATH = SKILL_ROOT / "references" / "visual-issue-actions.json"
STATE_SCHEMA_VERSION = "1.0"
TERMINAL_DECISIONS = {"keep", "reselect", "blocked"}
ALL_DECISIONS = TERMINAL_DECISIONS | {"revise"}
SEVERITIES = {"blocker", "major", "minor"}
SHA256_PREFIX = "sha256:"
EVIDENCE_RANK = {
    "pixels_only": 0,
    "image_metadata": 1,
    "image_code": 2,
    "image_code_data": 3,
}


class VisualReviewError(ValueError):
    """Raised when a state transition would violate the review contract."""


def canonical_json(value: Any) -> str:
    """Serialize *value* deterministically for hashing and state files."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: str | Path) -> str:
    target = Path(path).expanduser().resolve()
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return SHA256_PREFIX + digest.hexdigest()


def sha256_value(value: Any) -> str:
    return SHA256_PREFIX + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _valid_sha256(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    raw = value.removeprefix(SHA256_PREFIX)
    return len(raw) == 64 and all(character in "0123456789abcdef" for character in raw.lower())


def _digest_source(value: str | Path) -> dict[str, Any]:
    """Resolve a file or explicit sha256 digest into a traceable descriptor."""

    text = str(value)
    if _valid_sha256(text):
        digest = text if text.startswith(SHA256_PREFIX) else SHA256_PREFIX + text
        return {"path": None, "sha256": digest, "verification": "digest_supplied"}
    path = Path(text).expanduser().resolve()
    if not path.is_file():
        raise VisualReviewError(f"hash source is not a readable file: {path}")
    return {"path": str(path), "sha256": sha256_file(path), "verification": "file_hashed"}


def load_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve()
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualReviewError(f"cannot load visual issue registry: {exc}") from exc
    if not isinstance(registry.get("issues"), dict):
        raise VisualReviewError("visual issue registry has no issues mapping")
    return registry


def _read_png_metadata(path: Path) -> dict[str, Any] | None:
    """Small standard-library PNG fallback (IHDR and optional pHYs only)."""

    try:
        with path.open("rb") as handle:
            if handle.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
            width = height = None
            dpi_x = dpi_y = None
            while True:
                length_bytes = handle.read(4)
                if len(length_bytes) != 4:
                    break
                length = struct.unpack(">I", length_bytes)[0]
                kind = handle.read(4)
                payload = handle.read(length)
                handle.read(4)  # CRC; file hash already protects integrity.
                if kind == b"IHDR" and len(payload) >= 8:
                    width, height = struct.unpack(">II", payload[:8])
                elif kind == b"pHYs" and len(payload) == 9 and payload[8] == 1:
                    pixels_x, pixels_y = struct.unpack(">II", payload[:8])
                    dpi_x = pixels_x * 0.0254 if pixels_x else None
                    dpi_y = pixels_y * 0.0254 if pixels_y else None
                elif kind == b"IEND":
                    break
            if width and height:
                return {
                    "format": "PNG",
                    "pixel_width": int(width),
                    "pixel_height": int(height),
                    "dpi_x": round(dpi_x, 4) if dpi_x else None,
                    "dpi_y": round(dpi_y, 4) if dpi_y else None,
                    "metadata_reader": "stdlib_png",
                }
    except (OSError, struct.error):
        return None
    return None


def _image_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] | None = None
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            dpi = image.info.get("dpi")
            dpi_x = float(dpi[0]) if isinstance(dpi, (tuple, list)) and dpi else None
            dpi_y = float(dpi[1]) if isinstance(dpi, (tuple, list)) and len(dpi) > 1 else dpi_x
            metadata = {
                "format": image.format,
                "pixel_width": int(image.width),
                "pixel_height": int(image.height),
                "dpi_x": round(dpi_x, 4) if dpi_x and dpi_x > 0 else None,
                "dpi_y": round(dpi_y, 4) if dpi_y and dpi_y > 0 else None,
                "metadata_reader": "pillow",
            }
    except (ImportError, OSError, TypeError, ValueError):
        metadata = _read_png_metadata(path)

    if metadata is None:
        return {
            "format": path.suffix.removeprefix(".").upper() or None,
            "pixel_width": None,
            "pixel_height": None,
            "dpi_x": None,
            "dpi_y": None,
            "physical_width_in": None,
            "physical_height_in": None,
            "metadata_reader": "unavailable",
        }
    width = metadata.get("pixel_width")
    height = metadata.get("pixel_height")
    dpi_x = metadata.get("dpi_x")
    dpi_y = metadata.get("dpi_y")
    metadata["physical_width_in"] = round(width / dpi_x, 6) if width and dpi_x else None
    metadata["physical_height_in"] = round(height / dpi_y, 6) if height and dpi_y else None
    return metadata


def describe_artifact(path: str | Path) -> dict[str, Any]:
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise VisualReviewError(f"render artifact is not a readable file: {target}")
    result = {
        "path": str(target),
        "sha256": sha256_file(target),
        "bytes": target.stat().st_size,
    }
    result.update(_image_metadata(target))
    return result


def initialize_state(
    *,
    review_id: str,
    backend: str,
    data_source: str | Path,
    code_source: str | Path,
    input_source: str | Path,
    scheme_id: str | None = None,
    intent: Mapping[str, Any] | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    """Create a new immutable-baseline visual review state."""

    if backend.lower() not in {"python", "r"}:
        raise VisualReviewError("backend must be python or r")
    if not review_id.strip():
        raise VisualReviewError("review_id must be non-empty")
    registry = load_registry(registry_path)
    sources = {
        "data": _digest_source(data_source),
        "code": _digest_source(code_source),
        "input": _digest_source(input_source),
    }
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "review_id": review_id,
        "scheme_id": scheme_id,
        "backend": backend.lower(),
        "intent": copy.deepcopy(dict(intent or {})),
        "controller_capability": "state_and_policy_only_no_visual_model",
        "registry": {
            "path": str(Path(registry_path).expanduser().resolve()),
            "sha256": sha256_file(registry_path),
            "schema_version": registry.get("schema_version"),
        },
        "max_rounds": min(3, int(registry.get("max_rounds", 3))),
        "baseline": {
            "data_sha256": sources["data"]["sha256"],
            "code_sha256": sources["code"]["sha256"],
            "input_sha256": sources["input"]["sha256"],
            "sources": sources,
        },
        "status": "initialized",
        "decision": None,
        "rounds": [],
        "confirmations": [],
    }


def _current_hashes(state: Mapping[str, Any]) -> dict[str, str]:
    baseline = state.get("baseline", {})
    return {
        "data_sha256": str(baseline.get("data_sha256", "")),
        "code_sha256": str(baseline.get("code_sha256", "")),
        "input_sha256": str(baseline.get("input_sha256", "")),
    }


def _rehash_baseline_sources(state: Mapping[str, Any]) -> dict[str, str]:
    baseline = state.get("baseline", {})
    result = _current_hashes(state)
    for name in ("data", "code", "input"):
        descriptor = baseline.get("sources", {}).get(name, {})
        path = descriptor.get("path") if isinstance(descriptor, Mapping) else None
        if path:
            result[f"{name}_sha256"] = sha256_file(path)
    return result


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _confirmation_exists(
    state: Mapping[str, Any], *, round_number: int, issue_code: str, path: str
) -> bool:
    for confirmation in state.get("confirmations", []):
        if not isinstance(confirmation, Mapping) or confirmation.get("approved") is not True:
            continue
        if int(confirmation.get("round", -1)) != round_number:
            continue
        if confirmation.get("issue_code") != issue_code:
            continue
        scopes = confirmation.get("parameter_paths", [])
        if path in scopes or "*" in scopes:
            return True
    return False


def _previous_action_map(state: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rounds = state.get("rounds", [])
    if not rounds:
        return {}
    actions = rounds[-1].get("issue_actions", [])
    return {
        str(action.get("issue_code")): action
        for action in actions
        if isinstance(action, Mapping) and action.get("status") == "proposed"
    }


def validate_parameter_diff(
    state: Mapping[str, Any],
    *,
    round_number: int,
    parameter_diff: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Validate that a revision changes only issue-bound, approved parameters."""

    registry = registry or load_registry(state.get("registry", {}).get("path", DEFAULT_REGISTRY_PATH))
    if round_number == 1 and parameter_diff:
        raise VisualReviewError("round 1 is the baseline render and cannot have a parameter diff")
    if round_number > 1 and not parameter_diff:
        raise VisualReviewError("a revision render must declare a non-empty parameter diff")
    previous_actions = _previous_action_map(state)
    normalized: list[dict[str, Any]] = []
    for raw in parameter_diff:
        if not isinstance(raw, Mapping):
            raise VisualReviewError("each parameter diff entry must be an object")
        path = str(raw.get("path", "")).strip()
        issue_code = str(raw.get("issue_code", "")).strip()
        if not path or not issue_code or "before" not in raw or "after" not in raw:
            raise VisualReviewError("parameter diff requires path, issue_code, before, and after")
        if raw.get("before") == raw.get("after"):
            raise VisualReviewError(f"parameter diff has no change: {path}")
        if _matches_any(path, registry.get("forbidden_parameter_patterns", [])):
            raise VisualReviewError(f"data/statistical parameter is forbidden in visual review: {path}")
        action = previous_actions.get(issue_code)
        if round_number > 1 and action is None:
            raise VisualReviewError(f"parameter change is not tied to the prior native review: {issue_code}")
        issue_spec = registry.get("issues", {}).get(issue_code)
        if not isinstance(issue_spec, Mapping):
            raise VisualReviewError(f"unknown issue code cannot authorize changes: {issue_code}")
        allowed = issue_spec.get("allowed_parameter_patterns", [])
        if not _matches_any(path, allowed):
            raise VisualReviewError(f"parameter is not allowed for {issue_code}: {path}")
        requires_confirmation = bool(issue_spec.get("requires_confirmation")) or _matches_any(
            path, registry.get("confirmation_parameter_patterns", [])
        )
        if requires_confirmation and not _confirmation_exists(
            state, round_number=round_number, issue_code=issue_code, path=path
        ):
            raise VisualReviewError(
                f"parameter requires explicit confirmation for round {round_number}: {path}"
            )
        normalized.append(
            {
                "path": path,
                "issue_code": issue_code,
                "before": copy.deepcopy(raw.get("before")),
                "after": copy.deepcopy(raw.get("after")),
                "requires_confirmation": requires_confirmation,
                "automatic_visual_only": not requires_confirmation,
            }
        )
    return normalized


def register_render(
    state: Mapping[str, Any],
    *,
    round_number: int,
    original_path: str | Path,
    final_path: str | Path,
    parameter_diff: Sequence[Mapping[str, Any]] | None = None,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Register externally rendered artifacts and freeze their evidence hashes."""

    updated = copy.deepcopy(dict(state))
    maximum = int(updated.get("max_rounds", 3))
    rounds = updated.setdefault("rounds", [])
    if not 1 <= round_number <= maximum:
        raise VisualReviewError(f"round must be between 1 and {maximum}")
    if round_number != len(rounds) + 1:
        raise VisualReviewError("render rounds must be registered sequentially without replacement")
    if rounds and rounds[-1].get("decision") != "revise":
        raise VisualReviewError("a new render is allowed only after a revise decision")
    registry = load_registry(registry_path or updated.get("registry", {}).get("path", DEFAULT_REGISTRY_PATH))
    normalized_diff = validate_parameter_diff(
        updated,
        round_number=round_number,
        parameter_diff=list(parameter_diff or []),
        registry=registry,
    )
    expected_hashes = _current_hashes(updated)
    observed_hashes = _rehash_baseline_sources(updated)
    if observed_hashes["data_sha256"] != expected_hashes["data_sha256"]:
        updated["status"] = "blocked"
        updated["decision"] = "blocked"
        raise VisualReviewError("data hash changed during visual-only iteration")
    if round_number == 1 and observed_hashes["input_sha256"] != expected_hashes["input_sha256"]:
        raise VisualReviewError("input hash changed before the baseline render")
    if round_number == 1 and observed_hashes["code_sha256"] != expected_hashes["code_sha256"]:
        raise VisualReviewError("code hash changed before the baseline render")
    round_record = {
        "round": round_number,
        "data_sha256": observed_hashes["data_sha256"],
        "code_sha256": observed_hashes["code_sha256"],
        "input_sha256": observed_hashes["input_sha256"],
        "parameter_diff": normalized_diff,
        "artifacts": {
            "original": describe_artifact(original_path),
            "final": describe_artifact(final_path),
        },
        "native_review": None,
        "issue_actions": [],
        "decision": "pending",
    }
    rounds.append(round_record)
    updated["status"] = "awaiting_native_review"
    updated["decision"] = None
    return updated


def native_review_template(state: Mapping[str, Any], round_number: int | None = None) -> dict[str, Any]:
    rounds = state.get("rounds", [])
    if not rounds:
        raise VisualReviewError("register render artifacts before creating a review template")
    record = rounds[-1] if round_number is None else next(
        (item for item in rounds if item.get("round") == round_number), None
    )
    if not isinstance(record, Mapping):
        raise VisualReviewError("requested review round does not exist")
    artifacts = record.get("artifacts", {})
    return {
        "round": record.get("round"),
        "reviewer": {
            "method": "native_local_image_view",
            "tool": "REPLACE_WITH_NATIVE_VIEWER_NAME",
            "completed": False,
        },
        "image_hashes_seen": {
            "original": artifacts.get("original", {}).get("sha256"),
            "final": artifacts.get("final", {}).get("sha256"),
        },
        "evidence_level": "pixels_only",
        "original_size_reviewed": False,
        "final_size_reviewed": False,
        "visible": [],
        "interpretable": [],
        "confirmed": [],
        "cannot_assert": [],
        "findings": [],
        "decision": "keep",
        "recommendation": "",
    }


def _validate_native_review_payload(
    review: Mapping[str, Any], round_record: Mapping[str, Any], registry: Mapping[str, Any]
) -> None:
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, Mapping):
        raise VisualReviewError("native review requires reviewer metadata")
    if reviewer.get("method") not in registry.get("native_review_methods", []):
        raise VisualReviewError("review method is not an accepted native image-viewing method")
    if reviewer.get("completed") is not True or not reviewer.get("tool"):
        raise VisualReviewError("native image viewing must be explicitly completed with a named tool")
    if review.get("original_size_reviewed") is not True or review.get("final_size_reviewed") is not True:
        raise VisualReviewError("both original and final-size artifacts must be opened")
    evidence = review.get("evidence_level")
    if evidence not in registry.get("evidence_levels", []):
        raise VisualReviewError(f"invalid evidence level: {evidence}")
    if review.get("decision") not in ALL_DECISIONS:
        raise VisualReviewError("review decision must be keep, revise, reselect, or blocked")
    seen = review.get("image_hashes_seen")
    artifacts = round_record.get("artifacts", {})
    if not isinstance(seen, Mapping) or any(
        seen.get(name) != artifacts.get(name, {}).get("sha256") for name in ("original", "final")
    ):
        raise VisualReviewError("native review image hashes do not match registered artifacts")
    for field in ("visible", "interpretable", "confirmed", "cannot_assert"):
        if not isinstance(review.get(field), list):
            raise VisualReviewError(f"native review requires a list field: {field}")
    if evidence == "pixels_only" and review.get("confirmed"):
        raise VisualReviewError("pixels_only review cannot contain data/statistically confirmed claims")
    if not isinstance(review.get("findings"), list):
        raise VisualReviewError("native review findings must be a list")
    for finding in review.get("findings", []):
        if not isinstance(finding, Mapping):
            raise VisualReviewError("each finding must be an object")
        for field in ("issue_code", "severity", "status", "evidence", "source_view"):
            if not finding.get(field):
                raise VisualReviewError(f"finding is missing {field}")
        if finding.get("severity") not in SEVERITIES:
            raise VisualReviewError(f"invalid finding severity: {finding.get('severity')}")
        if finding.get("status") not in {"open", "resolved", "accepted"}:
            raise VisualReviewError(f"invalid finding status: {finding.get('status')}")
        if finding.get("source_view") not in {"original", "final", "both"}:
            raise VisualReviewError("finding source_view must be original, final, or both")
        issue_spec = registry.get("issues", {}).get(str(finding.get("issue_code")), {})
        minimum_evidence = issue_spec.get("minimum_evidence_level") if isinstance(issue_spec, Mapping) else None
        if minimum_evidence and EVIDENCE_RANK.get(str(evidence), -1) < EVIDENCE_RANK.get(
            str(minimum_evidence), 99
        ):
            raise VisualReviewError(
                f"{finding.get('issue_code')} requires at least {minimum_evidence} evidence"
            )


def ingest_native_review(
    state: Mapping[str, Any],
    review: Mapping[str, Any],
    *,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Attach a completed native review and derive bounded next actions."""

    updated = copy.deepcopy(dict(state))
    rounds = updated.get("rounds", [])
    if not rounds or updated.get("status") != "awaiting_native_review":
        raise VisualReviewError("state is not awaiting a native review")
    round_record = rounds[-1]
    if int(review.get("round", -1)) != int(round_record.get("round", -2)):
        raise VisualReviewError("native review round does not match the active render")
    live_hashes = _rehash_baseline_sources(updated)
    if live_hashes.get("data_sha256") != updated.get("baseline", {}).get("data_sha256"):
        raise VisualReviewError("data hash changed before native review")
    for key in ("code_sha256", "input_sha256"):
        if live_hashes.get(key) != round_record.get(key):
            raise VisualReviewError(f"{key} changed after render and before native review")
    for view in ("original", "final"):
        artifact = round_record.get("artifacts", {}).get(view, {})
        path = artifact.get("path") if isinstance(artifact, Mapping) else None
        if not path or not Path(str(path)).is_file():
            raise VisualReviewError(f"registered {view} artifact is unavailable for native review")
        if sha256_file(path) != artifact.get("sha256"):
            raise VisualReviewError(f"registered {view} artifact changed before native review")
    registry = load_registry(registry_path or updated.get("registry", {}).get("path", DEFAULT_REGISTRY_PATH))
    _validate_native_review_payload(review, round_record, registry)
    actions: list[dict[str, Any]] = []
    for finding in review.get("findings", []):
        if finding.get("status") != "open":
            continue
        issue_code = str(finding.get("issue_code"))
        issue_spec = registry.get("issues", {}).get(issue_code)
        if not isinstance(issue_spec, Mapping):
            actions.append(
                {
                    "issue_code": issue_code,
                    "status": "blocked_unknown_issue",
                    "safe_auto": False,
                    "requires_confirmation": True,
                    "action": "No registered action; obtain explicit scientific/implementation review.",
                    "allowed_parameter_patterns": [],
                }
            )
            continue
        actions.append(
            {
                "issue_code": issue_code,
                "severity": finding.get("severity"),
                "status": "proposed",
                "safe_auto": bool(issue_spec.get("safe_auto")),
                "requires_confirmation": bool(issue_spec.get("requires_confirmation")),
                "confirmation_scope": issue_spec.get("confirmation_scope"),
                "action": issue_spec.get("action"),
                "allowed_parameter_patterns": list(issue_spec.get("allowed_parameter_patterns", [])),
                "invariant": issue_spec.get("invariant"),
            }
        )
    decision = str(review.get("decision"))
    if decision == "revise" and not actions:
        raise VisualReviewError("revise decision requires at least one open finding")
    if decision == "keep":
        issue_statuses: dict[str, Mapping[str, Any]] = {}
        for earlier_round in rounds[:-1]:
            earlier_review = earlier_round.get("native_review")
            if not isinstance(earlier_review, Mapping):
                continue
            for earlier_finding in earlier_review.get("findings", []):
                if isinstance(earlier_finding, Mapping) and earlier_finding.get("issue_code"):
                    issue_statuses[str(earlier_finding["issue_code"])] = earlier_finding
        for current_finding in review.get("findings", []):
            if isinstance(current_finding, Mapping) and current_finding.get("issue_code"):
                issue_statuses[str(current_finding["issue_code"])] = current_finding
        unresolved_serious = [
            finding
            for finding in issue_statuses.values()
            if finding.get("status") != "resolved" and finding.get("severity") in {"blocker", "major"}
        ]
        if unresolved_serious:
            raise VisualReviewError("keep is invalid while blocker/major findings remain open")
    if decision == "revise" and int(round_record.get("round")) >= int(updated.get("max_rounds", 3)):
        decision = "blocked"
        review = dict(review)
        review["decision_requested"] = "revise"
        review["decision"] = "blocked"
        review["controller_note"] = "Maximum visual-only revision rounds reached."
    if any(action.get("status") == "blocked_unknown_issue" for action in actions) and decision == "revise":
        decision = "blocked"
        review = dict(review)
        review["decision_requested"] = "revise"
        review["decision"] = "blocked"
        review["controller_note"] = "An unregistered issue cannot authorize an automatic revision."
        updated["status"] = "blocked"
    elif decision == "revise" and any(action.get("requires_confirmation") for action in actions):
        updated["status"] = "awaiting_confirmation"
    else:
        updated["status"] = decision
    round_record["native_review"] = copy.deepcopy(dict(review))
    round_record["issue_actions"] = actions
    round_record["decision"] = decision
    updated["decision"] = decision if decision in TERMINAL_DECISIONS else None
    return updated


def record_confirmation(
    state: Mapping[str, Any],
    *,
    round_number: int,
    issue_code: str,
    parameter_paths: Sequence[str],
    approved_by: str,
    rationale: str,
) -> dict[str, Any]:
    """Record explicit approval for a scale-semantic parameter change."""

    updated = copy.deepcopy(dict(state))
    if not approved_by.strip() or not rationale.strip() or not parameter_paths:
        raise VisualReviewError("confirmation requires approver, rationale, and parameter paths")
    rounds = updated.get("rounds", [])
    if not rounds or int(rounds[-1].get("round", -1)) + 1 != round_number:
        raise VisualReviewError("confirmation round must be the next render round")
    action = _previous_action_map(updated).get(issue_code)
    if not action or action.get("requires_confirmation") is not True:
        raise VisualReviewError("issue does not have a pending confirmation-required action")
    updated.setdefault("confirmations", []).append(
        {
            "round": round_number,
            "issue_code": issue_code,
            "parameter_paths": sorted(set(str(path) for path in parameter_paths)),
            "approved": True,
            "approved_by": approved_by,
            "rationale": rationale,
        }
    )
    if updated.get("status") == "awaiting_confirmation":
        updated["status"] = "revise"
    return updated


def validate_state(
    state: Mapping[str, Any],
    *,
    verify_files: bool = True,
    require_terminal: bool = False,
) -> dict[str, Any]:
    """Validate state shape, hashes, review evidence, and delivery readiness."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def add(collection: list[dict[str, str]], code: str, message: str) -> None:
        collection.append({"code": code, "message": message})

    if state.get("schema_version") != STATE_SCHEMA_VERSION:
        add(errors, "schema_version", "unsupported or missing state schema version")
    if state.get("controller_capability") != "state_and_policy_only_no_visual_model":
        add(errors, "capability_claim", "controller capability boundary is missing")
    maximum = state.get("max_rounds")
    if not isinstance(maximum, int) or maximum < 1 or maximum > 3:
        add(errors, "max_rounds", "max_rounds must be an integer from 1 to 3")
        maximum = 3
    baseline = state.get("baseline", {})
    for key in ("data_sha256", "code_sha256", "input_sha256"):
        if not _valid_sha256(baseline.get(key)):
            add(errors, "baseline_hash", f"invalid baseline {key}")
    rounds = state.get("rounds")
    if not isinstance(rounds, list):
        add(errors, "rounds", "rounds must be a list")
        rounds = []
    if len(rounds) > maximum:
        add(errors, "round_limit", "visual review contains more than three rounds")
    expected_rounds = list(range(1, len(rounds) + 1))
    actual_rounds = [record.get("round") for record in rounds if isinstance(record, Mapping)]
    if actual_rounds != expected_rounds:
        add(errors, "round_sequence", "rounds must be consecutive integers starting at 1")
    registry_path = state.get("registry", {}).get("path", DEFAULT_REGISTRY_PATH)
    try:
        registry = load_registry(registry_path)
    except VisualReviewError as exc:
        add(errors, "registry", str(exc))
        registry = {"evidence_levels": [], "native_review_methods": [], "issues": {}}

    for index, record in enumerate(rounds, start=1):
        if not isinstance(record, Mapping):
            add(errors, "round_record", f"round {index} is not an object")
            continue
        if record.get("data_sha256") != baseline.get("data_sha256"):
            add(errors, "data_integrity", f"round {index} data_sha256 differs from baseline")
        for key in ("code_sha256", "input_sha256"):
            if not _valid_sha256(record.get(key)):
                add(errors, "round_hash", f"round {index} has invalid {key}")
            if index == 1 and record.get(key) != baseline.get(key):
                add(errors, "baseline_integrity", f"round 1 {key} differs from baseline")
        artifacts = record.get("artifacts")
        if not isinstance(artifacts, Mapping):
            add(errors, "artifacts", f"round {index} has no artifacts mapping")
            continue
        for view in ("original", "final"):
            artifact = artifacts.get(view)
            if not isinstance(artifact, Mapping):
                add(errors, "artifact_missing", f"round {index} lacks {view} artifact")
                continue
            if not artifact.get("path") or not _valid_sha256(artifact.get("sha256")):
                add(errors, "artifact_identity", f"round {index} {view} lacks path/hash")
            width, height = artifact.get("pixel_width"), artifact.get("pixel_height")
            if artifact.get("metadata_reader") != "unavailable" and (
                not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0
            ):
                add(errors, "artifact_dimensions", f"round {index} {view} has invalid pixel dimensions")
            dpi_x, dpi_y = artifact.get("dpi_x"), artifact.get("dpi_y")
            physical_x, physical_y = artifact.get("physical_width_in"), artifact.get("physical_height_in")
            if (dpi_x or dpi_y) and not (physical_x and physical_y):
                add(errors, "physical_size", f"round {index} {view} DPI lacks derived physical size")
            if width and dpi_x and physical_x and abs(float(physical_x) - (width / float(dpi_x))) > 1e-4:
                add(errors, "physical_size", f"round {index} {view} width/DPI is inconsistent")
            if height and dpi_y and physical_y and abs(float(physical_y) - (height / float(dpi_y))) > 1e-4:
                add(errors, "physical_size", f"round {index} {view} height/DPI is inconsistent")
            if not dpi_x or not dpi_y:
                add(warnings, "dpi_unavailable", f"round {index} {view} has no readable embedded DPI")
            if verify_files and artifact.get("path"):
                path = Path(str(artifact.get("path")))
                if not path.is_file():
                    add(errors, "artifact_unreadable", f"round {index} {view} file is missing")
                else:
                    actual = describe_artifact(path)
                    if actual.get("sha256") != artifact.get("sha256"):
                        add(errors, "artifact_hash", f"round {index} {view} file hash changed")
                    for metadata_key in (
                        "pixel_width",
                        "pixel_height",
                        "dpi_x",
                        "dpi_y",
                        "physical_width_in",
                        "physical_height_in",
                    ):
                        if actual.get(metadata_key) != artifact.get(metadata_key):
                            add(
                                errors,
                                "artifact_metadata",
                                f"round {index} {view} stored {metadata_key} does not match the file",
                            )
        review = record.get("native_review")
        if review is None:
            add(errors, "native_review_missing", f"round {index} has no completed native review")
        elif isinstance(review, Mapping):
            try:
                _validate_native_review_payload(review, record, registry)
            except VisualReviewError as exc:
                add(errors, "native_review_invalid", f"round {index}: {exc}")
        else:
            add(errors, "native_review_invalid", f"round {index} native review is not an object")
        try:
            validate_parameter_diff(
                {**state, "rounds": list(rounds[: index - 1])},
                round_number=index,
                parameter_diff=record.get("parameter_diff", []),
                registry=registry,
            )
        except VisualReviewError as exc:
            add(errors, "parameter_diff", f"round {index}: {exc}")

    # Data must remain immutable; code/config may change only through a declared
    # revision, so their live files should match the latest recorded round.
    if verify_files and rounds:
        try:
            live_hashes = _rehash_baseline_sources(state)
            if live_hashes["data_sha256"] != baseline.get("data_sha256"):
                add(errors, "data_integrity", "live data hash differs from immutable baseline")
            last_round = rounds[-1]
            for key in ("code_sha256", "input_sha256"):
                if live_hashes.get(key) != last_round.get(key):
                    add(errors, "live_hash", f"live {key} differs from the latest reviewed round")
        except (OSError, VisualReviewError) as exc:
            add(errors, "baseline_source", f"cannot verify live baseline sources: {exc}")

    issue_statuses: dict[str, Mapping[str, Any]] = {}
    for record in rounds:
        review = record.get("native_review") if isinstance(record, Mapping) else None
        if not isinstance(review, Mapping):
            continue
        for finding in review.get("findings", []):
            if isinstance(finding, Mapping) and finding.get("issue_code"):
                issue_statuses[str(finding["issue_code"])] = finding
    unresolved = [
        finding
        for finding in issue_statuses.values()
        if finding.get("status") != "resolved" and finding.get("severity") in {"blocker", "major"}
    ]
    if state.get("decision") == "keep" and unresolved:
        add(errors, "unresolved_serious", "keep state has unresolved blocker/major findings")
    if require_terminal and state.get("decision") not in TERMINAL_DECISIONS:
        add(errors, "not_terminal", "review has not reached keep, reselect, or blocked")
    if state.get("decision") == "keep" and len(rounds) == 0:
        add(errors, "empty_keep", "keep decision cannot be made without a reviewed render")
    ready = not errors and state.get("decision") == "keep" and not unresolved
    return {
        "ok": not errors,
        "ready_for_delivery": ready,
        "status": state.get("status"),
        "decision": state.get("decision"),
        "round_count": len(rounds),
        "errors": errors,
        "warnings": warnings,
        "unresolved_blocker_major": len(unresolved),
        "controller_capability": "state_and_policy_only_no_visual_model",
    }


def read_state(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualReviewError(f"cannot read review state: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualReviewError("review state root must be an object")
    return value


def write_state(path: str | Path, state: Mapping[str, Any]) -> None:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    handle, temporary = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json_argument(value: str) -> Any:
    path = Path(value)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="State-only controller for externally rendered and natively reviewed figures."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="initialize immutable review hashes")
    init.add_argument("--state", required=True)
    init.add_argument("--review-id", required=True)
    init.add_argument("--backend", required=True, choices=("python", "r"))
    init.add_argument("--data", required=True, help="data file or sha256 digest")
    init.add_argument("--code", required=True, help="code file or sha256 digest")
    init.add_argument("--input", required=True, help="input/config file or sha256 digest")
    init.add_argument("--scheme-id")
    init.add_argument("--intent", help="JSON string or file")
    init.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))

    render = subparsers.add_parser("register-render", help="register original/final artifacts")
    render.add_argument("--state", required=True)
    render.add_argument("--round", type=int, required=True)
    render.add_argument("--original", required=True)
    render.add_argument("--final", required=True)
    render.add_argument("--parameter-diff", default="[]", help="JSON string or file")

    template = subparsers.add_parser("review-template", help="emit a native-review JSON template")
    template.add_argument("--state", required=True)
    template.add_argument("--output")

    ingest = subparsers.add_parser("ingest-review", help="ingest native-viewer review JSON")
    ingest.add_argument("--state", required=True)
    ingest.add_argument("--review", required=True, help="JSON string or file")

    confirm = subparsers.add_parser("confirm", help="record confirmation-required scale change")
    confirm.add_argument("--state", required=True)
    confirm.add_argument("--round", type=int, required=True)
    confirm.add_argument("--issue-code", required=True)
    confirm.add_argument("--parameter", action="append", required=True)
    confirm.add_argument("--approved-by", required=True)
    confirm.add_argument("--rationale", required=True)

    validate = subparsers.add_parser("validate", help="validate review evidence and hashes")
    validate.add_argument("--state", required=True)
    validate.add_argument("--no-verify-files", action="store_true")
    validate.add_argument("--require-terminal", action="store_true")

    show = subparsers.add_parser("show", help="print state")
    show.add_argument("--state", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            state = initialize_state(
                review_id=args.review_id,
                backend=args.backend,
                data_source=args.data,
                code_source=args.code,
                input_source=args.input,
                scheme_id=args.scheme_id,
                intent=_load_json_argument(args.intent) if args.intent else {},
                registry_path=args.registry,
            )
            write_state(args.state, state)
            _print_json({"ok": True, "state": str(Path(args.state).resolve()), "status": state["status"]})
            return 0
        state = read_state(args.state)
        if args.command == "register-render":
            diff = _load_json_argument(args.parameter_diff)
            if not isinstance(diff, list):
                raise VisualReviewError("parameter diff must be a JSON list")
            state = register_render(
                state,
                round_number=args.round,
                original_path=args.original,
                final_path=args.final,
                parameter_diff=diff,
            )
            write_state(args.state, state)
            _print_json({"ok": True, "status": state["status"], "round": args.round})
            return 0
        if args.command == "review-template":
            template = native_review_template(state)
            if args.output:
                write_state(args.output, template)
                _print_json({"ok": True, "output": str(Path(args.output).resolve())})
            else:
                _print_json(template)
            return 0
        if args.command == "ingest-review":
            review = _load_json_argument(args.review)
            if not isinstance(review, dict):
                raise VisualReviewError("review must be a JSON object")
            state = ingest_native_review(state, review)
            write_state(args.state, state)
            _print_json({"ok": True, "status": state["status"], "decision": state["rounds"][-1]["decision"]})
            return 0
        if args.command == "confirm":
            state = record_confirmation(
                state,
                round_number=args.round,
                issue_code=args.issue_code,
                parameter_paths=args.parameter,
                approved_by=args.approved_by,
                rationale=args.rationale,
            )
            write_state(args.state, state)
            _print_json({"ok": True, "status": state["status"]})
            return 0
        if args.command == "validate":
            result = validate_state(
                state,
                verify_files=not args.no_verify_files,
                require_terminal=args.require_terminal,
            )
            _print_json(result)
            return 0 if result["ok"] else 2
        if args.command == "show":
            _print_json(state)
            return 0
    except (VisualReviewError, OSError, json.JSONDecodeError) as exc:
        _print_json({"ok": False, "error": str(exc), "controller_capability": "state_and_policy_only_no_visual_model"})
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
