source("recipe.R")

# `seurat_object` must be a caller-supplied, trusted Seurat object produced by
# Load10X_Spatial (or an equivalent audited workflow). No file is read here.
cluster_plot <- plot_seurat_spatial_overlay(
  seurat_object,
  mode = "identity",
  assay = "Spatial",
  image = "slice1",
  group_by = "seurat_clusters"
)

feature_plot <- plot_seurat_spatial_overlay(
  seurat_object,
  mode = "feature",
  assay = "Spatial",
  feature_assay = "SCT",
  image = "slice1",
  features = c("Hpca", "Ttr")
)

list(cluster = cluster_plot, features = feature_plot)
