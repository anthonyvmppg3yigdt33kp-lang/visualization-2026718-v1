# Visual-semantic ontology v2

Use this controlled vocabulary to parse `FigureIntent`, interpret
`VisualizationSchemeV2`, and separate scientific compatibility from appearance.
Preserve the user's words separately; normalize only catalog/search fields.

## Scientific intent

| Axis | Controlled values |
|---|---|
| `core_question` | `comparison`, `distribution`, `relationship`, `composition`, `trajectory`, `network`, `spatial_localization`, `prediction`, `validation` |
| `evidence_role` | `overview`, `discovery`, `comparison`, `mechanism`, `validation`, `robustness`, `clinical_relevance` |
| `unit_of_analysis` | `cell`, `spot`, `sample`, `donor`, `patient`, `gene`, `feature`, `pathway`, `interaction`, `timepoint` |
| `data_topology` | `table`, `matrix`, `embedding`, `network`, `time_to_event`, `image`, `spatial_image`, `genomic_track` |
| `statistical_intent` | `descriptive`, `exploratory`, `inferential` |
| `claim_status` | `provisional`, `analysis_supported`, `externally_validated` |

Unknown values remain `unknown`. Do not infer donor/sample structure from cell
rows or infer inferential intent from significance symbols.

## Broad families versus geometry subtypes

Use a broad family for scientific compatibility and an exact geometry subtype
for Scheme identity. Never replace the subtype with an article title or family.

- `embedding`: `umap_scatter`, `pca_scatter`, `pseudotime_embedding`, density or
  feature overlays.
- `dot_bubble`: expression/proportion dot plot and declared bubble encodings.
- `heatmap`: clustered, annotated, correlation, expression, enrichment.
- `differential`: `volcano`, `ma_plot`, `two_contrast_foldchange_concordance`.
- `enrichment`: GSEA running score, bar/dot/ridge/network,
  `radial_bar_lollipop`, `enrichment_comet_link_dot`,
  `enrichment_dendrogram_bar_composite`, `go_enrichment_circle`.
- `distribution`: violin, mirrored violin, ridge, raincloud, box, density.
- `composition`: stacked/connected proportion, alluvial, area,
  `ternary_composition_scatter`.
- `communication_network`: CellChat bubble, chord, graph, Sankey.
- `relationship`: scatter, regression, correlation, ternary.
- `set_overlap`: Venn, UpSet.
- `clinical_performance`: ROC, calibration, survival, forest/interval.
- `genomics`: mutation lollipop, oncoplot, CNV/LOH, genome track.
- `spatial_image`: HE overview, ROI, fluorescence, segmentation boundary,
  transcript/feature overlay.
- `layout_annotation`: palette, direct label, shared legend, multipanel layout.

Add a new subtype when mark arrangement, visual channel, or interpretation risk
materially differs. Add a new broad family only when the scientific question or
data topology cannot be expressed by an existing family.

## Method and variable gates

Treat field names as variables unless the query explicitly asks for source code
or a function identifier.

- ORA: `GeneRatio`, `Count`, `p.adjust`, term/category.
- GSEA: ranked statistic, `NES`, `FDR`, running enrichment score, leading edge.
- Marker dot plot: average expression, detected fraction, group, feature.
- Composition: numerator, denominator, biological replicate, group.
- ROC: outcome, score, split/cohort; discrimination is distinct from calibration.

Do not let style words bypass these gates. “Nature 风格” never supplies missing
FDR, direction, analysis unit, or uncertainty.

## Scheme semantic contract

Every scientific Scheme declares:

- source and target questions, analysis units, topologies, variables, and any
  adapter mapping;
- required/optional inputs and transformations, including scale scope;
- precise visual channels for position, angle, radius, color, size, shape, edge,
  facet, label, and annotation;
- supported claims, claim limits, statistics, misread risks, companions, and
  safer alternatives;
- confusable subtypes and negative terms for retrieval gating.

## Mandatory interpretation boundaries

| Scheme | Supports | Does not support by itself | Companion |
|---|---|---|---|
| UMAP/t-SNE | local embedding neighborhoods, labels, visible mixing | significance, global distance, direction, abundance change | donor/sample composition or model estimate |
| Dot/bubble | declared color/size summaries | marker significance, cell-level independence, causality | DE table, uncertainty or replicate summary |
| Heatmap | relative patterns under stated scaling/clustering | absolute expression when row-scaled, significance | scale legend, effect/uncertainty panel |
| Volcano | effect and significance under declared thresholds | importance, replication, causality | labeled effect table and validation |
| GSEA | ranked-set enrichment under stated method/FDR | per-cell pathway activity or causality | leading edge or orthogonal assay |
| CellChat/chord | model-inferred interaction structure | physical contact, proven communication, mechanism | expression and perturbation evidence |
| ROC | evaluated-cohort discrimination | calibration, clinical utility, transportability | calibration, decision curve, external validation |
| Survival | time-to-event association | causality or PH validity | adjusted model, diagnostics, risk table |
| Spatial overlay | visible localization under declared segmentation | interaction or enrichment significance | region-level quantification and uncertainty |
| Enrichment rose | declared radial multichannel summary | enrichment computation unless adapter fields prove it | tabular ORA/GSEA results and method note |

When the requested claim exceeds the Scheme boundary, add a companion analysis,
choose another Scheme, or downgrade the language; never solve it with styling.
