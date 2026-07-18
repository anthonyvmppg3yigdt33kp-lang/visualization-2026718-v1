# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-051-b002\n## 基础函数绘图\npar(bty=\"n\", mgp = c(1.5,.33,0), mar=c(4.5,3.5,3,3)+.1, las=1, tcl=-.3)\n\nplot(data_miRNA$Log2FC, y=-log10(data_miRNA$pvalue), xlab=\"\",\n     ylab=\"-log P-value\", col=data_miRNA$color1, pch=21, bg=data_miRNA$color,\n     cex = 1.5, lwd = 2.2, yaxt = \"n\",xaxt = \"n\", xlim=c(-2.5,2.5))\n\naxis(side = 2, at = seq(0, 4, by = 1),labels = 0:4, las = 1, lwd=0)\naxis(side = 1, at = seq(-2.5, 2.5, by = 1), las = 1, lwd = 2.5)\n\n# 添加x轴标题，使用下标表示log2\nmtext( expression(paste(Log[2],\" fold \",\"change\")), cex = 1.2, col = \"black\",side = 1, line = 2)\n\nabline(h = -log10(0.05), col = \"grey60\", lwd = 2.5, lty=3)\nabline(v = -1, col = \"grey60\", lwd = 2.5, lty=3)\nabline(v = 1, col = \"grey60\", lwd = 2.5, lty=3)\nabline(v = 0, col = \"black\", lwd = 2.5, lty=1)\n\n# 使用segments函数添加线段\nsegments(-0.1, 1, 0.1, 1, col = \"black\", lwd = 2.5)\nsegments(-0.1, 2, 0.1, 2, col = \"black\", lwd = 2.5)\nsegments(-0.1, 3, 0.1, 3, col = \"black\", lwd = 2.5)\nsegments(-0.1, 4, 0.1, 4, col = \"black\", lwd = 2.5)\n\n# 添加向右的箭头\narrows(x0 = 0.2, y0 = 3.8, x1 = 2.4, y1 = 3.8, length = 0.1, col = \"#FA8260\", lwd=4.5)\narrows(x0 = -0.2, y0 = 3.8, x1 = -2.4, y1 = 3.8, length = 0.1, col = \"#4D8FD1\", lwd=4.5)\n\n# 添加文本\ntext(1.2, 3.8, \"Higher in AA-E\", font=3, pos=3, adj = 1, col = \"#FA8260\", cex = 1.1)\ntext(-1.2, 3.8, \"Higher in control\", font=3, pos=3, adj = 1, col = \"#4D8FD1\", cex = 1.1)\n# 百分比\ntext(2.1, 3.3, \"4.4%\", font=3, pos=3, adj = 1, col = \"#FA8260\", cex = 1.1)\ntext(-2.1, 3.3, \"0.5%\", font=3, pos=3, adj = 1, col = \"#4D8FD1\", cex = 1.1)\n\n# 添加标题\ntitle(main = \"miRNA\")\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("cex", "ylab")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
