# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-017-b006\n#  Step 3: Vasualization\n## volcano\nlimma.res <- limma.res %>% mutate(group=factor(group,levels = c(\"Up in tumor\",\"Down in tumor\",\"Not significant\")))\nhead(limma.res)\n\np <- ggscatter(limma.res, x = \"logFC\", y = \"logP\", color = \"group\", size = 2,\n               main = paste0(\"Differential expressed proteins\nbetween tumor and TAT\"), # ***\n               xlab = \"\",\n               ylab = \"-log10(adjusted P.value)\",\n               palette = c(\"#D01910\",\"#00599F\",\"#CCCCCC\"),\n               ylim = c(-1, 70), xlim=c(-8,8)) +\n  geom_hline(yintercept = -log10(0.05), linetype=\"dashed\", color = \"#222222\") +\n  geom_vline(xintercept = 0.58 , linetype=\"dashed\", color = \"#222222\") +\n  geom_vline(xintercept = -0.58, linetype=\"dashed\", color = \"#222222\") +\n  xlab(label = expression(log[2](fold~change))) +\n  labs(color = \"Significance\") +  # 修改颜色图例的标题\n  annotate(\"text\", x = -5, y = 66, label = \"864 proteins\", size = 5, color = \"#00599F\", hjust = 0.5) + # 设置文本样式\n  annotate(\"text\", x = 5, y = 66, label = \"1,213 proteins\", size = 5, color = \"#D01910\", hjust = 0.5) + # 设置文本样式\n  theme_bw() +\n  theme(\n    plot.title = element_text(hjust = 0.5),\n    panel.grid.major = element_blank(),  # 去掉主要格子线\n    panel.grid.minor = element_blank(),  # 去掉次要格子线\n    plot.background = element_blank(),\n    legend.position = \"bottom\"\n    )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("legend.position", "plot.background", "panel.grid.minor", "panel.grid.major", "plot.title", "ylim", "palette", "ylab", "xlab", "main", "p", "limma.res")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
