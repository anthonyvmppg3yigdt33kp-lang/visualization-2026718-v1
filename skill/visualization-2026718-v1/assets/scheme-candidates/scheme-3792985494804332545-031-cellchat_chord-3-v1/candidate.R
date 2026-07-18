# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-031-b007\n## 指定名字对应的gap\ncircos.par(gap.after = c(\"S1\" = 5, \"S2\" = 5, \"S3\" = 15, \"E1\" = 5, \"E2\" = 5,\n                         \"E3\" = 5, \"E4\" = 5, \"E5\" = 5, \"E6\" = 15))\nchordDiagram(mat)\ncircos.clear()\n\n# source block: article-3792985494804332545-031-b009\n## small.gap参数\npar(mfrow = c(1, 2))\ncircos.par(start.degree = 85, clock.wise = FALSE)\nchordDiagram(mat)\ncircos.clear()\n\ncircos.par(start.degree = 85)\nchordDiagram(mat, order = c(rev(colnames(mat)), rev(rownames(mat)))) # 设置所有扇区的逆序\ncircos.clear()\n"

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
