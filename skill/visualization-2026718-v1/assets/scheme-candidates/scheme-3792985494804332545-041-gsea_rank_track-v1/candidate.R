# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-041-b008\np_merge <- list()\nfor(i in path_select) {\n# i <- \"INTERFERON_GAMMA_RESPONSE\"\nprint(i)\n# 创建数据框\n  temp <- pathways[i]\n  temp <- intersect(temp[[1]],names(ranks))\n  df <- data.frame(x=match(temp,names(ranks)), y=ranks[temp])\n  df\n\n## 绘制图形\n# x：线段的起始 x 坐标。\n# xend：线段的结束 x 坐标。\n# y：线段的起始 y 坐标。\n# yend：线段的结束 y 坐标。\n\n  label = sprintf(\"%.2f\",fgseaRes[fgseaRes$pathway==i,\"NES\"])\n\n  p_merge[[i]] <- ggplot(df, aes(x = x,y=y)) +\n    geom_segment(aes(x = x, xend = x, y = 0, yend = y), color = \"black\") +\n    geom_hline(yintercept = 0,color=\"blue\") +\n    scale_x_continuous(expand = c(0.01,0)) +\n    scale_y_continuous(sec.axis = sec_axis(trans = ~.*5, name = label)) + # 第二个y轴\n    labs(title = \"\", x = \"\", y = i) +\n    theme_bw() +\n    theme( panel.border = element_blank(),  # 去掉图形内部的边框\n      plot.background = element_blank(),  # 去掉整个图形的背景边框\n      panel.grid.major = element_blank(),  # 去掉主网格线\n      panel.grid.minor = element_blank(),  # 去掉次网格线\n      axis.text = element_blank(),\n      axis.ticks = element_blank(),  # 去掉 y 轴刻度线\n      plot.margin = unit(c(0,0,0.5,0), \"npc\"),\n      panel.spacing = unit(c(0,0,0,0), \"npc\"),\n      axis.title.y  = element_text(angle = 0, vjust = 0.5,hjust =1 ,size = 15),     # 旋转 y 轴标签\n      axis.title.y.right = element_text(angle = 0, vjust = 0.4,hjust =0,size = 15) # 右侧坐标轴注释的名称\n    )\n}\n\np <-  wrap_plots(p_merge, ncol = 1, axes=\"collect\") &\n  theme(plot.margin = unit(c(0, 0.3, 0, 0.1), \"cm\"))  # 设置整个图形的边距\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p", "axis.title.y.right", "axis.title.y", "panel.spacing", "plot.margin", "axis.ticks", "axis.text", "panel.grid.minor", "panel.grid.major", "plot.background", "label", "df", "temp", "p_merge")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
