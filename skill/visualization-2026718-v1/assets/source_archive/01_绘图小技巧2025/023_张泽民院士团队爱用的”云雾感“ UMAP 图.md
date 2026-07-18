# 张泽民院士团队爱用的”云雾感“ UMAP 图

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-09-02 22:28
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247545487&idx=1&sn=497b176fdc10855214d36d2a00413be5&chksm=9b4b7234ac3cfb226842e471118d8284472fb1953fe60a7f2b1fa57cf7c792248178ba60c581)

---
> 最近我们生信入门班的学员问起了一个大佬的文章，想知道里面的那种带有“云里雾里”感的 UMAP 如何实现！我看了下这个文献，然后找了找之前收集的张泽民院士团队的单细胞文章，发现里面全是这种风格，配色也好看，现在分享给大家！欢迎大家一键三连~

图来自国际期刊《cell》上以Resource形式在线发表的题为《A single-cell atlas reveals immune heterogeneity in anti-PD-1-treated non-small cell lung cancer》的研究论文。曾老板在昨天也进行了介绍：[用R绘图之前可以让ai先给出草稿代码](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247536629&idx=1&sn=74acdcba920c2a7437eefe5d762c6482#wechat_redirect)

![文章图片 1](assets/023_张泽民院士团队爱用的”云雾感“%20UMAP%20图/001.png)

当然是给出来全部的数据和代码啦：

> https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243013

```r
GSE243013_NMF_all_group_5.csv.gz 1.1 Kb (ftp)(http) CSV
GSE243013_NSCLC_immune_scRNA_counts.mtx.gz 6.6 Gb (ftp)(http) MTX
GSE243013_NSCLC_immune_scRNA_metadata.csv.gz 38.8 Mb (ftp)(http) CSV
GSE243013_RAW.tar 516.4 Mb (http)(custom) TAR (of TAR)
GSE243013_T_with_TCR_annotation.csv.gz 15.2 Mb (ftp)(http) CSV
GSE243013_UMAP_info.tar.gz 20.6 Mb (ftp)(http) TAR
GSE243013_barcodes.csv.gz 6.4 Mb (ftp)(http) CSV
GSE243013_genes.csv.gz 111.5 Kb (ftp)(http) CSV
```

## 绘图

绘图的代码其实非常简单，先读取数据：

```r
###
### Create: Jianming Zeng
### Date:  2023-12-31
### Email: jmzeng1314@163.com
### Blog: http://www.bio-info-trainee.com/
### Forum:  http://www.biotrainee.com/thread-1376-1-1.html
### CAFS/SUSTC/Eli Lilly/University of Macau
### Update Log: 2023-12-31   First version
### Update Log: 2024-12-09   by juan zhang (492482942@qq.com)
###
rm(list=ls())
options(stringsAsFactors = F)
library(ggsci)
library(dplyr)
library(future)
library(Seurat)
library(clustree)
library(cowplot)
library(data.table)
library(ggplot2)
library(patchwork)
library(stringr)
library(qs)
library(Matrix)

# 创建目录
getwd()
gse <- "GSE243013"
dir.create(gse)

# 下载raw文件夹
if(F) {
# https://mp.weixin.qq.com/s/uEso7yRZB300MnMhSpXH_Q
  library(GEOquery)
# filter_regex: 指定下载的
# fetch_files = F, 返回下载链接
  getGEOSuppFiles(gse,fetch_files = F)[,2]
}

up_pos <- rio::import('GSE243013/B_UMAP.csv' ,data.table = F)
head(up_pos)

meta  <- rio::import('GSE243013/GSE243013_NSCLC_immune_scRNA_metadata.csv.gz')
head(meta)

df <- merge(up_pos,meta,by='cellID')
colnames(df)
df <- df[,c(2,3,11)]
colnames(df) <- c('UMAP_1','UMAP_2','Cluster')
df$label <- "B cells"
head(df)
```

![文章图片 2](assets/023_张泽民院士团队爱用的”云雾感“%20UMAP%20图/002.png)

使用ggplot2绘图，秘诀在于： geom_point(size = 0.03,shape = 16, stroke = 0)

```r
color <- c("#919ac2","#ffac98","#70a4c8","#a5a9af","#63917d","#dbd1b4","#6e729a","#9ba4bd","#c5ae5f","#b9b8d6")

library(ggh4x)
p <- ggplot(df, aes(x = UMAP_1, y = UMAP_2, color = Cluster)) +
  geom_point(size = 0.03,shape = 16, stroke = 0) +
  scale_color_manual(values = color) +
  facet_grid(~label) +
  theme_classic() +  # 使用简洁主题
  theme( plot.background = element_blank(),  # 移除背景
         panel.grid.major = element_blank(),  # 移除主要网格线
         panel.grid.minor = element_blank(),  # 移除次要网格线
         margin = margin(),  # 增加顶部边距
         axis.title.x = element_blank(),  # 移除x轴标题
         axis.title.y = element_blank(),  # 移除y轴标题
         axis.text = element_blank(),  # 移除坐标轴刻度标签
         axis.ticks = element_blank(),  # 移除坐标轴刻度线
         axis.line = element_line(colour = "black", size = 0.3,
                                  arrow = arrow(length = unit(0.1, "cm"))),  # 加粗坐标轴并添加箭头
         strip.background = element_rect(fill = '#e6bac5',color=NA),
         strip.placement = 'outside',
         strip.text = element_text(size = 8),
         legend.position = "none",
         aspect.ratio = 1) +
  scale_x_continuous(limits = c(min(df$UMAP_1), max(df$UMAP_1)) ) +  # 设置x轴范围
  scale_y_continuous(limits = c(min(df$UMAP_2), max(df$UMAP_2)) )   # 设置y轴范围
p

ggsave(filename = "BCells_Umap.png",height = 2,width = 2,plot = p,dpi = 300,bg = "white")
```

![文章图片 3](assets/023_张泽民院士团队爱用的”云雾感“%20UMAP%20图/003.png)

## 图例绘制

这里图例单独绘制：

```r
ggplot(data = df, aes(x = UMAP_1, y = UMAP_2, color = Cluster)) +
  geom_point(size = 0, shape = 16,stroke = 0) +
  theme_void()+
  scale_color_manual(values = color, name = '') +
  theme( aspect.ratio = 1,
    legend.position = 'bottom',
    plot.margin = margin(0,0,0,0) ) +
  guides(color = guide_legend( ncol = 2, override.aes = list(size = 2, alpha = 1) )) +
  theme(legend.text = element_text(size = 5),
        legend.spacing.y = unit(0, 'cm'),
        legend.key.height = unit(0,"cm"),
        legend.box.spacing = unit(0, 'cm'))

ggsave( "FigureS1C_legend.pdf", width = 3.5, height = 6, dpi = 500 )
```

![文章图片 4](assets/023_张泽民院士团队爱用的”云雾感“%20UMAP%20图/004.png)

注意上面图片的保存格式，最后将两个图组合在一起就可以啦！

多个亚群都绘制然后用PS软件拼装在一起！

此外，我们的生信入门班每月都有一期，最近一期在9月8号开课，[生信入门&数据挖掘线上直播课9月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247545469&idx=1&sn=a6531c8c7f11db51a88c23525cb322d1#wechat_redirect)

## 报名咨询

![文章图片 5](assets/023_张泽民院士团队爱用的”云雾感“%20UMAP%20图/005.png)

## 招生对象

**「生信入门班：」**生物、医学、农学等方向需要学习生物信息学数据分析的人，本科、硕博、生信相关公司职员、医生等。

**「数据挖掘班：」**医学、网络药理学等方向需要利用生物信息学工具挖掘公共数据以及做下游分析的人，往期学员以医学生、医生为主。

**「选择困难症患者指南：」**非医学方向直接选择生信入门班（3699元）。 医学相关方向两个课程均适用，按需选择： 如果你只需要挖掘公共数据，或者从公司提供的表达矩阵开始做后续分析，可以选择数据挖掘班（2899元）。 如果你需要自己做上游+下游分析，选择生信入门班。 如果你还是选择困难，两个都要，联合报名优惠价4199元。

**「注：」**两个班都有R语言课程，是完全一致的；也都有下游分析内容，数据挖掘班的下游分析有更多的医学方向针对性，比如生存分析，数据挖掘文章图表复现等。

## 关于答疑

答疑我们诚意十足，真心满满，典型的问题我们会给出详细的答疑，之前答疑合集：

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

- [马拉松授课互动答疑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3398473750701146113#wechat_redirect)，里面包含了我们整理的每一期超详细的答疑

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

## 培训内容

# ![图片](assets/023_张泽民院士团队爱用的”云雾感“%20UMAP%20图/006.png)

# 快来上车，风里雨里就等你！

<!-- wechat-article-fetcher: complete -->
