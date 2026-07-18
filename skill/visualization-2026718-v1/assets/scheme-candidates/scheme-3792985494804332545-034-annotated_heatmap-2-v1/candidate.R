# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-034-b013\nsplit = sample(letters[1:5], 100, replace = TRUE)\nsentences = lapply(unique(split), function(x) {\n  random_text(3, 8)\n})\nnames(sentences) = unique(split)\n\n## 控制每一个文本框里面单词的宽度和每个单词为一行\nHeatmap(mat, name = \"mat\", row_split = split,\n        right_annotation = rowAnnotation(\n          textbox = anno_textbox(\n            split, sentences,\n            word_wrap = TRUE, # 控制单词换行和新行：\n            add_new_line = TRUE)\n        )\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("add_new_line", "word_wrap", "textbox", "right_annotation", "sentences", "split")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
