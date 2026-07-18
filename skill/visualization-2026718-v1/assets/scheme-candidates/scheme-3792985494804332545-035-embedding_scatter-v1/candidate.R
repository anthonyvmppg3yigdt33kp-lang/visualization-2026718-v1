# Reference-only, source-safe candidate source fragment.
candidate_source <- function() {
  return("# source block: article-3792985494804332545-035-b001\nlibrary(Seurat)\nlibrary(SeuratData) #加载seurat数据集\ngetOption('timeout')\noptions(timeout=10000)\n\n## 加载数据\n# InstallData(\"pbmc3k\")\ndata(\"pbmc3k\")\nsce <- pbmc3k.final\nsce <- UpdateSeuratObject(sce)\ntable(Idents(sce))\nDimPlot(sce,label = T)\n")
}
