# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-038-b009\n## 左边\ndf2 <- dat_plot[,c(\"Subset\", \"M1_signatures1\") ]\n\np2 <- ggplot(df2, aes(x = -M1_signatures1, y = Subset, fill = Subset)) +\n  geom_violin( alpha = 0.8,color=\"black\",trim = F) +\n  geom_boxplot(width = 0.16, fill = \"white\", outliers = FALSE) + #小提琴中的箱线图\n  labs(title = \"M1 Feature\") + # 添加顶部的文字\n  scale_fill_manual(values = mycol) + # 修改配色\n  scale_x_continuous(expand = c(0,0),position = \"top\",\n                     #breaks = seq(-0.5, 1.5, by = 0.5),  # 设置刻度线的位置，每隔0.5个单位一个刻度\n                     #labels = seq(-0.5, 1.5, by = 0.5),        # 设置刻度标签的格式，这里使用千位分隔符\n                     guide = guide_axis(angle = -90), # x轴标签旋转90度，竖着\n                     labels = function(x) format(-(x), nsmall = 1)\n                     ) + # 柱子贴坐标轴,横坐标放在顶部\n  geom_vline(xintercept = -0.25, linetype = \"dashed\", color = \"#bf1a2c\", size = 1) +\n  scale_y_discrete(position = \"right\") +\n  theme_classic() +\n  theme(legend.position = \"none\", # 去掉图例\n        plot.margin = margin(l = 5, b = 30,unit = \"pt\"),  # l：左侧边距的大小, b：底部边距的大小\n        plot.title = element_text(size=16,hjust = 0.5, vjust = -123, color = \"#f15929\"),\n        axis.line = element_line(color = \"black\", linewidth = 0.5),  # 设置坐标轴线的颜色和粗细\n        axis.title.y = element_blank(),# 去掉y轴标题\n        axis.title.x = element_blank(),# 去掉x轴标题\n        axis.text.x = element_text(size=16),   # x轴刻度标签加粗\n        axis.text.y = element_blank(),   # y轴刻度标签去除\n        axis.ticks = element_line(color = \"black\", size = 0.5),  # 设置刻度线的颜色和粗细\n        axis.ticks.length = unit(0.2, \"cm\")\n        )\np2\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.ticks.length", "axis.ticks", "axis.text.y", "axis.text.x", "axis.title.x", "axis.title.y", "axis.line", "plot.title", "plot.margin", "labels", "guide", "p2", "df2")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
