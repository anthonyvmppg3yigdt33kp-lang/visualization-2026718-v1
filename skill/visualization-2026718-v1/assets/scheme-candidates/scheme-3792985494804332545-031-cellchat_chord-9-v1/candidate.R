# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-031-b018\nlty_df = data.frame(c(\"S1\", \"S2\", \"S3\"), c(\"E5\", \"E6\", \"E4\"), c(1, 2, 3))\nlwd_df = data.frame(c(\"S1\", \"S2\", \"S3\"), c(\"E5\", \"E6\", \"E4\"), c(2, 2, 2))\nborder_df = data.frame(c(\"S1\", \"S2\", \"S3\"), c(\"E5\", \"E6\", \"E4\"), c(1, 1, 1))\nlty_df\nlwd_df\nborder_df\n\nchordDiagram(mat, grid.col = grid.col, link.lty = lty_df, link.lwd = lwd_df,\n             link.border = border_df)\ncircos.clear()\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("link.border", "border_df", "lwd_df", "lty_df")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
