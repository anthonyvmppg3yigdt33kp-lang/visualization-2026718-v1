# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-013-b005\n# 绘图\np <- ggplot(cell.prop,aes(CN_cluster,Proportion,fill=cell_state)) +\n  geom_bar(stat = \"identity\",position = \"fill\") +\n  ggtitle(\"Cell composition in each spatial niche\") +\n  ylab(label = \"Proportion of cell clusters\") +\n  scale_x_discrete(name = \"\", labels = rev(c(\"CN1_T\", \"CN2_PC\", \"CN3_Myeloid\",\"CN4_Stromal\",\"CN5_Tumor-B\",\n                                         \"CN6_Diffuse\",\"CN7_Mixe\"))) +\n  coord_flip() +\n  theme_bw() +\n  scale_fill_manual(values=color) +\n  theme_classic() +\n  theme(axis.ticks.length = unit(0.2,'cm'),\n        legend.position = \"right\",  # 设置图例位置\n        legend.direction = \"vertical\",  # 设置图例方向\n        legend.box = \"vertical\",  # 设置图例框的方向\n        legend.text = element_text( size = 12, face = \"plain\",color = \"black\"),\n        plot.title = element_text(size = 16),  # 修改图片标题的字体大小和样式\n        axis.title.x = element_text(size = 16),  # 修改x轴标题的字体大小\n        axis.text.x = element_text(size = 14),  # 修改x轴刻度标签的字体大小\n        axis.text.y = element_text(size = 16)   # 修改y轴刻度标签的字体大小\n        ) +\n  guides(fill=guide_legend(title = NULL,ncol=2))\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.text.y", "axis.text.x", "axis.title.x", "plot.title", "legend.text", "legend.box", "legend.direction", "legend.position", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
