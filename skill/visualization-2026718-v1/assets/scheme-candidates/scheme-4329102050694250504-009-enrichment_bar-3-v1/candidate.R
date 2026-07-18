# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-009-b007\n#### 改颜色和主题\n# 改颜色\np <- ggplot(data = dt, aes(x = -log10(p.adjust), y = Description, fill = -log10(p.adjust))) +\n  scale_fill_gradientn(values = seq(0,1,0.1),colours = c(\"#ffe10f\",\"#fdae61\",\"#ee561a\",\"#d73027\",\"#dc0224\")) +\n  geom_bar(stat = \"identity\", width = 0.8, alpha = 0.9) +\n  scale_x_continuous(expand = c(0,0)) + # 调整柱子底部与y轴紧贴\n  labs(x = \"\", y = \"\", title = \"\") +\n# x = 0.61 用数值向量控制文本标签起始位置\n  geom_text(size=4.3, aes(x = 0.05, label = Description), hjust = 0, color=rep(c(\"white\",\"black\"),times=c(7,8)) ) + # hjust = 0,左对齐\n  theme_void() +  # 使用完全空白的主题\n  theme(\n    axis.title = element_text(size = 13),\n    axis.text = element_blank(), # 在自定义主题中去掉 y 轴通路标签:\n    axis.ticks.length.y = unit(0,\"cm\"),\n    plot.title = element_text(size = 13, hjust = 0.5, face = \"bold\"),\n    legend.title = element_text(size = 13,angle = 90),\n    legend.text = element_text(size = 11),\n    legend.title.position = \"left\",  # 设置图例标题在左侧\n    legend.position = c(0.90, 0.15),  # 图例整体位置：右下角 (x=0.95, y=0.05)\n    plot.margin = margin(t = 5.5, r = 10, l = 5.5, b = 5.5)\n  )\n\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("plot.margin", "legend.position", "legend.title.position", "legend.text", "legend.title", "plot.title", "axis.ticks.length.y", "axis.text", "axis.title", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
