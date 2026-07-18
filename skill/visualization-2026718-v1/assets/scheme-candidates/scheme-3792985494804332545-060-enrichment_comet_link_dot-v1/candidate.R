# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-060-b004\n## 绘图\nlibrary(ggforce)\nhead(dt)\ntable(dt$Cluster)\n\ncolors <- c(\n  \"Macrophages\" = \"#B0C4DE\",\n  \"Mast cells\" = \"#FF69B4\",\n  \"Endothelial cells\" = \"#FFB6C1\",\n  \"ILC1/NK cells\" = \"#FFFFE0\",\n  \"B cells\" = \"#ADD8E6\",\n  \"T cells\" = \"#90EE90\",\n  \"Fibroblasts\" = \"#FFA07A\",\n  \"Smooth muscle cells\" = \"#D3D3D3\",\n  \"Epithelial cells\" = \"#D8BFD8\",\n  \"Cycling macrophages\" = \"#E6E6FA\",\n  \"Lymphatic endothelial cells\" = \"#FFD700\"\n)\n\np <- ggplot(dt) +\n  geom_link(aes(x = 0, y = Description,\n               xend = -log10(pvalue), yend = Description,\n               alpha = after_stat(index),\n               color = Cluster,\n               size = after_stat(index)),\n            n = 500, show.legend = T)\np\n\np1 <- p +\n  geom_point(aes(x = -log10(pvalue),y = Description), color = \"black\", fill = \"white\",size = 6,shape = 21) +\n  geom_text(aes(x = -log10(pvalue), y = Description), label=dt$Count, size=3, nudge_x=0.05) +\n  theme_classic() +\n  theme(panel.grid = element_blank(),\n        strip.text = element_text(face = \"bold.italic\"),\n        #axis.text = element_text(color = \"black\"),\n        axis.line = element_line(color = \"black\", size = 0.6), # 加粗x轴和y轴的线条\n        axis.text = element_text(face = \"bold\"), # 加粗x轴和y轴的标签\n        axis.title = element_text( size = 13)    # 加粗x轴和y轴的标题\n        ) +\n  xlab(\"-Log10 Pvalue\") + ylab(\"\") +\n  scale_color_manual(values = colors)\np1\n\n# source block: article-3792985494804332545-060-b005\n# 加分面\np2 <- p1 +\n  facet_wrap(~Cluster,scales = \"free\",ncol = 2)\np2\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p2", "p1", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
