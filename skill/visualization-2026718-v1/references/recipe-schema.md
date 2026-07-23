# Recipe and component schema

Formal recipes and components live in one directory each with a required
`recipe.json`. The schema is JSON-first and deterministic; examples below use
YAML-equivalent notation only for readability.

## Contents

- [Required fields](#required-fields)
- [Semantic and visual records](#semantic-and-visual-records)
- [Composition and lineage](#composition-and-lineage)
- [Validation and files](#validation-and-files)
- [Identity and compatibility rules](#identity-and-compatibility-rules)

## Required fields

```yaml
schema_version: "1.0"
id: umap-seurat-groups-v1
name: Seurat grouped UMAP
description: Embedding overview with direct group labels.
kind: base_recipe
family: embedding
backend: r
entrypoint: plot_umap_groups
tags: [umap, seurat, single-cell, direct-label]
requires:
  object_types: [Seurat]
  variables: [reduction, group]
  packages: [Seurat, ggplot2]
  capabilities: [embedding_coordinates]
provides:
  object_types: [ggplot]
  capabilities: [embedding_overview, group_color_mapping]
compatible_with:
  kinds: [aesthetic_modifier, layout, export]
  ids: []
conflicts: []
parameters: []
lineage: {}
semantic_card: {}
visual_fingerprint: {}
source: {}
validation: {}
files: {}
```

Allowed `kind` values:

- `adapter`
- `base_recipe`
- `semantic_modifier`
- `aesthetic_modifier`
- `layout`
- `export`

Allowed `backend` values are `r` and `python`. Every executable component is
backend-specific. Do not register cross-backend composition shims.

`entrypoint` names the callable used by preflight, materialization, and render.
Declare it explicitly whenever a module contains more than one public function;
do not rely on file order to choose between a summarizer and a plotting
function. R entrypoints receive the current object as their first argument;
Python base Recipes return Figure/Axes and modifiers return the updated object.

`parameters` entries declare `name`, `type`, `required`, `default`, `allowed`,
and `description`. A default must not change filtering, statistics, or claim
strength silently.

For a Recipe whose input artifact is passed as the first callable argument,
declare `input_parameter` with the matching parameter name. The runtime binds
that parameter from `--input`, rejects attempts to override it, and rejects
every runtime parameter not listed in `parameters`.

Recipes that support the native-review loop may add:

```yaml
visual_revision:
  parameter_policy: declared-only
  max_rounds: 3
  issue_parameter_map:
    label_overlap: [label_repel, label_size]
    point_density_occlusion: [point_size, alpha]
```

Each issue ID must exist in `visual-issue-actions.json`, and each mapped name
must be declared by that Recipe. The mapping authorizes only which existing
visual arguments may address a native finding; it does not detect the finding,
approve a value, or authorize data/statistical/scale-semantic changes.

## Semantic and visual records

`semantic_card` contains:

```yaml
questions_answered: [distribution]
evidence_roles: [overview, discovery]
units: [cell]
data_topologies: [embedding]
required_variables:
  - name: group
    role: color
    type: categorical
transformations:
  - field: coordinates
    method: precomputed_embedding
visual_channels:
  x: embedding_dimension_1
  y: embedding_dimension_2
  color: group_label
  size: constant_point_size
  shape: none
  alpha: point_density_control
  facet: optional_group
  annotation: optional_direct_label
supports_claims:
  - Shows local embedding neighborhoods and the displayed group distribution.
does_not_support:
  - Does not establish abundance differences, significance, trajectory, or causality.
required_statistics: [none]
misread_risks: [global_distance_interpretation, cell_as_replicate]
preferred_companions: [sample_level_composition]
safer_alternatives: []
```

`visual_fingerprint` contains:

```yaml
family: embedding
panels: 1
panel_structure: single
channels: [position, color]
legend_mode: direct_or_legend
information_density: medium
strengths: [cluster_overview]
risks: [overplotting, color_collision]
final_size_behavior: requires_point_and_label_check
evidence_level: image_code
reviewed: true
```

Use `unknown`, `[]`, or `null` for fields not yet verified. Never manufacture a
visual fingerprint without opening the selected preview.

## Composition and lineage

`compatible_with` is an allow-list; `conflicts` is a deny-list and wins. A
component is compatible only when all of the following hold:

- backends match;
- provided object/capability satisfies the next component's requirements;
- kind and any explicit ID constraints allow the link;
- neither component lists the other ID/capability as a conflict;
- parameter and package constraints are satisfiable.

Apply components only in this order:

`adapter → base_recipe → semantic_modifier → aesthetic_modifier → layout → export`

For a derived candidate, `lineage` contains:

```yaml
parent_id: umap-seurat-groups-v1
components:
  - id: modifier-arrow-axes-r-v1
    parameters: {position: lower_left}
source_fingerprints: [sha256:...]
derived_at: "2026-07-16T00:00:00Z"
```

`derived_at` is informational and must not participate in stable-ID or content
fingerprint generation. Formal base recipes use `parent_id: null` and may list
distillation source fingerprints.

## Validation and files

`source` contains:

```yaml
status: internal_distillation
articles:
  - source_id: album-3792985494804332545-074
    block_ids: [block-003, block-004]
    image_ids: [image-006]
license_status: unknown
transformation: generalized_rewrite
```

Allowed `source.status`: `original`, `internal_distillation`, `derived`, or
`unknown`. Unknown license/source material remains internal and is never presented
as independently redistributable.

`validation` contains:

```yaml
tier: verified
checks:
  schema: pass
  syntax: pass
  safety: pass
  fixture: pass
  render: pass
  visual: pass
  semantic: pass
  provenance: pass
last_validated: "2026-07-16"
runtime: R-4.5.3
notes: []
```

Allowed tiers:

- `verified`: schema, syntax, safety, applicable fixture/render, visual,
  semantic, and provenance checks pass.
- `parse-verified`: schema/syntax/safety pass, but specialist dependencies or
  valid domain fixtures prevent execution.
- `reference-only`: incomplete, unsafe until rewritten, or provenance-limited.
- `visual-only`: useful visual reference without reliable executable code.

`files` contains paths relative to the recipe directory:

```yaml
code: recipe.R
example: example.R
preview: preview.png
fixture: fixture.csv
```

Use `.py` modules for Python and `.R` functions for R. `code` and `example` are
required for executable kinds; `preview` is required before `verified` promotion.
An export component may omit a preview when its parent recipe's export fixture is
visually verified.

## Identity and compatibility rules

- IDs use lowercase ASCII letters, digits, and hyphens and end with a version,
  for example `dotplot-marker-box-r-v1`.
- Never derive identity from local path or display name. Once promoted, an ID is
  immutable; incompatible change creates a new version.
- Compute content fingerprints from normalized metadata and code, excluding
  timestamps, validation runtime, preview binary metadata, and local paths.
- Keep manual metadata separate from generated source/catalog fields. Updates may
  refresh fingerprints and source links but cannot overwrite curated semantics.
- Reject absolute paths, session tokens, credentials, installers, downloads,
  workspace clearing, working-directory changes, implicit output writes, and
  undeclared dependencies.
- Preserve catalog records for `reference-only` and `visual-only` sources, but do
  not treat them as executable formal recipes.
