# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-026-b006\n#自定义配色：\nlibrary(cols4all)\nc4a_gui()\nmycol <- c4a('rainbow_wh_rd',length(unique(df_plot$node)))\nmycol\n\n#绘图：\np2 <- ggplot(df_plot, aes(x = x, next_x = next_x, node = node, next_node = next_node, fill = node, label = node)) +\n  geom_sankey(flow.alpha = 0.5,\n              flow.fill = 'grey',\n              flow.color = 'grey80', #条带描边色\n              node.fill = mycol, #节点填充色\n              smooth = 8,\n              width = 0.16) +\n  geom_sankey_text(size = 3.2, color = \"black\")+\n  theme_void() +\n  theme(legend.position = 'none',\n        text = element_text(family = \"Arial\", size = 12, color = \"black\"),  # 设置全局字体样式\n        plot.margin = unit(c(0,5,0,0),units=\"cm\")\n        )\np2\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("plot.margin", "text", "width", "smooth", "node.fill", "flow.color", "flow.fill", "p2", "mycol")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
