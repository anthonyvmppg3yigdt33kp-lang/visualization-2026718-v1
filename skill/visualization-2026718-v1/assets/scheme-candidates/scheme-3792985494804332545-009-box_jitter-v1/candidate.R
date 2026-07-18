# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-009-b007\np <- ggplot(df, aes(x = RECIST.Response, y = Score, fill = RECIST.Response)) +\n  # 箱线图\n  geom_boxplot(alpha = 0.6, outlier.shape = NA, width = 0.4,lwd=1.2) +\n# 抖动散点\n  geom_jitter(aes(color = RECIST.Response),  width = 0.15, alpha = 0.8, size = 3) +\n# 手动添加短横线\n  geom_segment(aes(x = 1, xend = 2, y = y_line, yend = y_line), color = \"grey20\", linewidth = 0.8) +\n# 手动添加p值文本（斜体p）\n  annotate(\"text\", x = 1.5, y = y_text, label =  deparse(p_expression), parse = TRUE, size = 7, color = \"grey20\",fontface = \"bold\") +\n# 美化设置\n  scale_fill_manual(values = c(\"R\" = \"#fad5a0\", \"NR\" = \"#b5bcd6\")) +\n  scale_color_manual(values = c(\"R\" = \"#f4b75e\",  \"NR\" = \"#8492bb\")) +\n  scale_y_continuous(limits = c(0, NA)) +  # y轴从0开始\n  labs(title = \"HCC (GSE202069)\", x = \"\", y = \"C7-HLA−DR signature\") +\n  theme_classic() +\n  theme(\n    legend.position = \"none\",\n    # 标题灰黑色加粗加大\n    plot.title = element_text(size = 16, face = \"bold\", hjust = 0.5, color = \"grey20\"),\n    # 坐标轴标题灰黑色加粗加大\n    axis.title.x = element_text(size = 16, face = \"bold\", margin = margin(t = 10), color = \"grey20\"),\n    axis.title.y = element_text(size = 16, face = \"bold\", margin = margin(r = 10), color = \"grey20\"),\n    # 坐标轴刻度标签灰黑色加粗加大\n    axis.text.x = element_text(size = 14, face = \"bold\", color = \"grey20\"),\n    axis.text.y = element_text(size = 12, face = \"bold\", color = \"grey20\"),\n    # 坐标轴线灰黑色加粗\n    axis.line = element_line(linewidth = 1.2, color = \"grey20\"),\n    # 坐标轴刻度线灰黑色加粗\n    axis.ticks = element_line(linewidth = 1.2, color = \"grey20\"),\n    axis.ticks.length = unit(0.2, \"cm\")\n  )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("axis.ticks.length", "axis.ticks", "axis.line", "axis.text.y", "axis.text.x", "axis.title.y", "axis.title.x", "plot.title", "legend.position", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
