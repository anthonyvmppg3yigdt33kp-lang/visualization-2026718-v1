# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-077-b009\n##########################################################################\ngenes2 <- c(\"IL10\", \"CLEC12A\", \"AURKA\", \"MMP13\",\"CLEC2B\", \"CD58\")\n\nfig2d <- list()\nfor(i in 1:length(genes2)) {\n  #i <- 4\n  box_dat <- data.frame(exp=dat[genes2[i],], group=group_list)\n  head(box_dat)\n  max_pos <- max(box_dat$exp)\n\n  # 绘制小提琴图和显著性标记\n  B <- ggplot(data=box_dat,aes(x=group,y=exp,colour = group)) +\n    geom_boxplot(mapping=aes(x=group,y=exp,colour=group), size=0.6, width = 0.5) + # 箱线图\n    geom_jitter(mapping=aes(x=group,y=exp,colour = group),size=1.5) +  # 散点\n    scale_color_manual(limits=c(\"normal\",\"RApre\",\"RApost\"), values =c( \"#ed1a22\",\"#00a651\",\"#652b90\") ) + # 颜色\n    geom_signif(mapping=aes(x=group,y=exp), # 不同组别的显著性\n                comparisons = list(c(\"RApre\", \"normal\"), c(\"RApost\", \"normal\")),\n                map_signif_level=T, # T显示显著性，F显示p value\n                tip_length=c(0,0,0,0,0,0,0,0,0,0,0,0), # 修改显著性线两端的长短\n                y_position = c(max_pos*1.04,max_pos), # 设置显著性线的位置高度\n                size=0.8, # 修改线的粗细\n                textsize = 4, # 修改显著性标记的大小\n                test = \"t.test\") + # 检验的类型,可以更改\n    ylim(c(0,max_pos*1.12)) +\n    theme_classic() + #设置白色背景\n    labs(x=\"\",y=\"\")  + # 添加标题，x轴，y轴标签\n    ggtitle(label = genes2[i]) +\n    theme(plot.title = element_text(hjust = 0.5),\n          axis.line=element_line(linetype=1,color=\"black\",size=0.9))\n\n  B\n\n  fig2d[[i]] <- B\n\n}\n\np_d <- wrap_plots(fig2d,guides=\"collect\"，ncol=3)\np_d\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p_d", "axis.line", "test", "textsize", "size", "y_position", "tip_length", "map_signif_level", "comparisons", "B", "max_pos", "box_dat", "fig2d", "genes2")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
