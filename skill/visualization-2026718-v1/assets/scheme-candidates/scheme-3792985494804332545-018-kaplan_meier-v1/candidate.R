# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-018-b004\np <- ggsurvplot(fit, data = data, conf.int = TRUE,\n            pval = TRUE,             # 添加P值\n            surv.median.line = \"hv\", # 添加中位生存时间线\n            risk.table = TRUE,       # 添加风险表\n            legend = c(0.8,0.75),    # 指定图例位置\n            legend.title = \"\",       # 设置图例标题\n            legend.labs = c(\"CDS-A\", \"CDS-B\",\"CDS-C\"), # 指定图例分组标签\n            palette = c(\"#1f87be\", \"#e19433\",\"#cc5650\"),\n            xlab = \"Days\", # 指定x轴标签\n            break.x.by = 1000,          # 设置x轴刻度间距\n            title = \"\"  # 添加图表标题，\n           )\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("title", "break.x.by", "xlab", "palette", "legend.labs", "legend.title", "legend", "risk.table", "surv.median.line", "pval", "p")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
