# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-050-b004\n# 文献中的基因\ngenes <- c(\"S100A8\", \"S100A9\", \"S100A12\", \"VCAN\", \"FCN1\", \"FCER1A\", \"CD1C\", \"CLEC10A\",\n           \"CD1E\", \"AREG\", \"APOE\", \"APOC1\", \"C1QA\", \"C1QB\", \"C1QC\", \"LST1\", \"LINC01272\", \"FCGR3A\", \"IFITM2\")\n\nDotPlot(sce.all.int, features = genes,cols = \"RdBu\",col.min = 0, col.max = 1,cluster.idents = T,scale = T) +\n  RotatedAxis()  # 旋转坐标轴\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("genes")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
