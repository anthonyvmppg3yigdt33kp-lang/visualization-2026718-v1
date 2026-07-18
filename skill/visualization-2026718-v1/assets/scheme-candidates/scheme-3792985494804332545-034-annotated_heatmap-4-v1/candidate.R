# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-034-b015\n## anno_block\nsplit = rep(letters[1:10], 10)\nsplit\ntext = lapply(unique(split), function(x) {\n  random_text(10)\n})\nnames(text) = unique(split)\nstr(text)\n\nHeatmap(mat, name = \"mat\", row_split = split,\n        right_annotation = rowAnnotation(\n          textbox = anno_textbox(split, text, by = \"anno_block\")\n        )\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("textbox", "right_annotation", "text", "split")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
