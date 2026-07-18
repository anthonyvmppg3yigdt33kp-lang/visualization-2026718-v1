# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-007-b004\ncols <- c(\"#ac9a4f\", \"#da871e\", \"#f07277\", \"#a35305\", \"#77a7d8\", \"#6e696f\", \"#fac956\",\"#796652\")\nDimPlot(sce,reduction = 'umap',label = T,repel = T,group.by = \"anno\",cols = cols)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("cols")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
