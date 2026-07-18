# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-4329102050694250504-003-b008\nset.seed(0317)\nht <- Heatmap(Input,\n        cluster_columns = F,\n        name = 'NES',\n        col = col,\n        row_names_gp = gpar(fontsize = 9),  # 行名字体大小\n        top_annotation = AnnoCluster,\n        left_annotation = AnnoPathway,\n        column_split = c('A','B','C','D'),\n        column_title = NULL,\n        row_split = SelectPathway$Category,\n        row_title = NULL,\n        cluster_rows = F,\n        rect_gp = gpar(col = \"white\", lwd = 1), # 格子边框白色，线宽1\n        # 在格子中添加显著性符号*\n        cell_fun = function(j, i, x, y, width, height, fill) {\n          if(!is.na(InputSig[i, j]))\n            grid.text(InputSig[i, j], x, y, gp = gpar(fontsize = 9), just = c(\"centre\",\"center\"))\n        },\n        height = unit(40/2,'cm'), width = unit(4,'cm')\n        )\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("height", "cell_fun", "rect_gp", "cluster_rows", "row_title", "row_split", "column_title", "column_split", "left_annotation", "top_annotation", "row_names_gp", "col", "name", "cluster_columns", "ht")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
