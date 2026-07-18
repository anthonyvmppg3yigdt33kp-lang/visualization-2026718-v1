# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-004-b006\nupset(\n  movies,\n  genres,\n  base_annotations=list( 'Intersection size'=intersection_size( text_colors=c( on_background='brown', on_bar='yellow' ) )\n    + annotate(\n      geom='text', x=Inf, y=Inf, label=paste('Total:', nrow(movies)), vjust=1, hjust=1 ) # 右上角添加总数\n    + ylab('Intersection size') # y轴标题\n  ),\n  min_size=10,\n  width_ratio=0.1\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("width_ratio", "min_size", "geom", "base_annotations")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
