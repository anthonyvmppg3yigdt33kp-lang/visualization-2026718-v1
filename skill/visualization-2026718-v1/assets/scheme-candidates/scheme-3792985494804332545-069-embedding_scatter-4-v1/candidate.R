# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-069-b010\n## 文章中的\nhead(maskTable)\n\np1 <- DimPlot(sce.all.filt_sub, reduction = \"umap\", group.by = \"RNA_snn_res.0.5\", label = T) +\n  ggtitle(\"celltype_cluster\")\np1\n\n\nplots <- lapply(p1, `+`,\n                list(\n                  geom_path(data=maskTable[cluster==\"T cells\" | cluster==\"B cells\"| cluster==\"Plasma B cells\"],\n                            aes(x=umap_1, y=umap_2, group=group),linewidth=0.3,linetype = 2),\n                  # so that borders aren't cropped:\n                  scale_x_continuous(expand = expansion(mult = 0.05)),\n                  scale_y_continuous(expand = expansion(mult = 0.05)))\n)\n\npatchwork::wrap_plots(plots)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("plots", "p1")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
