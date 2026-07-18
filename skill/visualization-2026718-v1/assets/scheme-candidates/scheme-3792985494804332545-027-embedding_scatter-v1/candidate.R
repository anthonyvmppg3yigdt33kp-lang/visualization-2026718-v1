# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-027-b004\n################# 降为聚类分群\n# 标准化降维聚类\nobject <- sce.all\nobject <- SCTransform(object, assay = \"Spatial\")\nobject <- RunPCA(object, assay = \"SCT\") %>%\n  FindNeighbors(., reduction = \"pca\", dims = 1:30) %>%\n  FindClusters(resolution = 0.5) %>%\n  RunUMAP(., reduction = \"pca\", dims = 1:30)\n\nhead(object@meta.data)\nDimPlot(object, reduction = \"umap\", label = TRUE,label.size = 5)\nDimPlot(object, reduction = \"umap\", label = TRUE,label.size = 5,group.by = \"res.0.8\")\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("object")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
