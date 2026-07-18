# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-055-b002\n################## umap4：scCustomize\nlibrary(viridis)\nlibrary(Seurat)\nlibrary(scCustomize)\n\n# 绘图\np <- FeaturePlot_scCustom(seurat_object = sce.all.int, features = \"CD3E\", order = T,pt.size = 0.4) +\n  scale_color_gradient(low = \"grey\", high = \"#f32a1f\")  + # 更改填充颜色\n  theme_void() +  # 使用空白主题\n  theme( plot.title = element_text(hjust = 0.5, size = 16, face = \"italic\"), # 标题居中\n         legend.position = \"none\", # 去除图例\n         panel.border = element_blank(),\n         panel.grid.major = element_blank(),\n         panel.grid.minor = element_blank(),\n         panel.background = element_blank(),\n         plot.background = element_blank())\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("plot.background", "panel.background", "panel.grid.minor", "panel.grid.major", "panel.border", "legend.position", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
