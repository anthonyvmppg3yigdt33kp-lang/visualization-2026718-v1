# Visual review protocol v2

Use this protocol for source-image disposition, Scheme image linkage, and rendered
result review. Visual semantics require an image actually opened with native local
image viewing; metadata or code alone is insufficient.

## Evidence levels

| Level | Available evidence | Permitted claims |
|---|---|---|
| `pixels_only` | pixels only | layout, colors, marks, labels, overlap, visible trends |
| `image_metadata` | pixels plus axes/legend/title/caption | declared encodings and units |
| `image_code` | image plus exact plotting code | mappings, transformations, thresholds, plot parameters |
| `image_code_data` | image, code, auditable data/statistics | recomputed results, still bounded by study design |

Never infer p-values, sample size, normalization, significance, or causality at
`pixels_only`. Record confidence and evidence source per finding.

## Two separate decisions

For every image, record both:

1. `ImageDisposition.role`: scientific result, published reference, intermediate,
   console/data output, cover/web, code screenshot, promotion/QR, decorative, or
   uncertain.
2. Review evidence: native reviewed, deterministic only, unreviewed, or blocked.

Do not use a single `reviewed=true`. Also record Scheme-linkage confirmation,
code-image consistency, semantic review, and panel locator when relevant.

## Source-image workflow

1. Parse Markdown context, headings, image order, dimensions, aspect ratio,
   filename, and nearby code objects.
2. Apply deterministic QR/promotion/screenshot and obvious output checks.
3. Open every final, published reference, uncertain, shared, multipanel, or
   suspected-mismatch candidate with native local viewing.
4. Distinguish paper reference, rectangular intermediate, construction step, and
   final tutorial result. Never choose by nearest-code distance alone.
5. Link panels to the exact object chain and declare code-image consistency.
6. Create a VisualFingerprint only from the opened image.

A scientific-atlas primary must be `scientific_result` or
`published_reference`, `native_reviewed`, and not a code-image mismatch. A paper
reference anchors appearance but does not prove source-code reproduction.

## VisualFingerprint

Record exact subtype/family, panel structure, marks, visual channels, axes,
legend/colorbar mode, information density, dominant strengths, visible risks,
expected final-size behavior, panel locator, and evidence level. Use `unknown`
for unverified properties.

## Render review

1. Open original render and a final-physical-size view.
2. Identify panels, axes, legends/colorbars, annotations, and visible patterns.
3. Verify that mappings answer `FigureIntent` and preserve analysis unit.
4. Check clipping, overlap, occlusion, density, whitespace, hierarchy, labels,
   legend travel, and minimum readable type.
5. Check contrast, grayscale, color-vision accessibility, scale direction, and
   cross-panel identity.
6. Check aspect ratio, raster resolution, editable text, manipulation risk, and
   export cropping.
7. Decide `keep`, `revise`, or `reselect`; classify blocker/major/minor findings.

After explicit rendering, revise only visual parameters for at most three rounds
and re-open each output. Ask before changing filtering, normalization,
transformations, groups, thresholds, tests, multiple-testing correction, or
scientific claims. Report unresolved blockers; do not disguise them as complete.

## Deterministic review controller

Use `scripts/visual_review_controller.py` to keep the render-review-revise trail.
The controller is a state and policy layer only. It does **not** contain a visual
model, does not inspect image semantics, and must never be described as having
reviewed a figure. A native-capable Codex turn must open both artifacts and then
submit the structured review.

The state transition is:

```text
initialized
  -> awaiting_native_review
  -> keep | reselect | blocked
  -> revise -> awaiting_native_review (next render)
  -> awaiting_confirmation -> revise (approved scale-semantic change only)
```

There are at most three numbered render rounds. A third-round `revise` request is
recorded as `blocked`; it never silently starts a fourth round. Every round must
record:

- immutable data hash plus current code and input/config hashes;
- original and final-size paths, SHA-256, pixel size, and readable embedded DPI
  and physical size;
- an issue-bound parameter diff for revision rounds;
- the exact original/final hashes opened by the native reviewer;
- evidence level, findings, issue actions, and decision.

The submitted native review must name `native_local_image_view`, the actual tool,
and both image hashes, and must assert that original and final-size views were
opened. It must populate `visible`, `interpretable`, `confirmed`, and
`cannot_assert` separately. `pixels_only` cannot contain statistically confirmed
claims. Code inspection, metadata extraction, Pillow, OpenCV, or a heuristic
script is not acceptable native-review evidence.

Issue-to-action rules live in
`references/visual-issue-actions.json`. Automatic revision accepts only the
registered visual parameter paths. Data selection, filtering, normalization,
and transformations are forbidden inside this visual-only loop and require a
new scientifically approved analysis baseline. Statistics, thresholds, tests,
denominators, aggregation, scale midpoint/center, and other scale/encoding
semantic changes are never automatic: they require a registered semantic issue
and an explicit confirmation record before the next render. If any such change
alters the data artifact, the changed data hash blocks the transition and a new
baseline is mandatory.

The standalone interface is intentionally usable before integration with the
main library CLI:

```text
python scripts/visual_review_controller.py init ...
python scripts/visual_review_controller.py register-render ...
python scripts/visual_review_controller.py review-template ...
python scripts/visual_review_controller.py ingest-review ...
python scripts/visual_review_controller.py confirm ...
python scripts/visual_review_controller.py validate --require-terminal ...
```

## User-facing report

Report in this order:

1. **图中可见** — pixel-grounded observations.
2. **结合图例或代码可解释为** — metadata/code-grounded interpretation.
3. **经源数据或统计确认** — only verified computations.
4. **目前不能据此断言** — explicit claim limits.
5. **方案判断** — `keep`, `revise`, or `reselect`, with actionable changes.

If the image cannot be opened or native visual capability is unavailable, state
that no visual review was completed. Do not substitute code inspection.
