# Promote mode

Use only when the user explicitly asks to register a validated candidate as a
formal recipe or component.

1. Require an explicit candidate ID and explicit apply intent; otherwise produce a
   dry-run promotion report.
2. Load the recipe schema, QA contract, and extension protocol. Verify stable ID,
   backend, contract, SemanticCard, code, lineage, provenance, and preview.
3. Require syntax and fixture success where dependencies exist, plus visual review
   of the selected preview at final size. Missing specialist dependencies may
   retain `parse-verified` status but cannot be labeled `verified`.
4. Reject candidates containing installers, downloads, workspace clearing,
   working-directory changes, hard-coded private paths, implicit writes, invented
   statistics, or unresolved compatibility conflicts.
5. Register atomically, rebuild deterministic indexes, and verify that existing
   stable IDs and manual records remain unchanged.

Promotion never authorizes publishing, uploading, telemetry, or disclosure of
private source provenance.
