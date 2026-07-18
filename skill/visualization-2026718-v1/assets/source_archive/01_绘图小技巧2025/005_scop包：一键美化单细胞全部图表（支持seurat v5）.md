# scop包：一键美化单细胞全部图表（支持seurat v5）

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-12-12 22:25
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247547644&idx=1&sn=99621dde94be146b04aef77c6d6aa97a&chksm=9b4b7a47ac3cf351f26a5d4b100ba0cd415eecaaef92aee5141841d5d44ddcafe388b37ff091)

---
> [前面在 5种方式美化你的单细胞umap散点图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247536822&idx=1&sn=5f695d4ee6d8ba00a0961c02c4cf83bd#wechat_redirect) 一文中介绍过SCP包，非常好用，但是呢作者后来不更新了，目前只支持 seurat v4的版本，然后就有一个人按耐不住了，他在SCP的基础上，更新了这个包，使其变的支持seurat v5了！下面就来看看~

## 安装

https://github.com/mengxu98/scop

```r
## 使用西湖大学的 Bioconductor镜像
options(BioC_mirror="https://mirrors.westlake.edu.cn/bioconductor")
options("repos"=c(CRAN="https://mirrors.westlake.edu.cn/CRAN/"))
if (!require("pak", quietly = TRUE)) {
  install.packages("pak")
}
pak::pak("mengxu98/scop")


## 如果上面安装不上，请下载到本地后安装，命令如下
devtools::install_local("scop-main.zip",upgrade ="never" )

library(scop)
```

scop-main.zip链接： 链接: https://pan.baidu.com/s/1QfCQqN76TvB6B86wnWSQ8A?pwd=8uvc 提取码: 8uvc

## 示例数据

任何一个在seurat v5版本下生成的seurat对象都可以，这里就用官网的好了：

数据来源：https://journals.biologists.com/dev/article/146/12/dev173849/19483/Comprehensive-single-cell-mRNA-profiling-reveals-a

```r
library(Seurat)
packageVersion("Seurat")
library(scop)
data(pancreas_sub)
pancreas_sub <- NormalizeData(pancreas_sub)
head(pancreas_sub@meta.data)
print(pancreas_sub)

# An object of class Seurat
# 47994 features across 1000 samples within 3 assays
# Active assay: RNA (15998 features, 0 variable features)
# 1 layer present: counts
# 2 other assays present: spliced, unspliced
# 2 dimensional reductions calculated: X_pca, X_umap
```

## 来看看美图

### 一键添加左下角箭头

```r
CellDimPlot(
  srt = pancreas_sub,
  group.by = c("CellType", "SubCellType"),
  reduction = "UMAP",
  theme_use = "theme_blank"
)
```

![文章图片 1](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/001.png)

**干净清爽！**

如果你还希望手搓左下角箭头，看看这个：

R版本手搓：[一行代码给你的单细胞UMAP图添加左下角小箭头坐标轴](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546483&idx=1&sn=acea4ccfb046a373c767523ccc41a266#wechat_redirect)

python版本手搓：[python版本给单细胞umap添加左下角小箭头](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546890&idx=1&sn=8d08e66e866b4e41f82c7f991e320148#wechat_redirect)

还有一些其他的主题：

```r
CellDimPlot(pancreas_sub, group.by = "CellType", reduction = "UMAP")
CellDimPlot(pancreas_sub, group.by = "CellType", reduction = "UMAP",theme_use = "theme_void")
CellDimPlot(pancreas_sub, group.by = "CellType", reduction = "UMAP",theme_use = "theme_scop")
CellDimPlot(pancreas_sub, group.by = "CellType", reduction = "UMAP",theme_use = "theme_linedraw")
CellDimPlot(pancreas_sub, group.by = "CellType", reduction = "UMAP",theme_use = "theme_light")
CellDimPlot(pancreas_sub, group.by = "CellType", reduction = "UMAP",theme_use = "theme_dark")
```

这个里面：theme_void 也挺好用的，适合拼图的时候用。

![文章图片 2](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/002.png)

### 绘制多个marker基因

这个图也是很多高分文献里面经常看到的美图：

```r
FeatureDimPlot(
  srt = pancreas_sub,
  features = c("Sox9", "Neurog3", "Fev", "Rbp4"),
  reduction = "UMAP",
  theme_use = "theme_blank"
)
```

![文章图片 3](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/003.png)

还可以设置行列：

```r
FeatureDimPlot(
  srt = pancreas_sub,
  features = c("Sox9", "Neurog3", "Fev", "Rbp4"),
  reduction = "UMAP",
  theme_use = "theme_blank",ncol = 4
)
```

一行四列：

![文章图片 4](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/004.png)

### 基因共表达

之前还没发现这个：多个基因在同一个umap上面的可视化

```r
FeatureDimPlot(
  srt = pancreas_sub,
  features = c("Sox9", "Neurog3", "Fev", "Rbp4"),
  compare_features = TRUE,
  label = TRUE,
  label_insitu = TRUE,
  reduction = "UMAP",
  theme_use = "theme_blank",pt.size = 2
)
```

![文章图片 5](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/005.png)

### marker气泡

```r
ht <- GroupHeatmap(
  srt = pancreas_sub,
  features = c(
    "Sox9", "Anxa2", # Ductal
    "Neurog3", "Hes6", # EPs
    "Fev", "Neurod1", # Pre-endocrine
    "Rbp4", "Pyy", # Endocrine
    "Ins1", "Gcg", "Sst", "Ghrl"# Beta, Alpha, Delta, Epsilon
  ),
  group.by = c("SubCellType"),
  heatmap_palette = "YlOrRd",
# cell_annotation = c("Phase", "G2M_score", "Cdh2"),
  cell_annotation_palette = c("Dark2", "Paired", "Paired"),
#show_row_names = TRUE,
  row_names_side = "left",
  add_dot = TRUE,
  add_reticle = TRUE
)
print(ht$plot)
```

![文章图片 6](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/006.png)

### marker基因小提琴图

```r
# scop包
pancreas_sub <- NormalizeData(pancreas_sub)
FeatureStatPlot(
  srt = pancreas_sub,
  group.by = "SubCellType",
  #bg.by = "celltype",
  stat.by = c("Sox9", "Neurog3", "Fev", "Rbp4"),
  add_box = TRUE,
)
```

![文章图片 7](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/007.png)

### 三维UMAP图

```r
CellDimPlot3D(
  srt = pancreas_sub,
  group.by = "SubCellType"
)
```

![文章图片 8](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/008.png)

### 它还支持其他很多有意思的

如差异分析：

```r
pancreas_sub <- RunDEtest(
  srt = pancreas_sub,
  group_by = "CellType",
  fc.threshold = 1,
  only.pos = FALSE
)
VolcanoPlot(
  srt = pancreas_sub,
  group_by = "CellType"
)
```

![文章图片 9](assets/005_scop包：一键美化单细胞全部图表（支持seurat%20v5）/009.png)

但是呢这个代码会报错，现在github上面的提问也没有人回答了，我想这个包功能挺好，我打算后面去维护看看，我现在已经fork一份到我的github上面去了，大家如果有使用问题作者没有更新，可以来提交 Issues 。

> https://github.com/zhangj1115/scop_v1

今天分享到这~

转发：

- [生信入门&数据挖掘线上直播课12月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247547012&idx=1&sn=f55923d9a6d9e04c3e923c2a3cae6e56#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
