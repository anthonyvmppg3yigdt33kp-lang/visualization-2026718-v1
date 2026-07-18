# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-073-b002\n# 选取每个 category 类别中的top5通路进行绘图\nlibrary(dplyr)\ndat_top5 <- dat %>%\n  group_by(category) %>%\n  slice_head(n = 5) %>%\n  ungroup()\ncolnames(dat_top5)\n\n\ng_kegg <- ggplot(dat_top5, aes(y=Description, x=Count, fill=category)) +\n  geom_bar(stat=\"identity\",width = 0.6) +\n  scale_x_continuous(name =\"Relative abundance(%)\") +\n  scale_y_discrete(name =\"KEGG Pathway\") +\n  ggtitle(\"KEGG Enrichment\") +\n  theme(panel.background = element_rect(fill = \"white\",colour='black'),\n        panel.grid.major = element_line(color = \"grey\",linetype = \"dotted\",size = 0.3),\n        panel.grid.minor = element_line(color = \"grey\",linetype = \"dotted\",size = 0.3),\n        title = element_text(colour='black', size=20,face = \"bold\"),\n        axis.ticks.length = unit(0.4,\"lines\"),\n        axis.ticks = element_line(color='black'),\n        axis.line = element_line(colour = \"black\"),\n        axis.title.x=element_text(colour='black', size=20,face = \"bold\"),\n        axis.title.y=element_text(colour='black', size=20),\n        axis.text.x=element_text(colour='black',size=20),\n        axis.text.y = element_text(color = \"black\",size = 16),\n        legend.position = \"none\",\n        strip.text.y = element_text(angle = 0,size = 12,face = \"bold\")) +\n  facet_grid(category~.,space = \"free_y\",scales = \"free_y\")\ng_kegg\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("strip.text.y", "legend.position", "axis.text.y", "axis.text.x", "axis.title.y", "axis.title.x", "axis.line", "axis.ticks", "axis.ticks.length", "title", "panel.grid.minor", "panel.grid.major", "g_kegg", "dat_top5")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
