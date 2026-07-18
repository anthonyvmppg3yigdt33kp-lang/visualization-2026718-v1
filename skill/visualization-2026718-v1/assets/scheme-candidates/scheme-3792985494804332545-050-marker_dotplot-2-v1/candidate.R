# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-050-b005\nsce.sub <- subset(sce.all.int, idents = c(1,2,4,6) )\n# 简单注释一下\nlevels(sce.sub)\n\nnew.cluster.ids <- c(\"c1: Macrophages\", \"c2: CD1c+ DCs\", \"c4: CD14+ Mono\", \"c6: CD16+ Mono\")\nnames(new.cluster.ids) <- levels(sce.sub)\nsce.sub <- RenameIdents(sce.sub, new.cluster.ids)\nlevels(sce.sub) <- c(\"c4: CD14+ Mono\", \"c2: CD1c+ DCs\", \"c1: Macrophages\", \"c6: CD16+ Mono\")\n\np <- DotPlot(sce.sub, features = genes,cols = c(\"lightblue\",\"#e71d27\"), col.min = 0,col.max = 1,cluster.idents = F,scale = T) +\n  scale_color_gradientn(colors = c(\"lightblue\",\"#e71d27\"), values = scales::rescale(c(0, 1)),\n                        breaks = c(0,  1), labels = c(0, 1))  +\n  xlab(label = \"\") +\n  ylab(label = \"\") +\n  theme(axis.text.x = element_text(angle = 90, hjust = 1),  # 旋转x轴标签90度\n        axis.text.y = element_text(size = 16),\n        legend.position = \"top\",\n        legend.text.position = \"top\",\n        legend.title.position = \"bottom\")\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.title.position", "legend.text.position", "legend.position", "axis.text.y", "breaks", "p", "new.cluster.ids", "sce.sub")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
