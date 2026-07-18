# Source-safe candidate distilled from a traceable plotting chain.
CANDIDATE_SOURCE <- "# source block: article-3792985494804332545-067-b003\n## plot\n# violin plotting\ncol <- c(\"#1F78B4\",\"#A6CEE3\",\"#B2DF8A\",\"#33A02C\",\"#FB9A99\",\"#FDBF6F\",\"#E31A1C\")\np <- ggplot(df, aes(x=Group, y=Shannon_e, fill=Group)) +\n  geom_violin(position = position_dodge(width = 0.1), scale = 'width') +  # 小提琴\n  geom_boxplot(alpha=1,outlier.size=0, size=0.3, width=0.3,fill=\"white\") + # 小提琴中的箱线图\n  scale_fill_manual(values = col) + # 手动填充颜色\n  labs(x=\"\", y=\"Shannon index\", color=\"Group\")+\n  scale_x_discrete(limits=c(\"BS\",\"RS\",\"RE\",\"VE\",\"SE\",\"LE\",\"P\")) +\n  theme_classic() +\n  theme(axis.text.x = element_text(size = 10,face = \"bold\"),axis.text.y = element_text(size = 10))+\n  theme(axis.title.y= element_text(size=12,face = \"bold\"))+theme(axis.title.x = element_text(size = 12))+\n  theme(legend.title=element_text(size=10),legend.text=element_text(size=8))\n\np\n"

candidate_source <- function() CANDIDATE_SOURCE

build_candidate_plot <- function(bindings = list()) {
  if (!is.list(bindings)) stop('bindings must be a named list')
  env <- list2env(bindings, parent = parent.frame())
  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)
  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)
  preferred <- c("p", "col")
  for (name in preferred) {
    if (!exists(name, envir = env, inherits = FALSE)) next
    value <- get(name, envir = env, inherits = FALSE)
    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)
  }
  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')
}
