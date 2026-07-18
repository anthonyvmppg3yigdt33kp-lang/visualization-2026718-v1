# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-008-b003\np <- upset(df, nsets =4, sets =c(\"CTRL\",\"PA\",\"OA\",\"TGFB1\"),\n           keep.order =T, number.angles =0,\n           line.size =1.5, mb.ratio =c(0.6,0.4),  # 主条形图和矩阵图的比例\n           order.by =c(\"degree\"),\n           decreasing = F,\n\n           main.bar.color = c(\"#d56763\",\"#fcd2a1\",\"#477b80\",\"#808080\",rep(\"#000000\",11) ) , #上方y轴柱状图颜色\n           matrix.color = \"#000000\",             # 矩阵点颜色\n           sets.bar.color = \"#000000\",           # 集合柱状图颜色\n\n           point.size = 5, #矩阵中交点大小\n\n           # 只显示包含某一组的交集\n           queries = list(\n             list(query = intersects, params = list(\"CTRL\"),  color = \"#808080\", active = TRUE),\n             list(query = intersects, params = list(\"PA\"),  color = \"#ff7f0e\",  active = TRUE),\n             list(query = intersects, params = list(\"OA\"),  color = \"#fcd2a1\",  active = TRUE),\n             list(query = intersects, params = list(\"TGFB1\"),  color = \"#477b80\",  active = TRUE)\n             ),\n\n           # text.scale参数说明：\n           # • 第1个值：Y轴标题\n           # • 第2个值：Y轴刻度标签\n           # • 第3个值：X轴标题\n           # • 第4个值：X轴刻度标签\n           # • 第5个值：集合名字大小\n           # • 第6个值：柱体s上的数字\n           text.scale =c( 2, 2,1.8, 2,2,2.5),\n           # 标签\n           sets.x.label =\"\",\n           mainbar.y.label =\"n= 1,427 significant cell-specific\nreceptor-ligand interactions (p < 0.05)\",\n\n           # 边距\n           set.metadata =NULL\n           )\nlibrary(ggplotify)\nprint(p)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("set.metadata", "mainbar.y.label", "sets.x.label", "text.scale", "queries", "point.size", "sets.bar.color", "matrix.color", "main.bar.color", "decreasing", "order.by", "line.size", "keep.order", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
