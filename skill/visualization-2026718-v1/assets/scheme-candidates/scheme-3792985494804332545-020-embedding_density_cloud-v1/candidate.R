# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-020-b003\n# stat_density_2d：计算二维密度。\n# aes(fill = ..density..)：将密度值映射到填充颜色。\n# geom = \"raster\"：使用栅格几何对象来绘制密度图。\n# contour = F：不绘制等高线。\n\nFig2h_Umap = ggplot(data = data, aes(x = UMAP_1, y = UMAP_2)) +\n  stat_density_2d(aes(fill = ..density..), geom = \"raster\",contour = F) +\n  geom_point(color = 'white',size = .02) +\n  annotate(geom = \"text\", x = 1, y = 4, label = \"KACs\", color = \"white\",size =12) +\n  annotate(geom = \"text\", x = -2, y = 2, label = \"Other AICs\", color = \"white\",size = 12) +\n  annotate(geom = \"text\", x = 3, y = 6, label = \"LUAD\n(n=1,674)\", color = \"white\",size = 12) +\n  facet_wrap(~Field1,ncol = 1) +\n  scale_fill_viridis(option=\"magma\") +\n  galaxyTheme_black() +\n  theme_void() +\n  theme(strip.text = element_blank(),  # 去掉分面标题\n        legend.position = \"none\" )   # 去掉图例\nFig2h_Umap\n\n# source block: article-3792985494804332545-020-b004\n## 加圈\nlibrary(mascarade)\n# 制作masktable\n# smoothSigma = 0.05：控制加圈的平滑成都，值越大加的圈越平滑\n# minDensity ：控制 加圈的松紧成都，值越小，加的圈边界与umap散点距离越大越宽松\nmaskTable <- generateMask( dims=data[,2:3], cluster=data$celltype, minDensity = 15,smoothSigma = 0.1 )\nclass(maskTable)\ndim(maskTable)\nhead(maskTable)\n\nFig2h <- Fig2h_Umap +\n  geom_path(data=maskTable, aes(group=group),linewidth=0.6,linetype = 2, colour = \"white\")\nFig2h\n\n##suggest to save in a figure with large width and height, cause the cell dots plotted in a small figure affect the visualization of the actual density\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("Fig2h", "legend.position", "Fig2h_Umap")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
