# Nature Genetics杂志特别版单细胞marker基因气泡图

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-11-03 23:24
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546635&idx=1&sn=8a9fbdb461f7c704e07e61f054b3e200&chksm=9b4b77b0ac3cfea6cefc78cbecc2c36af1e5763c91a4b7c5e882b02550a29a4007eaa36e8b57)

---
> 单细胞的marker基因气泡图，我们前面已经绘制过几个，今天的这个还是来自王凌华团队的最新文献，来自**2025年10月21号发表在Nature Genetics杂志**上，标题为《Multi-modal spatial characterization of tumor immune microenvironments identifies targetable inflammatory niches in diffuse large B cell lymphoma》。这个图左边有带圈的点和x坐标轴有阴影区域，使得它比一般的气泡图又高档了一个档次！来看看~

专辑里面的气泡图：

- [Nature杂志同款高颜值单细胞基因表达气泡图（王凌华团队）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247545796&idx=1&sn=bb7ae79db9b3c3a0542187e1b6b31bc5#wechat_redirect)

- [高分杂志同款cellchat细胞通讯结果气泡图绘制（IF=25.083）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247544734&idx=1&sn=afb7ead473e91445b695efea54807327#wechat_redirect)

- 绘图小技巧进群方式：添加微信 Biotree123，发18.8的进群门票，可以在群里交流学习绘图，并发布许愿绘图~

Fig2中的e图：展示的是空间转录组数据中7个细胞生态位CN1-7中每个生态位里面不同细胞亚群的DEGs基因表达气泡图。

![文章图片 1](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/001.png)

图注：

> Fig. 2: Cellular neighborhood structures and unique spatial niches in B cell lymphoma.  f.The representative DEGs in each spatial niche.

## 数据背景

作者利用78例大B细胞淋巴瘤切除活检样本及5例对照组织（4例扁桃体、1例淋巴结）构建了六组组织微阵列。作者抽取了部分示例数据以及代码放在github上面：https://github.com/Coolgenome/Lymphoma-spatial

下载好的： 链接: https://pan.baidu.com/s/1ISXLXLEmgdwtBrLTTdkPOQ?pwd=b49k 提取码: b49k

详细介绍见：[一行代码给你的单细胞UMAP图添加左下角小箭头坐标轴](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546483&idx=1&sn=acea4ccfb046a373c767523ccc41a266#wechat_redirect)

## 数据处理

### 1.先读取绘图数据

需要的是一个数据框，每一个CN中不同细胞类型的组成：

```r
### Figure 2 ###
rm(list=ls())
### load essential packages ###
library(Seurat)
library(tidyverse)
library(dplyr)
library(ggplot2)
#devtools::install_github("junjunlab/jjAnno")
library(jjAnno) # 对ggplot2添加图形区域外的注释如点或者注释条

### Figure 2d-f ###
# k-means clustering based on neighborhood matrix to obtain 7 unique spatial cellular niches (CN).
# Here we directly provide the results with CN allocation of cells.
spatial_niche <- readRDS("./demo_data/spatial_niche.rds")
head(spatial_niche)
table(spatial_niche$CN_cluster)
```

niche数据为两列：第一列是细胞barcode，第二列是每个细胞所属的CN类型，总共有CN1-7七大类：

![文章图片 2](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/002.png)

接着是细胞亚群分类信息：

```r
### Data reading in, preprocessing, cleaning, and cell type and state identification are described in the separate script Preprocessing.r
### Here for demonstrating the workflow, we directly provide the demo data, including count matrix and metadata. The processing of demo data is described in Figure 1.r
### load data object ###
### This is saved from the step of Figure 1b.
Lymphoma_data <- readRDS("./demo_data/Lymphoma_data.rds")
Lymphoma_data
head(Lymphoma_data@meta.data)
```

需要其中的cell_state列，共19中细胞类型：

![文章图片 3](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/003.png)

将上面两种信息合并在一起：

```r
# DEGs among CNs (Figure 2f) #
spatial_niche <- column_to_rownames(spatial_niche, var="Barcode")
Lymphoma_data <- AddMetaData(Lymphoma_data, spatial_niche)
head(Lymphoma_data@meta.data)
Lymphoma_data$CN_cluster <- factor(Lymphoma_data$CN_cluster, levels =c(paste0("CN",7:1)) )
```

Lymphoma_data@meta.data 数据结构为：

![文章图片 4](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/004.png)

### 2.提取DEGs基因向量

从作者的代码里面搞来的，或者可以使用deepseek从图片中提取。我最近开始由kimi转向deepseek了，初步感觉deepseek要比kimi好用呢？kimi最近动不动就给我说：刚刚跟我聊的人有点多，我现在有点累了，你稍后再来！

我：一脸懵，使用的人太多了吗？

```r
CN_marker <- c("CD3D","CD3E","CD2","CD8A","GZMB","GZMK","NKG7","PRF1","GZMH","CXCL9","CXCL10","CCL5","CCL2","MZB1","IGHG1",
               "IGHG2","IGKC","CD68","C1QA","C1QB","C1QC","LYZ","APOE","APOC1","S100A9","COL1A1","COL1A2","COL3A1","FN1","DCN",
               "ACTA2","TIMP1","COL6A1","COL6A2","CD79A","MS4A1","CD19","TCL1A","IGHM","CD37","STMN1","TYMS","TOP2A","BCL2",
               "BTK","SYK","CD24","CD52")
```

## 开始绘图

### 作者的代码：

```r
p <- DotPlot(Lymphoma_data,features = CN_marker, scale.by = "size", group.by = "CN_cluster", scale.max = 50, scale = 10, col.max=1.5)+
    RotatedAxis()+
    scale_color_gradientn(values = seq(0,1,0.1),colours = c("#4575b4","#abd9e9","#e0f3f8","#ffffbf","#fdae61","#d73027","#800026"))

p
```

额，作者只放了一个半成品的代码：

![文章图片 5](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/005.png)

### 我来修饰一下：

先把坐标轴名字等细节改一下：

```r
p1 <- p +  scale_y_discrete(name = "", labels = rev(c("CN1_T", "CN2_PC", "CN3_Myeloid","CN4_Stromal","CN5_Tumor-B",
                                                "CN6_Diffuse","CN7_Mixe"))) +
  xlab(label = NULL)
p1
```

![文章图片 6](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/006.png)

现在使用老俊俊的jjAnno对ggplot2添加图形区域外的注释如点或者注释条。

添加坐标的点：

```r
# add right
annoPoint(object = p1,
          annoPos = 'left',
          yPosition = c(1:7))
```

好现在报错了：

![文章图片 7](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/007.png)

在上一次的教程中：[Nature杂志同款高颜值单细胞基因表达气泡图（王凌华团队）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247545796&idx=1&sn=bb7ae79db9b3c3a0542187e1b6b31bc5#wechat_redirect)，我的ggplot2还是3.5.2，现在更新到了4.0.0。然后很多人反馈这个图不能复现出来，时间也是正好卡在ggplot2发了重大更新的时候。

我现在本地安装 3.5.2：

```r
# 检查包的版本
packageVersion("ggplot2")
# 安装3.5.2版本
remotes::install_version("ggplot2", version = "3.5.2",force = T)
```

还是提示错误：

![文章图片 8](assets/012_Nature%20Genetics杂志特别版单细胞marker基因气泡图/008.png)

额，老俊俊已经去开心地开发其他的包去了，我今天就发这个跟作者一样的半成品吧，我的去看老俊俊的源码了（前面别人不能复现图的时候也有一些因为ggplot2版本原因报错，没有去看现在就是回旋镖！）。

友情转发：

- [生信入门&数据挖掘线上直播课11月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546276&idx=1&sn=b2a133dd0ff3c571eef5bfbe5dd82c59#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
