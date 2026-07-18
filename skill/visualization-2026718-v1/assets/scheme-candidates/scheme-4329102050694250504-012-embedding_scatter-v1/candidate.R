# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-012-b001\ngetOption('timeout')\noptions(timeout=10000)\nlibrary(SeuratData) #加载seurat数据集\nlibrary(Seurat)\nlibrary(tidyverse)\nlibrary(CellChat)\nlibrary(patchwork)\npackageVersion(\"CellChat\")\n\n# InstallData(\"pbmc3k\")\ndata(\"pbmc3k\")\nsce <- UpdateSeuratObject(pbmc3k)\ntable(sce$seurat_annotations)\ncolnames(sce@meta.data)\ndim(sce)\n# 去掉没有注释信息的细胞\nsce <- sce[ , which(!is.na(sce@meta.data$seurat_annotations))]\nsce <- sce %>%\n  NormalizeData %>%\n  FindVariableFeatures %>%\n  ScaleData %>%\n  RunPCA() %>%\n  FindNeighbors(dims = 1:10, verbose = FALSE) %>%\n  FindClusters(resolution = 0.5, verbose = FALSE) %>%\n  RunUMAP(dims = 1:10)\n\nsce\ntable(Idents(sce))\nIdents(sce) <- \"seurat_annotations\"\nDimPlot(sce,label = T)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("sce")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
