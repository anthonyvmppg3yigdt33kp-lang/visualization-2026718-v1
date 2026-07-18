# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-026-b004\n# 自定义主题与配色修改：\np <- ggplot() +\n  geom_point(data = data, aes(x = GeneRatio1, y = Description,  color = -log10(pvalue)), size =6) +\n  scale_colour_distiller(palette = \"Reds\", direction = 1) + #更改配色\n  labs(x = \"Gene Ratio\", y = \"\",color=\"-log10(Pvalue)\") +\n  theme_bw() +\n  theme(axis.title = element_text(size = 13),\n        axis.text = element_text(size = 11),\n        # axis.text.y = element_blank(), # 不展示y轴标题\n        # axis.ticks.y = element_blank(),\n        legend.title = element_text(size = 13),\n        legend.text = element_text(size = 11),\n        panel.grid.major = element_blank(),  # 去掉主要网格线\n        panel.grid.minor = element_blank()   # 去掉次要网格线\n  )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("panel.grid.minor", "panel.grid.major", "legend.text", "legend.title", "axis.text", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
