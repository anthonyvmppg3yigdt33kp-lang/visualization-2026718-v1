# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-004-b013\nupset(\n  movies, genres, name='genre', width_ratio=0.1, min_size=10,\n  annotations = list(\n    'Length'=list(\n      aes=aes(x=intersection, y=length),\n      geom=geom_boxplot(na.rm=TRUE)\n    )\n  ),\n  queries=list(\n    upset_query(\n      intersect=c('Drama', 'Comedy'),\n      color='red',\n      fill='red',\n      only_components=c('intersections_matrix', 'Intersection size')\n    ),\n    upset_query(\n      set='Drama',\n      fill='blue'\n    ),\n    upset_query(\n      intersect=c('Romance', 'Comedy'),\n      fill='yellow',\n      only_components=c('Length')\n    )\n  )\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("set", "only_components", "fill", "color", "intersect", "queries", "geom", "aes", "annotations")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
