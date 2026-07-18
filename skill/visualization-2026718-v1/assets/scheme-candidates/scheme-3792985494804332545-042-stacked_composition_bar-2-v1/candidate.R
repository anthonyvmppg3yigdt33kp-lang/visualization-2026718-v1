# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-042-b003\n# 左侧堆积柱状图\ndf2 <- df[df$time==\"PFS_cancerNum\", ]\np2 <- ggplot(df2, aes(x = count, y = celltype, fill = type)) +\n  geom_bar(position = \"stack\", stat=\"identity\", alpha = 1,color=\"black\") +\n  scale_y_discrete(position = \"right\") + # 将Y轴放到左侧\n  scale_x_reverse(expand = c(0,0)) + # 数值也需要同时逆转\n  xlab(\"\") +\n  scale_fill_manual(values = mycol) + # 修改配色\n  ggtitle(\"PFS in TCGA\") +\n  theme_classic() +\n  theme( # legend.position = \"none\", # 去掉图例\n        title = element_text(face = \"bold\",size=16,hjust = 0),\n        axis.line = element_line(color = \"black\", linewidth = 0.9),  # 设置坐标轴线的颜色和粗细\n        axis.title.y = element_blank(),\n        axis.text.x = element_text(face = \"bold\",size=16),   # x轴刻度标签加粗\n        axis.text.y = element_blank(),   # 去掉y轴标签\n        axis.ticks = element_line(color = \"black\", size = 1.1),  # 设置刻度线的颜色和粗细\n        axis.ticks.length = unit(0.2, \"cm\")          # 设置刻度线长度\n  )\np2\n\n# source block: article-3792985494804332545-042-b004\n## #拼图：\nlibrary(patchwork)\np <-  (p2 | p1) + plot_layout(guides = 'collect') &\n  theme( legend.justification = c(\"right\", \"bottom\"),\n         legend.text = element_text(face = \"bold\",size=15),  # 图例标签加粗\n         legend.title = element_blank() # 移除图例标题\n         )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.ticks.length", "axis.ticks", "axis.text.y", "axis.text.x", "axis.title.y", "axis.line", "title", "p2", "df2")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
