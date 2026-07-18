# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-072-b002\n# 假设有一个数据框，包含两组数据\ndf <- data.frame(\n  Group = c(rep(\"A\", 10), rep(\"B\", 10)),\n  Value = c(rnorm(10, mean = 50, sd = 10), rnorm(10, mean = 70, sd = 10))\n)\nboxplot(Value ~ Group, data = df, main = \"分组箱线图\", xlab = \"组别\", ylab = \"数值\")\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("Value", "Group", "df")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
