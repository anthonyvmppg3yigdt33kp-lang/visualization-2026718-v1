# tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-04-27 23:46
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247541550&idx=1&sn=3e75c276a57e4cdece16756dee5d993c&chksm=9b4b6395ac3cea835874b0f6f6530c7098e56704de61adc3429929c8614522ad5007946292f6)

---
> 今天来看看老板发来的一个全能绘图包，配色好看，一键式出图！这就分享给大家~

包为 tidyplots, 对应的文献信息：Engler JB (2025). “Tidyplots empowers life scientists with easy code-based data visualization” iMeta. https://doi.org/10.1002/imt2.70018.

官方提供了大量的用户代码案例, 大部分可以直接使用。

官方网址：https://tidyplots.org/use-cases/

绘图逻辑与参数细节如下：

![文章图片 1](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/001.png)

## 包的安装

使用关键词：`tidyplots r package` 检索一下包的来源，确定来自cran，安装代码如下：

```r
## 使用西湖大学的 Bioconductor镜像
options(BioC_mirror="https://mirrors.westlake.edu.cn/bioconductor")
options("repos"=c(CRAN="https://mirrors.westlake.edu.cn/CRAN/"))
install.packages("tidyplots")

# 设置R包路径
.libPaths(c('~/R/x86_64-pc-linux-gnu-library/4.4',
            '/refdir/Rlib',
            '/usr/local/lib/R/library',
            "/home/data/t020448/miniconda3/envs/R4.4/lib/R/library"))

# 加载包
library(tidyverse)
library(tidyplots)
```

里面的图比较多，我挑选了一些自己觉得比较有意思的~

## 高通量测序比对结果可视化

比如以用来绘制我们的生信入门课程第四周转录组测序部分结果的图。

这里提供的示例数据为STAR软件的比对结果，其他的软件同理，只需要整理成df相同的格式就可以啦：

```r
###################################################################
df <- read_csv("https://tidyplots.org/data/sequencing-qc-STAR.csv")
head(df)
# sample category           reads
# <chr>  <chr>              <dbl>
#   1 Eip_3  Uniquely mapped  2290862
# 2 Eip_5  Uniquely mapped 10414939
# 3 Eip_4  Uniquely mapped  4525002
# 4 Eip_2  Uniquely mapped  1599561
# 5 Eip_1  Uniquely mapped 15733471
# 6 Ein_3  Uniquely mapped 12839457

my_colors <- c("Uniquely mapped" = "#437bb1",
               "Mapped to multiple loci" = "#7cb5ec",
               "Mapped to too many loci" = "#f7a35c",
               "Unmapped: too short" = "#b1084c",
               "Unmapped: other" = "#7f0000")

my_colors

p <- df |>
  tidyplot(x = reads, y = sample, color = category) |>
  add_barstack_absolute(reverse = TRUE) |>
  theme_minimal_x() |>
  adjust_size(70, 50) |>
  adjust_colors(my_colors) |>
  adjust_x_axis(title = "Number of reads", cut_short_scale = TRUE) |>
  reorder_color_labels(names(my_colors)) |>
  remove_legend_title() |>
  remove_y_axis_title()
p
ggsave(filename = "maprateplot.png", width = 6, height = 4, plot = p)
```

堆积柱状图：每个样本中比对结果的read数

![文章图片 2](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/002.png)

还可以展示堆积柱状图百分比的形式：只需要 将 `add_barstack_absolute(reverse = TRUE)` 改成 `add_barstack_relative(reverse = TRUE) `

```r
# 百分比
p <- df |>
  tidyplot(x = reads, y = sample, color = category) |>
  add_barstack_relative(reverse = TRUE) |>
  theme_minimal_x() |>
  adjust_size(70, 50) |>
  adjust_colors(my_colors) |>
  adjust_x_axis(title = "Percentage of reads", labels = scales::percent) |>
  reorder_color_labels(names(my_colors)) |>
  remove_legend_title() |>
  remove_y_axis_title()
p
ggsave(filename = "maprateplot_percent.png", width = 6, height = 4, plot = p)
```

![文章图片 3](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/003.png)

## Feature counts定量read结果可视化

也可以是堆积柱状图和百分比的形式：

```r
################################################################################
df <- read_csv("https://tidyplots.org/data/sequencing-qc-featureCounts.csv")
head(df)
# sample category    reads
# <chr>  <chr>       <dbl>
#   1 Eip_3  Assigned  1440266
# 2 Eip_5  Assigned  7212279
# 3 Eip_4  Assigned  1837152
# 4 Eip_2  Assigned   817712
# 5 Eip_1  Assigned  6777689
# 6 Ein_3  Assigned 10231698

table(df$category)
# Assigned    Unassigned_Ambiguity Unassigned_MultiMapping   Unassigned_NoFeatures
# 20                      20                      20                      20

my_colors <- c("Assigned" = "#7cb5ec",
               "Unassigned_Ambiguity" = "#434348",
               "Unassigned_MultiMapping" = "#90ed7d",
               "Unassigned_NoFeatures" = "#f7a35c")

p1 <- df |>
  tidyplot(x = reads, y = sample, color = category) |>
  add_barstack_absolute(reverse = TRUE) |>
  theme_minimal_x() |>
  adjust_size(70, 50) |>
  adjust_colors(my_colors) |>
  adjust_x_axis(title = "Number of reads", cut_short_scale = TRUE) |>
  reorder_color_labels(names(my_colors)) |>
  remove_legend_title() |>
  remove_y_axis_title()

p2 <- df |>
  tidyplot(x = reads, y = sample, color = category) |>
  add_barstack_relative(reverse = TRUE) |>
  theme_minimal_x() |>
  adjust_size(70, 50) |>
  adjust_colors(my_colors) |>
  adjust_x_axis(title = "Percentage of reads", labels = scales::percent) |>
  reorder_color_labels(names(my_colors)) |>
  remove_legend_title() |>
  remove_y_axis_title()

p <- p1 / p2
ggsave(filename = "counts_plot.png", width = 7, height = 8, plot = p)
```

结果如下：

![文章图片 4](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/004.png)

## 散点图

```r
head(eu_countries)
str(eu_countries)

# area 与 population之间的关系
p <- eu_countries |>
  tidyplot(x = area, y = population,width = 80, height = 80) |>
  add_reference_lines(x = 2.5e5, y = 30) |>
  add_data_points(white_border = TRUE)
p
ggsave(filename = "points.png", width = 7, height = 8, plot = p, bg = "white")
```

![文章图片 5](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/005.png)

## 堆积柱状图

```r
head(energy)
p <- energy |>
  dplyr::filter(year >= 2008) |>
  tidyplot(x = year, y = energy, color = energy_source, width = 90,height = 80) |>
  add_barstack_relative()
p
```

![文章图片 6](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/006.png)

## 棒棒图

```r
head(study)

p <- study |>
  tidyplot(x = treatment, y = score, color = treatment, width = 90,height = 80) |>
  add_mean_dot(size = 2.5) |>
  add_mean_bar(width = 0.03) |>
  add_mean_value()
p
```

结果如下：

![1](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/007.png)

1

## 箱线图

不同分组的学习成绩分布差异：

```r
head(study)
str(study)
# tibble [20 × 7] (S3: tbl_df/tbl/data.frame)
# $ treatment  : chr [1:20] "A" "A" "A" "A" ...
# $ group      : chr [1:20] "placebo" "placebo" "placebo" "placebo" ...
# $ dose       : chr [1:20] "high" "high" "high" "high" ...
# $ participant: chr [1:20] "p01" "p02" "p03" "p04" ...
# $ age        : num [1:20] 23 45 32 37 24 23 45 32 37 24 ...
# $ sex        : chr [1:20] "female" "male" "female" "male" ...
# $ score      : num [1:20] 2 4 5 4 6 9 8 12 15 16 ...

p <- study |>
  tidyplot(x = treatment, y = score, color = treatment, width = 90,height = 80) |>
  add_boxplot() |>
  add_data_points_beeswarm()
p
```

![文章图片 8](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/008.png)

### 带显著性：

```r
p <- study |>
  tidyplot(x = group, y = score, color = dose, width = 90,height = 80) |>
  add_mean_bar(alpha = 0.3) |>
  add_sem_errorbar() |>
  add_data_points() |>
  add_test_asterisks(hide_info = TRUE)
p
```

![文章图片 9](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/009.png)

## 曲线分布

不同分组的score分布差异：

```r
str(time_course)
# spc_tbl_ [1,710 × 4] (S3: spec_tbl_df/tbl_df/tbl/data.frame)
# $ day      : num [1:1710] 0 0 0 0 0 0 0 0 0 0 ...
# $ subject  : chr [1:1710] "id1" "id2" "id3" "id4" ...
# $ score    : num [1:1710] 0 0 0 0 0 0 0 0 0 0 ...
# $ treatment: chr [1:1710] "untreated" "untreated" "untreated" "untreated" ...

p <- time_course |>
  tidyplot(x = day, y = score, color = treatment, dodge_width = 0, width = 90,height = 80) |>
  add_mean_line() |>
  add_sem_ribbon()
p
```

![文章图片 10](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/010.png)

## 小提琴图

不同分组打分差异：

```r
p <- study |>
  tidyplot(x = treatment, y = score, color = treatment, width = 90,height = 80) |>
  add_violin() |>
  add_data_points_beeswarm()
p
```

![文章图片 11](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/011.png)

### 基因表达分组差异：

```r
library(tidyverse)
head(gene_expression)

p <- gene_expression |>
  filter(external_gene_name %in% c("Apol6", "Col5a3", "Bsn", "Fam96b", "Mrps14", "Tma7")) |>
  tidyplot(x = sample_type, y = expression, color = condition) |>
  add_violin() |>
  add_data_points_beeswarm(white_border = TRUE) |>
  adjust_x_axis_title("") |>
  remove_legend() |>
  add_test_asterisks(hide_info = TRUE, bracket.nudge.y = 0.3) |>
  adjust_colors(colors_discrete_ibm) |>
  adjust_y_axis_title("Gene expression") |>
  split_plot(by = external_gene_name, ncol = 2)
p
```

![文章图片 12](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/012.png)

## 火山图

```r
# 导入差异分析结果
df <-
  read_csv("https://tidyplots.org/data/differential-expression-analysis.csv") |>
  mutate(
    neg_log10_padj = -log10(padj),
    direction = if_else(log2FoldChange > 0, "up", "down", NA),
    candidate = abs(log2FoldChange) >= 1 & padj < 0.05
  )
head(df)

# 绘图
p <- df |>
  tidyplot(x = log2FoldChange, y = neg_log10_padj,, width = 100,height = 90) |>
  add_data_points(data = filter_rows(!candidate),
                  color = "lightgrey", rasterize = TRUE) |>
  add_data_points(data = filter_rows(candidate, direction == "up"),
                  color = "#FF7777", alpha = 0.5) |>
  add_data_points(data = filter_rows(candidate, direction == "down"),
                  color = "#7DA8E6", alpha = 0.5) |>
  add_reference_lines(x = c(-1, 1), y = -log10(0.05)) |>
  add_data_labels_repel(data = min_rows(padj, 6, by = direction), label = external_gene_name,
                        color = "#000000", min.segment.length = 0, background = TRUE) |>
  adjust_x_axis_title("$Log[2]~fold~change$") |>
  adjust_y_axis_title("$-Log[10]~italic(P)~adjusted$")
p
```

差异结果格式df：

![文章图片 13](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/013.png)

绘图结果：

![文章图片 14](assets/043_tidyplots：一个全能绘图包(配色好看，一键式出图！可以取代ggplot2？)/014.png)

## Note：

这个绘图函数有个参数需要注意，`tidyplot(x = area, y = population,width = 80, height = 80)`，需要根据图进行调整 宽和高，不然有些图画出来超大的空白边！

如果出现如下报错，请将ggplot2更新到最新版 3.5.2：

> Error in is_theme(e1) : could not find function "is_theme"

#### 快去试试吧~

### **文末友情宣传**

- **[生信入门&数据挖掘线上直播课5月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247541231&idx=1&sn=6704a3ae8233d19ca94fd4929b5e1f63&scene=21#wechat_redirect)**

- **[时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5&scene=21#wechat_redirect)**

- **[满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247535760&idx=2&sn=1e02a2e982a046ecf6389231e6768d5b&scene=21#wechat_redirect)**

<!-- wechat-article-fetcher: complete -->
