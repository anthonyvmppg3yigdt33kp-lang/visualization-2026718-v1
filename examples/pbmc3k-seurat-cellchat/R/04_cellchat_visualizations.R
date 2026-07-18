source("R/helpers.R")
suppressPackageStartupMessages({
  library(CellChat)
  library(ggplot2)
  library(ComplexHeatmap)
  library(circlize)
})

set.seed(20260718)
skill_root <- Sys.getenv("VIS_SKILL_ROOT")
if (!nzchar(skill_root) || !file.exists(file.path(skill_root, "SKILL.md"))) stop("Set VIS_SKILL_ROOT to the tested visualization-2026718-v1 Skill directory.")
skill_root <- normalizePath(skill_root, winslash = "/", mustWork = TRUE)
for (recipe in c(
  "cellchat-matrix-adapter-r-v1", "cellchat-lr-adapter-r-v1",
  "cellchat-circle-r-v1", "cellchat-chord-r-v1",
  "cellchat-bubble-r-v1", "cellchat-heatmap-r-v1"
)) source_recipe(skill_root, recipe)

cellchat <- readRDS(project_path("data", "processed", "pbmc3k_cellchat.rds"))
weight <- cellchat_interaction_data(cellchat, measure = "weight", output = "matrix")
communication <- cellchat_lr_table(cellchat, slot_name = "net", threshold = 0.05)
utils::write.csv(communication, project_path("results", "tables", "cellchat_skill_lr_contract.csv"), row.names = FALSE)

palette <- c(
  "Naive CD4 T" = "#0072B2", "CD14 Mono" = "#D55E00", "Memory CD4 T" = "#56B4E9",
  "B" = "#009E73", "CD8 T" = "#CC79A7", "FCGR3A Mono" = "#E69F00",
  "NK" = "#6A3D9A", "DC" = "#8C564B", "Platelet" = "#7F7F7F"
)
palette <- palette[rownames(weight)]

top_edge_matrix <- function(matrix_data, top_n = 35L) {
  x <- matrix_data
  values <- as.vector(x)
  positive <- which(values > 0)
  if (length(positive) > top_n) {
    keep <- positive[order(values[positive], decreasing = TRUE)[seq_len(top_n)]]
    values[-keep] <- 0
    x[] <- values
  }
  x
}
chord_weight <- top_edge_matrix(weight, top_n = 35L)
utils::write.csv(chord_weight, project_path("results", "tables", "cellchat_chord_display_top35_matrix.csv"), row.names = TRUE)

save_base_pair(
  function() plot_cellchat_chord(chord_weight, group_colours = palette, transparency = 0.55, directional = TRUE),
  "cellchat_chord_top35", original_mm = c(180, 180), final_mm = c(180, 180)
)
save_base_pair(
  function() plot_cellchat_circle(weight, group_colours = palette, edge_width_max = 7, edge_alpha = 0.38, label_size = 0.72, title = "PBMC3K inferred communication network"),
  "cellchat_circle", original_mm = c(180, 180), final_mm = c(180, 180)
)

heatmap <- plot_cellchat_heatmap(weight, transform = "none", name = "Weight")
save_heatmap_pair(heatmap, "cellchat_heatmap", original_mm = c(155, 135), final_mm = c(155, 135))

p_bubble <- plot_cellchat_bubble(
  communication, top_n = 30, p_threshold = 0.05, p_floor = 1e-4,
  palette = c("#F7FBFF", "#6BAED6", "#08306B")
) +
  labs(
    title = "Top 30 inferred ligand–receptor communications",
    subtitle = "Display filter: CellChat p ≤ 0.05, ranked by communication probability"
  ) +
  theme(plot.title.position = "plot")
save_ggplot_pair(p_bubble, "cellchat_bubble_top30", original_mm = c(240, 190), final_mm = c(240, 190))

node_summary <- data.frame(
  cell_type = rownames(weight),
  outgoing_weight = rowSums(weight),
  incoming_weight = colSums(weight),
  total_weight = rowSums(weight) + colSums(weight),
  stringsAsFactors = FALSE
)
node_summary <- node_summary[order(node_summary$total_weight, decreasing = TRUE), , drop = FALSE]
utils::write.csv(node_summary, project_path("results", "tables", "cellchat_node_weight_summary.csv"), row.names = FALSE)

write_json(
  list(
    skill_root = skill_root,
    recipes = c("cellchat-matrix-adapter-r-v1", "cellchat-lr-adapter-r-v1", "cellchat-circle-r-v1", "cellchat-chord-r-v1", "cellchat-bubble-r-v1", "cellchat-heatmap-r-v1"),
    circle = list(matrix = "full aggregate CellChat net$weight", edge_width = "relative aggregate inferred weight", node_size = "incoming + outgoing aggregate weight"),
    chord = list(matrix = "aggregate CellChat net$weight", display_filter = "top 35 positive directed edges by weight", direction = TRUE),
    heatmap = list(matrix = "full aggregate CellChat net$weight", scale = "sequential", transform = "none"),
    bubble = list(rows = "CellChat subsetCommunication net slot", display_filter = "p <= 0.05 then top 30 by probability", colour = "communication probability", area = "-log10(CellChat model p), floored at 1e-4"),
    claim_limits = c("All views summarize model-inferred communication.", "No view proves physical binding, molecular flux, spatial contact, causal signaling or cross-donor reproducibility.", "Top-N filters affect display only and are exported explicitly.")
  ),
  project_path("results", "run_manifest_cellchat_visualizations.json")
)
capture_session_info(project_path("results", "logs", "session_info_cellchat_visualization.txt"))
message("Skill CellChat visualizations complete.")
complete_stage("04_cellchat_visualizations")
