# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-005-b005\n# 绘图\nhead(patient.prop)\n\np <- ggplot(patient.prop,aes(patient,Proportion,fill=ctniche)) +\n  geom_bar(stat = \"identity\",position = \"fill\") +\n  xlab(label = \"\") +  ylab(label = \"cell type proportion\") +\n  scale_fill_manual(values=cols) +\n  theme_classic() +\n  theme(\n    axis.ticks.length = unit(0.2,'cm'),\n    legend.position = \"right\",  # 设置图例位置\n    legend.direction = \"vertical\",  # 设置图例方向\n    legend.box = \"vertical\",  # 设置图例框的方向\n    legend.text = element_text( size = 12, face = \"plain\",color = \"black\"),\n    axis.line = element_line(linewidth = 1),     # 粗轴\n    axis.ticks = element_line(linewidth = 1),      # 所有刻度线\n    axis.title.y = element_text(size = 14),  # 修改x轴标题的字体大小\n    axis.text.x = element_text(size = 11,angle = 45, hjust = 1),  # 修改x轴刻度标签的字体大小\n    axis.text.y = element_text(size = 11)   # 修改y轴刻度标签的字体大小\n  ) +\n  guides(fill=guide_legend(title = NULL,ncol=1))\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.text.y", "axis.text.x", "axis.title.y", "axis.ticks", "axis.line", "legend.text", "legend.box", "legend.direction", "legend.position", "axis.ticks.length", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
