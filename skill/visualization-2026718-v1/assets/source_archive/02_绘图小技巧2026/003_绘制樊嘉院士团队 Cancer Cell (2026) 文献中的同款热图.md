# 绘制樊嘉院士团队 Cancer Cell (2026) 文献中的同款热图

- 专辑：绘图小技巧2026
- 公众号：生信技能树
- 发布时间：2026-01-12 22:36
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247548530&idx=1&sn=91477b0196d73a667e19359fbe1b52c1&chksm=9b4b7ec9ac3cf7df6bdf9f41d8ece28036ce77574ddfe5dd2c1d476795db157b8baf073d17c1)

---
> 樊嘉院士团队最近也发了几篇大作，咱们今天学习其于2026年1月8号发表在 Cancer Cell 杂志上的文献，标题为《Integrative proteogenomic analysis providesmolecular insights and clinical significance in gallbladder cancer》。

下面这幅热图主要通过通路富集分析揭示了四种TIME亚型之间不同的功能特征（图4B）：

A亚型表现出增殖表型，而B亚型显示抗原呈递和白介素信号通路的激活。C亚型在细胞间连接、ECM形成和血管生成方面显著富集。D亚型则表现出ECM降解、缺氧、氨基酸代谢和N-聚糖生物合成的增强。

![文章图片 1](assets/003_绘制樊嘉院士团队%20Cancer%20Cell%20(2026)%20文献中的同款热图/001.png)

图注：

> Figure 4. Immune landscape of FU-GBC cohort
>
> (B) Heatmap displaying enriched pathways at the multi-omics level across immune subtypes (\*p \< 0.05; Student’s t test).

## 数据准备

作者直接给了个功能分析的表格，在 1-s2.0-S1535610825005483-mmc6.xlsx 附表中，去读取进来：

```r
rm(list=ls())
library(ComplexHeatmap)
library(circlize)
library(openxlsx)

##### Vis input prep
### value matrix
PathwayPro <- readxl::read_excel("1-s2.0-S1535610825005483-mmc6.xlsx", sheet = "Table S5E")
PathwayPro <- as.data.frame(PathwayPro)
head(PathwayPro)
rownames(PathwayPro) <- PathwayPro$Pathway
PathwayPro <- PathwayPro[,-1]
```

![文章图片 2](assets/003_绘制樊嘉院士团队%20Cancer%20Cell%20(2026)%20文献中的同款热图/002.png)

四个样本亚型分组，每行是一个通路，表格中的值为GSVA富集打分。

### 制作通路分类行注释条

这部分作者是直接放在了代码中：

```r
##### Vis prep
SelectPathway <- tibble(
  Pathway = c(
    # cc
    'KEGG Cell cycle','KEGG DNA replication','HALLMARK_G2M_CHECKPOINT', # C1
    # metab
    'HALLMARK_FATTY_ACID_METABOLISM','KEGG Oxidative phosphorylation', # C1
    'HALLMARK_GLYCOLYSIS','KEGG N-Glycan biosynthesis','KEGG Lysine degradation', # C4
    # biologic process
    'KEGG Apoptosis','KEGG Autophagy',  # C2
    'HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION', # C3
    'HALLMARK_HYPOXIA','HALLMARK_ANGIOGENESIS', # C4
    # immune
    'REACTOME Antigen Presentation','REACTOME Signaling by Interleukins','REACTOME Cytokine Signaling in Immune system',
    'REACTOME Innate Immune System','REACTOME Adaptive Immune System','REACTOME Interferon gamma signaling',   # C2
    'HALLMARK_COMPLEMENT', # C4
    # signalings
    'REACTOME Signaling by NOTCH','REACTOME Signaling by Hedgehog','REACTOME Signaling by FGFR',   # C1
    'KEGG ErbB signaling pathway','KEGG NF-kappa B signaling pathway','KEGG VEGF signaling pathway','HALLMARK_PI3K_AKT_MTOR_SIGNALING', # C2
    'HALLMARK_TGF_BETA_SIGNALING','KEGG Hippo signaling pathway','REACTOME EPH-Ephrin signaling',   # C3
    'REACTOME Signaling by PDGF','HALLMARK_WNT_BETA_CATENIN_SIGNALING','KEGG AMPK signaling pathway','KEGG HIF-1 signaling pathway', # C4
    # cell junction
    'KEGG Tight junction','REACTOME Cell junction organization','KEGG Focal adhesion', # C3
    # ECM degradation
    'KEGG ECM-receptor interaction','REACTOME Activation of Matrix Metalloproteinases',
    'REACTOME Degradation of the extracellular matrix'# C4
  ),
  Category = c(rep('Cell cycle', 3),
               rep('Metabolism', 5),
               rep('Biologic processes', 5),
               rep('Immune response', 7),
               rep('Signalings', 14),
               rep('Cell junction', 3),
               rep('ECM', 3))
  )

Input <- PathwayPro[SelectPathway$Pathway, ]
Input <- as.matrix(Input)
```

### 制作显著性\*矩阵

这里作者没有提供数据，我们自己手动构建一个，实际分析中可以根据结果去调整，保证数据输入跟这里示例一样就行。

```r
### sig matrix
InputSig <- matrix(NA, nrow = nrow(Input),ncol = ncol(Input))
InputSig[c(1:23,27:37),1] <- "*"
InputSig[c(1:3,5,10:11,13:26,28,30:33,36,37),2] <- "*"
InputSig[c(3,5:12,14,16:19,25,27:28,31,34:37,39),3] <- "*"
InputSig[c(2:5,8,11:14,18,19,21,23:26,29:32,37:40),4] <- "*"
```

![文章图片 3](assets/003_绘制樊嘉院士团队%20Cancer%20Cell%20(2026)%20文献中的同款热图/003.png)

## 颜色设置

作者放了小部分数据在这里：https://github.com/ZLFu2000/GBC

颜色：

```r
##### Vis prep
#### 2 color
load('GBC-main/Data//Colors (ggsci).RData')
scales::show_col(ColJournal$Science)
ColImmune <- c(ColJournal$Nature[5], ColJournal$Nature[1],ColJournal$Nature[4], ColJournal$Nature[9])
names(ColImmune) <- c('A','B','C','D')
```

列注释条颜色：

```r
# 列注释条颜色 Anno
AnnoCluster <- columnAnnotation(Subtype = c('A','B','C','D'),
                                col = list( Subtype = ColImmune ),
                                gp = gpar(col = "white"),
                                annotation_name_side = "left",
                                simple_anno_size = unit(0.5, "cm"))
```

行注释条颜色：

```r
# 行注释条颜色设置
AnnoPathway <- rowAnnotation(Category = SelectPathway$Category,
                             col = list(
                               Category = c('Cell cycle' = ColJournal$COSMICsignature[1],
                                            'Biologic processes' = ColJournal$COSMICsignature[2],
                                            'ECM' = ColJournal$COSMICsignature[3],
                                            'Cell junction' = ColJournal$COSMICsignature[4],
                                            'Immune response' = ColJournal$COSMICsignature[5],
                                            'Metabolism' = ColJournal$COSMICsignature[6],
                                            'Signalings' = ColJournal$Science[8])
                             ),
                             gp = gpar(col = "white"),
                             # annotation_name_side = "left",
                             simple_anno_size = unit(0.5, "cm"))
```

热图自己的颜色：

```r
##### Vis
col <- colorRamp2(c(-1.5,-1,0,1,1.5),  c("#00685BFF","#4CB6ACFF","white","#FFDFB2FF","#EE6C00FF") )
```

## 热图绘制

万事具备，使用 ComplexHeatmap 画图：

```r
set.seed(0317)
ht <- Heatmap(Input,
        cluster_columns = F,
        name = 'NES',
        col = col,
        row_names_gp = gpar(fontsize = 9),  # 行名字体大小
        top_annotation = AnnoCluster,
        left_annotation = AnnoPathway,
        column_split = c('A','B','C','D'),
        column_title = NULL,
        row_split = SelectPathway$Category,
        row_title = NULL,
        cluster_rows = F,
        rect_gp = gpar(col = "white", lwd = 1), # 格子边框白色，线宽1
        # 在格子中添加显著性符号*
        cell_fun = function(j, i, x, y, width, height, fill) {
          if(!is.na(InputSig[i, j]))
            grid.text(InputSig[i, j], x, y, gp = gpar(fontsize = 9), just = c("centre","center"))
        },
        height = unit(40/2,'cm'), width = unit(4,'cm')
        )
```

调整图例位置并保存：

```r
pdf(file = "Fig4B.pdf", height = 12,width = 8)
draw(ht, heatmap_legend_side = 'right', annotation_legend_side = 'right',merge_legend = TRUE,gap = unit(5, "mm"))
dev.off()
```

![文章图片 4](assets/003_绘制樊嘉院士团队%20Cancer%20Cell%20(2026)%20文献中的同款热图/004.png)

## 到AI软件中修改一下

上面的图图例与通路有重叠部分，

![文章图片 5](assets/003_绘制樊嘉院士团队%20Cancer%20Cell%20(2026)%20文献中的同款热图/005.png)

上场！

1分钟修好，最终结果如下：

![文章图片 6](assets/003_绘制樊嘉院士团队%20Cancer%20Cell%20(2026)%20文献中的同款热图/006.png)

完美，如果希望绘图交流，进群见：加新叶的微信Biotree123。

今天分享到这里，如果对你有帮助，求一键三连！

转发：

- [生信入门&数据挖掘线上直播课2026年1月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247547917&idx=1&sn=76afb50b6e9e433e3f2b3d039f72dac4#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
