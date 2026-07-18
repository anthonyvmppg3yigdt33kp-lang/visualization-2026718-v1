# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-064-b002\n## 绘图\n# 绘制边框\ngp <- ggplot() +\n  geom_rect(data = subset(domain.df, Type == \"str\"),\n            mapping = aes(xmin = min(Start), xmax = max(End), ymin = 0.3, ymax = 0.7),\n            fill = str.fill,\n            colour = str.col)\ngp\n\n# source block: article-3792985494804332545-064-b004\n# 添加棒棒图\ngp <- gp + geom_segment(data = mut.df,\n                        mapping = aes(x = AA, xend = AA, y = 0.7, yend = Freq)) +\n  geom_point(data = mut.df,\n             mapping = aes(x = AA, y = Freq, fill = Type),\n             shape = 21,\n             size = 2) +\n  geom_text_repel(data = mut.df,\n                  mapping = aes(x = AA, y = Freq, label = Mut),\n                  bg.colour = \"white\",\n                  seed = 12345,\n                  nudge_y = 0.25)\n\ngp\n\n# source block: article-3792985494804332545-064-b005\n# 添加结构区域\ngp <- gp + geom_rect(data = subset(domain.df, Type == \"dom\"),\n                     mapping = aes(xmin = Start, xmax = End, ymin = 0.2, ymax = 0.8, fill = Feature, group = Feature),\n                     fill = dom.fill[subset(domain.df, Type == \"dom\")$Feature],\n                     colour = dom.col)\ngp\n\n# source block: article-3792985494804332545-064-b006\n# 修改主题\ngp <- gp +\n  theme_bw() +\n  theme(panel.grid.minor = element_blank(),\n        panel.grid.major.x = element_blank(),\n        panel.grid.major.y = element_line(linetype = \"dotted\")) +\n  labs(x = \"AA\", y = \"Freq\", fill = \"Mutation\")\n\ngp\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("gp")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
