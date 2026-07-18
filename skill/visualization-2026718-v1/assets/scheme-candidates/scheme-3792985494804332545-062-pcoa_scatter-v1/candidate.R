# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-062-b004\n# 设置颜色\ncol <- c(\"#1F78B4\",\"#A6CEE3\",\"#B2DF8A\",\"#33A02C\",\"#FB9A99\",\"#FDBF6F\",\"#E31A1C\")\n\n# 绘制 PCoA 分析结果点图\np <- ggplot(points, aes(x=x, y=y,color=Compartments,shape=Treatment)) +\n  geom_point(size=3) +\n  labs(x=paste(\"PCoA 1 (\", format(100 * eig[1] / sum(eig), digits=4), \"%)\", sep=\"\"),\n       y=paste(\"PCoA 2 (\", format(100 * eig[2] / sum(eig), digits=4), \"%)\",sep=\"\")) +\n  scale_colour_manual(values = col) +\n  theme_classic() +\n  theme(axis.text.x = element_text(size = 8),\n        axis.text.y = element_text(size = 8),\n        axis.title.y= element_text(size=12),\n        axis.title.x = element_text(size = 12),\n        legend.title=element_text(size=5),legend.text=element_text(size=5)\n        )\n\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.title", "axis.title.x", "axis.title.y", "axis.text.y", "y", "p", "col")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
