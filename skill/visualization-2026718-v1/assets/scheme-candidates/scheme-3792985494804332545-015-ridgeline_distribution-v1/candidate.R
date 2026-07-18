# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-015-b003\n## 绘图\ncolors <- c(\"#cae2ee\",\"#ded0e5\",\"#a68bc2\",\"#85c680\",\"#d09b7e\",\"#79aed2\",\"#ffb266\",\"#dcca83\",\"#ee7677\")\nnames(colors) <- c(\"Plasma cell\", \"Endothelial cell\",\"Fibroblast\",\"T cell\",\"Dendritic cell\",\n                   \"B cell\",\"Myeloid cell\",\"Mast cell\",\"Ovarian cancer cell\")\ncolors\n\n\nlibrary(ggridges)\np <- ggplot(df, aes(x = percent.mt, y = cell_type, fill = cell_type)) +\n  geom_density_ridges(quantile_lines = TRUE, quantiles = 2, color= 'white', # #显示分位数线,2为显示中位数，颜色为白色\n                      rel_min_height = 0.01, #尾部修剪，数值越大修剪程度越高\n                      scale = 2, #山脊重叠程度，数值越大重叠度越高\n                      ) +\n  scale_fill_manual(values = colors) +\n  ggtitle(\"Cell type\") +\n  theme_classic()\np\n\n# source block: article-3792985494804332545-015-b004\n## 美化\np1 <- p +\n  scale_x_continuous(limits = c(0.0, 20), breaks = seq(0, 20, by = 5)) +  # 设置线粒体范围0-20%\n  geom_vline(xintercept = c(0.0, 20),size = 0.5, color = 'grey',lty = 'dashed') + # 添加两条竖着的虚线\n  ylab(label = \"\") +\n  theme(legend.position = 'none',  # 去掉图例\n        # 设置标题居中、加粗、放大\n        plot.title = element_text(hjust = 0.5, size = 14, face = \"bold\"),\n        # 加粗和放大坐标轴线\n        axis.line = element_line(color = \"black\", size = 0.8),\n        # 加粗和放大x坐标轴刻度\n        axis.ticks = element_line(color = \"black\", size = 0.8),\n        axis.ticks.length = unit(0.2, \"cm\"),  # x坐标轴刻度线长度\n        # 加粗和放大x坐标轴刻度标签\n        axis.text = element_text(color = \"black\", size = 14, face = \"bold\"),\n        # 加粗和放大x坐标轴标题\n        axis.title = element_text(color = \"black\", size = 16, face = \"bold\")\n        )\np1\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p1", "scale", "rel_min_height", "p", "colors")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
