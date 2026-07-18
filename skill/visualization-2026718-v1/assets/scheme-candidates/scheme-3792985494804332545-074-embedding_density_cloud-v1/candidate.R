# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-074-b013\nlibrary(cetcolor)\nlibrary(Seurat)\nlibrary(ggplot2)\n\n# 设置颜色\nscale.col <- cet_pal(16, name = \"fire\")\n\n# generate UMAP plot\npl1 <- UMAPPlot(sce.all.int, combine = FALSE) # returns full ggplot object\npl1\n\n# make plot\npl1[[1]] &\n  stat_density_2d(aes_string(x = \"umap_1\", y = \"umap_2\", fill = \"after_stat(level)\"),\n                  linewidth = 0.2, geom = \"density_2d_filled\",\n                  colour = \"ivory\", alpha = 0.4, n = 150, h = c(1.2, 1.2)) &\n  scale_fill_gradientn(colours = scale.col) &\n  DarkTheme()\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("colour", "linewidth", "pl1", "scale.col")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
