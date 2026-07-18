# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-044-b006\n# 获取每种细胞亚群中Top10基因:\ntop10 <- diff_sc %>%\n  group_by(Group) %>%\n  top_n(10, abs(avg_log2FC)) %>%\n  ungroup() %>%\n  as.data.frame()\n\n# 文献中抠出来的颜色：\nmycol <- c('#b12d30', '#43b5e6', '#93ba1f', '#58ac41', '#f0bbcb','#f1aa41'\n           ,\"#6cc3b9\",\"#fc3c46\",\"#b76f9e\",\"#3568a3\",\"#f66464\")\n\n# 基础火山图绘制：\np <- ggplot() +\n  geom_point(data = diff_sc, aes(x = avg_log2FC, y = log10fdr),size = 0.8, color = 'grey') +\n  coord_flip() + # 坐标轴翻转\n  facet_grid(. ~ Group,scales = \"free\") + # 一行多列;\n  geom_point(data = top10, aes(x = avg_log2FC, y = log10fdr,color = Group)) + # 添加top点颜色\n  geom_vline(xintercept = c(-0.58, 0.58), size = 0.5, color = \"grey50\", lty = 'dashed')+ #添加阈值线\n  scale_color_manual(values = mycol) + #更改配色\n  xlab(label = \"avg_log2FC(IPF vs. normal)\") +\n  ylab(label = \"\") +\n  theme_bw()+\n  theme( legend.position = 'none', #去掉图例\n    panel.grid = element_blank(), #去掉背景网格\n    axis.text = element_text(size = 10), #坐标轴标签大小\n    axis.text.x = element_text(angle = 45, vjust = 0.8), #x轴标签旋转\n    strip.text.x = element_text(size = 10, face = 'bold') #加粗分面标题\n  )\n\n# source block: article-3792985494804332545-044-b007\n# 添加 top 基因 symbol：\np1 <- p +\n  geom_text_repel(\n    data = top10,\n    aes(x = avg_log2FC, y = log10fdr, label = gene, color = Group),\n    fontface = 'italic',\n    seed = 233,\n    size = 3,\n    min.segment.length = 0, # 始终为标签添加指引线段；若不想添加线段，则改为Inf\n    force = 12,           # 重叠标签间的排斥力\n    force_pull = 2,       # 标签和数据点间的吸引力\n    box.padding = 0.1,    # 标签周边填充量，默认单位为行\n    max.overlaps = Inf,   # 排斥重叠过多标签，设置为Inf则可以保持始终显示所有标签\n    segment.linetype = 3, # 线段类型,1为实线,2-6为不同类型虚线\n    segment.alpha = 0.5,  # 线段不透明度\n    direction = \"y\", # 按y轴调整标签位置方向，若想水平对齐则为x\n    hjust = 0        # 0右对齐，1左对齐，0.5居中\n  )\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p1", "strip.text.x", "axis.text.x", "axis.text", "panel.grid", "p", "mycol", "top10")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
