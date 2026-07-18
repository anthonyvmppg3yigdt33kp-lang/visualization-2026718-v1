# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-004-b006\np4 <- DimPlot(sce.all.filt,group.by = \"sample\",split.by = \"sample\",stroke.size=0.4,\n              cols = c(\"#f6a520\",\"#9fedda\",\"#eb8ea8\",\"#93caeb\",\"#4489e5\"),\n              reduction = \"tsne\",ncol = 3,combine = T) +\n  NoLegend() +\n  ggtitle(label = \"\") +\n  theme(\n    panel.grid = element_blank(),\n    # panel.background = element_rect(fill = NA, colour = \"black\", linewidth = 0.5),\n    plot.background = element_blank(),\n    axis.line = element_line(colour = \"black\", linewidth = 0),\n    # 移除坐标轴刻度和标签\n    axis.text = element_blank(),    # 刻度标签\n    axis.title = element_blank(),   # 坐标轴标题\n    axis.ticks = element_blank()   # 刻度线\n  )\np4\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.ticks", "axis.title", "axis.text", "axis.line", "plot.background", "panel.grid", "reduction", "cols", "p4")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
