# 画个同款新奇的“Galaxy”星系UMAP图（Nat Immunol：IF27.8）

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-02-24 12:16
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247538773&idx=1&sn=094b2cef83702267589de13dd50a0b58&chksm=9b4b18eeac3c91f8580c3a250080821e728175b503ece22ec3e66e10a36b5ad60463d48e58f5)

---
前面我们已经介绍了如何在umap图上加圈：[给你的单细胞umap图加个cell杂志同款的圈](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537290&idx=1&sn=ad76831349df67bb5236370dab088536&scene=21#wechat_redirect)，以及绘制星系umap图：[5种方式美化你的单细胞umap散点图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247536822&idx=1&sn=5f695d4ee6d8ba00a0961c02c4cf83bd&scene=21#wechat_redirect)，那两者组合起来呢？今天学习的这个好看的图来自文献《**The aged tumor microenvironment limits T cell control of cancer**》，**于2024年6月25日发表在Nat Immunol杂志上（IF27.8）**。如下：

颜色的深浅表示细胞密度，圈内为不同的细胞类型，左边为年轻组，右边为老年组，可以看出 yong 和 old组两种截然不同的细胞浸润模式。

![文章图片 1](assets/057_画个同款新奇的“Galaxy”星系UMAP图（Nat%20Immunol：IF27.8）/001.png)

图注：

>
>
> Fig. 1 ∣. Aging promotes tumor growth and alters CD8+ T cell fate and effector function. . e, Galaxy plots depicting the cell density in UMAP space for tumor-infiltrating CD8+ T cells from young (left) and aged (right) tumor-bearing mice.  Cooler colors indicate low density, and warmer colors indicate high density. The relative proportion of CD8+ T cells from young (blue, n = 5) and aged (red, n = 5) tumors within TProg, TTerm, dividing T (TDivi) and TTAD cell clusters is shown。

## 示例数据

使用的数据还是自 **GSE128531** 数据注释后的seurat对象，你自己用的时候可以使用任何一个经过了注释后的seurat对象。

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
library(COSG)
library(harmony)
library(ggsci)
library(dplyr)
library(future)
library(Seurat)
library(clustree)
library(cowplot)
library(data.table)
library(dplyr)
library(ggplot2)
library(patchwork)
library(stringr)
library(qs)

# 导入数据
sce.all.int <- readRDS('2-harmony/sce.all_int.rds')
sp <- 'human'
head(sce.all.int@meta.data)
load("phe.Rdata")
head(phe)
sce.all.int <- AddMetaData(sce.all.int, metadata = phe)

Idents(sce.all.int) <- "celltype"
```

## 先画银河中星系

用的 ggpointdensity 包，绘制不同的细胞密度：[5种方式美化你的单细胞umap散点图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247536822&idx=1&sn=5f695d4ee6d8ba00a0961c02c4cf83bd&scene=21#wechat_redirect)

```r
library(ggpointdensity)
# 提取数据
# dat <- Embeddings(sce.all.int, reduction = "umap")
# head(dat)

dat <- FetchData(object=sce.all.int, vars=c("umap_1","umap_2","celltype"))
head(dat)

p <- ggplot(data = dat, mapping = aes(x = umap_1, y = umap_2)) +
  geom_pointdensity() +
  scale_color_viridis_c(option="inferno", alpha = 0.4) +
  theme_classic(base_size = 15)
p
```

结果如下：

![文章图片 2](assets/057_画个同款新奇的“Galaxy”星系UMAP图（Nat%20Immunol：IF27.8）/002.png)

## 添加银河黑暗背景

这里简单的调整ggplot主题：

```r
p1 <- p +
  labs(color='Density') +  # 设置图例标题
  theme(
    panel.background = element_rect(fill = "black", color = "black"),  # 设置坐标轴内区域背景颜色为黑色
    plot.background = element_rect(fill = "white", color = "white"),  # 设置整个图形背景颜色为白色
    panel.grid.major = element_blank(),  # 去掉主要的网格线
    panel.grid.minor = element_blank(),  # 去掉次要的网格线
    axis.line = element_line(color = "white"),  # 设置坐标轴线颜色为白色
    axis.text = element_text(color = "white"),  # 设置坐标轴文本颜色为白色
    axis.ticks = element_line(color = "white"),  # 设置坐标轴刻度颜色为白色
    axis.title = element_text(color = "white"),  # 设置坐标轴标题文本颜色为白色
    legend.background = element_blank(),  # 设置图例背景为透明
    legend.key = element_blank(),  # 设置图例键为透明
    legend.text = element_text(color = "white"),  # 设置图例文本颜色为白色
    legend.title = element_text(color = "black"))  # 设置图例标题文本颜色为白色

p1
```

结果如下：

![文章图片 3](assets/057_画个同款新奇的“Galaxy”星系UMAP图（Nat%20Immunol：IF27.8）/003.png)

## 加圈圈住

上次介绍的办法：mascarade 包，[给你的单细胞umap图加个cell杂志同款的圈](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537290&idx=1&sn=ad76831349df67bb5236370dab088536&scene=21#wechat_redirect)

```r
# 加圈
library(mascarade)

# 制作masktable
# smoothSigma = 0.05：控制加圈的平滑成都，值越大加的圈越平滑
# minDensity ：控制 加圈的松紧成都，值越小，加的圈边界与umap散点距离越大越宽松
maskTable <- generateMask( dims=dat[,1:2], cluster=dat$celltype, minDensity = 15,smoothSigma = 0.1 )
class(maskTable)
dim(maskTable)
head(maskTable)

p2 <- p1 +
  geom_path(data=maskTable, aes(group=group),linewidth=0.6,linetype = 2, colour = "white")
p2
ggsave(filename = "Galaxy_UMP.pdf", width = 7.8, height = 6.5, plot = p2)
```

结果如下：

![文章图片 4](assets/057_画个同款新奇的“Galaxy”星系UMAP图（Nat%20Immunol：IF27.8）/004.png)

## PPT修饰

这里没有找到很好的办法加上细胞标签，用ppt好了，最终结果如下：

![文章图片 5](assets/057_画个同款新奇的“Galaxy”星系UMAP图（Nat%20Immunol：IF27.8）/005.png)

完美~，绘图小技巧开了新群，感兴趣的可以进：[绘图小技巧2025交流群](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247538699&idx=1&sn=871cb62f043fc30e1996066dc50430dd&scene=21#wechat_redirect)。

### **文末友情宣传**

- [生信入门&数据挖掘线上直播课3月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247538467&idx=1&sn=aa5500b24a92b86355c242d02e742f1b&scene=21#wechat_redirect)

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](http://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247524148&idx=1&sn=7806da6feb41a36493c519c1cfc1d3ac&chksm=9b4bdf8fac3c569960369602f1ef26639cb366b250f233b2297d1f059471c0458335bfc0b829&scene=21#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247535760&idx=2&sn=1e02a2e982a046ecf6389231e6768d5b&scene=21#wechat_redirect)

<!-- wechat-article-fetcher: complete -->
