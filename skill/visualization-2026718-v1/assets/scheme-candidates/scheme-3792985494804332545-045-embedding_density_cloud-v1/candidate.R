# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-045-b005\n# 单个基因\np <- do_NebulosaPlot(sample =pbmc3k.final, features = \"CD14\",legend.position = \"right\")\np\n\n# 两个基因\np <- do_NebulosaPlot(sample =pbmc3k.final, features = c(\"CD14\",\"CD3D\"),legend.position = \"right\")\np\n\n# 两个基因共表达\np <- do_NebulosaPlot(sample =pbmc3k.final, features = c(\"CD14\",\"CD3D\"),joint = T,return_only_joint = F,plot.axes = T,\n                     legend.position = \"none\")\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.position", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
