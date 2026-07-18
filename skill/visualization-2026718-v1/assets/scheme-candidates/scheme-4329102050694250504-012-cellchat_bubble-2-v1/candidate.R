# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-012-b007\np1 <- ggplot(data = grid_points, aes(x = x, y = y)) +\n  # 添加网格线\n  geom_hline(yintercept = y_positions, color = \"gray90\", linewidth = 0.2) +\n  geom_vline(xintercept = x_positions, color = \"gray90\", linewidth = 0.2) +\n# # 网格交点上的小点\n  geom_point(size = 1, color = \"gray20\",shape = 21,stroke = 0.5) +\n  geom_point(data = dt, aes(x = source.target, y = interaction_name_2,fill = prob, size = pval), color = 'black', shape = 21,stroke = 0.5) + # 带边的气泡图\n  scale_fill_gradientn(values = seq(-0.5,1,0.1),colours = c(\"#4575b4\",\"#abd9e9\",\"#ffffbf\",\"#fdae61\",\"#d73027\",\"#d62b23\")) +\n  scale_x_discrete() +\n  scale_y_discrete() +\n  xlab(\"\") + ylab(\"\") +\n  theme_bw() +\n  theme(\n    panel.grid.major = element_line(color = \"gray80\",linewidth = 0.2,linetype = \"solid\" ),     # 颜色\n    panel.grid.minor = element_line( color = \"gray90\", linewidth = 0.2,linetype = \"solid\"),\n    panel.border = element_rect(color = \"black\", fill = NA, linewidth = 0.5),\n    axis.line = element_blank(),\n    axis.text.x = element_text(angle = 40, hjust = 1,colour = \"black\",size = 7),  # 旋转45度，右对齐\n    axis.text.y = element_text(hjust = 1,size = 7,color = rep(c(\"#d10a18\",\"black\"),times=c(8,15))),  # 旋转45度，右对齐\n  )\np1\n\n\n# 保存\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.text.y", "axis.text.x", "axis.line", "panel.border", "panel.grid.minor", "panel.grid.major", "p1")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
