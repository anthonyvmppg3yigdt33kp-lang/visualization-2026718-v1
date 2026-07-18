# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-061-b004\np <- ggplot(data = data, aes(x = xlab, y = NES)) +\n  geom_point(aes(size = setSize_1, alpha = -log10(pvalue)), shape = 21, stroke = 0.7,fill = \"#0000ff\", colour = \"black\") + # stroke：设置点的边框宽度。\n  scale_size_continuous(range = c(0.2, 8)) +\n  xlab(label = \"Hallmark gene sets\") +\n  ylab(label = \"Normalized enrichment score (NES)\") +\n  theme_classic(base_size = 15) +\n  scale_x_continuous(breaks = seq(0, 50, by = 10), labels = seq(0, 50, by = 10) ) + # 设置x轴的刻度线和刻度标签\n  scale_y_continuous( breaks = seq(-4, 2.3, by = 1), labels = seq(-4, 2.3, by = 1) ) +\n  guides(size = guide_legend(title = \"Detection\\n(proportion)\"),\n         alpha = guide_legend(title = \"Significance\\n(-log10 p-val.)\") ) +  # 修改图例标题\n  theme(\n    axis.line = element_line(color = \"black\", size = 0.6), # 加粗x轴和y轴的线条\n    axis.text = element_text(face = \"bold\"), # 加粗x轴和y轴的标签\n    axis.title = element_text( size = 13)    # 加粗x轴和y轴的标题\n  )\n\np\n\n# source block: article-3792985494804332545-061-b005\n# 添加label：vjust（垂直调整）或hjust（水平调整）\np3 <- p +\n  geom_text_repel(data= data_label, aes(x = xlab, y = NES,label = ID), size = 3, color = data_label$col,\n                  force=20,                # 将重叠的文本标签相互推开的强度。force 参数的值越大，标签之间的排斥力度也越大，这会导致标签在图中更分散地排列\n                  point.padding = 0.5,     # 设置文本标签与对应点之间的最小距离\n                  min.segment.length = 0,  # 长度大于0就可以添加引线\n                  hjust = 1.2,             # 文本标签的右侧与指定位置对齐\n                  segment.color=\"grey20\",\n                  segment.size=0.3,        # 设置引导线的粗细\n                  segment.alpha=0.8,       # 文本标签中连接线段的透明度\n                  nudge_y=-0.1             # 在y轴方向上微调标签位置\n                  )\np3\n\n# 保存\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p3", "axis.title", "axis.text", "axis.line", "alpha", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
