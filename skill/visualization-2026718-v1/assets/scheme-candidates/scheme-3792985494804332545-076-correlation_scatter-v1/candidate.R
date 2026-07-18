# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-076-b005\n# 画布基本设置\npar(bty=\"o\", mgp = c(2,0.5,0), mar = c(4.1,4.1,2.1,4.1), tcl=-.25, font.main=3)\n# 先绘制一个空的画布，仅有边框和坐标名\nplot(NULL, NULL, ylim = ylim, xlim = xlim, xlab = \"Chronological age \", ylab = \"DNA methylation age\",col=\"white\",main = \"\")\n# rect基础函数 给画布设置背景色，掩盖边框\nrect(par(\"usr\")[1], par(\"usr\")[3], par(\"usr\")[2], par(\"usr\")[4], col = \"#EAE9E9\",border = F)\n# grid函数添加网格\ngrid(col = \"white\", lty = 1, lwd = 1.5)\n\n# source block: article-3792985494804332545-076-b006\n# 在画布中添加肿瘤组的散点\npoints(data_t$age, data_t$dnamage, pch = 19, col = ggplot2::alpha(\"#E51718\",0.8),cex = data_t$size)\n# 添加回归线\nabline(lm(dnamage~age, data=data_t), lwd = 2, col = \"#E51718\")\n\n# 在画布中添加正常组的散点\npoints(data_n$age, data_n$dnamage, pch = 19, col = ggplot2::alpha(\"#1D2D60\",0.8), cex = data_n$size)\nabline(lm(dnamage~age, data=data_n), lwd = 2, col = \"#1D2D60\")\n\n# source block: article-3792985494804332545-076-b007\n# 添加边际地毯线显示数据分布情况\nrug(data$age, col=\"black\", lwd=1, side=3)\nrug(data$dnamage, col=\"black\", lwd=1, side=4)\n\n# source block: article-3792985494804332545-076-b008\ntext(20,150, adj = 0,expression(\"Tumour: N = 252; \"~rho~\" = 0.30; \"~italic(P)~\" < 0.001\"), col = c(\"#E51718\"), cex=1)\ntext(20,140,adj = 0,expression(\"Normal: N = 200; \"~rho~\" = 0.82; \"~italic(P)~\" < 0.001\"), col = c(\"#1D2D60\"), cex=1)\n\n# source block: article-3792985494804332545-076-b009\n# 计算图例里需要绘制多少圆圈\nnum <- length(unique(data$range2))\nnum\n\n# 散点图例\npoints(x = rep(par(\"usr\")[2] + 2.2, num), y = seq(80,60, length.out = num),\n       pch = 19, bty = \"n\", cex = sort(unique(data$range2)), col = \"black\")\n\n# 点的文字\ntext(x = rep(par(\"usr\")[2] + 3.8, num + 1), y = c(95, seq(80,60,length.out = num)),\n     labels = c(\"Absolute\\nVertical\\nShift\", round(10^(sort(unique(data$range2))) - 1,0)),\n     adj = 0,cex = 0.8)\n\n# 做分组的圆圈（肿瘤和正常）\npoints(x = rep(par(\"usr\")[2] + 2.2, 2), y = c(130, 120),\n       pch = 19, bty = \"n\", cex = 1.8, col = c(\"#E51718\",\"#1D2D60\"))\n\n# 做分组图图例的文字\ntext(x = rep(par(\"usr\")[2] + 3.8, num + 1), y = c(130, 120),\n     labels = c(\"Tumour\",\"Normal\"),  adj = 0,cex = 0.8)\n\n# source block: article-3792985494804332545-076-b010\n# 设置new = TRUE时，新的图形会叠加在现有的图形上\n# 设置bty=\"o\"会使得图形具有一个完整的矩形边框\npar(new = T, bty=\"o\")\n\n# 这行代码创建一个空白的图形窗口，具有指定的坐标轴范围，但没有轴标签和刻度。\nylim <- range(data$dnamage)\nxlim <- range(data$age)\nplot(-1, -1, col = \"white\",xlim = xlim, ylim = ylim, xlab = \"\", ylab = \"\", xaxt = \"n\", yaxt = \"n\")\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c()
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
