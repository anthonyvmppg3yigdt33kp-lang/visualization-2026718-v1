# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-047-b002\n# 换个颜色，使用 Snipaste 从文献中获取同款颜色\ncolors <- c(\"#0069db\", \"#b80000\", \"#00a700\", \"#6858c5\",\"#6858c5\", \"#fd8c00\", \"#71c3fb\", \"#89194a\", \"#007a0d\",\"#ff7f00\", \"#235a8a\")\n\n# 对小提琴做一下排序\nsce.all.int$celltype <- factor(sce.all.int$celltype,\n                               levels = c(\"TECs\",\"LOH\",\"DT\",\"IC_PC\",\"MES\",\"ENDO\",\"T\",\"B\",\"Neutrophils\",\"NK\",\"Myeloid\"))\nIdents(sce.all.int) <- \"celltype\"\n\np1 <- VlnPlot(sce.all.int, unlist(cell_types), stack = TRUE, sort = FALSE, cols = colors) +\n  theme(legend.position = \"none\")\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p1", "levels", "colors")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
