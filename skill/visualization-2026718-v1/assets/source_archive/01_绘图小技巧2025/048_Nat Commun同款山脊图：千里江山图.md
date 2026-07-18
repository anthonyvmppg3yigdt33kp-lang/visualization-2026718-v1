# Nat Commun同款山脊图：千里江山图

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-04-07 19:29
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247540687&idx=1&sn=315b1f5757a97375a6425c3e751f7304&chksm=9b4b1f74ac3c96629f0cb9d12cad65d6e67b0be9bb7e0d99ab77e5f9e547ca63c8e3a83033e5)

---
>
>
> 今天来学习一幅配色非常优秀的山峦图，不同层次的山峦彼此起伏，宛如一幅《千里江山图》。如果你看过《国家宝藏》这档节目，肯定知道北京故宫就藏有一幅来自北宋王希孟的传世名画《千里江山图》：https://www.bilibili.com/video/BV1Sm421N7J2，还有一个视频：https://www.bilibili.com/video/BV11Z4y1G7YB/ 讲解了这幅国宝的详细制作过程。

而我们本次学习的千里江山图来自文献：《Early-life thymectomy leads to an increase of granzyme-producing γδ T cells in children with congenital heart disease》，于2024年11月13号发表在nature communications上：

这幅图展示了6个蛋白在单细胞免疫组库测序结果中的表达特征，配色非常有水墨画风格。

![文章图片 1](assets/048_Nat%20Commun同款山脊图：千里江山图/001.png)

>
>
> 图注：Fig. 3 \| Increase of CD28hiCD161hi Vγ9Vδ2 T cells in children with CHD.

## 示例数据

额，还没有学过免疫组库的数据分析，这里我就找一个单细胞转录组数据吧（单细胞转录组数据画出来可能没有这么好看，因为基因表达矩阵的稀疏性）。数据来自GSE144469，前面的帖子中有处理方式：[给你的单细胞umap图加个cell杂志同款的圈](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537290&idx=1&sn=ad76831349df67bb5236370dab088536&scene=21#wechat_redirect)

也可以在这里得到：https://github.com/zhangj1115/example_data

读取进来，获取几个基因的表达：

```r
rm(list=ls())

## 使用西湖大学的 Bioconductor镜像
options(BioC_mirror="https://mirrors.westlake.edu.cn/bioconductor")
options("repos"=c(CRAN="https://mirrors.westlake.edu.cn/CRAN/"))
# remotes::install_github("alserglab/mascarade")
library(Seurat)
library(SeuratData)
library(mascarade)
library(tidyverse)
library(Seurat)
library(data.table)
library(qs)
library(ggridges)

## Seurat对象
sce.all.filt <- qread("GSE144469/cd45/2-harmony/sce.all_int.qs")
sce.all.filt
table(Idents(sce.all.filt))
table(sce.all.filt$RNA_snn_res.0.1)
head(sce.all.filt@meta.data)

# 提取数据，这个基因可以自己指定想展示的
g <- c("PTPRC","CD3D","CD3E","CD3G","CD79A","NKG7")

df <- FetchData(object=sce.all.filt, vars=c("RNA_snn_res.0.1",g))
head(df)
colnames(df)[1] <- "class"
df$class <- paste0("c",df$class)
df$class <- factor(df$class, levels = rev(c(paste0("c",0:8))))
table(df$class)
class(df$class)
```

![文章图片 2](assets/048_Nat%20Commun同款山脊图：千里江山图/002.png)

## 颜色获取

这里的颜色层次比较分明也比较少，我就直接使用`Snipaste`软件获取了，评论区有人问如何获取，方法如下：

```r
colors <- c("#93aeda","#f69b80","#9fcb98","#9b93c7","#959495","#fbbc8a","#fde89b","#c9e2ed","#d4d4d4")
names(colors) <- c(paste0("c",0:8))
```

![文章图片 3](assets/048_Nat%20Commun同款山脊图：千里江山图/003.png)

## 先绘制一个基因的看看

就用这个表达比较高的CD45蛋白，基因名称为PTPRC：

```r
ggplot(df, aes(x = PTPRC, y = class, fill = class)) +
  geom_density_ridges(quantile_lines = TRUE, quantiles = 2) +
  scale_fill_manual(values = colors) +
  ggtitle("CD45+") +
  theme_test()
```

![文章图片 4](assets/048_Nat%20Commun同款山脊图：千里江山图/004.png)

## 绘制多个并美化

这里需要对数据做一步转换：

```r
# 绘制多个，加一个分面
library(reshape2)
# id.vars：指定哪些列是标识符，不需要被转换。
# variable.name：新列的列名，默认为“variable”。
# value.name：新列中数值的列名，默认为“value”。

df_all <- melt(df, id.vars="class", variable.name="markers", value.name="expression")
head(df_all)

p <- ggplot(df_all, aes(x = expression, y = class, fill = class)) +
  geom_density_ridges(quantile_lines = TRUE, quantiles = 2) +
  scale_fill_manual(values = colors) +
  facet_wrap(markers~., ncol = 6,scales = "free_x") +
  ylab("") + xlab("Expression") +
  theme_test(base_size = 15) +
  theme(panel.border=element_rect(linewidth = 1, color = "black"),
        strip.background = element_rect(linewidth = 1, fill = "white"),
        strip.text = element_text(size = 18),
        axis.title.x = element_text(size = 16),
        axis.text = element_text(size = 16, colour = "black"),
        axis.line = element_line(size = 0.6),
        legend.position = "none")
p

ggsave(filename = "Ridge.pdf", width = 10, height = 5,plot = p)
```

#### 就问你美不美吧~

![单细胞转录组数据画出来可能没有这么好看，因为基因表达矩阵的稀疏性](assets/048_Nat%20Commun同款山脊图：千里江山图/005.png)


单细胞转录组数据画出来可能没有这么好看，因为基因表达矩阵的稀疏性

### 文末友情宣传

- [生信入门&数据挖掘线上直播课4月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247539788&idx=1&sn=62a09c7af6373658bf81c149eb0b4026&scene=21#wechat_redirect)

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](http://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247524148&idx=1&sn=7806da6feb41a36493c519c1cfc1d3ac&chksm=9b4bdf8fac3c569960369602f1ef26639cb366b250f233b2297d1f059471c0458335bfc0b829&scene=21#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247535760&idx=2&sn=1e02a2e982a046ecf6389231e6768d5b&scene=21#wechat_redirect)

<!-- wechat-article-fetcher: complete -->
