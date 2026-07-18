# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-055-b003\n# 确定特征基因\nselected_genes <- list(\"macrophages\"=\"AIF1\",\n                       \"keratinocytes\"=\"KRT1\",\n                       \"T lymphocytes\"=\"CD3D\",\n                       \"fibroblasts\"=\"COL1A1\",\n                       \"endothelial cells\"=\"VWF\",\n                       \"mast cells\"=\"TPSAB1\",\n                       \"secretory (glandular) cells\"=\"SCGB1B2P\",\n                       \"pericytes\"=\"RGS5\",\n                       \"melanocytes\"=\"PMEL\",\n                       \"B cells\"=\"MS4A1\",\n                       \"smooth muscle cells\"=\"DES\",\n                       \"dendritic cells\"=\"CD1C\")\ng <- unlist(selected_genes)\ng\n\n# 生成一个存储多个ggplot对象的list\np_merge <- list()\n\nfor(i in 1:length(g)) {\n# 打印动态\nprint(g[i])\n# 绘图\n  p_merge[[i]] <- FeaturePlot_scCustom(seurat_object = sce.all.int, features = g[i], order = T,pt.size = 0.6) +\n    scale_color_gradient(low = \"grey\", high = \"#f32a1f\")  + # 更改填充颜色\n    theme_void() +  # 使用空白主题\n    theme( plot.title = element_text(hjust = 0.5, size = 16, face = \"bold\"), # 标题居中\n      legend.position = \"none\", # 去除图例\n      panel.border = element_blank(),\n      panel.grid.major = element_blank(),\n      panel.grid.minor = element_blank(),\n      panel.background = element_blank(),\n      plot.background = element_blank())\n}\n\n# 拼图\nlibrary(patchwork)\n# 有多少个基因，3行4咧\nlength(g)\n# 使用 patchwork 的 wrap_plots() 函数组合图表\ncombined_plot <- wrap_plots(p_merge, ncol = 4)\ncombined_plot\n\n# 保存\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("combined_plot", "plot.background", "panel.background", "panel.grid.minor", "panel.grid.major", "panel.border", "legend.position", "p_merge", "g", "selected_genes")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
