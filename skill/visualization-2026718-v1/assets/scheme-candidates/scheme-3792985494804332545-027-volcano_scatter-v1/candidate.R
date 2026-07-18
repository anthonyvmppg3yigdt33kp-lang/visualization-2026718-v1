# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-027-b006\n## 绘图整体\n# 绘制每个Cluster 的散点火山图：\nlibrary(ggrepel)\np <- ggplot() +\n  geom_jitter(data = sce.markers, aes(x = cluster, y = avg_log2FC, color = sig),\n              size = 0.6, width =0.4) +\n  geom_jitter(data = top10, aes(x = cluster, y = avg_log2FC, color = sig),\n              size = 1, width =0.4) + ## top10的点，大小突出一下\n  scale_color_manual(name=NULL, values = c(\"#f05f63\",\"#1b1b1b\")) + ## 点的颜色调整\n  geom_text_repel(data=top10, aes(x=cluster,y=avg_log2FC,label=gene), force = 1.2,\n    arrow = arrow(length = unit(0.008, \"npc\"),type = \"open\", ends = \"last\") ) ## 添加文字标签\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("arrow", "size", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
