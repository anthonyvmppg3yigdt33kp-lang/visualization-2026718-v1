# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-048-b004\n# 绘制多个，加一个分面\nlibrary(reshape2)\n# id.vars：指定哪些列是标识符，不需要被转换。\n# variable.name：新列的列名，默认为“variable”。\n# value.name：新列中数值的列名，默认为“value”。\n\ndf_all <- melt(df, id.vars=\"class\", variable.name=\"markers\", value.name=\"expression\")\nhead(df_all)\n\np <- ggplot(df_all, aes(x = expression, y = class, fill = class)) +\n  geom_density_ridges(quantile_lines = TRUE, quantiles = 2) +\n  scale_fill_manual(values = colors) +\n  facet_wrap(markers~., ncol = 6,scales = \"free_x\") +\n  ylab(\"\") + xlab(\"Expression\") +\n  theme_test(base_size = 15) +\n  theme(panel.border=element_rect(linewidth = 1, color = \"black\"),\n        strip.background = element_rect(linewidth = 1, fill = \"white\"),\n        strip.text = element_text(size = 18),\n        axis.title.x = element_text(size = 16),\n        axis.text = element_text(size = 16, colour = \"black\"),\n        axis.line = element_line(size = 0.6),\n        legend.position = \"none\")\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.position", "axis.line", "axis.text", "axis.title.x", "strip.text", "strip.background", "p", "df_all")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
