# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-066-b006\nmyHierarchy <- data.table(\"mutation\"=c(\"nonsense\", \"frame_shift_del\", \"frame_shift_ins\", \"in_frame_del\", \"splice_site_del\", \"splice_site\", \"missense\",\"splice_region\", \"rna\"),\ncolor=c(\"#FF0000\", \"#00A08A\", \"#F2AD00\", \"#F98400\", \"#5BBCD6\", \"#046C9A\", \"#D69C4E\", \"#000000\", \"#446455\"))\n\n# 绘图\nplotData <- Waterfall(myVars, mutationHierarchy = myHierarchy)\n\n# 保存\ndrawPlot(plotData)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("plotData", "color", "myHierarchy")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
