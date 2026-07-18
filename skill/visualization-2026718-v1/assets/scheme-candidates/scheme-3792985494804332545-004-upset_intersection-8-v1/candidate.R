# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-004-b010\nupset(\n  movies, genres,\n  min_size=10,\n  width_ratio=0.3,\n  encode_sets=FALSE,  # for annotate() to select the set by name disable encoding\n  set_sizes=(\n    upset_set_size()\n    + geom_text(aes(label=..count..), hjust=1.1, stat='count')\n    # you can also add annotations on top of bars:\n    + annotate(geom='text', label='@', x='Drama', y=850, color='white', size=3)\n    + expand_limits(y=1100)\n    + theme(axis.text.x=element_text(angle=90))\n  )\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("set_sizes", "encode_sets", "width_ratio", "min_size")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
