# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-018-b006\np <- ggplot(df , aes(x = umap_1, y = umap_2)) +\n  stat_unchull(aes(fill = newMainCellTypes, color = newMainCellTypes),\n               alpha = 0.05, size = 1, lty = 2, delta=0.25, show.legend=F) +\n  geom_point(aes(color = RNA_snn_res.0.5), size = 0.2, show.legend = FALSE) + #亚群的颜色\n  scale_color_manual(values = cols)\np\n\n# source block: article-4329102050694250504-018-b007\n# 数字标签\np1 <- p +\n  geom_text_repel(data=sub_type_med, aes(label=RNA_snn_res.0.5),color=\"black\" ,\n                  fontface=\"bold\",show.legend=F, size=4)\np1\n\n# 大亚群标签\np2 <- p1 +\n  geom_text_repel(data=main_type_med, aes(label=newMainCellTypes, color=newMainCellTypes),\n                  fontface=\"bold\",show.legend=F, size=6)\np2\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p2", "p1", "alpha", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
