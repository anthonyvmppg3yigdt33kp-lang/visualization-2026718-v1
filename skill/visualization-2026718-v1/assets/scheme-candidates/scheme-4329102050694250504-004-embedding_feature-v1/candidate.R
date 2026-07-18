# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-004-b005\n# marker基因\ngene <- c(\"CD3D\",\"CD4\",\"CD8A\",\"NKG7\",\"CD79A\",\"CD68\")\n# # scRNAtoolVis\n# p3 <- scRNAtoolVis::featurePlot(sce.all.filt, genes = gene, dim = \"tsne\",ncol = 3)\n# p3\n# scCustomize\np3 <- FeaturePlot_scCustom( seurat_object= sce.all.filt,order = T, features = gene,pt.size = 0.25,stroke.size=0.1,\n                            num_columns = 3,reduction = \"tsne\") &\n  scale_color_gradient(low = \"grey\", high = \"#f32a1f\") &\n  NoLegend() &\n  theme(\n    panel.grid = element_blank(),\n    panel.background = element_rect(fill = NA, colour = \"black\", linewidth = 0.5),\n    plot.background = element_blank(),\n    axis.line = element_line(colour = \"black\", linewidth = 0.1),\n    # 移除坐标轴刻度和标签\n    axis.text = element_blank(),    # 刻度标签\n    axis.title = element_blank(),   # 坐标轴标题\n    axis.ticks = element_blank()   # 刻度线\n  )\np3\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.ticks", "axis.title", "axis.text", "axis.line", "plot.background", "panel.background", "panel.grid", "num_columns", "p3", "gene")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
