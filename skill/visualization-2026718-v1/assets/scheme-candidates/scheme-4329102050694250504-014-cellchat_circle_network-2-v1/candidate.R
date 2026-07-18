# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-014-b005\nnetVisual_circle(mat2,\n                 vertex.weight = groupSize,\n                 weight.scale = T,\n                 label.edge = T, # 边上显示pro值\n                 alpha.edge = 0.5, # 修改边的透明度\n                 edge.width.max = 20, # 修改边的粗细\n                 edge.weight.max = max(mat),\n                 title.name = rownames(mat))\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("title.name", "edge.weight.max", "edge.width.max", "alpha.edge", "label.edge", "weight.scale", "vertex.weight")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
