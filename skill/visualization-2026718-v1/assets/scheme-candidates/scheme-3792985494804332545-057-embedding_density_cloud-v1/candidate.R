# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-057-b002\nlibrary(ggpointdensity)\n# 提取数据\n# dat <- Embeddings(sce.all.int, reduction = \"umap\")\n# head(dat)\n\ndat <- FetchData(object=sce.all.int, vars=c(\"umap_1\",\"umap_2\",\"celltype\"))\nhead(dat)\n\np <- ggplot(data = dat, mapping = aes(x = umap_1, y = umap_2)) +\n  geom_pointdensity() +\n  scale_color_viridis_c(option=\"inferno\", alpha = 0.4) +\n  theme_classic(base_size = 15)\np\n\n# source block: article-3792985494804332545-057-b003\np1 <- p +\n  labs(color='Density') +  # 设置图例标题\n  theme(\n    panel.background = element_rect(fill = \"black\", color = \"black\"),  # 设置坐标轴内区域背景颜色为黑色\n    plot.background = element_rect(fill = \"white\", color = \"white\"),  # 设置整个图形背景颜色为白色\n    panel.grid.major = element_blank(),  # 去掉主要的网格线\n    panel.grid.minor = element_blank(),  # 去掉次要的网格线\n    axis.line = element_line(color = \"white\"),  # 设置坐标轴线颜色为白色\n    axis.text = element_text(color = \"white\"),  # 设置坐标轴文本颜色为白色\n    axis.ticks = element_line(color = \"white\"),  # 设置坐标轴刻度颜色为白色\n    axis.title = element_text(color = \"white\"),  # 设置坐标轴标题文本颜色为白色\n    legend.background = element_blank(),  # 设置图例背景为透明\n    legend.key = element_blank(),  # 设置图例键为透明\n    legend.text = element_text(color = \"white\"),  # 设置图例文本颜色为白色\n    legend.title = element_text(color = \"black\"))  # 设置图例标题文本颜色为白色\n\np1\n\n# source block: article-3792985494804332545-057-b004\n# 加圈\nlibrary(mascarade)\n\n# 制作masktable\n# smoothSigma = 0.05：控制加圈的平滑成都，值越大加的圈越平滑\n# minDensity ：控制 加圈的松紧成都，值越小，加的圈边界与umap散点距离越大越宽松\nmaskTable <- generateMask( dims=dat[,1:2], cluster=dat$celltype, minDensity = 15,smoothSigma = 0.1 )\nclass(maskTable)\ndim(maskTable)\nhead(maskTable)\n\np2 <- p1 +\n  geom_path(data=maskTable, aes(group=group),linewidth=0.6,linetype = 2, colour = \"white\")\np2\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p2", "p1", "p", "dat")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
