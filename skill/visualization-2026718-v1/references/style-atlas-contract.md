# Scheme v2 visual-atlas contract

Load this reference when browsing visual examples, matching an appearance,
exporting the manual, or auditing why a Scheme is displayed or withheld.

## Atlas purpose

The atlas is a visual decision surface over `scheme-catalog.jsonl`; it is not a
gallery of every source image. Keep scientific evidence selection and appearance
matching as separate decisions:

- `scientific_primary` chooses a valid evidence design from the question, unit,
  data topology, variables, statistics, backend, and output role.
- `appearance_anchor` finds a compatible geometry, encoding, modifier, layout,
  or reference in the private source library.

If the two disagree, scientific fitness wins. Report the appearance Scheme as
rejected, supplementary, or usable only after a declared adapter.

## Sections

| Section | Admission rule | Normal use |
|---|---|---|
| 科研方案 | `scientific_scheme` plus a safe native-reviewed preview | Scientific design and code retrieval |
| 语义组件 | `semantic_modifier` | Highlights/annotations that change evidence emphasis |
| 美学 / 配色 | `aesthetic_modifier` | Non-semantic styling and accessibility |
| 布局资源 | `layout_resource` | Multipanel composition, legends, sizing, export |
| 视觉参考 | `visual_reference` | Appearance inspiration without executable target code |
| 排除审计 | `excluded` or failed atlas admission | Traceable reason; never scientific evidence |

The HTML opens on 科研方案. A Scheme that lacks native visual review may remain
searchable in the catalog but must not appear there. Christmas trees, QR codes,
promotion, covers, code screenshots, and decorative results only appear in the
audit section when traceability is useful.

## Card content

Every card exposes:

- stable `scheme_id`, exact `geometry_subtype`, broad family, and method;
- scientific position and source-versus-target semantics;
- visual channels and required inputs;
- code, Recipe, image-role, native-review, and code-image-consistency status;
- controlled aliases/visual features explaining why the Scheme can match;
- supported claims, forbidden claims, misread risks, and companion evidence;
- internal lineage only on explicit audit; ordinary output hides paths and
  private filenames.

`why_match` is not a scientific approval. It describes aliases, mark structure,
and fuzzy visual descriptions used by the appearance channel.

## Scientific image gate

A scientific card requires all of:

1. `eligibility=scientific_scheme`.
2. Primary image role is `scientific_result` or `published_reference`.
3. `image_evidence.review_status=native_reviewed`.
4. Code-image consistency is not `mismatch`.

Do not choose an image by nearest-code distance alone. Distinguish final tutorial
render, published reference, intermediate construction step, and shared
multipanel image. A published reference demonstrates appearance, not executable
reproduction.

## CLI and export

```text
python scripts/plot_library.py atlas --scope scientific --query "通路围成一圈，柱高和点代表不同指标" --format json
python scripts/plot_library.py atlas --scope modifier --subtype marker-group-box --format json
python scripts/plot_library.py inspect --id <scheme-id> --include-lineage --include-visual
python scripts/export_style_atlas.py --output-dir <dir> --scope all
```

`atlas` may filter by `scope`, `subtype`, `method`, and review status. `inspect`
expands code lineage or image evidence only when requested. The legacy
`style-atlas.jsonl` is a compatibility export; it does not define v2 semantics.

## Legacy migration

- Preserve old `style_id` values in `scheme-aliases.json`.
- Return all targets for one-to-many splits; never choose the first silently.
- Map invalid/decorative legacy cards to deprecated excluded records.
- Keep `formal_exact`, `formal_family`, and `source_only` only in the legacy
  compatibility view. Scheme v2 reports code and Recipe states separately.

## Export acceptance

- HTML defaults to the scientific section and exposes the other sections through
  explicit tabs.
- Scientific cards with heuristic/deterministic-only previews equal zero.
- Every displayed image resolves locally; stale generated assets are removed.
- Every card states subtype, scientific position, visual channels, code/image/
  Recipe/review state, matching rationale, and claim boundary.
- User-facing HTML contains no private absolute path or raw source filename.
