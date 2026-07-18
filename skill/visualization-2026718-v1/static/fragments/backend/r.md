# R backend fragment

Use R exclusively for drawing, previewing, exporting, and render-based QA after
the backend gate resolves to R.

- Adapt code into functions with explicit arguments and return a `ggplot`,
  `Heatmap`, `grob`, or documented domain object. Do not call `print()`, open a
  device, or save by default.
- Prefer adapters that produce tidy plotting data; keep statistical computation
  separate from visual modifiers. Preserve Seurat, CellChat, MAF, survival, and
  other domain-object semantics rather than coercing blindly.
- Use namespaces or declare packages in recipe metadata. Never install packages
  from a recipe. Check `Rscript` and required packages before requested execution.
- Treat `ComplexHeatmap` and grid objects as distinct from `ggplot2`; compose only
  through components whose compatibility metadata explicitly permits it.
- Use explicit export profiles (`ggsave`, `svglite`, `cairo_pdf`, `ragg`, or
  appropriate grid-device flow) only when export is requested. Honor final physical
  dimensions and editable-text requirements.
- Parse every promoted `.R` file and run fixtures where dependencies exist. If a
  package is unavailable, report `parse-verified` rather than cross-rendering in
  Python.
- Use the local image viewer on R-generated artifacts for visual review. Do not use
  Python plotting libraries to create replacement previews.
