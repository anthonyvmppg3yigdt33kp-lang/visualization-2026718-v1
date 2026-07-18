# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-014-b004\n# 左下小箭头\np <- ggplot(Lymphoma_data@meta.data, aes(x=UMAP1, y=UMAP2, color=cell_state)) +\n  geom_point(size=0.1, alpha=0.3,shape = 21, stroke = 0.9) +\n  scale_color_manual(values=color) +\n  guides( color = guide_legend( title = \"\", override.aes = list( fill=color,color = \"black\",stroke = 0.3, size = 4, alpha = 1), ncol = 2 )) +  # 图例中点的大小\n  theme_dr() +   # 应用带小箭头的坐标轴主题（来自tidydr包）\n  theme( panel.grid = element_blank(),\n         legend.text = element_text( size = 12, face = \"plain\",color = \"black\")\n         )    # 去除所有网格线\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.text", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
