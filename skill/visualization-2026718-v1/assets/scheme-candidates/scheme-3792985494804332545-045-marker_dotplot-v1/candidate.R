# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-045-b008\ngenes <- list(\"Naive CD4+ T\" = c(\"IL7R\", \"CCR7\"),\n              \"CD14+ Mono\" = c(\"CD14\", \"LYZ\"),\n              \"Memory CD4+\" = c(\"S100A4\"),\n              \"B\" = c(\"MS4A1\"),\n              \"CD8+ T\" = c(\"CD8A\"),\n              \"FCGR3A+ Mono\" = c(\"FCGR3A\", \"MS4A7\"),\n              \"NK\" = c(\"GNLY\", \"NKG7\"),\n              \"DC\" = c(\"FCER1A\", \"CST3\"),\n              \"Platelet\" = c(\"PPBP\"))\n\np <- do_DotPlot(sample =pbmc3k.final, features = genes,dot_border = F)\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p", "genes")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
