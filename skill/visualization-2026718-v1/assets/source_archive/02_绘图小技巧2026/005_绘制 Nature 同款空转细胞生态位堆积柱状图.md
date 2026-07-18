# 绘制 Nature 同款空转细胞生态位堆积柱状图

- 专辑：绘图小技巧2026
- 公众号：生信技能树
- 发布时间：2026-01-26 16:51
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247548888&idx=1&sn=1bf3807617d6fbfd91d43b0d0bba031b&chksm=9b4b7f63ac3cf67552a225a490f44c2eea72fa6abdb6f0c71e8be6cf7e6f6c2db8fa616e33a5)

---
>
>
> 今天的绘图来看看 2022 年 8 月 10 号发表在 Nature 杂志上的一篇文献，标题为《Spatial multi-omic map of human myocardial infarction》， 这篇文献是一篇非常经典的空间转录组数据分析文章，今天绘制一个不同样本里细胞生态位不同比例的堆积柱状图~

图如下：图的含义非常好理解，跟不同样本里面不同细胞类型比例的含义差不多。

![文章图片 1](assets/005_绘制%20Nature%20同款空转细胞生态位堆积柱状图/001.png)

图注：

>
>
> Extended Data Fig. 3 \| Cell-type niches and spatially contextualized views analysis.  c, Cell-type niche compositions across patient sample

## 数据准备

这里使用了作者提供好的rds文件，下载地址：https://zenodo.org/records/6580069

下载好的在这里： https://pan.baidu.com/s/13i8gOruqXMrjHr2eFMsaXA?pwd=8yxd

### 数据读取

读取不同的rds对象

```r
rm(list=ls())
library(compositions)
library(tidyverse)
library(clustree)
library(Seurat)
packageVersion("Seurat")
library(scran)
library(cluster)
library(data.table)

## step0：输入数据准备 ----
## 读取空转数据
# recursive = T 是否递归搜索子目录
samples <- list.files("data/", pattern = "rds$", include.dirs = T,recursive = T, full.names = T)
samples

splist <- list()
for(i in samples) {
# i <- samples[1]
print(i)
  name <- gsub(".rds","",basename(i))
  object <- readRDS(file = i)
# object <- UpdateSeuratObject(object) # 如果出现下面的merge报错，就需要运行这个
  splist[[name]] <- object
}
splist
spatial <- merge(x = splist[[1]], y = splist[-1])
spatial
```

![文章图片 2](assets/005_绘制%20Nature%20同款空转细胞生态位堆积柱状图/002.png)

合并好了不同的seurat对象后，提取metadata信息：

```r
meta <- spatial@meta.data
head(meta)
table(meta$patient_region_id)
table(meta$celltype_niche)
```

![文章图片 3](assets/005_绘制%20Nature%20同款空转细胞生态位堆积柱状图/003.png)

### 计算每个样本中的细胞生态位比例：

核心代码：

`patient.prop <- as.data.frame(prop.table(stat,margin = 2)) # 按列计算比例`

```r
stat <- table(meta$celltype_niche, meta$patient_region_id)
stat
patient.prop <- as.data.frame(prop.table(stat,margin = 2)) # 按列计算比例
colnames(patient.prop) <- c("ctniche","patient","Proportion")
head(patient.prop) # 得到每一个patient中不同细胞亚群的相对比例
sum(patient.prop[patient.prop$patient=="control_P1",3]) # 看一个patient里面的不同ctniche比例是不是1
```

![文章图片 4](assets/005_绘制%20Nature%20同款空转细胞生态位堆积柱状图/004.png)

每个patient里面的不同细胞生态位的加和一定等于1，是个百分比。

## 开始绘图

依然使用ggplot2，非常简单。

先设置一下颜色和横轴的顺序（使用因子变量）

```r
# 设置堆积柱状图中细胞亚群的放置顺序，因子变量
patient.prop$patient <- factor(patient.prop$patient, levels=names(table(meta$patient_region_id)) )
patient.prop$ctniche # 这个已经是factor了

# 设置颜色
cols <- c("#d51f26","#272e6a","#208a42","#89288f","#f47d2b","#fee500","#8a9fd1","#c06cab","#d8a767")
names(cols) <- paste0("ctniche_",1:9)
cols
```

![文章图片 5](assets/005_绘制%20Nature%20同款空转细胞生态位堆积柱状图/005.png)

使用 Snipaste软件去文献里面提取的颜色，方法见：

[独家私藏秘技：如何获取高分文章中的图片配色？](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247540968&idx=1&sn=e6d61914bf98a2e5044c5fc5429039b5#wechat_redirect)

绘制图：

```r
# 绘图
head(patient.prop)

p <- ggplot(patient.prop,aes(patient,Proportion,fill=ctniche)) +
  geom_bar(stat = "identity",position = "fill") +
  xlab(label = "") +  ylab(label = "cell type proportion") +
  scale_fill_manual(values=cols) +
  theme_classic() +
  theme(
    axis.ticks.length = unit(0.2,'cm'),
    legend.position = "right",  # 设置图例位置
    legend.direction = "vertical",  # 设置图例方向
    legend.box = "vertical",  # 设置图例框的方向
    legend.text = element_text( size = 12, face = "plain",color = "black"),
    axis.line = element_line(linewidth = 1),     # 粗轴
    axis.ticks = element_line(linewidth = 1),      # 所有刻度线
    axis.title.y = element_text(size = 14),  # 修改x轴标题的字体大小
    axis.text.x = element_text(size = 11,angle = 45, hjust = 1),  # 修改x轴刻度标签的字体大小
    axis.text.y = element_text(size = 11)   # 修改y轴刻度标签的字体大小
  ) +
  guides(fill=guide_legend(title = NULL,ncol=1))
p
ggsave(filename = "figs3c.pdf", width = 10,height = 6,plot = p)
```

![文章图片 6](assets/005_绘制%20Nature%20同款空转细胞生态位堆积柱状图/006.png)

完美！

今天分享到这里~如果上面的内容对你有用，欢迎一键三连~

转发：

- [生信入门&数据挖掘线上直播课2026年1月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247547917&idx=1&sn=76afb50b6e9e433e3f2b3d039f72dac4#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
