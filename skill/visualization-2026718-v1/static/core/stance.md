# Default stance

- Start from the scientific question, analysis unit, data topology, and evidence
  role; treat style words as secondary constraints.
- Prefer a quantitative sample-, donor-, or patient-level panel when an embedding
  only offers a cell-level overview. Pair overview and evidence when one chart
  cannot support the claim.
- Distinguish visible pixels, metadata/legend interpretation, code-confirmed
  mappings, and source-data-confirmed results. Do not upgrade evidence implicitly.
- Treat association, prediction, inferred communication, and dimensionality
  reduction as distinct from causation, mechanism, physical interaction, and
  statistical significance.
- Prefer direct, legible encodings and restrained color. Preserve condition colors
  across panels; do not use color as the only carrier of critical information.
- Keep raw sources immutable. Preserve provenance and lineage internally, but do
  not expose private paths, internal filenames, or template identifiers unless
  the user explicitly requests an audit trail.
- Keep retrieval offline and deterministic. Do not add embeddings, network calls,
  implicit package installation, downloads, or telemetry.
- Return plot objects by default. Do not clear the workspace, change the working
  directory, hard-code local paths, or save files unless explicitly requested.
- Use `r` fences for R and `python` fences for Python. Do not silently translate a
  recipe across backends.
- If image viewing is unavailable or an artifact cannot be opened, report that
  visual review was not performed. Never infer a rendered result solely from code.
- A derived candidate is temporary. Register it only through explicit promotion
  after code, semantic, visual, execution, and provenance gates pass.
