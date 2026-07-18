# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-035-b004\nlibrary(ggplot2)\np1 <- FeaturePlot(sce,features = \"Naive1\",order = T) +\n  ggtitle(\"Naive\") +\n  scale_color_gradientn(colors = c(\"#4f5da7\", \"white\", \"#ea3433\"))\np1\n\np2 <- FeaturePlot(sce,features = \"Activation_Effector_function2\",order = T) +\n  ggtitle(\"Activation/Effector_function\") +\n  scale_color_gradientn(colors = c(\"#4f5da7\", \"white\", \"#ea3433\"))\np2\n\np3 <- FeaturePlot(sce,features = \"Cytotoxicity3\",order = T) +\n  ggtitle(\"Cytotoxicity\") +\n  scale_color_gradientn(colors = c(\"#4f5da7\", \"white\", \"#ea3433\"))\np3\n\np4 <- FeaturePlot(sce,features = \"Exhaustion4\",order = T) +\n  ggtitle(\"Exhaustion\") +\n  scale_color_gradientn(colors = c(\"#4f5da7\", \"white\", \"#ea3433\"))\np4\n\nlibrary(patchwork)\np <- patchwork::wrap_plots(list(p1,p2,p3,p4), nrow = 1)\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p", "p4", "p3", "p2", "p1")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
