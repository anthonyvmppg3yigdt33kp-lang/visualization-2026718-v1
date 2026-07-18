# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-030-b008\n## 美化\np <- netVisual_bubble(cellchat, sources.use = 5, targets.use = c(1,2,3,4,6,7,8), remove.isolate = FALSE,pairLR.use = pairLR.use, grid.on=T,color.grid = \"black\")\n\n# 看颜色范围\nrange(p$data$prob,na.rm = T)\nsummary(p$data$prob,na.rm = T)\n\np1 <- p + scale_size_continuous(range = c(4, 8), guide = \"none\") +   # 调整气泡大小范围\n  scale_color_gradientn(\n    colours = c(\"#2760a9\", \"white\", \"#e50f20\"),  # 定义颜色向量\n    values = scales::rescale(c(0.2, 0.35, 0.5)),  # 定义颜色映射的范围\n    name = \"Commun. Prob.\" ) +  # 图例标题\n  xlab(label = NULL) +\n  ylab(label = NULL) +\n  geom_vline(xintercept = seq(1.5, length(unique(df.net$source)) - 0.5, 1)[1:6],lwd = 0.5) + ## 根据 netVisual_bubble 函数的源码，修改格子线的粗细\n  geom_hline(yintercept = seq(1.5, length(unique(df.net$interaction_name_2)) - 0.5, 1)[1:3], lwd = 0.5) +\n  theme(axis.title.x = element_text(size = 16),  # 设置 x 轴标题字体大小\n    axis.title.y = element_text(size = 16),  # 设置 y 轴标题字体大小\n    axis.text.x = element_text(size = 14),  # 设置 x 轴刻度标签字体大小\n    axis.text.y = element_text(size = 14, face = \"italic\"),   # 设置 y 轴刻度标签字体大小\n    panel.border = element_rect(color = \"black\", fill=NA, size=1),  # 设置四周边框的颜色和粗细\n    legend.key.size = unit(0.6, 'cm'),  # 设置图例键的大小\n    legend.text = element_text(size = 12),  # 设置图例文本的大小\n    legend.title = element_text(size = 13)\n  )\np1\n\n# 保存\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.title", "legend.text", "legend.key.size", "panel.border", "axis.text.y", "axis.text.x", "axis.title.y", "name", "values", "colours", "p1", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
