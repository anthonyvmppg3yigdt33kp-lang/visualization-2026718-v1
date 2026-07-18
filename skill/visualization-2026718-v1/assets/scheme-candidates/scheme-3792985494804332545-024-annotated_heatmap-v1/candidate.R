# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-024-b002\n# 选择差异变化大的基因算相关性\n# mad: 绝对中位差\n# sd:标准差\nexprSet <- dat\nexprSet <- exprSet[names(sort(apply(exprSet, 1, mad),decreasing = T)[1:20]),]\nexprSet <- t(exprSet)\ndim(exprSet)\npheatmap::pheatmap(cor(exprSet))\n\n\ncor_value <- cor(exprSet)\ncor_test_mat <- corr.test(exprSet)$p\n\ncor_pp1 <- ggcorrplot(cor_value, method = \"ellipse\",type = \"lower\",\n                    p.mat = cor_test_mat,\n                    col = c(\"#8aa3db\", \"white\", \"#fd9a9a\"),\n                    pch.cex = 4.5, # 显著性*号的大小\n                    insig = \"label_sig\", sig.lvl = c(0.05, 0.01, 0.001) # (e.g. \"*\", \"**\", \"***\")\n                    )  +\n  guides(color = guide_legend(override.aes = list(size = 1))) +\n  theme(axis.text = element_text(size=10),\n        legend.key.width = unit(0.5, \"lines\"),  # 调整图例键的宽度\n        legend.key.height = unit(0.5, \"lines\")  # 调整图例键的高度\n  )\n\ncor_pp1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.key.height", "legend.key.width", "insig", "pch.cex", "col", "p.mat", "cor_pp1", "cor_test_mat", "cor_value", "exprSet")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
