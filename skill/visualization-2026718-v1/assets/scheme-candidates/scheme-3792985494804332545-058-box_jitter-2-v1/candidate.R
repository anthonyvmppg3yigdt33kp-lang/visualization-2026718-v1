# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-058-b006\n# 绘制箱线\np <- ggplot(data=dt,aes(x=group,y=exp,colour = group)) +\n  geom_boxplot(mapping=aes(x=group,y=exp,colour=group), size=0.6, width = 0.8) + # 箱线图，要宽一点\n  geom_jitter(mapping=aes(x=group,y=exp,colour = group),size=1.5,width = 0.2) +  # 抖动散点，要窄一点\n  scale_color_manual(values =color ) + # 颜色，使用人工智能kimi提取 非常方便\n  geom_signif(mapping=aes(x=group,y=exp), # 不同组别的显著性\n              comparisons =compara ,\n              hjust = -1,\n              map_signif_level=T, # T显示显著性，F显示p value\n              tip_length=0, # 修改显著性线两端竖着的长短\n              size=0, # 修改线的粗细\n              textsize = 0, # 修改显著性标记的大小，变成0之前可以看一眼都要哪些显著，用于下面p1的修改\n              test = \"t.test\")  # 检验的类型,可以更改\n\np1 <- p +\n  # 手动添加显著性标记，具体根据个人数据进行调整\n  annotate('text', label = c('*',\"***\",\"***\"), x =c(4,5,6), y =c(1.8,2.6,3.2), size =5,color=\"black\") +\n  theme_bw() + # 设置白色背景\n  labs(x=\"\",y=\"log2-normalized expression\")  + # 添加标题，x轴，y轴标签\n  ggtitle(label = \"CD40LG\") +\n  theme(plot.title = element_text(hjust = 0.5),\n        #axis.line = element_line(linetype=1,color=\"black\",size=0.9),\n        panel.border = element_rect(color = \"black\", fill=NA, size=1.5),\n        axis.title.y =element_text(size=14, face = \"bold\"),\n        axis.text.x =element_text(size=12,angle = 90, face = \"bold\",hjust = 1),\n        axis.text.y =element_text(size=10, face = \"bold\"),\n        legend.position = \"none\" # 不要图例\n        )\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.position", "axis.text.y", "axis.text.x", "axis.title.y", "panel.border", "p1", "test", "textsize", "size", "tip_length", "map_signif_level", "hjust", "comparisons", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
