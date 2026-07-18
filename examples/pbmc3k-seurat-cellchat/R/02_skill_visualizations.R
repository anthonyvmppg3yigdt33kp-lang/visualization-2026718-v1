source("R/helpers.R")
suppressPackageStartupMessages({
  library(Seurat)
  library(ggplot2)
  library(ggrepel)
  library(patchwork)
})

set.seed(20260718)
skill_root <- Sys.getenv("VIS_SKILL_ROOT")
if (!nzchar(skill_root) || !file.exists(file.path(skill_root, "SKILL.md"))) stop("Set VIS_SKILL_ROOT to the tested visualization-2026718-v1 Skill directory.")
skill_root <- normalizePath(skill_root, winslash = "/", mustWork = TRUE)
for (recipe in c(
  "seurat-embedding-adapter-r-v1", "umap-dataframe-r-v1", "arrow-axes-r-v1",
  "dark-nebula-r-v1", "seurat-marker-summary-adapter-r-v1", "marker-dotplot-r-v1"
)) source_recipe(skill_root, recipe)

pbmc <- readRDS(project_path("data", "processed", "pbmc3k_seurat.rds"))
palette <- c(
  "Naive CD4 T" = "#0072B2", "CD14 Mono" = "#D55E00", "Memory CD4 T" = "#56B4E9",
  "B" = "#009E73", "CD8 T" = "#CC79A7", "FCGR3A Mono" = "#E69F00",
  "NK" = "#6A3D9A", "DC" = "#8C564B", "Platelet" = "#7F7F7F"
)
embedding <- seurat_embedding_frame(pbmc, reduction = "umap", group = "cell_type")
embedding$cluster <- factor(embedding$cluster, levels = levels(pbmc$cell_type))
centres <- stats::aggregate(embedding[c("umap_1", "umap_2")], list(cell_type = embedding$cluster), stats::median)

p_clean <- plot_umap_groups(
  embedding, palette = palette, point_size = 0.55, alpha = 0.82,
  label_groups = FALSE, coordinate_padding = 0.12
) +
  ggrepel::geom_label_repel(
    data = centres, aes(x = umap_1, y = umap_2, label = cell_type),
    inherit.aes = FALSE, seed = 20260718, size = 3.1, label.size = 0.18,
    box.padding = 0.35, point.padding = 0.15, min.segment.length = 0,
    fill = grDevices::adjustcolor("white", alpha.f = 0.9), colour = "#17202A"
  ) +
  labs(title = "PBMC3K cell identities", subtitle = "Seurat UMAP; direct labels are descriptive") +
  theme(legend.position = "none", plot.title.position = "plot")

p_arrow <- add_arrow_axes(
  plot_umap_groups(embedding, palette = palette, point_size = 0.58, alpha = 0.78, coordinate_padding = 0.12),
  line_width = 0.42, arrow_length_mm = 2.1
) +
  labs(title = "Arrow-axis variant", subtitle = "Arrows are coordinate cues, not trajectory") +
  theme(legend.position = "right", legend.title = element_blank(), plot.title.position = "plot")

p_dark <- add_dark_nebula(
  plot_umap_groups(embedding, point_size = 0.45, alpha = 0.78, coordinate_padding = 0.12),
  palette = palette, halo_size = 2.4, halo_alpha = 0.075
) +
  ggrepel::geom_text_repel(
    data = centres, aes(x = umap_1, y = umap_2, label = cell_type),
    inherit.aes = FALSE, seed = 20260718, size = 3.0, colour = "#F4F7FA",
    min.segment.length = 0, segment.color = "#8294A6"
  ) +
  labs(title = "Dark-nebula variant", subtitle = "Decorative halo; not density") +
  theme(legend.position = "none", plot.title.position = "plot")

save_ggplot_pair(p_clean, "umap_clean", original_mm = c(150, 125), final_mm = c(150, 125))
save_ggplot_pair(p_arrow, "umap_arrow", original_mm = c(160, 125), final_mm = c(160, 125))
save_ggplot_pair(p_dark, "umap_dark_nebula", original_mm = c(150, 125), final_mm = c(150, 125), background = "#081018")
umap_multistyle <- (p_clean | p_arrow | p_dark) +
  plot_annotation(title = "PBMC3K UMAP: one embedding, three presentation styles", tag_levels = "A")
save_ggplot_pair(umap_multistyle, "umap_multistyle", original_mm = c(330, 120), final_mm = c(330, 120))

selected <- utils::read.csv(project_path("results", "tables", "pbmc3k_selected_markers.csv"), check.names = FALSE)
marker_frame <- seurat_marker_summary(
  pbmc, features = selected$gene, group = "cell_type", assay = "RNA", layer = "data",
  average_transform = "expm1", scale_average = TRUE, scale_clip = 2.5
)
utils::write.csv(marker_frame, project_path("results", "tables", "pbmc3k_marker_dotplot_data.csv"), row.names = FALSE)
p_marker <- plot_marker_dotplot(
  marker_frame, palette = c("#2166AC", "#F7F7F7", "#B2182B"),
  size_range = c(0.7, 7.5), size_breaks = c(0, 25, 50, 75, 100),
  fill_title = "Scaled average\nexpression", size_title = "Percent\nexpressed"
) +
  labs(
    title = "Top positive features for each PBMC3K cluster",
    subtitle = "Colour: per-gene z-scaled group average (clipped ±2.5); area: cells with normalized value > 0"
  ) +
  theme(plot.title.position = "plot", axis.text.x = element_text(angle = 50, hjust = 1), legend.position = "right")
save_ggplot_pair(p_marker, "marker_dotplot", original_mm = c(230, 170), final_mm = c(230, 170))

write_json(
  list(
    skill_root = skill_root,
    recipes = c("seurat-embedding-adapter-r-v1", "umap-dataframe-r-v1", "arrow-axes-r-v1", "dark-nebula-r-v1", "seurat-marker-summary-adapter-r-v1", "marker-dotplot-r-v1"),
    UMAP = list(source_reduction = "existing Seurat umap", recomputed = FALSE, group = "cell_type", point_mapping = "one point per cell", styles = c("clean direct labels", "arrow axes", "dark nebula decorative halo")),
    marker_dotplot = list(features = as.list(as.character(selected$gene)), group = "cell_type", assay = "RNA", layer = "data", linear_average = "mean(expm1(log-normalized value))", colour = "per-gene z-scaled group average clipped to +/-2.5", area = "percent cells with layer value > 0"),
    claim_limits = c("UMAP does not establish abundance, significance, trajectory, global distance or causality.", "Marker dot plot is descriptive and does not establish marker specificity, independent replication or causality.")
  ),
  project_path("results", "run_manifest_skill_visualizations.json")
)
capture_session_info(project_path("results", "logs", "session_info_visualization.txt"))
message("Skill UMAP and marker visualizations complete.")
complete_stage("02_skill_visualizations")
