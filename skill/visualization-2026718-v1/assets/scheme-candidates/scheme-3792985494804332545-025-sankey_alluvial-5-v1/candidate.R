# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-025-b005\n#########################\ndata <- as.data.frame(UCBAdmissions)\nhead(data)\n\nlibrary(ggalluvial)\ngg <- ggplot(data, aes(y = Freq, axis1 = Gender, axis2 = Dept, axis3 = Admit)) +\n  geom_alluvium(color=\"red\", aes(fill=Dept),width=1/12) +\n  geom_stratum(color=\"blue\", aes(fill=Dept),width=1/12) +\n  geom_text(stat = \"stratum\", aes(label = paste(after_stat(stratum)))) +\n  ggtitle(\"UC Berkeley admissions and rejections\") +\n  coord_flip()\ngg\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("gg", "data")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
