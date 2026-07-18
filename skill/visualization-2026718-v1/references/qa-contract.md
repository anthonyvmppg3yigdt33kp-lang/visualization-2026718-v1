# QA contract v2

Apply relevant gates before delivery and every gate before promotion. Record
`pass`, `fail`, `blocked`, or `not_applicable`; never convert blocked or missing
evidence to pass.

## 1. Inventory and dispositions

- All 97 articles, 621 source fences, and 709 images resolve to the immutable
  source snapshot and checksums.
- Every block has exactly one BlockDisposition; every image has exactly one
  ImageDisposition. Counts, duplicates, unknown roles, and unresolved IDs are
  release failures.
- Install/download, prompt-only, decorative, and non-plot blocks never become
  plotting code. Christmas-tree/decorative records never enter scientific
  search or the scientific atlas.
- No-code visual references remain `visual_only`; do not fabricate code for
  pseudotime, ROC, GSEA, CellChat, or any other reference-only article.

## 2. Scheme and retrieval semantics

- Every Scheme has a stable ID, exact subtype, broad family, source semantics,
  target adapter, variables, visual channels, claim limits, lineage, image
  evidence, and controlled eligibility/status.
- Source and target semantics are not conflated. A generalized enrichment rose
  adapter does not imply that source hiking data computed NES/FDR.
- ORA (`GeneRatio`, `Count`, `p.adjust`) and GSEA (`rank`, `NES`, `FDR`) pass
  distinct method/variable gates.
- Exact subtype and confusable-pair tests distinguish mirrored lollipop versus
  violin versus mutation lollipop; GOCircle versus GSEA running score versus
  radial rose versus comet; fold-change concordance versus volcano.
- A mixed scientific/style request preserves `scientific_primary` separately
  from `appearance_anchor`; style similarity cannot override unit, variable,
  statistic, object, backend, or code-availability gates.
- Exact Scheme Top-1 is 100%; fuzzy Top-3 is at least 95%; scientific-primary
  Top-1 is at least 95%; hard gates and requested modifier retention are 100%.
- Ambiguous “圆形图” or “棒棒图” returns focused clarification options when
  competing subtypes remain; it does not pad three unrelated results.
- The benchmark asserts appearance Top-1 for exact controlled aliases. If an
  exact subtype is absent (for example a GSEA running-score curve), both
  scientific and appearance channels return no false substitute and expose the
  unavailable subtype in structured clarification.
- Warm p95 over at least 50 mixed queries is at most 750 ms. Normal search uses
  the precomputed index; full source freshness runs only in validate/update.

## 3. Code and execution

- Intent parsing keeps `action_intent`, `source_lookup`, and
  `requires_executable` separate. Calling/running/rendering code never enters raw
  source-identifier lookup unless the user explicitly requests source text.
- An execution request hard-excludes `visual_only`, `reference_only`, and
  non-callable candidates. Each accepted Scheme exposes a deterministic
  Scheme → adapter → base Recipe → modifiers → export plan and current runtime
  availability.
- Schema, syntax/AST, dependencies, input/output types, object chain, and example
  calls are valid.
- Candidate object chains are definition-use closed. Every intermediate plot
  object resolves to an included safe source fence; unresolved chains expose no
  executable entry point and are reported as non-callable.
- No installer, network download, workspace clearing, working-directory change,
  private absolute path, credential, implicit write, or caller-object mutation.
- R returns the declared plot/Heatmap/grob; Python returns Figure/Axes or the
  declared object. Rendering never crosses the selected backend.
- Composition materializes a callable backend-pure `build_plot`; a component
  inventory or arbitrary code splice is not executable composition.
- Runtime preflight checks the actual interpreter, declared packages, syntax,
  and entrypoints. Non-zero subprocess status, timeout, access violation,
  unsupported R object contract, or partial artifact is a blocker and is never
  relabeled as a successful render.
- A fixture proves execution when dependencies and valid representative data
  exist. Missing specialist dependencies cap status at `parse_verified`.
- Candidate code and formal Recipe promotion are distinct. Only explicit
  `promote --apply` with zero blocker/major findings creates a formal Recipe.

## 4. Scientific and statistical meaning

- Analysis unit, grouping, repeat level, denominator, transformations, scaling,
  Top-N, thresholds, direction, and correction match the intended claim.
- Effect, uncertainty, sample size, test, and multiple-testing correction are
  supplied when inference requires them.
- Cells/spots are not treated as biological replicates for donor/sample/patient
  claims. Overview embeddings are paired with replicate-level evidence when
  abundance or condition difference is claimed.
- Code mappings, SemanticCard visual channels, and labels agree. No annotation
  claims significance, mechanism, communication, calibration, utility, or
  causality without supporting evidence.

## 5. Images and visual QA

- All 709 images have one role and reason. Final/reference/uncertain/shared/
  multipanel/mismatch candidates receive native visual inspection.
- Scientific atlas has zero heuristic/deterministic-only previews. Each displayed
  scientific Scheme uses a native-reviewed `scientific_result` or
  `published_reference` with declared code-image consistency.
- QR/promotion, cover/web, code screenshot, decorative, or mismatched images are
  never scientific previews. A published reference is labeled as reference, not
  executable reproduction.
- Review records separate image role, Scheme linkage, code-image consistency,
  semantic review, VisualFingerprint, evidence level, and panel locator.
- Actual render and final-size view are opened. Labels, legends, colorbars,
  scales, marks, density, clipping, palette, grayscale, accessibility, panel
  consistency, hierarchy, and whitespace pass the output role.
- Visual-only auto-revision stops after three rounds and never changes data,
  filtering, normalization, thresholds, tests, or scientific meaning silently.
- A render-review-revise delivery has a valid
  `scripts/visual_review_controller.py` state. Rounds are exactly numbered 1--3;
  each stores data/code/input hashes, original/final artifact hashes and readable
  dimensions, parameter diffs, native-view evidence, issue actions, and a
  decision. A changed data hash is a blocker.
- Native review evidence names the native viewing method/tool, binds to both
  registered image hashes, confirms original and final-size inspection, and
  separates visible/interpretable/confirmed/cannot-assert statements. Python
  metadata or deterministic image checks cannot satisfy this gate.
- Every revision parameter is authorized by the previous round's open issue and
  `references/visual-issue-actions.json`. Unregistered changes fail. Data
  selection/filtering/normalization changes require a new baseline.
  `wrong_midpoint`, statistical changes, and other scale/encoding-semantic
  changes require an explicit confirmation record; they are never automatic
  visual fixes and still fail if they change the immutable data hash.
- `keep` is invalid while any blocker/major issue from any prior round lacks an
  explicit `resolved` finding. `reselect` and `blocked` are honest terminal
  outcomes but are not delivery-ready figures.

## 6. Export, provenance, and migration

- Dimensions, DPI, format, fonts/editable text, transparency, raster/vector
  choice, and microscopy/spatial aspect ratio meet the export contract.
- Source article/block/image IDs, checksums, transformation state, stable ID,
  lineage, and rights status remain traceable internally.
- Every old `style_id` maps to an array in `scheme-aliases.json`. One-to-many
  migration returns all targets; it never silently selects the first.
- Regeneration preserves manual metadata, promoted IDs, exclusions, Recipes, and
  lineage. A no-change rebuild is deterministic and idempotent.
- User-facing output omits local paths and internal filenames unless provenance
  audit was explicitly requested.

## Severity and release

- `blocker`: invalid unit/claim, fabricated statistic/code, unsafe execution,
  wrong backend, corrupt export, missing source, or scientific decorative leak.
- `major`: wrong subtype/method, misleading scale/legend, failed fixture,
  unreviewed scientific preview, inaccessible encoding, or unresolved lineage.
- `minor`: polish or maintainability issue without interpretive effect.

Delivery may disclose minor findings. `validate --all --strict` must report no
blocker/major for v2 release. `verified` promotion requires all gates; a
`parse_verified`, `reference_only`, or `visual_only` Scheme must remain labeled.
