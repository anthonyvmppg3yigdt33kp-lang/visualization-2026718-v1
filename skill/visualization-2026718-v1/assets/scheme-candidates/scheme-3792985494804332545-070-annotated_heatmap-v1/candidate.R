# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-070-b005\np <- Heatmap(exp_scale, # 表达矩阵\n             col = colorRampPalette(c(\"#524b9a\",\"white\",\"#e63118\"))(100),#颜色定义\n             name = \"Gene Expression\\n(Z-score)\", # 设置表达矩阵的图例标题\n             heatmap_legend_param = list(direction = \"horizontal\",nrow = 1),\n             show_row_names = T,     # 展示行名\n             show_column_names = F,  # 不显示列名\n             show_row_dend = F,\n             show_column_dend = F,\n             top_annotation = ha,       # 顶部分组信息\n             column_title_side = c(\"top\"),\n             column_split = annotation_col$KRAS_status, # 用group 信息将热图分开，以 group 聚类\n             row_split = annotation_row$gene_class,\n             column_title = T\n             )\np\n\n# 保存\ndraw(p, heatmap_legend_side = \"bottom\", annotation_legend_side = \"bottom\",merge_legend = TRUE)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("column_title", "row_split", "column_split", "column_title_side", "top_annotation", "show_column_dend", "show_row_dend", "show_column_names", "show_row_names", "heatmap_legend_param", "name", "col", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
