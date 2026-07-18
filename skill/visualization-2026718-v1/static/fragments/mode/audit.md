# Audit mode

Use for read-only assessment of code, recipes, catalog records, provenance,
coverage, or an existing figure workflow.

1. Declare the audited artifacts and available evidence; do not infer absent data,
   packages, execution, or visual inspection.
2. Load the recipe schema and QA contract. Check contract completeness, stable IDs,
   code safety, compatibility, lineage, source status, validation tier, and claim
   boundaries.
3. Inspect an actual image before making visual findings. A code-only audit may
   assess mappings but not rendered appearance.
4. Prioritize findings by scientific invalidity, execution failure, misleading
   encoding, provenance risk, then maintainability.
5. Report evidence and residual uncertainty. Do not edit, promote, or rerender
   unless the user separately authorizes that action.

Backend is optional for static audit; it becomes mandatory before execution or
backend-specific rendering.
