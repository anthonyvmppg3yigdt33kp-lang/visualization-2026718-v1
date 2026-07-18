# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-043-b008\nhead(study)\nstr(study)\n# tibble [20 × 7] (S3: tbl_df/tbl/data.frame)\n# $ treatment  : chr [1:20] \"A\" \"A\" \"A\" \"A\" ...\n# $ group      : chr [1:20] \"placebo\" \"placebo\" \"placebo\" \"placebo\" ...\n# $ dose       : chr [1:20] \"high\" \"high\" \"high\" \"high\" ...\n# $ participant: chr [1:20] \"p01\" \"p02\" \"p03\" \"p04\" ...\n# $ age        : num [1:20] 23 45 32 37 24 23 45 32 37 24 ...\n# $ sex        : chr [1:20] \"female\" \"male\" \"female\" \"male\" ...\n# $ score      : num [1:20] 2 4 5 4 6 9 8 12 15 16 ...\n\np <- study |>\n  tidyplot(x = treatment, y = score, color = treatment, width = 90,height = 80) |>\n  add_boxplot() |>\n  add_data_points_beeswarm()\np\n"

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
