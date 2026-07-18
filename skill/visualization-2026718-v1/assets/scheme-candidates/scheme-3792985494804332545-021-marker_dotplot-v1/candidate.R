# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-021-b002\n## 设置颜色\ncolors = c('#fcfbfd', '#efedf5', '#dadaeb', '#bcbddc', '#9e9ac8', '#807dba', '#6a51a3', '#4a1486')\ncolors1 = colorRampPalette(colors)(50)\n\nFig2e <- ggplot(data, aes(y = features.plot, x = id)) + ## global aes\n  geom_point(aes(fill = avg.exp.scaled, size =pct.exp), color='black',shape=21)  +  ## geom_point for circle illusion\n  scale_fill_gradientn(colours=colors1,  limits = c(-1,1.5)) +  ## color of the corresponding aes\n  labs(x='',y='') +\n  scale_size(range = c(0,10), limits = c(0, 100), breaks = c(0,25,50,75,100)) +   ## to tune the size of circles\n  coord_cartesian(clip = 'off') +\n  theme_bw(base_size = 14) +\n  theme(panel.grid.major = element_blank(),\n    panel.grid.minor = element_blank(),\n    panel.background = element_blank(),\n    axis.line = element_line(colour = \"black\"),\n    plot.margin = margin(t = 20, r = 20, b = 30, l = 20, unit = \"pt\"),  # 设置四周的空白区域\n    axis.text.x=element_blank(),\n    axis.ticks.x = element_blank(),\n    axis.ticks.y = element_blank(),\n    axis.text.y = element_text(\n      face = \"bold\",  # 设置字体为斜体\n      # family = \"Arial\" ,  # 设置字体为 Times New Roman\n      hjust = 1,  # 设置文本右对齐\n      size = 14,\n      margin = margin(r = 20))  # 调整 y 轴刻度标签与 y 轴的距离\n    )\n\nprint(Fig2e)\n\n# source block: article-3792985494804332545-021-b004\n# annotate mannually\nFig2e <- annoSegment(object = Fig2e, annoPos = 'left', annoManual = T,\n            xPosition = rep(0.2, 5),\n            yPosition = list(c(1,7,11,16), c(6,10,15,18) ),\n            pCol = c(\"#f3e637\",\"#e273ad\",\"#f2640e\",\"#2a9afe\"),\n            segWidth = 0.56, lwd = 23)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("margin", "size", "hjust", "face", "axis.text.y", "axis.ticks.y", "axis.ticks.x", "axis.text.x", "plot.margin", "axis.line", "panel.background", "panel.grid.minor", "Fig2e", "colors1", "colors")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
