# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-049-b003\n####### 3.双向条形图\nlibrary(tidyverse)\nlibrary(ggthemes)\nlibrary(ggprism)\n\n# 载入gsva的差异分析结果\ndat_plot <- data.frame(id=row.names(diff), p=diff$P.Value, tvalue= diff$t)\ndat_plot$group <- ifelse(dat_plot$tvalue >0 ,1,-1)    # 将上调设为组1，下调设为组-1\n\n# 阈值自己的项目需要调整，我这里因为显著的pvalue比较少，使用了0.2, 没有统计学意义\ndat_plot$g <- \"Not\"\ndat_plot$g[ dat_plot$tvalue>0 & dat_plot$p < 0.2 ] <- \"Up\"\ndat_plot$g[ dat_plot$tvalue<0 & dat_plot$p < 0.2 ] <- \"Down\"\ntable(dat_plot$g)\ndat_plot$g <- factor(dat_plot$g, levels=c('Up','Down','Not'))\n\n# 添加label颜色\ndat_plot$color <- ifelse(dat_plot$g==\"Not\", '#cccccc',\"black\")\n\n# 排个序\ndat_plot <- dat_plot[order(dat_plot$tvalue,decreasing = T), ]\ndat_plot$id <- factor(dat_plot$id,levels = rev(dat_plot$id))\n\n# 调整添加的y轴方向通路的对其方式\ndat_plot$lable_hjust <- ifelse(dat_plot$tvalue>0, 1, 0)\n\n# 对其的x轴起点，上调通路在x轴右边，起点隔0.05, 避免与柱子粘在一起\ndat_plot$lable_xloc <- ifelse(dat_plot$tvalue>0, -0.05, 0.05)\n\n# 虚线阈值\nt_up <- min(dat_plot[dat_plot$g==\"Up\",\"tvalue\"]);t_up\nt_down <- max(dat_plot[dat_plot$g==\"Down\",\"tvalue\"]);t_down\n\np <- ggplot(data = dat_plot,aes(x = id, y = tvalue, fill = g)) +\n  geom_col() +\n  coord_flip() +\n  scale_fill_manual(values = c('Up'= '#36648b','Not'='#cccccc','Down'='#7ccd7c')) +\n  geom_hline(yintercept = c(t_down,t_up), color = 'white', size = 0.5,lty='dashed') +\n  xlab('') +\n  ylab('t value of GSVA score, treat \\n versus control') +\n  guides(fill=\"none\") +\n  theme_prism(border = T) +\n  theme( axis.text.y = element_blank(),\n         axis.ticks.y = element_blank() ) +\n  geom_text(data = dat_plot, aes(x=id, y = lable_xloc, label = id, hjust = lable_hjust),\n            color=dat_plot$color, size = 4.2) #+  # 添加通路名称\n\np\n# 保存\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("color", "axis.ticks.y", "p", "t_down", "t_up", "dat_plot")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
