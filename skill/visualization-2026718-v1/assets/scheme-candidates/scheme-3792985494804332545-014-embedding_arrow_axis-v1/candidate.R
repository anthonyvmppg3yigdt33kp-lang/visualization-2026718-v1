# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-014-b002\n# 设置颜色\n### Figure 2a ###\n### UMAP for cell states ###\ncolor <- c(\"#96F148\",\"#ff7f00\",\"#e5f5f9\",\"#bebada\",\"#df65b0\",\"#D10000\",\"#0000FF\",\"#fff7fb\",\"#fccde5\",\n           \"#bc80bd\",\"#d9d9d9\",\"#ffed6f\",\"#d6604d\",\"#02818a\",\"#ccecb5\",\"#80b1d3\",\"#fb9a99\",\"#006837\",\n           \"#6a3d9a\")\n\np <- ggplot(Lymphoma_data@meta.data, aes(x=UMAP1, y=UMAP2, color=cell_state)) +\n  geom_point(size=0.1, alpha=0.3,shape = 21, stroke = 0.9) +\n  scale_color_manual(values=color)\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p", "color")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
