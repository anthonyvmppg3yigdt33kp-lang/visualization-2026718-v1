# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-033-b006\n# 文本框注释条在右边\nht_list = Heatmap(mat, name = \"mat\", cluster_rows = FALSE, row_split = split,\n        show_row_names = F,  # 去掉行名\n        cluster_columns = F, # 列不聚类\n        row_title_rot = 0,   # 右边的标题水平放着\n        row_title_gp = gpar(fontsize = 12),\n        heatmap_legend_param = list(direction = \"horizontal\",nrow = 1), # 图例水平放置\n        column_names_side = c(\"top\"),\n        right_annotation =  ha\n        ) +\n  ha1 + ha2\n\ndraw(ht_list,heatmap_legend_side = \"bottom\") # 图例放在底部\n\n# 给三个文本注释框添加标题\ndecorate_annotation(\"textbox1\",{\n  grid.text(\"Genes\", y = unit(1, \"npc\") + unit(2, \"mm\"), just = \"bottom\")\n})\ndecorate_annotation(\"textbox2\",  {\n  grid.text(\"Annotation\", y = unit(1, \"npc\") + unit(2, \"mm\"), just =c(\"right\",\"bottom\"))\n})\ndecorate_annotation(\"textbox3\",  {\n  grid.text(\"Adj.Pvalue\", y = unit(1, \"npc\") + unit(2, \"mm\"), just = \"bottom\")\n})\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("right_annotation", "column_names_side", "heatmap_legend_param", "row_title_gp", "row_title_rot", "cluster_columns", "show_row_names", "ht_list")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
