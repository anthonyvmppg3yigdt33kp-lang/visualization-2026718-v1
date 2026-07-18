# Discover mode

Use for natural-language search, browsing, comparison, or figure recommendation.

1. Build the partial `FigureIntent`; keep unknowns explicit.
2. Search the catalog through the bundled CLI. Backend may remain unset; when the
   user specifies R/Python, apply it as a hard filter.
   - When the user describes a desired appearance, asks to browse examples, or
     refers to a source-library style, search `style-atlas.jsonl` first through
     `plot_library.py atlas`; use its `style_id`, sample image, source blocks, and
     coverage status to anchor the request.
   - Then run the normal scientific search. An atlas title/style match never
     overrides FigureIntent, data compatibility, statistics, or claim boundaries.
3. Apply hard compatibility gates, semantic scoring, and diversity reranking from
   the selection policy. Do not rank by title or style keywords alone.
4. Inspect the full recipe and SemanticCard for the top candidates before replying.
5. Return one primary, one conservative, and one information-dense option when
   genuinely distinct; return fewer rather than padding weak choices.
   - For a mixed scientific-and-style request, merge the two searches explicitly:
     keep the scientifically valid primary and conservative option, then use the
     best atlas style as the information-dense/appearance option only when its
     encoding is compatible. If it is incompatible, list it separately as a
     rejected appearance reference and explain why.
   - Never let an image/article/source block outrank a decision strategy or formal
     Recipe as the scientific primary merely because its title matches the style
     wording. Keep the atlas `coverage_status` visible in the recommendation.
6. Explain visual channels, inputs, claim boundaries, and companion-evidence needs.
7. Do not execute, render, install dependencies, or promote anything.

If no exact match exists, identify the closest base recipe, compatible modifiers,
missing inputs, and the validation status of the proposed derivation.

Interpret atlas coverage strictly: `formal_exact` has direct Recipe/component
lineage, `formal_family` has only a same-family generalized Recipe,
`source_only` is reference code plus a sample image without a validated Recipe,
and `resource_only` is not a scientific evidence template. Never present
family-level or source-only coverage as exact reproducibility.
