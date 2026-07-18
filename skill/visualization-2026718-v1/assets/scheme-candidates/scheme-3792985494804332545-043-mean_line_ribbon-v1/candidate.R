# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-043-b010\nstr(time_course)\n# spc_tbl_ [1,710 × 4] (S3: spec_tbl_df/tbl_df/tbl/data.frame)\n# $ day      : num [1:1710] 0 0 0 0 0 0 0 0 0 0 ...\n# $ subject  : chr [1:1710] \"id1\" \"id2\" \"id3\" \"id4\" ...\n# $ score    : num [1:1710] 0 0 0 0 0 0 0 0 0 0 ...\n# $ treatment: chr [1:1710] \"untreated\" \"untreated\" \"untreated\" \"untreated\" ...\n\np <- time_course |>\n  tidyplot(x = day, y = score, color = treatment, dodge_width = 0, width = 90,height = 80) |>\n  add_mean_line() |>\n  add_sem_ribbon()\np\n"

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
