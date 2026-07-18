# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-017-b003\n# 绘图\np <- ggplot(pca_df, aes(x = PC1, y = PC2, color = group)) +\n  geom_point(size = 3, alpha = 0.8) +\n  geom_text_repel(aes(label = sample), size = 3) +  # 使用 ggrepel 避免重叠\n  stat_ellipse(aes(fill = group), alpha = 0.2, geom = \"polygon\") +\n  labs(x = paste0(\"PC1 (\", round(var_explained[1]*100, 2), \"%)\"),\n       y = paste0(\"PC2 (\", round(var_explained[2]*100, 2), \"%)\")) +\n  theme_bw() +\n  theme()\np\n\n# source block: article-4329102050694250504-017-b004\n#  #个性化散点属性\np1 <- p +\n  geom_point(data = pca$x, aes(x = PC1,y = PC2), shape = 21, size = 3,\n             stroke = 0.5, alpha = 0.8, color = \"black\" )\np1\n\n# source block: article-4329102050694250504-017-b005\nmycol <- c(healthy=\"#8ce5bb\",NAFLD=\"#7a7a7a\",NASH=\"#f6c6f4\",obese=\"#dcf7ea\")\n\np2 <- p1 +\n  scale_fill_manual(values = mycol) + #填充颜色自定义\n  scale_color_manual(values = mycol) #描边颜色自定义\np2\n\n# source block: article-4329102050694250504-017-b006\nc4a_gui() #查看色板\nmycol <- c4a('accent',4) #配色挑选\nmycol <- c4a('dark2', 4)\nmycol <- c4a('paired', 4)\nmycol <- c4a('pastel1', 4)\nmycol <- c4a('area7', 4)\n\np2 <- p1 +\n  scale_fill_manual(values = mycol) + #填充颜色自定义\n  scale_color_manual(values = mycol) #描边颜色自定义\np2\n\n# source block: article-4329102050694250504-017-b007\np3 <- p2 +\n  theme(panel.background = element_rect(fill = 'white', colour = 'black'),  # 设置背景为白色，边框为黑色\n        axis.title = element_text(colour = \"black\", size = 12, margin = margin(t = 12)),\n        axis.text = element_text(color = \"black\"),  # 设置轴刻度文字颜色\n        plot.title = element_blank(),  # 不显示标题\n        legend.title = element_blank(),  # 不显示图例标题\n        legend.key = element_blank(),  # 使图例背景透明\n        legend.text = element_text(color = \"black\", size = 9),  # 设置图例文本颜色和大小\n        legend.spacing.x = unit(0.06, 'cm'),  # 设置图例文本之间的水平间距\n        legend.key.width = unit(0.01, 'cm'),  # 设置图例的水平大小\n        legend.key.height = unit(0.01, 'cm'),  # 设置图例的垂直大小\n        legend.background = element_blank(),  # 使图例背景透明\n        legend.position = c(0.2, 0.8) # 图例位置\n        )\np3\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p3", "p2", "p1", "y", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
