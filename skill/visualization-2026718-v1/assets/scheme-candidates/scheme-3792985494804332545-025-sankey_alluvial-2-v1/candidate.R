# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-025-b002\ndata(majors)\nmajors$curriculum <- as.factor(majors$curriculum)\nhead(majors)\ntable(majors$semester)\ntable(majors$curriculum)\ntable(majors$student)\n\n# lode.guidance 参数控制流动路径的绘制方式。在这里，\"frontback\" 表示流动路径会从前面（front）到后面（back）绘制\ngg <- ggplot(majors,aes(x = semester, stratum = curriculum, alluvium = student,fill = curriculum, label = curriculum)) +\n  geom_flow(stat = \"alluvium\", lode.guidance = \"frontback\",color = \"darkgray\") +\n  geom_stratum() +\n  ggtitle(\"student curricula across several semesters\")\ngg\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("gg")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
