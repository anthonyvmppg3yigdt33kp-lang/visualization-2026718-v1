# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-056-b004\n############################## 绘制聚类树\n# 到这里的时候我感觉这个通路聚类的指标很迷惑，这里就当做单纯的绘图技巧了吧，数据没有意义\n# 通路聚类至少要有两个特征\n# 这里选择 pvalue, p.adjust 绘制通路聚类树\ntemp <- dat_plot[, c(\"p.adjust\",\"log10PAD\")]\nrownames(temp) <- dat_plot$ID\ntemp\n\ntree <-  hclust(dist(temp))\ntree\nplot(tree, hang=-1)\n\n# 绘图颜色\ncolors <- c(GOBP=\"#90c5b1\", KEGG=\"#c6c6e0\", REACTOME=\"#766fb3\", GOCC=\"#f0b895\")\ncolors\n\n# 使用ggtree\np1 <- ggtree(tree, branch.length=\"none\") %<+% dat_plot +\n  geom_tippoint(aes(fill=class, color=class),shape=21,size=4) +\n  scale_fill_manual(values = colors) +\n  scale_color_manual(values = colors) +\n  theme(legend.position = \"none\")\np1\n\n# source block: article-3792985494804332545-056-b005\n## 绘制条形图\nhead(dat_plot)\np2 <- ggplot(data = dat_plot, aes(x = log10PAD,y = ID,fill=class),color=\"black\")+\n  geom_bar(stat=\"identity\",position=\"stack\",color=\"black\") +\n  geom_text(aes(label = sig), hjust = -0.2, size = 5) +  # 添加文本标签\n  labs(x=\"Enrichment(-log10 adj.p-val)\",y=NULL) +\n  scale_x_continuous(expand=c(0,0)) +\n  coord_cartesian(clip = 'off') +\n  # scale_fill_brewer(palette=\"Paired\") + # 这个色板挺好看的\n  scale_fill_manual(values = colors) +\n  scale_x_continuous(breaks = seq(0, 30, by = 5)) +  # 设置x轴的刻度间隔为2\n  theme_classic() +\n  theme(axis.title.x=element_blank(),\n        axis.text.x=element_text(color=\"black\",size=10),\n        axis.ticks.x=element_line(size = 1  ),\n        axis.line.x=element_line(size = 1),\n        # y轴设置\n        axis.ticks.y=element_blank(),\n        axis.line.y = element_blank(), # 隐藏y轴的线\n        axis.text.y=element_text(face = \"bold\",size = 10),\n        legend.title=element_blank(),\n        legend.spacing.x=unit(0.2,'cm'),\n        legend.key=element_blank(),\n        legend.key.width=unit(0.5,'cm'),\n        legend.key.height=unit(0.5,'cm'),\n        plot.margin = margin(1,0.5,0.5,1,unit=\"cm\"))\np2\n\n# source block: article-3792985494804332545-056-b006\n# 拼图\np <- p2 %>%\n  insert_left(p1,width=.5) %>%\n  as.grob() %>%\n  ggdraw()\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p", "p2", "p1")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
