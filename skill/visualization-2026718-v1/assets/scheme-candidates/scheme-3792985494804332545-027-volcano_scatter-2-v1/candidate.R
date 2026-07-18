# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-027-b007\n## 灰色背景柱子\n#根据图p中log2FC区间确定背景柱长度：\ntop_log2FC <- sce.markers %>%\n  group_by(cluster) %>%       # 按cluster分组\n  slice_max(avg_log2FC, n = 1) %>%# 在每个分组中选择log2FC最大的值\n  ungroup()                   # 取消分组\n\ndown_log2FC <- sce.markers %>%\n  group_by(cluster) %>%       # 按cluster分组\n  slice_min(avg_log2FC, n = 1) %>%# 在每个分组中选择log2FC最大的值\n  ungroup()                   # 取消分组\n\ndfbar <- data.frame(cluster=unique(sce.markers$cluster), up=top_log2FC$avg_log2FC, down=down_log2FC$avg_log2FC)\n\n## 绘制背景柱：这里注意要将背景画在底部，不然放在点图后面会遮住点\np <- ggplot() +\n  geom_col(data = dfbar, mapping = aes(x = cluster,y = up), fill = \"#efefef\") +\n  geom_col(data = dfbar,mapping = aes(x = cluster,y = down), fill = \"#efefef\") +\n  geom_jitter(data = sce.markers, aes(x = cluster, y = avg_log2FC, color = sig),\n              size = 0.6, width =0.4) +\n  geom_jitter(data = top10, aes(x = cluster, y = avg_log2FC, color = sig),\n              size = 1, width =0.4) + ## top10的点，大小突出一下\n  scale_color_manual(name=NULL, values = c(\"#f05f63\",\"#1b1b1b\")) + ## 点的颜色调整\n  geom_text_repel(data=top10, aes(x=cluster,y=avg_log2FC,label=gene), force = 1.2,\n                  arrow = arrow(length = unit(0.008, \"npc\"),type = \"open\", ends = \"last\") ) ## 添加文字标签\n\np\n\n# source block: article-3792985494804332545-027-b008\n## 添加cluster方框\n## 方框的高度为前面 log2FC的阈值的两倍，好看一点可以*0.8\n# 添加X轴的cluster色块标签：\ndfcol <- data.frame(x= unique(sce.markers$cluster), y=0, label=unique(sce.markers$cluster),\n                    labelcol = c(\"white\",rep(\"black\",3),rep(\"white\",2),rep(\"black\",3),\"white\" )\n                    )\ndfcol\nmycol <- c(\"#2f3084\",\"#76a5d9\",\"#43a8a8\",\"#3c75a9\",\"#197638\",\"#a44395\",\"#f9a213\",\"#dba478\",\"#969730\",\"#000000\")\n\np2 <- p +\n  geom_tile(data = dfcol, aes(x=x,y=y), height=0.5 * 2 * 0.8, color = \"black\", fill = mycol,  show.legend = F) +\n  geom_text(data=dfcol, aes(x=x,y=y,label=label), size =6, color = dfcol$labelcol) ## 添加方框中的cluster标签\n\np2\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p2", "arrow", "size", "p", "dfbar", "down_log2FC", "top_log2FC")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
