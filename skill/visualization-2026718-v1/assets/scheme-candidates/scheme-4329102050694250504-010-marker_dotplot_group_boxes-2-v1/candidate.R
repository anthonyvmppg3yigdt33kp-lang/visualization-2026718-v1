# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-010-b004\np <- ggplot(dt, aes(x = id, y = features.plot)) +\n  geom_point( aes(fill = avg.exp.scaled, size = pct.exp), color = 'black', shape = 21,stroke = 0.5) + # 带边的气泡图\n  xlab(\"\") + ylab(\"\") +\n  scale_fill_gradientn( colours = c(\"#01009c\",\"#0000de\",\"#9559c8\",\"#faea4d\",\"#f09b37\",\"#ca2b1c\",\"#8b1a10\") ) +\n  scale_size( range = c(0, 7),limits = c(0, 100),breaks = c(0,20,40,60,80,100) )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
