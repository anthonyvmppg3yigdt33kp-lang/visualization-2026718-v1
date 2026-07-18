# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-043-b012\nlibrary(tidyverse)\nhead(gene_expression)\n\np <- gene_expression |>\n  filter(external_gene_name %in% c(\"Apol6\", \"Col5a3\", \"Bsn\", \"Fam96b\", \"Mrps14\", \"Tma7\")) |>\n  tidyplot(x = sample_type, y = expression, color = condition) |>\n  add_violin() |>\n  add_data_points_beeswarm(white_border = TRUE) |>\n  adjust_x_axis_title(\"\") |>\n  remove_legend() |>\n  add_test_asterisks(hide_info = TRUE, bracket.nudge.y = 0.3) |>\n  adjust_colors(colors_discrete_ibm) |>\n  adjust_y_axis_title(\"Gene expression\") |>\n  split_plot(by = external_gene_name, ncol = 2)\np\n"

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
