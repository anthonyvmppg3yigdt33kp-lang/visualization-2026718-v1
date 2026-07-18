# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-011-b003\np <- ggplot(pcaScores, aes(x = PC1, y = PC2, colour = Grade)) +\n  geom_point(size = 3) +\n  scale_colour_manual(name='', values = color1)  +\n  xlab(label = paste0(\"PC1 (\", round(eigenvalues[1,2],2),\"%)\") ) +\n  ylab(label = paste0(\"PC2 (\", round(eigenvalues[2,2],2),\"%)\") ) +\n  theme_bw(base_size = 15) +\n  guides(color=guide_legend(nrow = 4,override.aes = list(size=4))) +\n  theme(axis.text = element_text(colour = 'black'),\n        axis.ticks = element_line(colour = 'black'),\n        plot.title = element_text(hjust = 0.5),\n        panel.grid = element_blank(),\n        legend.position = \"bottom\"\n        )\np\n\n# source block: article-3792985494804332545-011-b005\n# 设置放大区域；\n# Names xmin, xmax, ymin, ymax are optional:\nfrom <- c(xmin = -18, xmax = 20.5, ymin = -10, ymax = 20)\nto <- c(-100, -40, -21, 33)\n\n# t (top): 上边距 = 10\n# r (right): 右边距 = 60\n# b (bottom): 下边距 = 10\n# l (left): 左边距 = 10\n\np1 <- p +\n# xlim(-20, 50)  + # 从2到8\n  coord_cartesian(clip = \"off\") +\n  theme(plot.margin = ggplot2::margin(t = 1, r = 3, b = 1, l = 15,unit = \"cm\")) +\n  geom_magnify(from = from, to = to,\n               target.linetype = 2,\n               proj.linetype = 2, linewidth = 0.6)\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p1", "legend.position", "panel.grid", "plot.title", "axis.ticks", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
