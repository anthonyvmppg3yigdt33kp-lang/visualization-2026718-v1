# Compose mode

Use to derive a candidate from an adapter, base recipe, semantic/aesthetic
modifiers, layout, and export profile.

1. Enforce the backend gate and load the recipe schema.
2. Resolve components by stable ID. Check `requires`, `provides`,
   `compatible_with`, `conflicts`, backend, object type, and version constraints.
3. Reject incompatibilities with an actionable reason. Never assemble code by
   arbitrary string concatenation.
4. Apply components in canonical order: adapter → base recipe → semantic modifier
   → aesthetic modifier → layout → export.
5. Materialize a backend-pure callable `build_plot` through the declared
   component entrypoints. Record `parent_id`, components, parameters, source
   fingerprints, preflight, and lineage in a temporary candidate. A component
   list without callable code is not a completed composition.
6. Validate syntax, dependencies, object contracts, and entrypoints; render only
   when explicitly requested. A successful composition remains temporary until
   explicit promotion.

Semantic modifiers that change thresholds, grouping, statistics, or the evidence
claim require confirmation; aesthetic modifiers may be iterated within the stated
visual-review limit.
