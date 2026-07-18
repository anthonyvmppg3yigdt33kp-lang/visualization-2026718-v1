# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-017-b008\n# plot\ncolor.bin <- c(\"#00599F\",\"#D01910\")\n\np <- ggscatter(plot.data,\n               x = \"LogFDR\",\n               y = \"Fold.Enrichment\",\n               color = \"Type\",\n               main = \"\",\n               size = \"Ratio\",\n               shape = 16,\n               label = plot.data$Term,\n               palette = color.bin,\n               repel =T\n               )\np\n\np <- p +\n  scale_size(range = c(4,20)) +\n  scale_x_continuous(limit = c(-15, 40), breaks = seq(-10,40,by=10)) +\n  xlab(label = expression(-log[10](adjusted~p~value))) +\n# with_inner_glow(\n#   geom_circle(aes(x0 = offset/6+6, y0 = y, r = r/2, fill = col, group = city), df_circle, colour = NA),\n#   colour = \"grey20\", expand = 2, sigma = 5) + # 添加带内部发光的圆形\n  geom_vline(xintercept = 0, linetype = \"solid\", color = \"black\", size =0.6) +\n  annotate(\"text\", x = -1.2, y = c(0,3,6,9,12), label = c(0,3,6,9,12), color = \"black\", size = 5) +\n  geom_segment(aes(x = -0.5, xend = 0, y = 0, yend = 0),  linetype = \"solid\", size = 0.4) +\n  geom_segment(aes(x = -0.5, xend = 0, y = 3, yend = 3),  linetype = \"solid\", size = 0.4) +\n  geom_segment(aes(x = -0.5, xend = 0, y = 6, yend = 6),  linetype = \"solid\", size = 0.4) +\n  geom_segment(aes(x = -0.5, xend = 0, y = 9, yend = 9),  linetype = \"solid\", size = 0.4) +\n  geom_segment(aes(x = -0.5, xend = 0, y = 12, yend = 12),  linetype = \"solid\", size = 0.4) +\n# theme_bw() +\n  theme(\n    plot.title = element_text(hjust = 0.5),\n    panel.grid.major = element_blank(),  # 去掉主要格子线\n    panel.grid.minor = element_blank(),  # 去掉次要格子线\n    plot.background = element_blank(),\n    axis.line.y = element_blank(),  # 去掉y轴的轴线\n    axis.text.y = element_blank(),  # 去掉y轴的刻度标签\n    axis.ticks.y = element_blank(),  # 去掉y轴的刻度线\n    axis.title.y = element_blank(),\n    legend.position = \"right\"\n  )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.position", "axis.title.y", "axis.ticks.y", "axis.text.y", "axis.line.y", "plot.background", "panel.grid.minor", "panel.grid.major", "plot.title", "repel", "palette", "label", "shape", "size", "main", "color", "y", "x", "p", "color.bin")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
