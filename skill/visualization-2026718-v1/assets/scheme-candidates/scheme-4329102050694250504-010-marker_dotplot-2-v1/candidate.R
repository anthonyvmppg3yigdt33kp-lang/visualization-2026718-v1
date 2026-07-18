# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-010-b004\np <- ggplot(dt, aes(x = id, y = features.plot)) +\n  geom_point( aes(fill = avg.exp.scaled, size = pct.exp), color = 'black', shape = 21,stroke = 0.5) + # 带边的气泡图\n  xlab(\"\") + ylab(\"\") +\n  scale_fill_gradientn( colours = c(\"#01009c\",\"#0000de\",\"#9559c8\",\"#faea4d\",\"#f09b37\",\"#ca2b1c\",\"#8b1a10\") ) +\n  scale_size( range = c(0, 7),limits = c(0, 100),breaks = c(0,20,40,60,80,100) )\np\n\n# source block: article-4329102050694250504-010-b005\np1 <- p +\n  labs( fill = \"Average expression\",  size = \"Percent expressed\"  ) +  # 修改图例标题\n  theme(\n    panel.grid.major = element_blank(),\n    panel.grid.minor = element_blank(),\n    panel.background = element_blank(),\n    axis.line = element_line(colour = \"black\"),\n    axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1,size = 14,color = \"black\"), # x轴文本靠右对齐\n    axis.text.y = element_text(angle = 0, vjust = 0.5, hjust = 1,size = 14, face = \"italic\",color = \"black\"), # y轴文本靠右对齐\n    legend.position = \"right\", # 将图例放在右侧\n    legend.title = element_text(size = 13)\n  ) +\n  guides(\n    size = guide_legend( title.position = \"top\", title.hjust = 0.5, ncol = 1, byrow = TRUE, override.aes = list(stroke = 0.4) ),\n    fill = guide_colourbar( title.position = \"top\", title.hjust = 0.5 )\n    )\np1\n\n# source block: article-4329102050694250504-010-b006\n# 添加方框\np2 <- p1 +\n  scale_x_discrete(expand = expansion(mult = c(0.08, 0.08))) + # 增加x轴与y轴的距离（在左侧和右侧添加更多空间）\n  geom_rect(aes(xmin=0.5,xmax=2.5, ymin=0.5, ymax=5.5),fill=NA,linetype = 1,linewidth = 0.3,color=\"black\")\np2\n\n# source block: article-4329102050694250504-010-b007\n# 添加方框\np3 <- p2 +\n  geom_rect(aes(xmin=7.5,xmax=11.5, ymin=5.5, ymax=15.5),fill=NA,linetype = 1,linewidth = 0.3,color=\"black\") +\n  geom_rect(aes(xmin=1.5,xmax=6.5, ymin=15.5, ymax=20.5),fill=NA,linetype = 1,linewidth = 0.3,color=\"black\")\np3\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p3", "p2", "p1", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
