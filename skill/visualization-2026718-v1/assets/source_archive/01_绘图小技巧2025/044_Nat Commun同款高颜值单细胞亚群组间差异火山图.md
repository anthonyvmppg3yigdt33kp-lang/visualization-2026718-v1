# Nat Commun同款高颜值单细胞亚群组间差异火山图

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-04-23 17:19
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247541328&idx=1&sn=8236af56b7ae118299426bb30380e527&chksm=9b4b62ebac3cebfd0bdd0533c9079d9d8b2a258eb1e243356fb6e801c8a3d543873754d8493f)

---
> 单细胞的亚群组间差异分析会得到每个亚群一个差异结果，如何同时展示呢？看看这篇NC杂志：2025年2月11号发表在Nature Communications杂志，文献标题为《The spatiotemporal transcriptional profiling of murine brain during cerebral malaria progression and after artemisinin treatment》，结果展示如下：

![文章图片 1](assets/044_Nat%20Commun同款高颜值单细胞亚群组间差异火山图/001.png)

图注：

> Fig. 7 \| Unremitting interferon responses in neurons during ECM and after ART treatment. e Volcano plots show the DEGs of ECM vs. CON in each neuron region. The representative upregulated and down-regulated genes were labeled. adj_p_val of DEGs were calculated by Wilcoxon rank-sum test.

## 示例数据

数据就用我们之前的一个吧，样本正好有两个分组：[用流星图/彗星图（在此之前还不认识这种图呢！）展示富集分析结果](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247538003&idx=1&sn=e7489f68ec86515c43ac902f485daeef&scene=21#wechat_redirect) ，数据的处理注释就在里面。

数据标号为：GSE128033，https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE128033。

包括 8个特发性纤维化（IPF）样本和10个正常样本，共66500个细胞（文章中过滤后的细胞数）。

![文章图片 2](assets/044_Nat%20Commun同款高颜值单细胞亚群组间差异火山图/002.png)

已经处理好的可以seurat对象在这里下载：链接: https://pan.baidu.com/s/1w4nsR3GkUJfpecC6VkhLmQ?pwd=jctq

```r
# 加载R包
library(org.Hs.eg.db)
library(ggplot2)
packageVersion("ggplot2")
library(Seurat)
library(qs)
library(tidyverse)
library(ggrepel)
packageVersion("Seurat")

## 加载数据以及注释信息
sce <- qread("2-harmony/sce.all_int.qs")
table(Idents(sce))

meta <- readRDS("3-check-by-0.3/phe.RData")
head(meta)
sce <- AddMetaData(sce, metadata = meta)
Idents(sce) <- "celltype"
table(Idents(sce))
table(sce$orig.ident)
sce <- subset(sce, celltype!="Double_cells")

## 添加group分组信息
# 给一个初始值全为IPF组
sce$group <- "IPF"
# normal组的样本id
unique(grep("NOR", sce$orig.ident, value = T))
# normal组别的地方赋值为normal
sce$group[ sce$orig.ident %in% unique(grep("NOR", sce$orig.ident, value = T)) ] <- "normal"

# 看下结果检查一下
table(sce$orig.ident, sce$group)
```

## 组间差异分析

对每一个亚群做 IPF vs normal 组间差异分析，得到差异结果用于绘图：

```r
## 3.组间差异分析
# 处理一下细胞名字，差异分析名字不要有特殊字符
sce$celltype <- as.character(sce$celltype)
sce$celltype <- gsub(" ","_",sce$celltype)
sce$celltype <- gsub("/","_",sce$celltype)

celltype <- unique(sce$celltype)
celltype

# 制作组间差异分组信息
sce$g <- paste(sce$celltype, sce$group, sep = "_")
table(sce$g)
Idents(sce) <- "g"
DefaultAssay(sce) <- "RNA"
```

![文章图片 3](assets/044_Nat%20Commun同款高颜值单细胞亚群组间差异火山图/003.png)

### 组间差异：

```r
# 保存差异结果
diff_res <- list()
# 循环每个亚群
for(i in 1:length(celltype)){
# i <- 1
# 确保两个分组中有对应的细胞
  ncell1 <- rownames(sce@meta.data[sce$g == paste0(celltype[i], "_IPF"),])
  ncell2 <- rownames(sce@meta.data[sce$g == paste0(celltype[i], "_normal"),])

  name <- paste0(celltype[i],": IPF(" ,length(ncell2)," cells)",
                 " vs ","normal(",length(ncell1)," cells)")

print(name)

# Cell group must has more than 2 cells(at least 3 cells)
# 如果两个分组中有任意一组细胞数小于等于2，跳过差异并打印提示信息
if( length(ncell1)>2 && length(ncell2)>2 ) {
    sce.markers <- FindMarkers(sce,
                               logfc.threshold=0.25,
                               min.pct=0.1,
                               test.use = "wilcox",
                               fc.name = "avg_log2FC",
                               ident.1=paste0(celltype[i], "_IPF"),
                               ident.2=paste0(celltype[i], "_normal")
    )
    sce.markers$gene <- rownames(sce.markers)
    sce.markers$Group <- celltype[i]
    sce.markers$Regulated <- if_else(sce.markers$avg_log2FC > 0, "Up", "Down")
  } else{
    print(paste0("Only One group or group cells num < 3: ",celltype[i]))
    cat("\n")
    next
  }

# save out
  diff_res[[celltype[i]]] <- sce.markers
}
```

动态监控日志：

```r
[1] "ILC1_NK_cells: IPF(3331 cells) vs normal(2594 cells)"
[1] "Macrophages: IPF(15125 cells) vs normal(10910 cells)"
[1] "Endothelial_cells: IPF(1529 cells) vs normal(3991 cells)"
[1] "Smooth_muscle_cells: IPF(178 cells) vs normal(723 cells)"
[1] "T_cells: IPF(2153 cells) vs normal(2576 cells)"
[1] "B_cells: IPF(292 cells) vs normal(529 cells)"
[1] "Epithelial_cells: IPF(4334 cells) vs normal(5162 cells)"
[1] "Fibroblasts: IPF(753 cells) vs normal(2966 cells)"
[1] "Cycling_macrophages: IPF(301 cells) vs normal(540 cells)"
[1] "Lymphatic_endothelial_cells: IPF(341 cells) vs normal(375 cells)"
[1] "Mast_cells: IPF(345 cells) vs normal(1392 cells)"
```

### 整合差异结果：

```r
## combine cluster diff result
diff_sc <- do.call(rbind, diff_res)
head(diff_sc)
# save(diff_sc, diff_res, file = "diff_res.RData")
# load("diff_res.RData")
table(diff_sc$Group)
diff_sc <- diff_sc[abs(diff_sc$avg_log2FC)>0.58, ]
diff_sc$log10fdr <- -log10(diff_sc$p_val_adj)
diff_sc$log10fdr[diff_sc$log10fdr=="Inf"] <- max(diff_sc$log10fdr[diff_sc$log10fdr!=Inf])
```

![文章图片 4](assets/044_Nat%20Commun同款高颜值单细胞亚群组间差异火山图/004.png)

如果想直接用 diff_sc，数据见：链接: https://pan.baidu.com/s/14QwEXvrBiGqhiv3EYQbJWQ?pwd=fbhd

## 开始绘图

这次绘图使用ggplot2，这期间遇到了一个bug，见：[抽风的ggplot2版本让我排查bug到半夜！！！](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247541310&idx=1&sn=012b6a78d2ab641df1f9e92587a7fa8f&scene=21#wechat_redirect)

配色从文章中抠出来，方法见我们之前分享的帖子：[独家私藏秘技：如何获取高分文章中的图片配色？](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247540968&idx=1&sn=e6d61914bf98a2e5044c5fc5429039b5&scene=21#wechat_redirect)

### 基础绘图

先绘制基本图形：

```r
# 获取每种细胞亚群中Top10基因:
top10 <- diff_sc %>%
  group_by(Group) %>%
  top_n(10, abs(avg_log2FC)) %>%
  ungroup() %>%
  as.data.frame()

# 文献中抠出来的颜色：
mycol <- c('#b12d30', '#43b5e6', '#93ba1f', '#58ac41', '#f0bbcb','#f1aa41'
           ,"#6cc3b9","#fc3c46","#b76f9e","#3568a3","#f66464")

# 基础火山图绘制：
p <- ggplot() +
  geom_point(data = diff_sc, aes(x = avg_log2FC, y = log10fdr),size = 0.8, color = 'grey') +
  coord_flip() + # 坐标轴翻转
  facet_grid(. ~ Group,scales = "free") + # 一行多列;
  geom_point(data = top10, aes(x = avg_log2FC, y = log10fdr,color = Group)) + # 添加top点颜色
  geom_vline(xintercept = c(-0.58, 0.58), size = 0.5, color = "grey50", lty = 'dashed')+ #添加阈值线
  scale_color_manual(values = mycol) + #更改配色
  xlab(label = "avg_log2FC(IPF vs. normal)") +
  ylab(label = "") +
  theme_bw()+
  theme( legend.position = 'none', #去掉图例
    panel.grid = element_blank(), #去掉背景网格
    axis.text = element_text(size = 10), #坐标轴标签大小
    axis.text.x = element_text(angle = 45, vjust = 0.8), #x轴标签旋转
    strip.text.x = element_text(size = 10, face = 'bold') #加粗分面标题
  )
ggsave(filename = "Fig.7e-1.png", width = 16, height =3.8,plot = p)
```

结果如下：

![文章图片 5](assets/044_Nat%20Commun同款高颜值单细胞亚群组间差异火山图/005.png)

### 添加基因symbol

```r
# 添加 top 基因 symbol：
p1 <- p +
  geom_text_repel(
    data = top10,
    aes(x = avg_log2FC, y = log10fdr, label = gene, color = Group),
    fontface = 'italic',
    seed = 233,
    size = 3,
    min.segment.length = 0, # 始终为标签添加指引线段；若不想添加线段，则改为Inf
    force = 12,           # 重叠标签间的排斥力
    force_pull = 2,       # 标签和数据点间的吸引力
    box.padding = 0.1,    # 标签周边填充量，默认单位为行
    max.overlaps = Inf,   # 排斥重叠过多标签，设置为Inf则可以保持始终显示所有标签
    segment.linetype = 3, # 线段类型,1为实线,2-6为不同类型虚线
    segment.alpha = 0.5,  # 线段不透明度
    direction = "y", # 按y轴调整标签位置方向，若想水平对齐则为x
    hjust = 0        # 0右对齐，1左对齐，0.5居中
  )
ggsave(filename = "Fig.7e.png", width = 16, height =3.8,plot = p1)
```

完美：

![文章图片 6](assets/044_Nat%20Commun同款高颜值单细胞亚群组间差异火山图/006.png)

#### 你学会了吗？

### **文末友情宣传**

- **[生信入门&数据挖掘线上直播课5月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247541231&idx=1&sn=6704a3ae8233d19ca94fd4929b5e1f63&scene=21#wechat_redirect)**

- **[时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5&scene=21#wechat_redirect)**

- **[满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247535760&idx=2&sn=1e02a2e982a046ecf6389231e6768d5b&scene=21#wechat_redirect)**

<!-- wechat-article-fetcher: complete -->
