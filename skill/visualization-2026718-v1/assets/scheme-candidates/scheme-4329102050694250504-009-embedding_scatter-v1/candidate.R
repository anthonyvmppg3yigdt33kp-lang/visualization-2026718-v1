# Reference-only, source-safe candidate source fragment.
candidate_source <- function() {
  return("# source block: article-4329102050694250504-009-b001\nlibrary(Seurat)\nlibrary(patchwork)\nlibrary(dplyr)\nlibrary(ggplot2)\n\nlibrary(SeuratData) #加载seurat数据集\ngetOption('timeout')\noptions(timeout=10000)\n# InstallData(\"pbmc3k\")\ndata(\"pbmc3k\")\n\nsce <- updateObject(pbmc3k.final  )\ntable(Idents(sce))\np1 <- DimPlot(sce,label = T)\np1\n")
}
