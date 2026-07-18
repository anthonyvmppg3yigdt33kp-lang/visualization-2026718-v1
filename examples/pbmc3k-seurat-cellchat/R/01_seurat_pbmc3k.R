source("R/helpers.R")
suppressPackageStartupMessages({
  library(Seurat)
  library(dplyr)
  library(ggplot2)
  library(patchwork)
  library(clue)
})

set.seed(20260718)
archive <- project_path("data", "raw", "pbmc3k_filtered_gene_bc_matrices.tar.gz")
matrix_dir <- project_path("data", "raw", "extracted", "filtered_gene_bc_matrices", "hg19")
expected_sha256 <- "847d6ebd9a1ec9a768f2be7e40ca42cbfe75ebeb6d76a4c24167041699dc28b5"
if (!file.exists(archive)) stop("Official PBMC3K archive is missing: ", archive)
actual_sha256 <- sha256_file(archive)
if (!identical(tolower(actual_sha256), expected_sha256)) stop("PBMC3K archive SHA256 mismatch: ", actual_sha256)
if (!dir.exists(matrix_dir)) stop("Extracted PBMC3K matrix directory is missing: ", matrix_dir)

pbmc_counts <- Read10X(data.dir = matrix_dir)
if (!all(dim(pbmc_counts) == c(32738L, 2700L))) {
  stop("Unexpected official PBMC3K matrix dimensions: ", paste(dim(pbmc_counts), collapse = " x "))
}

pbmc <- CreateSeuratObject(
  counts = pbmc_counts,
  project = "PBMC3K_official_10X",
  min.cells = 3,
  min.features = 200
)
if (!all(dim(pbmc) == c(13714L, 2700L))) {
  stop("Unexpected post-CreateSeuratObject dimensions: ", paste(dim(pbmc), collapse = " x "))
}
pbmc[["percent.mt"]] <- PercentageFeatureSet(pbmc, pattern = "^MT-")
cells_before_qc <- ncol(pbmc)
pbmc <- subset(pbmc, subset = nFeature_RNA > 200 & nFeature_RNA < 2500 & percent.mt < 5)
cells_after_qc <- ncol(pbmc)
if (cells_after_qc < 2500L || cells_after_qc > 2670L) stop("QC-retained cell count is outside the expected PBMC3K range: ", cells_after_qc)

pbmc <- NormalizeData(pbmc, normalization.method = "LogNormalize", scale.factor = 10000, verbose = FALSE)
pbmc <- FindVariableFeatures(pbmc, selection.method = "vst", nfeatures = 2000, verbose = FALSE)
pbmc <- ScaleData(pbmc, features = rownames(pbmc), verbose = FALSE)
pbmc <- RunPCA(pbmc, features = VariableFeatures(pbmc), npcs = 50, seed.use = 20260718, verbose = FALSE)
pbmc <- FindNeighbors(pbmc, dims = 1:10, verbose = FALSE)
pbmc <- FindClusters(pbmc, resolution = 0.5, random.seed = 20260718, verbose = FALSE)
pbmc <- RunUMAP(pbmc, dims = 1:10, seed.use = 20260718, verbose = FALSE)

observed_clusters <- sort(unique(as.character(pbmc$seurat_clusters)))
expected_clusters <- as.character(0:8)
if (!identical(observed_clusters, expected_clusters)) {
  stop(
    "Seurat version/algorithm produced clusters ", paste(observed_clusters, collapse = ", "),
    "; the official PBMC3K teaching annotation expects exactly 0:8. Stop rather than silently mislabel."
  )
}

signatures <- list(
  "Naive CD4 T" = c("CCR7", "MAL", "TCF7", "LEF1"),
  "Memory CD4 T" = c("IL7R", "AQP3", "LTB", "IL32"),
  "CD14 Mono" = c("S100A8", "S100A9", "S100A12", "CD14", "LYZ"),
  "B" = c("MS4A1", "CD79A", "CD79B", "CD37", "HLA-DRA"),
  "CD8 T" = c("CD8A", "CD8B", "CCL5", "GZMK", "CTSW"),
  "FCGR3A Mono" = c("FCGR3A", "MS4A7", "LST1", "FCER1G", "IFITM3"),
  "NK" = c("GNLY", "NKG7", "PRF1", "GZMB", "KLRD1"),
  "DC" = c("FCER1A", "CD1C", "CLEC10A", "CST3", "HLA-DPA1"),
  "Platelet" = c("PPBP", "PF4", "GP9", "ITGA2B", "GNG11")
)
signature_features <- intersect(unique(unlist(signatures)), rownames(pbmc))
normalized <- SeuratObject::LayerData(pbmc, assay = "RNA", layer = "data")[signature_features, , drop = FALSE]
signature_average <- sapply(expected_clusters, function(cluster) {
  Matrix::rowMeans(expm1(normalized[, as.character(pbmc$seurat_clusters) == cluster, drop = FALSE]))
})
colnames(signature_average) <- expected_clusters
signature_z <- t(scale(t(as.matrix(signature_average))))
signature_z[!is.finite(signature_z)] <- 0
signature_scores <- do.call(cbind, lapply(signatures, function(genes) {
  colMeans(signature_z[intersect(genes, rownames(signature_z)), , drop = FALSE])
}))
rownames(signature_scores) <- expected_clusters
assignment <- clue::solve_LSAP(signature_scores - min(signature_scores), maximum = TRUE)
cluster_labels <- stats::setNames(colnames(signature_scores)[as.integer(assignment)], rownames(signature_scores))
assigned_scores <- signature_scores[cbind(seq_len(nrow(signature_scores)), as.integer(assignment))]
if (!setequal(unname(cluster_labels), names(signatures)) || any(assigned_scores < 0.5)) {
  stop("Canonical marker-signature annotation failed its one-to-one or minimum-score guard.")
}
signature_score_table <- data.frame(cluster = rownames(signature_scores), signature_scores, check.names = FALSE)
signature_mapping <- data.frame(cluster = names(cluster_labels), cell_type = unname(cluster_labels), assigned_score = assigned_scores, stringsAsFactors = FALSE)
utils::write.csv(signature_score_table, project_path("results", "tables", "pbmc3k_signature_scores.csv"), row.names = FALSE)
utils::write.csv(signature_mapping, project_path("results", "tables", "pbmc3k_signature_mapping.csv"), row.names = FALSE)
pbmc$cell_type <- factor(
  unname(cluster_labels[as.character(pbmc$seurat_clusters)]),
  levels = names(signatures)
)
Idents(pbmc) <- "seurat_clusters"

markers <- FindAllMarkers(
  pbmc, only.pos = TRUE, min.pct = 0.25, logfc.threshold = 0.25,
  test.use = "wilcox", verbose = FALSE
)
fold_column <- intersect(c("avg_log2FC", "avg_logFC"), names(markers))[1]
if (is.na(fold_column)) stop("FindAllMarkers output has no recognized fold-change column.")
markers$cell_type <- unname(cluster_labels[as.character(markers$cluster)])
markers <- markers |>
  arrange(cluster, p_val_adj, desc(.data[[fold_column]]))
utils::write.csv(markers, project_path("results", "tables", "pbmc3k_all_markers.csv"), row.names = FALSE)

selected_markers <- markers |>
  filter(p_val_adj < 0.05, .data[[fold_column]] > 0.25, !grepl("^(MT-|RPS|RPL)", gene)) |>
  group_by(cluster) |>
  slice_max(order_by = .data[[fold_column]], n = 3, with_ties = FALSE) |>
  ungroup() |>
  mutate(cell_type = unname(cluster_labels[as.character(cluster)]))
if (n_distinct(selected_markers$cluster) != 9L) stop("Could not select markers for all nine PBMC3K clusters.")
utils::write.csv(selected_markers, project_path("results", "tables", "pbmc3k_selected_markers.csv"), row.names = FALSE)

cluster_sizes <- as.data.frame(table(pbmc$seurat_clusters, pbmc$cell_type), stringsAsFactors = FALSE)
names(cluster_sizes) <- c("cluster", "cell_type", "cells")
cluster_sizes <- cluster_sizes[cluster_sizes$cells > 0, , drop = FALSE]
utils::write.csv(cluster_sizes, project_path("results", "tables", "pbmc3k_cluster_sizes.csv"), row.names = FALSE)

qc_summary <- data.frame(
  stage = c("raw_10x_matrix", "CreateSeuratObject", "post_qc"),
  features = c(nrow(pbmc_counts), nrow(pbmc), nrow(pbmc)),
  cells = c(ncol(pbmc_counts), cells_before_qc, cells_after_qc),
  stringsAsFactors = FALSE
)
utils::write.csv(qc_summary, project_path("results", "tables", "pbmc3k_qc_summary.csv"), row.names = FALSE)

p_qc <- VlnPlot(pbmc, features = c("nFeature_RNA", "nCount_RNA", "percent.mt"), ncol = 3, pt.size = 0.05) +
  plot_annotation(title = "PBMC3K post-QC distributions")
save_ggplot_pair(p_qc, "pbmc3k_qc", original_mm = c(210, 85), final_mm = c(210, 85))

saveRDS(pbmc, project_path("data", "processed", "pbmc3k_seurat.rds"), compress = "xz")
capture_session_info(project_path("results", "logs", "session_info_seurat.txt"))
write_json(
  list(
    dataset = list(
      source = "Seurat PBMC3K tutorial / 10x Genomics filtered matrix",
      url = "https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz",
      archive_sha256 = actual_sha256,
      raw_dimensions = unname(dim(pbmc_counts))
    ),
    software = list(R = as.character(getRversion()), Seurat = as.character(packageVersion("Seurat")), SeuratObject = as.character(packageVersion("SeuratObject"))),
    seeds = list(global = 20260718, PCA = 20260718, clustering = 20260718, UMAP = 20260718),
    qc = list(min_features_create = 200, min_features_filter_exclusive = 200, max_features_filter_exclusive = 2500, max_percent_mt_exclusive = 5, cells_before = cells_before_qc, cells_after = cells_after_qc),
    normalization = list(method = "LogNormalize", scale_factor = 10000),
    variable_features = list(method = "vst", nfeatures = 2000),
    neighbors = list(dims = 1:10), clustering = list(resolution = 0.5, clusters = observed_clusters),
    annotation = list(method = "one-to-one maximum-weight assignment of z-scored canonical marker-signature means; never map labels from numeric cluster IDs alone", signatures = signatures, mapping = as.list(cluster_labels), minimum_assigned_score = min(assigned_scores)),
    markers = list(test = "Wilcoxon", only_positive = TRUE, min_pct = 0.25, logfc_threshold = 0.25, selected_top_n_per_cluster = 3)
  ),
  project_path("results", "run_manifest_seurat.json")
)
message("Seurat PBMC3K complete: ", nrow(pbmc), " features x ", ncol(pbmc), " cells; ", length(levels(pbmc$cell_type)), " annotated groups.")
complete_stage("01_seurat_pbmc3k")
