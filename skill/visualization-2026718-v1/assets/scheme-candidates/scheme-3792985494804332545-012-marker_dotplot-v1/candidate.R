# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-012-b005\np <- DotPlot(Lymphoma_data,features = CN_marker, scale.by = \"size\", group.by = \"CN_cluster\", scale.max = 50, scale = 10, col.max=1.5)+\n    RotatedAxis()+\n    scale_color_gradientn(values = seq(0,1,0.1),colours = c(\"#4575b4\",\"#abd9e9\",\"#e0f3f8\",\"#ffffbf\",\"#fdae61\",\"#d73027\",\"#800026\"))\n\np\n\n# source block: article-3792985494804332545-012-b006\np1 <- p +  scale_y_discrete(name = \"\", labels = rev(c(\"CN1_T\", \"CN2_PC\", \"CN3_Myeloid\",\"CN4_Stromal\",\"CN5_Tumor-B\",\n                                                \"CN6_Diffuse\",\"CN7_Mixe\"))) +\n  xlab(label = NULL)\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p1", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
