# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-010-b003\nsce.all.filt <- sce\nsce.all.filt\nhead(sce.all.filt@meta.data)\n\ngenes <- c(\"Itgax\", \"Flt3\", \"Xcr1\", \"Irf8\", \"Cd36\", \"Cd207\", \"Nr4a1\",\n           \"Ly6D\", \"Sirpa\", \"Irf4\", \"Tcf4\", \"Cd209a\", \"Mgl2\", \"Ccr2\",\n           \"Epcam\", \"Ccl17\", \"Cd14\", \"Cx3cr1\", \"Ccr7\", \"Cd63\", \"Il12b\",\n           \"Fabp5\", \"Ccl22\")\n\np <- DotPlot(sce.all.filt, features = rev(genes), group.by = \"RNA_snn_res.0.5\") +\n  coord_flip()\np\n\n# 取出来绘图数据\ndt <- p@data\nhead(dt)\nrange(dt$avg.exp.scaled)\nrange(dt$pct.exp)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("dt", "p", "genes", "sce.all.filt")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
