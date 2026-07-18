# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-037-b002\nlibrary(ggprism)\nlibrary(RColorBrewer)\nlibrary(circlize)\ncolors <- colorRampPalette(rev(brewer.pal(n = 11, name = \"RdYlBu\")))(100)\nvalues <- seq(0, 303, length.out = 101)[-101]\ncol_fun <- colorRamp2(values, colors)\ncol_fun\n\n\np <- ggplot(data = deg, aes(x = rank, y = avg_logFC,color = -log10(p_val_adj) )) +\n  geom_point(aes(size = 6)) +\n  xlab(label = \"DEGs\") +\n  ylab(label = \"avg_logFC\") +\n  labs(title = \"CD8 T cells -\nmost DE genes in\ncolitis-associated clusters\") +\n#scale_color_gradient2(low = \"black\",mid=\"blue\",high = \"#ed382b\", midpoint = 43,limit = c(0, 303))  + # 更改填充颜色\n  scale_color_gradientn(colors = col_fun(values)) +\n  theme_bw(base_size = 15) +\n  scale_x_continuous(breaks = seq(0, 3000, by = 1000), labels = seq(0, 3000, by = 1000) ) + # 设置x轴的刻度线和刻度标签\n  guides(size = \"none\", color = guide_colourbar(title = \"Adjusted\nPvalue\") ) +  # 修改图例标题，guide_colourbar图例使用长方形显示\n  theme(\n    #axis.line = element_line(color = \"black\", size = 0.6), # 加粗x轴和y轴的线条\n    plot.title = element_text(hjust = 0.5, size = 15, color = \"black\"),\n    panel.border = element_rect(color = \"black\", size = 1.3, fill = NA),\n    axis.text = element_text(face = \"bold\"), # 加粗x轴和y轴的标签\n    axis.title = element_text( size = 15)    # 加粗x轴和y轴的标题\n  )\n\np\n\n# source block: article-3792985494804332545-037-b003\n# 添加label：vjust（垂直调整）或hjust（水平调整）\np3 <- p +\n  geom_text_repel(data= top, aes(x =rank, y = avg_logFC,label = Gene), size = 4.5, color = \"#5f70b3\",\n                  force=20,                # 将重叠的文本标签相互推开的强度。force 参数的值越大，标签之间的排斥力度也越大，这会导致标签在图中更分散地排列\n                  point.padding = 0.5,     # 设置文本标签与对应点之间的最小距离\n                  min.segment.length = 0,  # 长度大于0就可以添加引线\n                  hjust = 1.2,             # 文本标签的右侧与指定位置对齐\n                  segment.color=\"grey20\",\n                  segment.size=0.3,        # 设置引导线的粗细\n                  segment.alpha=0.8,       # 文本标签中连接线段的透明度\n                  nudge_y=-0.1             # 在y轴方向上微调标签位置\n  )\np3\n\n# 保存\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p3", "axis.title", "axis.text", "panel.border", "plot.title", "p", "col_fun", "values", "colors")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
