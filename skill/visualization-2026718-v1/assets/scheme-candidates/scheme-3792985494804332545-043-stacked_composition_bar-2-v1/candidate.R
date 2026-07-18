# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-043-b003\n# 百分比\np <- df |>\n  tidyplot(x = reads, y = sample, color = category) |>\n  add_barstack_relative(reverse = TRUE) |>\n  theme_minimal_x() |>\n  adjust_size(70, 50) |>\n  adjust_colors(my_colors) |>\n  adjust_x_axis(title = \"Percentage of reads\", labels = scales::percent) |>\n  reorder_color_labels(names(my_colors)) |>\n  remove_legend_title() |>\n  remove_y_axis_title()\np\n"

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
