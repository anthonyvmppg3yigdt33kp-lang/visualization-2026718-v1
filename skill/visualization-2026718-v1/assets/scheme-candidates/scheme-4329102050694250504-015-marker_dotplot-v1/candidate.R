# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-015-b004\ntable(kera_sub$newCellTypes)\nfac_levs <- c(\"Bas-I\", \"Bas-prolif\", \"Bas-mig\", \"Bas-II\",\n              \"Spi-I\", \"Spi-II\",\"Spi-mig\",\n              \"Gra-I\")\n\nkera_sub$upCellTypes <- factor(kera_sub$newCellTypes, levels = rev(fac_levs))\nplot_marker <- DotPlot(kera_sub, features = top_repre_markers,\n                       group.by = \"upCellTypes\", cols = c(\"white\", \"#cb181d\"),\n                       dot.scale = 5, col.min = 0, dot.min = 0.1) +\n  labs(x=\"\", y=\"\") +\n  theme(axis.text.x = element_text(angle = 90, hjust = 1),\n        panel.border = element_rect(colour = \"black\", fill=NA)\n        )\n\nplot_marker\n\n# source block: article-4329102050694250504-015-b007\n# plot\nobject = plot_marker\nfor (i in 1:nPoints)  {\n  object <- object +\n    ggplot2::annotation_custom(\n      grob = grid::rectGrob(\n        gp = grid::gpar(col = \"black\",fill = pCol[i],\n                        lwd = 1.3, lty = \"solid\", lineend = 'square', alpha = 1 )\n      ),\n      xmin = xmin[i],\n      xmax = xmax[i],\n      ymin = ymin,    # 需要高度\n      ymax = ymax     # 需要高度\n    ) +\n    coord_cartesian(ylim = c(1, 8), clip = \"off\")\n}\nobject +\n  theme(plot.margin = margin(t = 30, unit = \"pt\"))\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("panel.border", "dot.scale", "group.by", "plot_marker", "fac_levs")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
