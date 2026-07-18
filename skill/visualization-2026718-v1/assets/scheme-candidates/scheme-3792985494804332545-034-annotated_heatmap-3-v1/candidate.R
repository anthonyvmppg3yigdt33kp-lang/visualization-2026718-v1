# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-034-b014\n## 只显示一两个\nalign_to = split(seq_along(split), split)\nalign_to # list对象\nalign_to[c(\"a\", \"b\")]\nsentences[c(\"a\", \"b\")]\n\nHeatmap(mat, name = \"mat\", row_split = split,\n        right_annotation = rowAnnotation(\n          textbox = anno_textbox(\n            align_to[c(\"a\", \"b\")],\n            sentences[c(\"a\", \"b\")], # names should match\n            word_wrap = TRUE,\n            add_new_line = TRUE)\n        )\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("add_new_line", "word_wrap", "textbox", "right_annotation", "align_to")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
