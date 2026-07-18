# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-009-b006\np <- ggplot(data = dt, aes(x = -log10(p.adjust), y = Description, fill = -log10(p.adjust))) +\n  scale_fill_gradientn(values = seq(0,1,0.1),colours = c(\"#4575b4\",\"#abd9e9\",\"#e0f3f8\",\"#ffffbf\",\"#fdae61\",\"#d73027\",\"#800026\")) +\n  geom_bar(stat = \"identity\", width = 0.7, alpha = 0.8) +\n  scale_x_continuous(expand = c(0,0)) + # 调整柱子底部与y轴紧贴\n  labs(x = \"-Log10(pvalue)\", y = \"\", title = \"KEGG Pathway enrichment\") +\n# x = 0.61 用数值向量控制文本标签起始位置\n  geom_text(size=4.3, aes(x = 0.05, label = Description), hjust = 0, color=rep(c(\"white\",\"black\"),times=c(3,12)) ) + # hjust = 0,左对齐\n  theme_classic() +\n  theme(\n    axis.title = element_text(size = 13),\n    axis.text = element_text(size = 11),\n    axis.text.y = element_blank(), # 在自定义主题中去掉 y 轴通路标签:\n    axis.ticks.length.y = unit(0,\"cm\"),\n    plot.title = element_text(size = 13, hjust = 0.5, face = \"bold\"),\n    legend.title = element_text(size = 13),\n    legend.text = element_text(size = 11),\n    plot.margin = margin(t = 5.5, r = 10, l = 5.5, b = 5.5)\n  ) +\n  NoLegend()\n\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("plot.margin", "legend.text", "legend.title", "plot.title", "axis.ticks.length.y", "axis.text.y", "axis.text", "axis.title", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
