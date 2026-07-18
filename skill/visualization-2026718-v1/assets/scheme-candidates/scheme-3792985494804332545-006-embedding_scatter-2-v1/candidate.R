# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-006-b006\n## 2.使用CellTrek进行细胞图谱构建----\nbrain_traint <- traint(st_data=brain_st_cortex,\n                       sc_data=brain_sc,\n                       sc_assay='RNA',\n                       cell_names='cell_type'# 单细胞数据注释label\n                      )\nbrain_traint\n\n## We can check the co-embedding result to see if there is overlap between these two data modalities\nDimPlot(brain_traint, group.by = \"type\")\n\n# After coembedding, we can chart single cells to their spatial locations.\n# Here, we use the non-linear interpolation (intp = T, intp_lin=F) approach to augment the ST spots.\nbrain_celltrek <- celltrek(st_sc_int=brain_traint, int_assay='traint',\n                           sc_data=brain_sc, sc_assay = 'RNA',\n                           reduction='pca',\n                           intp=T, intp_pnt=5000, intp_lin=F,\n                           nPCs=30, ntree=1000,\n                           dist_thresh=0.55, top_spot=5, spot_n=5,\n                           repel_r=20, repel_iter=20, keep_model=T)$celltrek\n\n## 3.可视化结果----\n# 交互式可视化\nunique(brain_celltrek$cell_type)\nbrain_celltrek$cell_type <- factor(brain_celltrek$cell_type, levels=sort(unique(brain_celltrek$cell_type)))\n\ndf <- brain_celltrek@meta.data %>%\n  dplyr::select(coord_x, coord_y, cell_type:id_new)\nhead(df)\nbrain_celltrek@images$anterior1@image\nbrain_celltrek@images$anterior1@scale.factors$lowres\n\nCellTrek::celltrek_vis(df, brain_celltrek@images$anterior1@image, brain_celltrek@images$anterior1@scale.factors$lowres)\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("df", "repel_r", "dist_thresh", "nPCs", "intp", "reduction", "brain_celltrek", "cell_names", "sc_assay", "sc_data", "brain_traint")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
