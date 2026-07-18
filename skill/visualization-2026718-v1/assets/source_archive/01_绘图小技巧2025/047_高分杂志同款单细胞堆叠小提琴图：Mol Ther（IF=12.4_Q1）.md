# 高分杂志同款单细胞堆叠小提琴图：Mol Ther（IF=12.4/Q1）

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-04-14 12:51
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247540944&idx=1&sn=2155a2274a710a3eb1127ffc4bf491a9&chksm=9b4b606bac3ce97df8620f0acec5f47fe526201d6de5a76979f4a368fca566fdfa51cbdf61aa)

---
关于单细胞数据结果的美化，我们已经分享过好几篇：

- [Nat Commun同款山脊图：千里江山图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247540687&idx=1&sn=315b1f5757a97375a6425c3e751f7304&scene=21#wechat_redirect)

- [顶刊Cell杂志单细胞特征基因气泡图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247540219&idx=1&sn=99fddc26ccbd5ffe6640c09d94e987dd&scene=21#wechat_redirect)

- [展示你的特征基因：带"辣椒粉"的markers基因umap图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247539400&idx=1&sn=ffa29d61d95453199ad6157d743403d7&scene=21#wechat_redirect)

- [给你的单细胞umap图加个cell杂志同款的圈](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537290&idx=1&sn=ad76831349df67bb5236370dab088536&scene=21#wechat_redirect)

- [5种方式美化你的单细胞umap散点图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247536822&idx=1&sn=5f695d4ee6d8ba00a0961c02c4cf83bd&scene=21#wechat_redirect)

- [画个同款新奇的“Galaxy”星系UMAP图（Nat Immunol：IF27.8）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247538773&idx=1&sn=094b2cef83702267589de13dd50a0b58&scene=21#wechat_redirect)

**今天来看看如何使用堆叠小提琴图展示你的特征基因，这个需求在单细胞分析中也是非常常见。**图来自文献《Single-cell dissection of cellular and molecular features underlying mesenchymal stem cell therapy in ischemic acute kidney injury》，于2023年10月4号发表在Mol Ther（12.4/Q1）。

如下：

![文章图片 1](assets/047_高分杂志同款单细胞堆叠小提琴图：Mol%20Ther（IF=12.4_Q1）/001.png)

## 数据处理

文献中注释到了九种不同的细胞：

- **TECs**：Lrp2，tubular epithelial cells，肾小管上皮细胞：是肾小管的内衬细胞，位于肾单位的各个部分，包括近曲小管、髓袢和远曲小管等。这些细胞在肾脏的结构和功能中起着关键作用；

- **DT**：Slc12a3，distal tubular cells，远曲小管细胞，是肾小管远曲小管（Distal Convoluted Tubule，DCT）的内衬细胞。远曲小管位于肾小管的远端，紧接在致密斑（macula densa）之后，是肾单位的重要组成部分；

- **IC/PC**：Aqp2，Atp6v1g3，intercalated cells/principal cells，闰细胞/主细胞，闰细胞是肾小管集合管中的上皮细胞，主要分布在集合管的皮质和外髓层。它们在调节酸碱平衡、钾和氨的转运中起重要作用；主细胞是肾小管集合管中的主要上皮细胞类型，主要负责钠和水的重吸收；

- **LOH**：Slc12a1，loop of Henle，Henle袢是肾单位（nephron）的一部分，呈U形结构；

- **ENDO**：Emcn，endothelial cells；

- **MES**：Pdgfrb，mesangial cells，系膜细胞，是肾小球中的基质细胞，位于毛细血管袢之间，与肾小球基底膜紧密相连；系膜细胞通常呈星形或梭形，具有丰富的细胞器，如线粒体和内质网；

- **T cells**：Cd3d；

- **B cells**：Cd79a；

- **myeloid cells**：Cd68。

![文章图片 2](assets/047_高分杂志同款单细胞堆叠小提琴图：Mol%20Ther（IF=12.4_Q1）/002.png)

数据读取见之前的推文：[创建Seurat对象时忽略的两个参数竟然有这样的功能？](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247539626&idx=3&sn=3777fe488001afe9e6e72c824367a7fa&scene=21#wechat_redirect)

数据注释见推文：[单细胞数据重新挖掘会有什么意外惊喜吗？（IF=12.4/Q1）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247540930&idx=1&sn=609ca51dad791c1691cf08b4bc1048f7&scene=21#wechat_redirect)

如果你想要同款数据，可以联系微信：Biotree123 或者百度网盘：链接: https://pan.baidu.com/s/1l8fMsokPOoo_sluGf4in4g?pwd=4ax2 提取码: 4ax2

当然任何一个做了注释或者分群的单细胞数据seurat对象都可以，再加上自己精心挑选的想展示的marker基因，这里的marker基因为每种细胞亚群中特异性表达的，也可以是其他的你想要展示的基因~

## 开始绘图

使用的是seurat包自带的函数`VlnPlot`，这个函数可以绘制一个基因或者多个基因，如果想展示堆叠效果，设置 参数：`stack = TRUE`

```r
rm(list=ls())
library(Seurat)
library(ggplot2)
library(qs)

###### step4:  看标记基因库 ######
# 原则上分辨率是需要自己肉眼判断，取决于个人经验
# 为了省力，我们直接看  0.1和0.8即可
sce.all.int <- qread("2-harmony/sce.all_int.qs")
load("3-check-by-0.3/phe.RData")
sce.all.int <- AddMetaData(sce.all.int, metadata = phe)
Idents(sce.all.int) <- "celltype"
table(Idents(sce.all.int))

# TECs     Myeloid         LOH          DT        ENDO Neutrophils       IC_PC          NK           T         MES           B
# 63167       19755        5180        4124        2960        1952        1499        1386        1199        1020         820

## 小提琴图
################################ 本数据marker：OMIX004421
cell_types <- list(
  TECs = c("Lrp2"),
  LOH = c("Slc12a1"),
  DT = c("Slc12a3"),
  IC_PC = c("Aqp2","Atp6v1g3"),
  MES = c("Pdgfrb"),
  ENDO = c("Emcn"),
  T = c("Cd3d"),
  B = c("Cd79a"),
  Neut = c("S100a9"),
  Myeloid = c("Cd68")
)

# Print the list to verify
print(cell_types)

# stack = TRUE, 堆叠小提琴图
VlnPlot(sce.all.int, unlist(cell_types), stack = TRUE, sort = TRUE)
```

![文章图片 3](assets/047_高分杂志同款单细胞堆叠小提琴图：Mol%20Ther（IF=12.4_Q1）/003.png)

## 美化一下

美化的地方有：换个颜色，使用 Snipaste 从文献中获取同款颜色，然后对小提琴做一下排序，可以像文献中那样做到基因表达实拍在一个对象线上，更具有视觉上的引导效果。

如果你想旋转一下图的方向设置：`flip = TRUE` 即可

```r
# 换个颜色，使用 Snipaste 从文献中获取同款颜色
colors <- c("#0069db", "#b80000", "#00a700", "#6858c5","#6858c5", "#fd8c00", "#71c3fb", "#89194a", "#007a0d","#ff7f00", "#235a8a")

# 对小提琴做一下排序
sce.all.int$celltype <- factor(sce.all.int$celltype,
                               levels = c("TECs","LOH","DT","IC_PC","MES","ENDO","T","B","Neutrophils","NK","Myeloid"))
Idents(sce.all.int) <- "celltype"

p1 <- VlnPlot(sce.all.int, unlist(cell_types), stack = TRUE, sort = FALSE, cols = colors) +
  theme(legend.position = "none")
p1
ggsave(filename = "vlnplot_stack.pdf", width = 5.5, height = 4.5, plot = p1)
```

结果如下：

![文章图片 4](assets/047_高分杂志同款单细胞堆叠小提琴图：Mol%20Ther（IF=12.4_Q1）/004.png)

#### 学废了吗~

### 文末友情宣传

- [生信入门&数据挖掘线上直播课4月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247539788&idx=1&sn=62a09c7af6373658bf81c149eb0b4026&scene=21#wechat_redirect)

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](http://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247524148&idx=1&sn=7806da6feb41a36493c519c1cfc1d3ac&chksm=9b4bdf8fac3c569960369602f1ef26639cb366b250f233b2297d1f059471c0458335bfc0b829&scene=21#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247535760&idx=2&sn=1e02a2e982a046ecf6389231e6768d5b&scene=21#wechat_redirect)

<!-- wechat-article-fetcher: complete -->
