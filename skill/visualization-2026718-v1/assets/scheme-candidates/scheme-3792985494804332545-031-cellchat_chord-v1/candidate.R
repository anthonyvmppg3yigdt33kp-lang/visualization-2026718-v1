# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-031-b004\n# 绘图\nchordDiagram(mat)\ncircos.clear()\n\n# source block: article-3792985494804332545-031-b005\n## 修改顺序\npar(mfrow = c(1, 2))\nmat\nchordDiagram(mat, order = c(\"S2\", \"S1\", \"S3\", \"E4\", \"E1\", \"E5\", \"E2\", \"E6\", \"E3\"))\ncircos.clear()\n\nchordDiagram(mat, order = c(\"S2\", \"S1\", \"E4\", \"E1\", \"S3\", \"E5\", \"E2\", \"E6\", \"E3\"))\ncircos.clear()\n\n# source block: article-3792985494804332545-031-b008\n## big.gap参数\nchordDiagram(mat, big.gap = 30)\ncircos.clear()\n\n# source block: article-3792985494804332545-031-b011\n## 设置连接线的颜色\ngrid.col\nchordDiagram(mat, grid.col = grid.col, transparency = 0)\ncircos.clear()\n\n# source block: article-3792985494804332545-031-b014\nchordDiagram(mat, grid.col = grid.col, row.col = 1:3)\nchordDiagram(mat, grid.col = grid.col, column.col = 1:6)\ncircos.clear()\n\n# source block: article-3792985494804332545-031-b015\nchordDiagram(mat, grid.col = grid.col, link.lwd = 2, link.lty = 2, link.border = \"red\")\ncircos.clear()\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c()
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
