# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-023-b003\ncolor <- c(\"#919ac2\",\"#ffac98\",\"#70a4c8\",\"#a5a9af\",\"#63917d\",\"#dbd1b4\",\"#6e729a\",\"#9ba4bd\",\"#c5ae5f\",\"#b9b8d6\")\n\nlibrary(ggh4x)\np <- ggplot(df, aes(x = UMAP_1, y = UMAP_2, color = Cluster)) +\n  geom_point(size = 0.03,shape = 16, stroke = 0) +\n  scale_color_manual(values = color) +\n  facet_grid(~label) +\n  theme_classic() +  # 使用简洁主题\n  theme( plot.background = element_blank(),  # 移除背景\n         panel.grid.major = element_blank(),  # 移除主要网格线\n         panel.grid.minor = element_blank(),  # 移除次要网格线\n         margin = margin(),  # 增加顶部边距\n         axis.title.x = element_blank(),  # 移除x轴标题\n         axis.title.y = element_blank(),  # 移除y轴标题\n         axis.text = element_blank(),  # 移除坐标轴刻度标签\n         axis.ticks = element_blank(),  # 移除坐标轴刻度线\n         axis.line = element_line(colour = \"black\", size = 0.3,\n                                  arrow = arrow(length = unit(0.1, \"cm\"))),  # 加粗坐标轴并添加箭头\n         strip.background = element_rect(fill = '#e6bac5',color=NA),\n         strip.placement = 'outside',\n         strip.text = element_text(size = 8),\n         legend.position = \"none\",\n         aspect.ratio = 1) +\n  scale_x_continuous(limits = c(min(df$UMAP_1), max(df$UMAP_1)) ) +  # 设置x轴范围\n  scale_y_continuous(limits = c(min(df$UMAP_2), max(df$UMAP_2)) )   # 设置y轴范围\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("aspect.ratio", "legend.position", "strip.text", "strip.placement", "strip.background", "arrow", "axis.line", "axis.ticks", "axis.text", "axis.title.y", "axis.title.x", "margin", "panel.grid.minor", "panel.grid.major", "p", "color")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
