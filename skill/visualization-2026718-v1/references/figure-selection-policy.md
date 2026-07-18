# Figure selection policy v2

Apply this policy after building `FigureIntent`. Scientific evidence selection
and appearance anchoring are parallel rankings with separate outputs; never blend
their scores into one opaque result.

## Hard gates before scoring

Reject a scientific candidate when any known requirement fails:

- eligibility is decorative, excluded, non-plot, prompt-only, install/download,
  or visual-only when executable code is required;
- selected backend differs from candidate backend;
- object/topology cannot satisfy the adapter;
- analysis unit, biological repeat, or denominator is incompatible;
- required variables, transformations, channels, or statistics are absent;
- ORA/GSEA method fields conflict;
- component kind, object type, dependency, or conflict rules block composition;
- code, review, provenance, or validation status is below requested assurance.

Unknown intent fields are not automatic failures. Keep a compatible candidate
with explicit `missing_inputs` only when the unknown does not invalidate the
scientific question. Style/title overlap never reverses a hard gate.

### ORA and GSEA

- ORA expects term/category with fields such as `GeneRatio`, `Count`, and
  adjusted p value.
- GSEA expects an ordered statistic/rank, running enrichment score, `NES`, `FDR`,
  and optionally leading edge.
- Treat `p.adjust`, `GeneRatio`, `Count`, `avg.exp`, and `pct.exp` as variables,
  not requests for code containing those strings.
- Enter source-code mode only for explicit “源码/函数/包含某标识符/代码块” intent.

## Scientific-primary score

Score only hard-gate-compatible candidates:

| Dimension | Weight | Full-credit condition |
|---|---:|---|
| Scientific question and evidence role | 30% | answers the core question at the intended evidence role |
| Data/object compatibility | 20% | unit, topology, object, variables, denominator, and repeats match |
| Visual encoding fitness | 15% | channels communicate the intended quantities without avoidable ambiguity |
| Requested visual intent | 10% | semantic emphasis and compatible modifiers satisfy the request |
| Executability/validation | 10% | code/dependencies/status support the requested action |
| Final readability/output | 10% | works at target size, density, and export context |
| Source quality/diversity | 5% | traceable source and a materially distinct option |

Return dimension scores, missing inputs, hard-gate decisions, and a concise
`why_match`. Exact normalized terms outrank controlled aliases, which outrank
2–4 character Chinese n-grams and token fuzzy matches. Single Chinese-character
overlap scores zero.

## Appearance-anchor score

Run this channel even when the query is primarily scientific; it may legitimately
return no compatible anchor.

| Dimension | Weight | Full-credit condition |
|---|---:|---|
| Exact subtype / controlled alias | 40% | exact geometry or unambiguous bilingual alias |
| Mark structure and visual channels | 25% | requested positions, angle/radius, color, size, edge, facet, labels match |
| Modifier, palette, and layout | 15% | compatible requested treatments are present |
| Private-library fuzzy description | 10% | personalized description matches without contradictory terms |
| Image review and code consistency | 10% | native-reviewed evidence and code-image linkage support the appearance |

Appearance score selects an anchor, not primary evidence. A published reference
or `reference_only` Scheme must retain that status. An appearance candidate that
fails scientific gates is listed in `rejected_candidates` with the exact reason.
Generic shape anchors such as `棒棒图`, `lollipop`, or `圆形图` receive only a
partial alias score; they must not tie or outrank a full controlled alias such as
`背靠背棒棒图`.

## Ambiguity and clarification

Clarify instead of guessing when a short visual noun maps to materially different
subtypes. Examples:

- “圆形图”: enrichment rose, GOCircle, chord, circos, donut, polar heatmap.
- “棒棒图”: mirrored dual-metric, mutation-domain, radial bar-lollipop.

Return two or three concrete options describing the distinguishing variables or
mark structure. Do not ask when supplied fields, method, code object, or image
already resolves the subtype.

When the request resolves to an exact subtype that has no source-backed Scheme,
return a structured `clarification` with `requested_subtypes`, suppress the
appearance substitute, and label any nearby options as non-equivalent. For
example, a GSEA rank track or score-dot summary must not masquerade as a GSEA
running-score curve.

## Candidate roles and diversity

Return at most three scientific decisions:

1. `primary`: best scientific/evidence fit.
2. `conservative`: lowest interpretation/reviewer risk among near-top choices.
3. `information_dense`: complementary exploratory or supplementary evidence.

Require a different evidence role, family, or material encoding tradeoff. Return
fewer than three when no real alternative exists; never add unrelated heatmaps or
bubble plots to fill a quota.

## Default evidence pairings

| Question | Primary evidence | Common companion |
|---|---|---|
| cluster/state overview | embedding | donor/sample composition or effect panel |
| condition composition | replicate-level proportion/interval/model | embedding as context only |
| marker pattern | dot/bubble or heatmap | DE effect/uncertainty at replicate level |
| differential result | volcano/MA/effect plot | labeled estimates and validation |
| ORA enrichment | term bar/dot/rose with declared fields | method/FDR table |
| GSEA enrichment | running score/rank or declared summary | leading edge and orthogonal assay |
| communication | bubble/network/chord | expression and perturbation evidence |
| spatial localization | image/segmentation overlay | region-level estimate and uncertainty |
| prediction | ROC plus calibration | external validation and decision utility |
| time-to-event | survival/forest | risk table, adjusted model, diagnostics |

## Response contract

JSON exposes:

- `scientific_decisions`
- `appearance_matches`
- `rejected_candidates` with gate/reason
- `clarification` or `null`

For each presented choice, state why it fits, visual channels, inputs/statistics,
supported and forbidden claims, why it outranks plausible alternatives, companion
evidence, backend, code/Recipe/review state, and whether adaptation is required.
If no exact Scheme exists, return the closest compatible base plus an explicit
component plan and label it temporary/unvalidated.
