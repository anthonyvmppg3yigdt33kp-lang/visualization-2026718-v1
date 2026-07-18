# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-004-b014\nupset(\n  movies, c(\"Action\", \"Comedy\", \"Drama\"),\n  width_ratio=0.2,\n  group_by='sets',\n  queries=list(\n    # 1. 高亮 \"Drama + Comedy\" 组合（红色）\n    upset_query(\n      intersect=c('Drama', 'Comedy'),\n      color='red',\n      fill='red',\n      only_components=c('intersections_matrix', 'Intersection size')\n    ),\n    # 2-4. 按组着色（在交集矩阵中）\n    upset_query(group='Drama', color='blue'),\n    upset_query(group='Comedy', color='orange'),\n    upset_query(group='Action', color='purple'),\n    # 5-7. 集合大小面板着色\n    upset_query(set='Drama', fill='blue'),\n    upset_query(set='Comedy', fill='orange'),\n    upset_query(set='Action', fill='purple')\n  )\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("only_components", "fill", "color", "intersect", "queries", "group_by", "width_ratio")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
