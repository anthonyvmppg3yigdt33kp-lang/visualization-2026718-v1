# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-066-b010\n# Create data\nchromosome <- \"chr14\"\ncoordinate <- sort(sample(0:106455000, size = 2000, replace = FALSE))\ncn <- c(rnorm(300, mean = 3, sd = 0.2), rnorm(700, mean = 2, sd = 0.2), rnorm(1000,\n                                                                              mean = 3, sd = 0.2))\ndata <- as.data.frame(cbind(chromosome, coordinate, cn))\ndata\nhead(data)\n\n# Call cnView with basic input\ncnView(data, chr = \"chr14\", genome = \"hg19\", ideogram_txtSize = 4)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("data", "mean", "cn", "coordinate", "chromosome")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
