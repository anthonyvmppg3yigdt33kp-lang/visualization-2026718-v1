# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-023-b004\nggplot(data = df, aes(x = UMAP_1, y = UMAP_2, color = Cluster)) +\n  geom_point(size = 0, shape = 16,stroke = 0) +\n  theme_void()+\n  scale_color_manual(values = color, name = '') +\n  theme( aspect.ratio = 1,\n    legend.position = 'bottom',\n    plot.margin = margin(0,0,0,0) ) +\n  guides(color = guide_legend( ncol = 2, override.aes = list(size = 2, alpha = 1) )) +\n  theme(legend.text = element_text(size = 5),\n        legend.spacing.y = unit(0, 'cm'),\n        legend.key.height = unit(0,\"cm\"),\n        legend.box.spacing = unit(0, 'cm'))\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.box.spacing", "legend.key.height", "legend.spacing.y", "plot.margin", "legend.position")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
