# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-004-b007\n# 默认配色\nupset(\n  movies,\n  genres,\n  base_annotations=list('Intersection size'=intersection_size( counts=FALSE, mapping=aes(fill=mpaa)) ), # 按照mpaa填充\n  width_ratio=0.1\n)\n# 修改配色\nupset(\n  movies,\n  genres,\n  base_annotations=list(\n    'Intersection size'=intersection_size( counts=FALSE, mapping=aes(fill=mpaa)) +  # 按照mpaa填充\n     scale_fill_manual(values=c('R'='#E41A1C', 'PG'='#377EB8','PG-13'='#4DAF4A', 'NC-17'='#FF7F00'))\n  ),\n  width_ratio=0.1\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("width_ratio", "base_annotations")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
