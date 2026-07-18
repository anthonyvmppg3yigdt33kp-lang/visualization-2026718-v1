# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-007-b001\n## 加载R包\nlibrary(Seurat)\nlibrary(ggplot2)\nlibrary(tidyverse)\nlibrary(SeuratData)\n# InstallData(\"pbmc3k\")   #  (89.4 MB)\ndata(\"pbmc3k\")\nsce <-  UpdateSeuratObject(pbmc3k.final)\nsce$anno <- sce$seurat_annotations\nsce$anno <- gsub(\"Naive CD4 T\",\"CD4 T\",sce$anno)\nsce$anno <- gsub(\"Memory CD4 T\",\"CD4 T\",sce$anno)\n# sce$anno <- gsub(\"CD8 T\",\"T\",sce$anno)\nhead(sce@meta.data)\ncols = c(\"#c84825\",\"#E3B05C\",\"#BAAEAE\",\"#8C99B1\",\"#147097\",\"#35402D\",\"#4D86AA\",\"#E1DDC8\")\nDimPlot(sce,reduction = 'umap',label = T,repel = T,group.by = \"anno\",cols = cols)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("cols", "sce")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
