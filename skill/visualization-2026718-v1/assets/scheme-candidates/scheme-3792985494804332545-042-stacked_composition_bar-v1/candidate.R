# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-042-b002\n## 绘图\n# 右侧堆积柱状图\ndf1 <- df[df$time==\"OS_cancerNum\", ]\np1 <- ggplot(df1, aes(x = count, y = celltype, fill = type)) +\n  geom_bar(position = \"stack\", stat=\"identity\", alpha = 1,color=\"black\") +\n  xlab(\"\") +\n  scale_fill_manual(values = mycol) + # 修改配色\n  scale_x_continuous(expand = c(0,0)) + # 柱子贴坐标轴\n  ggtitle(\"OS in TCGA\") +\n  theme_classic() +\n  theme( # legend.position = \"none\", # 去掉图例\n        title = element_text(face = \"bold\",size=16),\n        axis.line = element_line(color = \"black\", linewidth = 0.9),  # 设置坐标轴线的颜色和粗细\n        axis.title.y = element_blank(),,# 去掉y轴标题\n        axis.text.x = element_text(face = \"bold\",size=16),   # x轴刻度标签加粗\n        axis.text.y = element_text(face = \"bold\",size=16,hjust = 0.5,color=\"black\"),   # y轴刻度标签加粗\n        axis.ticks = element_line(color = \"black\", size = 1.1),  # 设置刻度线的颜色和粗细\n        axis.ticks.length = unit(0.2, \"cm\")          # 设置刻度线长度\n        )\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.ticks.length", "axis.ticks", "axis.text.y", "axis.text.x", "axis.title.y", "axis.line", "title", "p1", "df1")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
