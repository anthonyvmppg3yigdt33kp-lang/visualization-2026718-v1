# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-058-b005\n# 提取目标基因的表达矩阵\ngroup_list\ndt <- data.frame(exp=dat[\"CD40LG\", ],group=group_list)\nhead(dt)\nmax_pos <- max(dt$exp)\nmax_pos\n\ncolor <- c(\"Healthy\"=\"#db000e\", \"OA\"=\"#367bb7\", \"Arthralgia\"=\"#4ea732\", \"UA\"=\"#9f4495\",\n           \"Early RA\"=\"#ed7800\",  \"Est RA\"=\"#aa5118\")\ncolor\n\n# 组件比较\ncompara <- list(c(\"OA\", \"Healthy\"),\n                c(\"Arthralgia\", \"Healthy\"),\n                c(\"UA\", \"Healthy\"),\n                c(\"Early RA\", \"Healthy\"),\n                c(\"Est RA\", \"Healthy\"))\n\n# 绘制箱线\np <- ggplot(data=dt,aes(x=group,y=exp,colour = group)) +\n  geom_boxplot(mapping=aes(x=group,y=exp,colour=group), size=0.6, width = 0.8) + # 箱线图，要宽一点\n  geom_jitter(mapping=aes(x=group,y=exp,colour = group),size=1.5,width = 0.2) +  # 抖动散点，要窄一点\n  scale_color_manual(values =color ) + # 颜色，使用人工智能kimi提取 非常方便\n  geom_signif(mapping=aes(x=group,y=exp), # 不同组别的显著性\n              comparisons =compara ,\n              hjust = -1,\n              map_signif_level=T, # T显示显著性，F显示p value\n              tip_length=0, # 修改显著性线两端竖着的长短\n              size=0, # 修改线的粗细\n              textsize = 4, # 修改显著性标记的大小，变成0之前可以看一眼都要哪些显著，用于下面p1的修改\n              test = \"t.test\")  # 检验的类型,可以更改\n\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("test", "textsize", "size", "tip_length", "map_signif_level", "hjust", "comparisons", "p", "compara", "color", "max_pos", "dt")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
