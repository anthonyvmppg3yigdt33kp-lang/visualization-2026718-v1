# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-031-b016\nlwd_mat = matrix(1, nrow = nrow(mat), ncol = ncol(mat))\nlwd_mat[mat > 12] = 2\nborder_mat = matrix(NA, nrow = nrow(mat), ncol = ncol(mat))\nborder_mat[mat > 12] = \"red\"\nchordDiagram(mat, grid.col = grid.col, link.lwd = lwd_mat, link.border = border_mat)\ncircos.clear()\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("border_mat", "lwd_mat")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
