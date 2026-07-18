# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-022-b004\nlibrary(pheatmap)\npheatmap(data,scale = \"none\",treeheight_row = 0,treeheight_col = 0,show_colnames = F,\n         annotation_col = anno[,1,drop=F],annotation_names_col=F,\n         cluster_cols = F,cluster_rows = F,  annotation_colors = ann_colors,\n         col = colorRampPalette(c(\"#ceb0ff\",\"white\",\"#ff4628\"))(100),\n         fontsize_row=8\n         )\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("fontsize_row", "col", "cluster_cols", "annotation_col")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
