# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-025-b001\ndata <- as.data.frame(UCBAdmissions)\nhead(data)\n#\n# Admit Gender Dept Freq\n# 1 Admitted   Male    A  512\n# 2 Rejected   Male    A  313\n# 3 Admitted Female    A   89\n# 4 Rejected Female    A   19\n# 5 Admitted   Male    B  353\n# 6 Rejected   Male    B  207\n\nlibrary(ggalluvial)\ngg <- ggplot(data, aes(y = Freq, axis1 = Gender, axis2 = Dept, axis3 = Admit)) +\n  geom_alluvium() +\n  geom_stratum() +\n  geom_text(stat = \"stratum\", aes(label = paste(after_stat(stratum)))) +\n  ggtitle(\"UC Berkeley admissions and rejections\")\ngg\n"

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
