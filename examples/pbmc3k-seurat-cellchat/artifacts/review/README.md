# Visual-review evidence

Each `*.review.json` file is the native-viewer review submitted to `scripts/visual_review_controller.py` for one figure pair. The original and final SHA-256 digests in the JSON bind the review to the committed PNG files.

All nine reviews passed `validate --require-terminal` with decision `keep` on 2026-07-18:

- UMAP: clean, arrow-axis, dark-nebula, and three-panel comparison
- marker dot plot
- CellChat: circle, chord, bubble, and heatmap

The controller state files are not committed because they contain machine-local absolute paths and hashes of large intermediate RDS objects that are intentionally excluded. The portable reviewer records, committed images, executable scripts, manifests, tables, and `renv.lock` retain the reusable evidence needed for this teaching case.
