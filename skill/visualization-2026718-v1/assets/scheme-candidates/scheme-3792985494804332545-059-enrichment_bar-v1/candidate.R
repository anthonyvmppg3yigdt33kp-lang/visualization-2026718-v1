# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-059-b005\n## 绘图\ncolor <- c(up=\"#e15759\", down=\"#586ea6\")\ncolor\n\np <- ggplot(dt, aes(x = pvalue_loc, y = Description, fill = Cluster)) +\n  geom_bar(stat = \"identity\",color=\"black\", width = 0.6) + # 绘制条形图，边框为黑色\n  scale_fill_manual(values = color) +\n  scale_x_continuous(limits = c(-34,34)) +\n  geom_text(data = dt, aes(x=lable_xloc, y = Description, label = Description, hjust = lable_hjust),\n            color=dt$label_color, size = 4.5) +  # 添加通路名称\n  labs(x=\"Log10(pvalue)\", y=NULL, title=\"\") +\n  annotate(\"text\", x = 25,  y = 15, label = \"Up\", size=6, fontface = \"bold\", color=\"black\") +\n  annotate(\"text\", x = -25, y =5, label = \"Down\", size=6, fontface = \"bold\", color=\"black\") +\n  theme_classic() +\n  theme( axis.text.x = element_text(size = 15),\n    axis.title.x = element_text(size = 15),\n    axis.text.y = element_blank(), # 不显示Y轴标签\n    axis.line.y = element_blank(),\n    axis.ticks.y = element_blank(),\n    legend.position = 'none' )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.position", "axis.ticks.y", "axis.line.y", "axis.text.y", "axis.title.x", "p", "color")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
