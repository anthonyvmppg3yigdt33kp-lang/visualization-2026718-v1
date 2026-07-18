# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-016-b003\n## 2.ggplot2绘图\np <- ggplot(data = dt, aes(x=CRCvsNormal.avg_log2FC, y=LMvsCRC.avg_log2FC)) +\n  geom_point(aes(size = LMvsCRC.avg_log2FC, color=LMvsCRC.avg_log2FC), shape = 19) + # stroke：设置点的边框宽度。\n  scale_size_continuous(range = c(1, 4)) +  # 调整点的大小范围\n  scale_color_gradientn(\n    colors = c(\"#5961a3\", \"#54aca5\", \"#eff1b4\", \"#fdae61\", \"#cb4958\"),\n    values = scales::rescale(c(-5, -4, -2, 0, 2.5)),  # 关键节点位置\n    limits = c(-5, 2.6))\np\n\n# source block: article-4329102050694250504-016-b004\np1 <- p  +\n  geom_text_repel(data= dt, aes(x=CRCvsNormal.avg_log2FC, y=LMvsCRC.avg_log2FC,label = CRCvsNormal.X), size =2.4,\n                  force_pull=2,         # 设置标签吸引力为 0，标签不会被强制拉回到数据点\n                  point.padding = 0,     # 设置文本标签与对应点之间的最小距离\n                  box.padding = 0.01,       # 设置标签与数据点之间的最小距离,值：0.5\n                  min.segment.length = 0.03,  # 长度大于0就可以添加引线\n                  segment.color=\"grey20\",\n                  segment.size=0.5,        # 设置引导线的粗细\n                  segment.alpha=0.8,       # 文本标签中连接线段的透明度\n                  max.overlaps = Inf,\n                  seed = 123, max.time = 1, max.iter = Inf)\n\np1\n\n# source block: article-4329102050694250504-016-b005\np2 <- p1 +\n  geom_vline(xintercept = 0, linetype = \"dashed\", color = \"gray50\", linewidth = 0.8) +\n  geom_hline(yintercept = 0, linetype = \"dashed\", color = \"gray50\", linewidth = 0.8) +\n  scale_alpha_continuous(range = c(0.3, 1)) +  # 调整透明度范围\n  xlab(label = \"CRC vs. Normal log2 Fold Change\") +\n  ylab(label = \"LM vs. Normal log2 Fold Change\") +\n  ggtitle(\"DEG profiles across CRC vs. Normal, LM vs. Normal,\nand LM vs. CRC\")\np2\n\np3 <- p2 +\n  theme_bw() +\n  theme (legend.position = \"right\",\n         legend.text = element_text(size = 12),\n         panel.border = element_rect( color = \"black\", fill = NA, linewidth = 1.2 ),\n         # 去掉所有背景格子线\n         panel.grid.major = element_blank(),   # 去掉主要网格线\n         panel.grid.minor = element_blank(),   # 去掉次要网格线\n         plot.title = element_text(size = 16, face = \"bold\",hjust = 0.5),\n         axis.title.x = element_text(size = 16),\n         axis.title.y = element_text(size = 16),\n         axis.text.x = element_text(size = 12),\n         axis.text.y = element_text(size = 12))\n\np3\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p3", "p2", "p1", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
