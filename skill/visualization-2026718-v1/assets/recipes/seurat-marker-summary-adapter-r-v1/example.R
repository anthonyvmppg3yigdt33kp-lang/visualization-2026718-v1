source("recipe.R")
# Trusted local input only; never readRDS() from an untrusted source.
pbmc <- readRDS("pbmc3k_seurat.rds")
marker_summary <- seurat_marker_summary(
  pbmc,
  features = c("MS4A1", "CD3D", "LYZ"),
  group = "cell_type",
  assay = "RNA",
  layer = "data",
  average_transform = "expm1",
  scale_average = TRUE
)
