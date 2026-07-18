# Review mode

Use to interpret a result image, assess readability, or decide whether to keep,
revise, or replace a figure plan.

1. Load the visual-review protocol and classify the available evidence level:
   pixels only, image metadata, image plus code, or image plus code and data.
2. View the actual artifact. If it cannot be opened, stop visual claims and report
   the limitation.
3. Separate visible observations, metadata/code-supported interpretation,
   data/statistics-confirmed findings, and prohibited conclusions.
4. Check scientific fitness as well as layout, legibility, color, accessibility,
   cropping, density, cross-panel consistency, integrity, and export quality.
5. Return `keep`, `revise`, or `reselect` with confidence and concrete actions.
6. For generated results, register original/final artifacts in the hash-bound
   visual controller, submit only evidence from images actually opened with a
   native viewer, and validate the terminal state. The controller itself has no
   visual model.

A pixels-only review does not require a backend. Any requested code change,
rerender, preview, or export triggers the backend gate and same-backend rule.
Aggregation, denominator, filtering, normalization, statistical, threshold, or
scale-semantic changes are not visual-only fixes and require confirmation/new
baseline as specified by the visual protocol.
