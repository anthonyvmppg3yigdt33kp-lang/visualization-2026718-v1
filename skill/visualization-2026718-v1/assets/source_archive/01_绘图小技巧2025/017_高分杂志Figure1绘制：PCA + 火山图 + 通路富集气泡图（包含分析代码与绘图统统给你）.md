# 高分杂志Figure1绘制：PCA + 火山图 + 通路富集气泡图（包含分析代码与绘图统统给你）

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-10-07 08:58
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546074&idx=1&sn=ce925f6bdd09969000d7089d924e24e6&chksm=9b4b7461ac3cfd7738153adb91f558c21ee218fedf61fd2470c84d6c17d3934be9e951f2713e)

---
> 前面我们给大家分享了一个将文章分析的数据和代码整理为在线书籍形式的文献，见：[分享一篇将代码整理成在线book形式的顶刊文献（Q1/IF: 58.7）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546052&idx=1&sn=3d8867c62915252658653addb274042c#wechat_redirect)，今天就来学习其中的Figure1绘制，这里我修改优化了作者提供的一些代码。

## 文献中的图一：PDAC中的肿瘤特异性通路特征

b，PCA图显示治疗前肿瘤及其配对的TATs（肿瘤邻近组织）中可分析的蛋白质。

c，火山图显示肿瘤与TATs之间差异丰富的蛋白质。

d，点图展示基于显著上调/下调的蛋白质识别的富集通路。

![文章图片 1](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/001.png)

## Figure1b 绘制

涉及4787种可分析蛋白质的主成分分析（PCA）揭示了肿瘤和TACs之间明显的分离。

#### step1：读取数据

读取蛋白表达矩阵 20230412_PDAC_PRO_exp.rds 以及 样本表型信息 20230412_PDAC_PRO_meta.rds

```r
rm(list=ls())
library(scatterplot3d)
library(tidyverse)
library(openxlsx)
library(factoextra) # Extract and Visualize the Results of Multivariate Data Analyses
color.bin <- c("#00599F","#D01910")
dir.create("./results/Figure1",recursive = T)

#  Step 1: Load Proteomics data
# 4787 protein * 281 samples
pro  <- readRDS("./PDAC2_data_results/data/proteomics/20230412_PDAC_PRO_exp.rds")
dim(pro)
pro[1:5,1:5]

meta <- readRDS("./PDAC2_data_results/data/proteomics/20230412_PDAC_PRO_meta.rds")
head(meta)
table(meta$Type,meta$paired)
table(meta$Type)
identical(rownames(meta),colnames(pro)) # check name
```

![文章图片 2](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/002.png)

#### step2：PCA分析

这里使用 prcomp 函数运行pca分析，并使用了两种方法计算每个pc的贡献度：

```r
#  Step 2: PCA
res.pca.comp <- prcomp(pro, scale = F)
head(res.pca.comp$sdev)
# 计算每个主成分的贡献度
# 贡献度 = 每个主成分的方差 / 总方差
pca_variance <- res.pca.comp$sdev^2  # 主成分的方差
total_variance <- sum(pca_variance)  # 总方差
contribution <- pca_variance / total_variance  # 贡献度
head(contribution)

# 计算贡献度方法2
# variance percent of each PC
p <- fviz_eig(res.pca.comp)
var_explained <- get_eig(res.pca.comp)
# var_explained <- res.pca.comp$sdev^2 / sum(res.pca.comp$sdev^2)
head(var_explained)

# 提取top10 PC
plot.data <- as.data.frame(res.pca.comp$rotation[, 1:10])
head(plot.data)
```

![文章图片 3](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/003.png)

#### step3：绘图

使用 scatterplot3d 函数绘制，并保存出去。这里的图片没有办法加上像文献中一样的阴影区域，后面可以使用pdf文件用AI打开，然后添加上去：

```r
#  Step 3: Plot
plot.data <- plot.data %>%
  mutate(ID=rownames(plot.data),
         Type=meta$Type,
         TypeColor=color.bin[as.numeric(as.factor(Type))])
head(plot.data)

pdf("./results/Figure1/1B.PRO_PCA3d.pdf", width = 7, height = 7)
scatterplot3d(x = plot.data$PC2,
              y = plot.data$PC1,
              z = plot.data$PC3,
              color = plot.data$TypeColor,
              pch = 16, cex.symbols = 1,
              scale.y = 0.7, angle = 45,
              xlab = paste0("PC2(",round(var_explained[2,2], digits = 2),"%)"),
              ylab = paste0("PC1(", round(var_explained[1,2], digits = 2),"%)"),
              zlab = paste0("PC3(",round(var_explained[3,2], digits = 2),"%)"),
              main="Protein",
              col.axis = "#444444", col.grid = "#CCCCCC")
legend("bottom", legend = levels(as.factor(meta$Type)),
       col =  color.bin,  pch = 16,title = "Tissue",
       inset = -0.15, xpd = TRUE, horiz = TRUE)
dev.off()
```

效果如下：

![文章图片 4](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/004.png)

## Figure1c 绘制

接下来绘制火山图！

显示肿瘤与TACs之间差异表达蛋白的火山图，其中1213种蛋白在肿瘤中显著上调，864种蛋白下调。

#### Step 1: Load Proteomics data

```r
################ fig1c
library(limma)
library(tidyverse)
library(openxlsx)
library(ggpubr)
library(ggthemes)


#  Step 1: Load Proteomics data
# 4787 protein * 281 samples
exp  <- readRDS("./PDAC2_data_results/data/proteomics/20230412_PDAC_PRO_exp.rds")
dim(exp)
exp[1:5,1:5]
meta <- readRDS("./PDAC2_data_results/data/proteomics/20230412_PDAC_PRO_meta.rds")
head(meta)
identical(rownames(meta),colnames(exp)) # check names
```

#### Step 2: limma 差异分析

```r
#  Step 2: limma
meta      <- meta %>% mutate(contrast=as.factor(Type))
design    <- model.matrix(~ 0 + contrast , data = meta) # un-paired
head(design)
fit       <- lmFit(exp, design)
contrast  <- makeContrasts( Tumor_Normal = contrastT - contrastN , levels = design)
fits      <- contrasts.fit(fit, contrast)
ebFit     <- eBayes(fits)
limma.res <- topTable(ebFit, coef = "Tumor_Normal", adjust.method = 'fdr', number = Inf)
## result
limma.res <- limma.res %>% filter(!is.na(adj.P.Val)) %>%
  mutate( logP = -log10(adj.P.Val) ) %>%
  mutate( tag = "Tumor -vs- Normal")%>%
  mutate( Gene = ID)
# cutoff:  FC:1.5   adj.p:0.05
limma.res <- limma.res %>% mutate(group=case_when(
  (adj.P.Val < 0.05 & logFC > 0.58) ~ "Up in tumor",
  (adj.P.Val < 0.05 & logFC < -0.58) ~ "Down in tumor",
  .default = "Not significant"))
table(limma.res$group) # UP:1213 ; DOWN:864 ; not:2710
## output
write.xlsx( limma.res, "./results/Figure1/1C.PRO_Limma_fc1.5.xlsx", overwrite = T, rowNames = F)
```

差异结果如下：UP:1213 ; DOWN:864 ; not:2710

![文章图片 5](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/005.png)

#### Step 3: 差异结果可视化&绘制火山图

这里的代码我自己加了一些修饰，因为作者给的代码绘图结果与文献中的不一样：

```r
#  Step 3: Vasualization
## volcano
limma.res <- limma.res %>% mutate(group=factor(group,levels = c("Up in tumor","Down in tumor","Not significant")))
head(limma.res)

p <- ggscatter(limma.res, x = "logFC", y = "logP", color = "group", size = 2,
               main = paste0("Differential expressed proteins
between tumor and TAT"), # ***
               xlab = "",
               ylab = "-log10(adjusted P.value)",
               palette = c("#D01910","#00599F","#CCCCCC"),
               ylim = c(-1, 70), xlim=c(-8,8)) +
  geom_hline(yintercept = -log10(0.05), linetype="dashed", color = "#222222") +
  geom_vline(xintercept = 0.58 , linetype="dashed", color = "#222222") +
  geom_vline(xintercept = -0.58, linetype="dashed", color = "#222222") +
  xlab(label = expression(log[2](fold~change))) +
  labs(color = "Significance") +  # 修改颜色图例的标题
  annotate("text", x = -5, y = 66, label = "864 proteins", size = 5, color = "#00599F", hjust = 0.5) + # 设置文本样式
  annotate("text", x = 5, y = 66, label = "1,213 proteins", size = 5, color = "#D01910", hjust = 0.5) + # 设置文本样式
  theme_bw() +
  theme(
    plot.title = element_text(hjust = 0.5),
    panel.grid.major = element_blank(),  # 去掉主要格子线
    panel.grid.minor = element_blank(),  # 去掉次要格子线
    plot.background = element_blank(),
    legend.position = "bottom"
    )
p
ggsave("./results/Figure1/1C.PRO_Limma_fc1.5.pdf", p, width = 5.8, height = 6)
```

结果如下：

![文章图片 6](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/006.png)

## Figure1d 绘制

点图展示了基于显著上调/下调蛋白鉴定的富集通路。红色点表示在肿瘤中与TACs相比上调蛋白富集的通路（校正P值\<0.05），而蓝色点表示在肿瘤中下调蛋白富集的通路（校正P值\<0.05）。

#### 读取数据：

```r
################ fig1d
# data : enriched pathways table
plot.data <- read.xlsx("./PDAC2_data_results/data/Extended Data Table 3.xlsx", sheet = 2, startRow = 2)
head(plot.data)
plot.pathway <- c("GO:0006730~one-carbon metabolic process","GO:0006888~ER to Golgi vesicle-mediated transport","hsa00020:Citrate cycle (TCA cycle)",
                  "hsa00071:Fatty acid degradation","hsa00190:Oxidative phosphorylation","hsa00250:Alanine, aspartate and glutamate metabolism",
                  "hsa00260:Glycine, serine and threonine metabolism","hsa00280:Valine, leucine and isoleucine degradation",
                  "hsa00480:Glutathione metabolism","hsa00520:Amino sugar and nucleotide sugar metabolism","hsa00620:Pyruvate metabolism",
                  "hsa00630:Glyoxylate and dicarboxylate metabolism","hsa00640:Propanoate metabolism","hsa01100:Metabolic pathways","hsa01200:Carbon metabolism",
                  "hsa01212:Fatty acid metabolism","hsa01240:Biosynthesis of cofactors","hsa03010:Ribosome","hsa03060:Protein export",
                  "hsa04141:Protein processing in endoplasmic reticulum","hsa04972:Pancreatic secretion","GO:0001916~positive regulation of T cell mediated cytotoxicity",
                  "GO:0006096~glycolytic process","GO:0007165~signal transduction","GO:0007266~Rho protein signal transduction","GO:0045087~innate immune response",
                  "GO:0050778~positive regulation of immune response","GO:0050853~B cell receptor signaling pathway","GO:0050870~positive regulation of T cell activation",
                  "GO:0071346~cellular response to interferon-gamma","hsa04015:Rap1 signaling pathway","hsa04062:Chemokine signaling pathway",
                  "hsa04066:HIF-1 signaling pathway","hsa04151:PI3K-Akt signaling pathway","hsa04512:ECM-receptor interaction","hsa04610:Complement and coagulation cascades",
                  "hsa04621:NOD-like receptor signaling pathway","hsa04666:Fc gamma R-mediated phagocytosis")

plot.data <- plot.data %>%
  filter(Term %in% plot.pathway) %>%
  mutate(LogFDR= -log10(FDR))
head(plot.data)
```

![文章图片 7](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/007.png)

#### 绘图：

这里我也做了很多修改，原代码根本不能画出文献中的效果：

```r
# plot
color.bin <- c("#00599F","#D01910")

p <- ggscatter(plot.data,
               x = "LogFDR",
               y = "Fold.Enrichment",
               color = "Type",
               main = "",
               size = "Ratio",
               shape = 16,
               label = plot.data$Term,
               palette = color.bin,
               repel =T
               )
p

p <- p +
  scale_size(range = c(4,20)) +
  scale_x_continuous(limit = c(-15, 40), breaks = seq(-10,40,by=10)) +
  xlab(label = expression(-log[10](adjusted~p~value))) +
# with_inner_glow(
#   geom_circle(aes(x0 = offset/6+6, y0 = y, r = r/2, fill = col, group = city), df_circle, colour = NA),
#   colour = "grey20", expand = 2, sigma = 5) + # 添加带内部发光的圆形
  geom_vline(xintercept = 0, linetype = "solid", color = "black", size =0.6) +
  annotate("text", x = -1.2, y = c(0,3,6,9,12), label = c(0,3,6,9,12), color = "black", size = 5) +
  geom_segment(aes(x = -0.5, xend = 0, y = 0, yend = 0),  linetype = "solid", size = 0.4) +
  geom_segment(aes(x = -0.5, xend = 0, y = 3, yend = 3),  linetype = "solid", size = 0.4) +
  geom_segment(aes(x = -0.5, xend = 0, y = 6, yend = 6),  linetype = "solid", size = 0.4) +
  geom_segment(aes(x = -0.5, xend = 0, y = 9, yend = 9),  linetype = "solid", size = 0.4) +
  geom_segment(aes(x = -0.5, xend = 0, y = 12, yend = 12),  linetype = "solid", size = 0.4) +
# theme_bw() +
  theme(
    plot.title = element_text(hjust = 0.5),
    panel.grid.major = element_blank(),  # 去掉主要格子线
    panel.grid.minor = element_blank(),  # 去掉次要格子线
    plot.background = element_blank(),
    axis.line.y = element_blank(),  # 去掉y轴的轴线
    axis.text.y = element_blank(),  # 去掉y轴的刻度标签
    axis.ticks.y = element_blank(),  # 去掉y轴的刻度线
    axis.title.y = element_blank(),
    legend.position = "right"
  )
p
ggsave(paste0("./results/Figure1/1D.PRO_deg.tn_enrich.pdf"), p, width = 11, height = 10)
```

![文章图片 8](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/008.png)

## 最终图：拼图

将上面保存的三个pdf使用 Adobe lllustrator 软件进行拼接，最终效果如下：

![文章图片 9](assets/017_高分杂志Figure1绘制：PCA%20+%20火山图%20+%20通路富集气泡图（包含分析代码与绘图统统给你）/009.png)

今天分享到这~

友情转发：

- [生信入门&数据挖掘线上直播课10月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247545889&idx=1&sn=b7b37a458eead4645137126753d58c34#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
