# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-010-b004\n## 绘制左边的图\np1 <- DotPlot(object = subset(Lymphoma_data, cell_state == \"C5_T\"),features = T_cell_naive_mem_markers, group.by=\"CN_cluster\", scale.by = \"size\", scale=5, col.max = 1.3) +\n  RotatedAxis() +\n  scale_color_gradientn(values = seq(0,1,0.1),colours = c(\"#4575b4\",\"#abd9e9\",\"#e0f3f8\",\"#ffffbf\",\"#fdae61\",\"#d73027\",\"#800026\"))\np1\nrange(p1@data$pct.exp)\n\n# source block: article-3792985494804332545-010-b005\n## 添加注释框\np1 <- p1 +\n  xlab(label = \"\") + ylab(label = \"\") +\n  scale_size_continuous( range = c(1.2, 10) ) +\n# 第一列\n  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color=\"black\") +\n  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=5.7,ymax=6.3),fill=NA,linetype = 2,linewidth = 0.8,color=\"black\") +\n  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=2.7,ymax=3.3),fill=NA,linetype = 2,linewidth = 0.8,color=\"black\") +\n# 第二列\n  geom_rect(aes(xmin=2.7,xmax=3.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color=\"black\") +\n# 第三列\n  geom_rect(aes(xmin=3.7,xmax=4.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color=\"black\")\np1\n\n# source block: article-3792985494804332545-010-b006\n## 添加底部文字\np1 <- p1 +\n  geom_segment(x=0.5,xend=6.5,y=-0.8,yend=-0.8,linewidth = 0.45) +\n  annotate(geom=\"text\",x = 4, y = -Inf,label=\"Naive and memory\",hjust = 0.5, vjust = 6,size=6.3) +\n  coord_cartesian(clip=\"off\")  +\n  labs(title = \"C5_T in different spatial niches\") +\n  theme( plot.margin = margin(r = 0,b = 30) ,\n         plot.title = element_text(size = 15),\n         axis.text = element_text(size = 14) )\n\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p1")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
