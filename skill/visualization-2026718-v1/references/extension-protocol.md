# Scheme v2 extension protocol

Use this protocol to refresh sources, add Schemes/Recipes/components, or change
vocabulary/ranking without destabilizing the curated library.

## Source refresh

1. Run `plot_library.py audit-source --source <path>` and
   `plot_library.py update --source <path> --dry-run`.
2. Compare normalized article content and checksums, not filename alone. Keep the
   source archive immutable.
3. Assign every new/changed fence one BlockDisposition and every image one
   ImageDisposition. Preserve raw language labels and provenance.
4. Extract independent visual encodings by code object chain and image panels;
   do not aggregate an article into one broad family card.
5. Separate source semantics from any biomedical target adapter. Record all
   required variable mappings and unsupported claims.
6. Native-review every final, reference, uncertain, shared, multipanel, or
   suspected-mismatch image before scientific-atlas admission.
7. Produce added, changed, split, deprecated, excluded, conflicting, and
   unresolved sets. Never delete or overwrite curated content on ambiguity.
8. Rebuild Scheme catalog, dispositions, aliases, retrieval index, coverage,
   legacy compatibility atlas, and HTML/Markdown/CSV export deterministically.
9. Reject atomic swap if a promoted Recipe source ID/fingerprint, compatibility
   reference, alias, image, or lineage parent no longer resolves.
10. Apply only with explicit authorization. Exclude state, cookies, sessions,
    credentials, user history, and temporary tools.

## Add a Scheme

1. Search exact subtype, source fingerprints, object chains, and controlled
   aliases for duplicates.
2. Create `VisualizationSchemeV2` with exact geometry subtype, source/target
   semantics, inputs, transformations, channels, claim boundaries, confusable
   subtypes, lineage, image evidence, and statuses.
3. Link all relevant base/modifier/layout/export blocks and object evolution;
   classify non-participating blocks independently.
4. Assign image roles, panel locators, native review, code-image consistency, and
   VisualFingerprint. Do not use nearest-image distance alone.
5. Add aliases only when their meaning is controlled. Add negative terms for
   common false matches and preserve one-to-many ambiguity.

## Add a formal Recipe or component

1. Keep the Scheme/candidate record separate from formal Recipe storage.
2. Generalize source logic into a callable R function or Python module. Remove
   hard-coded data, paths, install/download, workspace clearing, and implicit
   writes; preserve lineage/fingerprints.
3. Define SemanticCard, compatibility, conflicts, parameters, outputs, claim
   limits, fixture, and final-size export contract.
4. Validate schema, syntax, safety, semantics, execution, render, native visual
   review, provenance, and export.
5. Promote only through explicit `promote --apply` with no blocker/major finding.

## Extend vocabulary or ranking

- Add bilingual aliases only for an unambiguous method, subtype, variable,
  object, or visual treatment. Chinese lexical matching uses 2–4 character
  n-grams; single-character overlap never scores.
- Treat `p.adjust`, `GeneRatio`, `Count`, `avg.exp`, and `pct.exp` as variables
  unless the request explicitly asks for source code/function identifiers.
- Add a subtype for a materially different mark/channel/interpretation. Add a
  broad family only for a new scientific question or data topology.
- Change scientific or appearance weights only with versioned benchmarks that
  preserve all hard gates and target metrics.
- Feedback learning, embeddings, telemetry, and network retrieval remain off.

## Stable identity and migration

- Promoted IDs are immutable. Wording or alias clarification keeps the ID;
  incompatible behavior/input/statistics/output changes create a new major ID.
- Store alias targets as arrays. Split legacy cards into all exact Schemes and
  require disambiguation instead of choosing one silently.
- Map invalid/decorative legacy cards to deprecated excluded records so audit
  lineage remains visible.
- Generated fields never overwrite curated semantics, visual decisions, Recipes,
  or promotion status.

## Acceptance

- Disposition accounting is exact, Scheme links resolve, and no private path or
  request history enters public search text.
- New exact and fuzzy prompts retrieve the Scheme; representative old prompts
  preserve a valid scientific Top-3.
- Scientific atlas contains no decorative or non-native preview.
- Incompatible component combinations fail with actionable explanations.
- A no-change update is byte-stable except explicitly declared timestamps.
