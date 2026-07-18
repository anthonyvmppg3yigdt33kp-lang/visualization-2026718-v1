# Python backend fragment

Use Python exclusively for drawing, previewing, exporting, and render-based QA
after the backend gate resolves to Python.

- Adapt code into importable functions with explicit arguments. Return
  `matplotlib.figure.Figure`, `Axes`, or a documented domain object; do not call
  `plt.show()` or save by default.
- Keep AnnData/Scanpy adapters and statistical computation separate from visual
  modifiers. Avoid mutating `.obs`, `.var`, embeddings, or caller-owned frames
  unless the function explicitly returns a copy.
- Declare dependencies in recipe metadata and import them normally. Never run
  package installers or downloads from a recipe. Check Python and packages before
  requested execution.
- Compose only objects and modifiers whose compatibility metadata agree; do not
  concatenate arbitrary source strings or mix incompatible artist lifecycles.
- Export with explicit `Figure.savefig` profiles only when requested. Honor final
  physical dimensions, DPI, transparency, fonts, and vector-text requirements.
- Run AST/compile checks on every promoted module and fixtures where dependencies
  exist. Missing packages yield `parse-verified`, not an R-rendered substitute.
- Use the local image viewer on Python-generated artifacts for visual review. Do
  not use R graphics to create replacement previews.
