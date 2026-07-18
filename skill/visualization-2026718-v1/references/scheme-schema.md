# Scheme v2 data contract

Load this reference when building, validating, migrating, inspecting, or
exporting the Scheme catalog and its source dispositions.

## Contents

1. [Record sets](#record-sets)
2. [VisualizationSchemeV2](#visualizationschemev2)
3. [Source semantics and target application](#source-semantics-and-target-application)
4. [Code lineage](#code-lineage)
5. [Image evidence](#image-evidence)
6. [BlockDisposition](#blockdisposition)
7. [ImageDisposition](#imagedisposition)
8. [Eligibility, code, Recipe, and review states](#eligibility-code-recipe-and-review-states)
9. [Stable IDs and aliases](#stable-ids-and-aliases)
10. [Validation invariants](#validation-invariants)

## Record sets

Scheme v2 uses six deterministic generated files:

| File | Purpose |
|---|---|
| `scheme-catalog.jsonl` | One record per independent visual encoding Scheme. |
| `block-dispositions.jsonl` | Exactly one role and reason for every source code fence. |
| `image-dispositions.jsonl` | Exactly one role and reason for every source image. |
| `scheme-aliases.json` | Legacy ID and controlled text aliases; one-to-many mappings remain arrays. |
| `retrieval-index.json` | Precomputed offline token-to-Scheme inverted index. |
| `scheme-coverage.json` | Counts, integrity checks, exclusions, and release-gate summary. |

These files are generated views. Curated Recipes, native visual-review decisions
under `native-visual-reviews/*.jsonl`, callable-but-unpromoted candidate modules
under `assets/scheme-candidates/`, and promotion records remain separate and may
not be overwritten by regeneration.

## VisualizationSchemeV2

Each line in `scheme-catalog.jsonl` is a JSON object with:

- `schema_version`: exactly `2.0`.
- `scheme_id`: stable ID defined below.
- `title`: concise, specific human name.
- `eligibility`: one controlled eligibility value.
- `broad_family`: scientific family used for high-level compatibility.
- `geometry_subtype`: the exact mark/geometry arrangement; never replace this
  with the broad family.
- `appearance_subtype`: the more specific native-image phenotype when the
  reviewed preview distinguishes variants inside the parsed geometry subtype
  (for example `embedding_density_contour` versus a generic embedding family).
- `analysis_method`: method represented by the source or `general_visualization`.
- `source_semantics`: what the source code actually visualizes.
- `target_application`: any generalized biomedical/omics use and its explicit
  adapter contract.
- `visual_channels`: semantic mapping for position, angle, radius, color, size,
  shape, alpha, edge, facet, label, and annotation as applicable.
- `required_inputs`, `optional_inputs`, and `transformations`.
- `code_lineage` and `image_evidence`.
- `supported_claims`, `claim_limits`, `misread_risks`, and
  `recommended_companion`.
- `aliases_zh`, `aliases_en`, `fuzzy_descriptions`, `visual_feature_terms`,
  `confusable_with`, and `negative_terms`.
- `backends`, `code_status`, and structured `validation`.
- `source`: article ID, title, album ID, and sequence. Local paths are internal
  provenance and must not appear in ordinary user-facing output.
- `legacy_style_ids`: zero or more compatibility aliases.
- `search_document`: normalized deterministic retrieval text; it is not a
  replacement for the structured fields.

Do not create a Scheme merely because an article mentions a package or contains
a code fence. A Scheme requires an identifiable visual encoding, a visual-only
reference, or an explicitly classified modifier/resource/exclusion.

## Source semantics and target application

Keep source truth separate from intended reuse.

`source_semantics` declares:

- `question`
- `unit`
- `data_topology`
- `variables`
- `statistical_intent`

`target_application` declares:

- `question`
- `adapter_required`
- `variable_mapping`

For example, a radial hiking summary may be adapted to an enrichment rose plot,
but the record must state that the source does not itself calculate NES or FDR.
The adapter maps pathway, direction, adjusted significance, count, or another
declared field; it does not silently invent those values.

## Code lineage

`code_lineage` records all code involved in the final Scheme:

- `block_ids`: ordered union of relevant blocks.
- `base_block_ids`: base plotting objects.
- `modifier_block_ids`: semantic or aesthetic changes.
- `layout_block_ids`: panel assembly and legend layout.
- `export_block_ids`: explicit export only.
- `object_chain`: object evolution such as `plt -> p1 -> p2`.
- `calls`: detected plotting and composition calls.

A block may contribute to more than one Scheme, but every source block has one
global BlockDisposition. Never concatenate arbitrary strings to derive a Recipe.
Use the component compatibility contract.

## Image evidence

`image_evidence` declares:

- `primary_image_id`
- `final_image_ids`
- `reference_image_ids`
- `intermediate_image_ids`
- `review_status`
- `code_image_consistency`
- `evidence_level`: `none`, `image_metadata`, or `image_code` for generated
  Scheme records; never use `image_code_data` unless the underlying values and
  statistics were actually recomputed.
- `panel_locator`: the reviewed panel or crop when an image contains more than
  one visual Scheme.

The primary image is not selected by proximity alone. It must be linked through
article context, code lineage, panel structure, and native visual inspection when
used in the scientific atlas.

Scientific-atlas admission requires all of:

1. `eligibility=scientific_scheme`.
2. Primary image role is `scientific_result` or `published_reference`.
3. `review_status=native_reviewed`.
4. Code-image consistency is declared; `mismatch` is excluded.

An unreviewed scientific Scheme remains searchable/auditable but is withheld from
the default scientific visual atlas. A visual-only paper reference may be
admitted only as `visual_reference`, never as executable code.

## BlockDisposition

Every one of the 621 source fences has one record containing at least
`schema_version`, `block_id`, `article_id`, `disposition`, `reason`, and source
provenance. `disposition` is exactly one of:

- `setup`
- `install_download`
- `data_prep`
- `plot_base`
- `semantic_modifier`
- `aesthetic_modifier`
- `layout`
- `export`
- `analysis_only`
- `prompt_non_code`
- `decorative`
- `nonplot_output`

BlockDisposition describes the block's primary global role. Scheme lineage then
describes how eligible blocks participate in one or more specific schemes.
Install/download, prompt-only, decorative, and non-plot records are never treated
as plotting code.

## ImageDisposition

Every one of the 709 source images has one record containing at least
`schema_version`, `image_id`, `article_id`, `role`, `reason`, and source
provenance. `role` is exactly one of:

- `scientific_result`
- `published_reference`
- `intermediate_step`
- `data_or_console_output`
- `cover_or_web_screenshot`
- `code_screenshot`
- `promotion_or_qr`
- `decorative_result`
- `uncertain`

Role assignment is distinct from native visual review. Deterministic metadata can
classify obvious files, but it cannot produce a SemanticCard or claim code-image
consistency.

## Eligibility, code, Recipe, and review states

### Eligibility

| Value | Meaning |
|---|---|
| `scientific_scheme` | Evidence-bearing scientific or data-analysis visualization. |
| `semantic_modifier` | Changes what evidence is emphasized or annotated. |
| `aesthetic_modifier` | Changes appearance without changing data meaning. |
| `layout_resource` | Panel composition, legend, sizing, or export resource. |
| `visual_reference` | Useful appearance/reference image without reliable target code. |
| `excluded` | Decorative, promotional, non-plot, or otherwise ineligible item. |

### Code status

- `verified`: executable and passed all declared code/fixture gates.
- `parse_verified`: syntax, safety, contract, and provenance pass; execution may
  be blocked by specialist dependencies or fixtures.
- `candidate` / `callable_candidate`: cleaned callable fragment not yet promoted;
  use one project-wide spelling in generated data.
- `reference_only`: source logic is indexed but unsafe, incomplete, or not yet
  generalized.
- `visual_only`: no reliable target plotting code exists.
- `not_applicable`: resource or exclusion has no executable contract.

The initial full-library build uses `reference_only` or `visual_only`; later QA
may raise a record to a candidate, `parse_verified`, or `verified` state.
`code_status` never implies formal Recipe promotion. Initial generated
`validation` records include catalog linkage, execution, source-code, visual, and
`promotable` fields. Promotion becomes `formal` only after explicit
`promote --apply` with zero blocker/major findings.

### Review status

- `native_reviewed`: pixels were opened with native local image viewing and the
  role/linkage were confirmed.
- `native_reviewed_nonfinal`: pixels were opened, but only an intermediate or
  non-scientific role is linked; the Scheme is withheld from the scientific atlas.
- `no_confirmed_native_image`: the relevant article images were opened, but none
  positively supports this Scheme; no fallback preview may be invented.
- `deterministic_only`: classified from context/metadata without semantic visual
  inspection.
- `unreviewed`: no sufficient review exists.
- `blocked`: the image could not be opened or required evidence is unavailable.

Do not use generic `reviewed=true`; preserve separate role, linkage,
code-image-consistency, semantic-review, and evidence-level fields.

Native review rows may also contain `scheme_consistency`, keyed by Scheme ID,
and `rejected_scheme_ids`. A Scheme-specific mismatch is audit evidence only:
it must be removed from the positive `native_scheme_ids` used for previews and
retrieval, while remaining visible in the generated image disposition record.

Generated candidate modules expose both a source accessor and an explicit
`build_candidate_plot` entry point. R candidates accept a named `bindings` list
and return a `ggplot`, `Heatmap`/`HeatmapList`, or grob when the source contract is
satisfied. Python candidates accept a bindings dictionary and return a
Matplotlib `Figure`/`Axes`. They remain `reference_only` until dependencies,
representative inputs, execution, statistics, and native rendering pass QA; the
presence of a callable wrapper is not Recipe promotion.

Before exposing `build_candidate_plot`, generation must close the declared
plot-object chain by locating the defining fence for every intermediate object
(`plt -> p1 -> p2`, for example). A globally `analysis_only` fence is included
when it defines a required Scheme-chain object. If any definition is absent or
removed by safety cleaning, metadata records `callable=false` and the unresolved
objects, and the module exposes only its source accessor. It must not emit a
wrapper that merely postpones the missing-object error until runtime.

## Stable IDs and aliases

Use:

```text
scheme-<album>-<article-sequence>-<geometry-subtype>-v<major>
```

Rules:

- Normalize subtype to lowercase ASCII hyphen form.
- Keep an ID when only wording, aliases, or clarified metadata changes.
- Increment the major suffix when behavior, required inputs, statistical
  meaning, or output object changes incompatibly.
- Never recycle or silently repoint a promoted ID.
- Map every legacy `style_id` in `scheme-aliases.json`.
- Store alias targets as arrays. One legacy article/family card may split into
  multiple Scheme IDs; clients must return the list or ask for disambiguation,
  never select the first item silently.
- Map invalid legacy scientific cards, including decorative Christmas-tree
  composition cards, to deprecated/excluded records rather than deleting their
  provenance.

## Validation invariants

- Every catalog source block and image has exactly one disposition.
- Every Scheme source/article/block/image ID resolves.
- Every scientific-atlas image is native reviewed and has a safe role.
- `decorative`, `prompt_non_code`, `install_download`, and non-plot records never
  enter scientific retrieval as plotting evidence.
- ORA variables (`GeneRatio`, `Count`, `p.adjust`) and GSEA variables (`rank`,
  `NES`, `FDR`) remain method-distinct.
- `search_document` contains no private absolute path or user query history.
- Regeneration is deterministic and preserves manual semantics, stable IDs,
  aliases, Recipe lineage, and explicit exclusions.
- Coverage reports record failures and withheld Schemes; they never convert
  `blocked` or missing native review to `pass`.
