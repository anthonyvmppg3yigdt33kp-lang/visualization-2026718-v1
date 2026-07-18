# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-031-b010\n## 修改颜色\ngrid.col = c(S1 = \"red\", S2 = \"green\", S3 = \"blue\",\n             E1 = \"grey\", E2 = \"grey\", E3 = \"grey\", E4 = \"grey\", E5 = \"grey\", E6 = \"grey\")\nchordDiagram(mat, grid.col = grid.col)\nchordDiagram(t(mat), grid.col = grid.col)\ncircos.clear()\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("E1", "grid.col")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
