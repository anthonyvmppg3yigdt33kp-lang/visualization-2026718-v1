# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-030-b005\nnetVisual_bubble(cellchat,remove.isolate = F)\n\n# source block: article-3792985494804332545-030-b006\n# 这里的数字为注释水平的顺序，从1开始，比如 5表示 \"CD8 T\"\nlevels(cellchat@idents) # show factor levels of the cell labels\n# [1] \"Naive CD4 T\"  \"Memory CD4 T\" \"CD14+ Mono\"   \"B\"            \"CD8 T\"        \"FCGR3A+ Mono\" \"NK\"           \"DC\"           \"Platelet\"\n\nnetVisual_bubble(cellchat, sources.use = 5, targets.use = c(1,2,3,4,6,7,8), remove.isolate = FALSE)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c()
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
