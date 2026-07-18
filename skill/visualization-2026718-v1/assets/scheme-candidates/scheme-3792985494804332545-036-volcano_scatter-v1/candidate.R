# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-036-b006\n## ggplot2 绘图\n\n# 颜色设置\ncolors <- c(\"upIn\"=\"#a73336\",\"up\"=\"#fe8264\",\"downIn\"=\"#333aab\",\"down\"=\"#b5dbe6\",\"normal\"=\"#474747\",\"normalIn\"=\"#474747\")\ncolors\n\n# 看一眼数据\nhead(diff_g1)\n\np <- ggplot(diff_g1, aes(x = logFC, y = -log10(adj.P.Val)))  +\n  geom_point(data = data_bg, shape = 21, fill=\"#474747\",color =\"black\" , alpha = 0.8, size = 1.3, stroke = 0.3) +  # 不显著的灰色点：shape=21带边框的圆形，stroke点的边框宽度\n  geom_point(data = data_sig, aes(fill = color), shape = 21, color = \"black\", size = 2, stroke = 0.3) +  # 显著的点\n  scale_fill_manual(values = colors,  # 点的颜色\n                    labels = c(\"upIn\" = \"In ERK Compendium\", \"downIn\" = \"\",\n                               \"up\" = \"Not ERK Compendium\", \"down\" = \"\")  # 自定义图例标签\n                    ) +\n  geom_text_repel(data= data_label, aes(x = logFC, y = -log10(adj.P.Val),label = phos.name), size = 3,\n                  force_pull=0,         # 设置标签吸引力为 0，标签不会被强制拉回到数据点\n                  point.padding = 0,     # 设置文本标签与对应点之间的最小距离\n                  box.padding = 1,       # 设置标签与数据点之间的最小距离,值：0.5\n                  min.segment.length = 0,  # 长度大于0就可以添加引线\n                  vjust = 0.5,            # 文本标签的右侧与指定位置对齐\n                  segment.color=\"grey20\",\n                  segment.size=0.5,        # 设置引导线的粗细\n                  segment.alpha=0.8,       # 文本标签中连接线段的透明度\n                  max.overlaps = Inf,\n                  seed = 123, max.time = 1, max.iter = Inf,\n                  nudge_y=0.5,nudge_x=-0.3 )  +       # 在y轴方向上微调标签位置\n  geom_hline(yintercept = -log10(0.05), color = \"#474747\", linewidth = 0.6, linetype = \"dashed\") + # 添加显著性虚水平线\n  scale_x_continuous(limits = c(-3, 3), breaks = seq(-3, 3, 1)) +\n  scale_y_continuous(expand = c(0, 0)) + # 点的y轴起点紧贴x轴线\n  labs(title = \"1 h ERKi\", x = expression(log[2](FC)), y = expression(-log[10](adj.p))) +\n  theme_classic() +\n  theme (legend.position = \"right\",\n         legend.text = element_text(size = 12),\n         plot.title = element_text(size = 16, face = \"bold\",hjust = 0.5),\n         axis.title.x = element_text(size = 16),\n         axis.title.y = element_text(size = 16),\n         axis.text.x = element_text(size = 12),\n         axis.text.y = element_text(size = 12))\n\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.text.y", "axis.text.x", "axis.title.y", "axis.title.x", "plot.title", "legend.text", "nudge_y", "seed", "max.overlaps", "segment.alpha", "segment.size", "segment.color", "vjust", "min.segment.length", "box.padding", "point.padding", "force_pull", "labels", "p", "colors")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
