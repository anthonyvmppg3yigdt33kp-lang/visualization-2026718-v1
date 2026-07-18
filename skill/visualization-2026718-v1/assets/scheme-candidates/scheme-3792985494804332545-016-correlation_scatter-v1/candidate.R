# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-016-b003\n## 绘图\np <- ggscatter(data, x = \"CD8A\", y = \"FOLR2\", color = \"#a6d38d\", add = \"none\", conf.int =F,size = 3) +  # 置信区间的填充色\n  stat_cor(method = \"pearson\",  # 相关系数的计算方法\n           label.x = 1,  # 相关系数标签的 x 坐标\n           label.y = 7, # 相关系数标签的 y 坐标\n           size = 7) +  # 相关系数标签的大小\n  geom_smooth(method = \"lm\", color = \"black\", linetype = \"solid\",linewidth = 0.8,se = F) + # 回归线的线型\n  labs(x = \"CD8A\", y = \"FOLR2\") +\n  facet_grid(~g) +\n  theme_bw() +\n  theme(\n    # 加粗边框\n    panel.border = element_rect(color = \"black\", size = 0.8, fill = NA),\n    # 加粗加大坐标轴标签\n    axis.text = element_text(face = \"bold\", size = 14),\n    axis.title = element_text(face = \"italic\", size = 16),\n    # 加粗加大分面标题\n    strip.text = element_text(face = \"bold\", size = 16, color = \"black\"),\n    # 去掉背景网格线\n    panel.grid.major = element_blank(),\n    panel.grid.minor = element_blank()\n  )\np\n\n# 保存，找到一个合适的尺寸保存\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("panel.grid.minor", "panel.grid.major", "strip.text", "axis.title", "axis.text", "panel.border", "size", "label.y", "label.x", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
