# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-072-b009\n# 载入ggplot2包\nlibrary(ggplot2)\ndf <- data.frame(group=gp,expression=v)\nhead(df)\n# group expression\n# 1 Normal   8.311357\n# 2 Normal   8.965637\n# 3 Normal   8.856947\n# 4 Normal   8.534809\n# 5 Normal   8.830902\n# 6 Normal   8.346746\n\np <- ggplot(data = df, aes(x = group, y = expression, fill = group)) +\n  geom_boxplot(width = 0.7) +\n  geom_jitter(width = 0.2, color = \"black\", alpha = 0.5) +\n  labs(title = \"Expression Level by Group\", x = \"Group\", y = \"Expression Level\") +\n  theme_minimal()\n\n# 添加显著性检验\nmax_pos <- max(df$expression)\np1 <- p +\n  geom_signif(mapping=aes(x=group,y=expression), #不同组别的显著性\n              comparisons = list(c(\"Normal\", \"Tumor\")),\n              map_signif_level=T, # T显示显著性，F显示p value\n              tip_length=c(0,0,0,0,0,0,0,0,0,0,0,0), # 修改显著性线两端的长短\n              y_position = c(max_pos, max_pos*1.02), # 设置显著性线的位置高度\n              size=0.8, # 修改线的粗细\n              textsize = 4, # 修改显著性标记的大小\n              test = \"t.test\")  # 检验的类型,可以更改\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("test", "textsize", "size", "y_position", "tip_length", "map_signif_level", "comparisons", "p1", "max_pos", "p", "df")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
