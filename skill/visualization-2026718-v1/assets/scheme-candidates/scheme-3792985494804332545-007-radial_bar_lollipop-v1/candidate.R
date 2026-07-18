# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-007-b005\n### 绘图\nplt <- ggplot(plot_df) +\n# Make custom panel grid\n  geom_hline(aes(yintercept = y), data.frame(y = c(0:3) * 1000),color = \"lightgrey\" ) +\n# Add bars to represent the cumulative track lengths\n# str_wrap(region, 5) 每行最多5个字符\n  geom_col( aes( x = reorder(str_wrap(region, 5), sum_length), y = sum_length, fill = n),\n    position = \"dodge2\", show.legend = TRUE, alpha = .9 ) +\n# Add dots to represent the mean gain\n  geom_point( aes( x = reorder(str_wrap(region, 5),sum_length), y = mean_gain), size = 3, color = \"gray12\" ) +\n  geom_segment(aes(x = reorder(str_wrap(region, 5), sum_length), y = 0,\n                   xend = reorder(str_wrap(region, 5), sum_length), yend = 3000), linetype = \"dashed\", color = \"gray12\" )\nplt\n\n# source block: article-3792985494804332545-007-b006\n# 掰弯极坐标\np1 <- plt +\n  coord_polar()\np1\n\n# source block: article-3792985494804332545-007-b007\n## 优化\np2 <- p1 +\n# 为柱形和棒棒糖图添加标注\n  annotate(x = 11, y = 1300,label = \"Mean Elevation Gain\n[FASL]\", geom = \"text\",angle = -67.5,color = \"gray12\",size = 2.5,family = \"Bell MT\" ) +\n  annotate(x = 11, y = 3150,label = \"Cummulative Length [FT]\",geom = \"text\",angle = 23, color = \"gray12\",size = 2.5,family = \"Bell MT\") +\n# 在图表内部添加自定义比例尺标注\n  annotate(x = 11.7, y = 1100, label = \"1000\", geom = \"text\", color = \"gray12\", family = \"Bell MT\" ) +\n  annotate(x = 11.7, y = 2100, label = \"2000\", geom = \"text\", color = \"gray12\", family = \"Bell MT\") +\n  annotate(x = 11.7, y =3100, label = \"3000\",  geom = \"text\", color = \"gray12\", family = \"Bell MT\") +\n# 调整Y轴尺度，避免柱形从中心点开始\n  scale_y_continuous( limits = c(-1500, 3500),expand = c(0, 0), breaks = c(0, 1000, 2000, 3000) ) +\n# 为各地区路线数量设置新的填充色和图例标题\n  scale_fill_gradientn( colours = c( \"#6C5B7B\",\"#C06C84\",\"#F67280\",\"#F8B195\")) + # \"Amount of Tracks\"\n# 将填充色的图例设置为离散型\n  guides( fill = guide_colorsteps(\n      barwidth = 15, barheight = .5, title.position = \"top\", title.hjust = .5 )\n      ) +\n  theme(\n    axis.title = element_blank(),\n    axis.ticks = element_blank(),\n    axis.text.y = element_blank(),\n    axis.text.x = element_text(color = \"gray12\", size = 12),\n    legend.position = \"bottom\",\n  )\np2\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p2", "p1", "plt")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
