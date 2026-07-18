# 顶刊杂志同款CD8+ T cells亚群signature score的umap图绘制（IF=58.7）

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-06-24 23:21
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247543628&idx=1&sn=744ce66821f9501950c357b401ac9129&chksm=9b4b6bf7ac3ce2e1b61e545d1b8dece46706b53da5445585a7d7ab56e86db8e215824aba8cb1)

---
> 收到我们生信入门班的一个学员求助，希望能看看下面这篇高分文献中的图怎么分析和绘制！既然是学员的请求，当然马上开干！
>
> \
>
> 此外，我们生信技能树**每个月都有一期带领初学者，0基础的生信入门培训，会有各种贴心的答疑，最新一期在7月3号**，感兴趣的可以去看看呀：[7月3日开课：生信入门&数据挖掘线上直播课7月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247543525&idx=1&sn=14058118935bd7393156b1d292dca8f9#wechat_redirect)

这幅图来自**2023年5月29号发表在Nature Medicine杂志（IF=58.7）**上的文献，标题为《Pan-cancer T cell atlas links a cellular stress response state to immunotherapy resistance》。主要展示了CD8+ T cells亚群中不同的基因集打分umap图展示：

![文章图片 1](assets/035_顶刊杂志同款CD8+%20T%20cells亚群signature%20score的umap图绘制（IF=58.7）/001.png)

图注：

> Fig. 2 \| Transcriptional diversity of CD8+ T cells. f, Expression of four representative gene signatures selected from e.
>
> note: curated gene signatures (Fig. 2e and Supplementary Table 4)

### 示例数据

因为这里只是为了展示打分技巧不涉及结果解读，所以就用经典的单细胞示例数据 pbmc3k 吧：

```r
rm(list = ls())
library(Seurat)
# install.packages('devtools')
# devtools::install_github('satijalab/seurat-data')
library(SeuratData) #加载seurat数据集
getOption('timeout')
options(timeout=10000)

## 加载数据
# InstallData("pbmc3k")
data("pbmc3k")
sce <- pbmc3k.final
sce <- UpdateSeuratObject(sce)
table(Idents(sce))
DimPlot(sce,label = T)
```

![文章图片 2](assets/035_顶刊杂志同款CD8+%20T%20cells亚群signature%20score的umap图绘制（IF=58.7）/002.png)

刚刚整理了一下这篇文献中使用的  gene signatures，见稿子：[CNS大刊超爱用的CD8+ T cells亚群的gene signatures](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247543616&idx=1&sn=4f29e5fb07cbbfc78f91eb4e232e1b19#wechat_redirect)

这个图中的四个 signatures 薅出来：

```r
# 创建一个空的list对象
gene_signatures <- list(
  Naive = c("IL7R", "CCR7", "SELL", "FOXO1", "KLF2", "KLF3", "LEF1", "TCF7", "ACTN1", "FOXP1"),
  Activation_Effector_function = c("FAS", "FASLG", "CD44", "CD69", "CD38", "NKG7", "KLRB1", "KLRD1",
                                    "KLRF1", "KLRG1", "KLRK1", "FCGR3A", "CX3CR1", "CD300A", "FGFBP2", "ID2",
                                    "ID3", "PRDM1", "RUNX3", "TBX21", "ZEB2", "BATF", "IRF4", "NR4A1", "NR4A2",
                                    "NR4A3", "PBX3", "ZNF683", "HOPX", "FOS", "FOSB", "JUN", "JUNB", "JUND", "STAT1",
                                    "STAT2", "STAT5A", "STAT6", "STAT4", "EOMES"),
  Cytotoxicity = c("GZMA", "GZMB", "GZMH", "GZMK", "GZMH", "GNLY", "PRF1", "IFNG", "TNF", "SERPINB1", "SERPINB6", "SERPINB9",
                    "CTSA", "CTSB", "CTSC", "CTSD", "CTSW", "CST3", "CST7", "CSTB", "LAMP1", "LAMP3", "CAPN2"),
  Exhaustion = c("PDCD1", "LAYN", "HAVCR2", "LAG3", "CD244", "CTLA4", "LILRB1", "TIGIT", "TOX", "VSIR", "BTLA", "ENTPD1", "CD160", "LAIR1")
)
gene_signatures
```

### 计算基因集打分

计算基因集打分有非常多算法：[使用decoupleR一次性实现11种基因集的活性打分（R与Python我都要）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247535495&idx=1&sn=a7e5218bfeaa70ca81b1c5bc1d9ac832#wechat_redirect)

我们这里就用文献中的吧：addModuleScore函数

![文章图片 3](assets/035_顶刊杂志同款CD8+%20T%20cells亚群signature%20score的umap图绘制（IF=58.7）/003.png)

打分计算：

```r
#########################
# AddModuleScore 得到的是每个细胞中算出来的我们感兴趣的基因的表达均值
# 创建一个空的list对象
gene_signatures <- list(
  Naive = c("IL7R", "CCR7", "SELL", "FOXO1", "KLF2", "KLF3", "LEF1", "TCF7", "ACTN1", "FOXP1"),
  Activation_Effector_function = c("FAS", "FASLG", "CD44", "CD69", "CD38", "NKG7", "KLRB1", "KLRD1",
                                    "KLRF1", "KLRG1", "KLRK1", "FCGR3A", "CX3CR1", "CD300A", "FGFBP2", "ID2",
                                    "ID3", "PRDM1", "RUNX3", "TBX21", "ZEB2", "BATF", "IRF4", "NR4A1", "NR4A2",
                                    "NR4A3", "PBX3", "ZNF683", "HOPX", "FOS", "FOSB", "JUN", "JUNB", "JUND", "STAT1",
                                    "STAT2", "STAT5A", "STAT6", "STAT4", "EOMES"),
  Cytotoxicity = c("GZMA", "GZMB", "GZMH", "GZMK", "GZMH", "GNLY", "PRF1", "IFNG", "TNF", "SERPINB1", "SERPINB6", "SERPINB9",
                    "CTSA", "CTSB", "CTSC", "CTSD", "CTSW", "CST3", "CST7", "CSTB", "LAMP1", "LAMP3", "CAPN2"),
  Exhaustion = c("PDCD1", "LAYN", "HAVCR2", "LAG3", "CD244", "CTLA4", "LILRB1", "TIGIT", "TOX", "VSIR", "BTLA", "ENTPD1", "CD160", "LAIR1")
)
gene_signatures

sce =  AddModuleScore(object = sce,features = gene_signatures,name=names(gene_signatures) )
colnames(sce@meta.data)
```

得到四列打分值：

![文章图片 4](assets/035_顶刊杂志同款CD8+%20T%20cells亚群signature%20score的umap图绘制（IF=58.7）/004.png)

### 绘图：

```r
library(ggplot2)
p1 <- FeaturePlot(sce,features = "Naive1",order = T) +
  ggtitle("Naive") +
  scale_color_gradientn(colors = c("#4f5da7", "white", "#ea3433"))
p1

p2 <- FeaturePlot(sce,features = "Activation_Effector_function2",order = T) +
  ggtitle("Activation/Effector_function") +
  scale_color_gradientn(colors = c("#4f5da7", "white", "#ea3433"))
p2

p3 <- FeaturePlot(sce,features = "Cytotoxicity3",order = T) +
  ggtitle("Cytotoxicity") +
  scale_color_gradientn(colors = c("#4f5da7", "white", "#ea3433"))
p3

p4 <- FeaturePlot(sce,features = "Exhaustion4",order = T) +
  ggtitle("Exhaustion") +
  scale_color_gradientn(colors = c("#4f5da7", "white", "#ea3433"))
p4

library(patchwork)
p <- patchwork::wrap_plots(list(p1,p2,p3,p4), nrow = 1)
p
ggsave(filename = "cd8t_score.png", width = 16,height = 3.5,plot = p,bg = "white")
```

结果如下：

![文章图片 5](assets/035_顶刊杂志同款CD8+%20T%20cells亚群signature%20score的umap图绘制（IF=58.7）/005.png)

是不是很简单，你学会了吗~

#### 文末友情宣传

强烈建议你推荐给身边的**博士后以及年轻生物学PI**，多一点数据认知，让他们的科研上一个台阶：

- [生信入门&数据挖掘线上直播课7月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247543316&idx=1&sn=c8569d0d202077108063c17964e8c128#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
