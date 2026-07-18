# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-071-b003\np1 <- ggplot(data = dat, aes(x = 1, y = rev(Description), colour = -log10(p.adjust))) +\n  geom_text(size=-log10(dat$p.adjust)*0.3, aes( label = Description), hjust = 0.5) + # hjust = 0.5,居中对齐\n  scale_color_gradient(low = \"#98bf92\", high = \"#006a01\") +   # 创建颜色渐变\n  scale_x_continuous(expand = c(0,0)) + # 调整柱子底部与y轴紧贴\n  labs(x = \" \", y = \" \", title = \"PDAC KRAS-ERK UP\", color=\"Significance\\n(-log10 adj. p-val.)\") +\n  theme(axis.text = element_blank(),  # 隐藏x/y轴标签\n        axis.ticks = element_blank(), # 隐藏x/y轴刻度\n        # 隐藏其他边框线\n        panel.grid.major = element_blank(),\n        panel.grid.minor = element_blank(),\n        plot.background = element_rect(fill = \"white\", color = NA),\n        panel.background = element_rect(fill = \"white\", color = NA),\n        # 隐藏边框线\n        panel.border = element_blank(),\n        plot.title = element_text(hjust = 0.5) # 标题居中\n        ) +\n  # 添加顶部横着的黑线\n  annotate(\"segment\", x = 0, xend = 2, y = 10.6, yend = 10.6, color = \"black\", size = 1.1)\n\np1\n\n# 保存，这里的保存宽和高进行了调整，可以使得结果比较美观\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("plot.title", "panel.border", "panel.background", "plot.background", "panel.grid.minor", "panel.grid.major", "axis.ticks", "p1")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
