# Reference-only, source-safe candidate source fragment.
candidate_source <- function() {
  return("# source block: article-3792985494804332545-072-b004\n# 使用上述 df 数据框\nggplot(df, aes(x = Group, y = Value)) +\n  geom_boxplot() +\n  labs(title = \"分组箱线图\", x = \"组别\", y = \"数值\") +\n  theme_minimal()\n")
}
