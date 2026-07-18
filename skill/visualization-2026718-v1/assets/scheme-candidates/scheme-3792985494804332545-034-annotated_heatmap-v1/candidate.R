# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-034-b012\n## 热图与文本框链接\nmat = matrix(rnorm(100*10), nrow = 100)\nmat\ndim(mat)\n\nsplit = sample(letters[1:10], 100, replace = TRUE)\nsplit\nlength(split)\n\ntext = lapply(unique(split), function(x) {\n  random_text(10)\n})\nnames(text) = unique(split)\ntext\nstr(text)\n\n# 文本框注释条在右边\nHeatmap(mat, name = \"mat\", cluster_rows = FALSE, row_split = split,\n        right_annotation = rowAnnotation(textbox = anno_textbox(split, text)) # split 与 text的名字对应\n)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("right_annotation", "text", "split", "mat")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
