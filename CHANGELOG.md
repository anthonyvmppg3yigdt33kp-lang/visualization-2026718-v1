# Changelog

## Unreleased

## V1.2.0 - 2026-07-23

### Added

- Five explicit v2 R components for Seurat teaching workflows: `seurat-embedding-adapter-r-v2`, `umap-dataframe-r-v2`, `seurat-marker-summary-adapter-r-v2`, `marker-dotplot-r-v2`, and `seurat-spatial-overlay-r-v2`.
- Declared-only visual revision contracts, issue-to-parameter allow-lists, and a runtime gate that rejects undeclared parameters or input-object rebinding.
- Hash-bound real-data validation evidence and reviewed v2 preview pairs for PBMC3K UMAP, PBMC3K marker dot plot, and Visium identity/feature overlays.
- Deterministic `build_public_runtime.py build|verify` packaging that enforces the public install profile, applies runtime overlays, refuses overwrite, and emits a relative-path/size/content SHA-256 inventory.
- Reproducible PBMC3K Seurat + CellChat teaching case with `renv.lock`, official-data checksum, executable R scripts, figures, tables, manifests, session information, prompt guide, interpretation guide, and visual-review evidence.
- Standard-library case validator for pinned versions, JSON integrity, stage markers, and review-to-PNG hash bindings.
- Formal recipes for CellChat circle, ligand-receptor bubble, sender-receiver heatmap, CellChat ligand-receptor adaptation, Seurat marker-summary adaptation, and the dark-nebula UMAP modifier.
- Real PBMC3K previews at original and final 300 dpi sizes.
- Original `seurat-spatial-overlay-r-v1` Recipe with Spatial assay/image/scale-factor checks, barcode-coordinate reconciliation, coordinate-faithful Seurat plotting APIs, and a synthetic contract fixture.

### Fixed

- Normalize JSON-derived named R palettes to identity-preserving character vectors in v2 UMAP and spatial Recipes.
- Namespace marker aggregation with `stats::ave()` for isolated R runtime execution.
- Keep the official Seurat 5.5.0 `SpatialFeaturePlot()` path and replace only its returned continuous fill palette, because that API version does not accept `cols`; a warning-emitting intermediate `SpatialPlot()` implementation is excluded.
- Preserve explicit visual-review intent in requests that ask to render and then review.
- Give marker/gene dot-plot context priority over the generic word “比例”.
- Give CellChat context priority over marker routes and restrict adapter composition to compatible CellChat recipe chains.
- Permit explicitly trusted local RDS inputs while retaining a clear untrusted-deserialization warning.
- Preserve `source_archive` bytes across clean clones so checksum and catalog-freshness validation remain reproducible.
- Restore native Windows X64 architecture only in R child-process environments so package preflight and rendering do not inherit an absent `PROCESSOR_ARCHITECTURE`; the parent environment remains unchanged and conflicting architecture values fail closed.

### Validated

- Fresh R 4.5.3 / Seurat 5.5.0 execution of the v2 PBMC3K adapter/base chains on a hash-bound 2,638-cell object: UMAP round 1 `KEEP`; marker round 1 `axis_label_clipped` revised only through declared visual parameters and round 2 `KEEP`.
- Fresh final-code execution of `seurat-spatial-overlay-r-v2` on a hash-bound 2,695-spot Visium object, with terminal `KEEP` reviews for both identity and Hpca/Ttr original/final pairs.
- Independent Seurat 5.5.0 Recipe harness on a trusted object derived from the official 10x Mouse Brain Sagittal-Anterior section: native R exit 0, zero warning/error-pattern matches, 2,695 Spatial-assay/image/coordinate barcodes with zero six-way set differences, and hash-bound `KEEP` native reviews for cluster and Hpca/Ttr original/final-size overlays. This validates the Recipe on that object, not the workflow or wrapper that produced it.
- Seurat 5.4.0 workflow on official PBMC3K: 2638 QC-retained cells and 9 signature-annotated groups.
- CellChat 2.2.0.9001: 441 communication rows at model `p <= 0.05`, 15 pathways, and 74 nonzero aggregate edges.
- Nine hash-bound original/final native visual reviews with terminal `keep` decisions.

## V1.0.0 - 2026-07-18

- Initial public release under the display name “可视化2026718V1” and machine name `visualization-2026718-v1`.
