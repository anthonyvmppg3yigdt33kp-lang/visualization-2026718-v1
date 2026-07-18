# Core contract

Treat every scientific figure as an evidence interface, not decoration. Before
searching or changing code, normalize the request into a `FigureIntent`; before
recommending a recipe, compare its `SemanticCard` with that intent.

## Minimum FigureIntent

Record known values and use `unknown` rather than guessing:

- `core_question`: comparison, distribution, relationship, composition,
  trajectory, network, spatial localization, prediction, or validation.
- `scientific_claim`: the intended claim; mark it `provisional` when the user has
  not supplied analysis evidence.
- `evidence_role`: overview, discovery, comparison, mechanism, validation,
  robustness, or clinical relevance.
- `unit_of_analysis`: cell, sample, patient, gene, pathway, interaction, spatial
  spot, or another explicit unit.
- `data_topology`: table, matrix, embedding, network, time-to-event, image, or
  spatial coordinates plus image.
- `statistical_intent`: descriptive, exploratory, or inferential.
- `backend`, input object, variable types, groups, and repeated-measure level.
- `visual_intent`: highlights, boxes, circles, arrow axes, labels, annotations,
  facets, shared legends, or other requested treatments.
- `output_context`: single plot or panel, manuscript role, final dimensions,
  editable-text requirement, and export formats.
- `action_intents`: ordered discover/adapt/execute/render/review actions;
  `requires_executable` remains true when a requested review follows execution.
- `retrieval_family`: internal broad-family routing kept separate from the
  scientific `core_question` (for example ORA is pathway enrichment, not GSEA).

Ask only for missing fields that block safe selection or execution. Discovery may
proceed with partial intent and must expose the missing assumptions.

## Backend gate

Discovery, pixels-only review, and read-only non-rendering audit may be
backend-neutral. Before executable adaptation, composition, rendering, preview,
export, or backend-specific visual QA, resolve Python or R from an explicit choice
or clearly language-specific input. If unresolved, ask exactly **Python or R?**
and stop. Once selected, use that backend exclusively for all visual outputs.

## Decision output

Return at most three meaningfully different recommendations by default:

1. `primary`: best fit to the scientific question and evidence role.
2. `conservative`: lowest interpretation and review risk.
3. `information_dense`: richer exploratory or supplementary view.

For each, state why it fits, what each visual channel means, required inputs and
statistics, supported and unsupported claims, why it outranks alternatives, and
whether a companion panel is needed. Never recommend a prettier but scientifically
weaker chart as primary.

## Execution and review boundary

Search and adaptation do not authorize execution. Render only when requested.
After a requested render, rebuild layout-aware components at the final physical
size, then inspect both original and final-size outputs with local
image viewing, declare the available evidence level, and iterate purely visual
parameters for at most three rounds. Never change filtering, normalization,
thresholds, statistical methods, or the scientific claim without confirmation.
