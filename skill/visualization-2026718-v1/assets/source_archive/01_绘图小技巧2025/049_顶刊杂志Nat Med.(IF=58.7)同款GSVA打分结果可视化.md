# 顶刊杂志Nat Med.(IF=58.7)同款GSVA打分结果可视化

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-03-31 13:50
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247540344&idx=1&sn=747fd12b9392a30263f9b4dcca84fc28&chksm=9b4b1ec3ac3c97d514db10aa76bd962beadfaf22b318791a0ba2c6ab620eca586663f43fed7c)

---
>
>
> 最近在上我们的生信马拉松入门课的第四周转录组学的时候，对GSVA代码进行了更新，现在顺便来对GSVA可视化结果搞一个高级好看的图，然后翻到了曾老板以前写的，里面有我想要的这个双向条形图，但是还没有辣么好看！这就来给他优化一下~。
>
> 此外，最新一期生信入门就在今天开课，还没上车的可以看一看瞄一瞄：[生信入门&数据挖掘线上直播课4月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247539788&idx=1&sn=62a09c7af6373658bf81c149eb0b4026&scene=21#wechat_redirect)

曾老板的帖子：[RNA-seq入门实战（八）：GSVA——基因集变异分析](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247514959&idx=2&sn=76ba7b67967b20fe186afa28fa5992eb&scene=21#wechat_redirect)

这个打分的双向条形图我印象中最深的是他出现在2018年8月24发表在顶刊杂志Nat Med.(IF=58.7)中，文献的标题为《Phenotype molding of stromal cells in the lung tumor microenvironment》，长得很好看：

这个结果就是GSVA分析后得到的通路水平的打分矩阵，使用limma进行差异分析（x坐标为差异结果中的t值，图中有两条竖着的虚线用来表示显著性阈值），用这种双向条形图展示两个分组之间通路活性打分的差异性。

![文章图片 1](assets/049_顶刊杂志Nat%20Med.(IF=58.7)同款GSVA打分结果可视化/001.png)

图注：Fig. 2 \| Endothelial cell clusters

## GSVA获得打分

首先我们来简单运行一下GSVA分析，输入数据为基因表达矩阵，以及通路基因集。

表达矩阵：count值或者标化后的tpm都可以，示例数据：https://github.com/zhangj1115/example_data

通路基因集：这里选择 MsigDB 数据库的 50 条癌症相关的通路 h.all.v2024.1.Hs.symbols.gmt，下载地址 https://www.gsea-msigdb.org/gsea/msigdb/human/collections.jsp#H

```r
# 清空当前环境变量
rm(list = ls())
options(stringsAsFactors = F)

# 加载包
library(GSEABase)
library(clusterProfiler)
library(enrichplot)
library(ggplot2)
library(stats)
library(GSVA)

# 加载数据
load("Step01-airwayData.Rdata")
ls()
# 表达矩阵
exp <- filter_count
exp[1:5,1:5]

# 转换为基因symbol
library(AnnoProbe)
library(org.Hs.eg.db)
keytypes(org.Hs.eg.db)
e2s <- AnnotationDbi::select(org.Hs.eg.db, keys= rownames(exp),
                             columns="SYMBOL", keytype = "ENSEMBL")
head(e2s)
ids <- na.omit(e2s)
ids <- ids[!duplicated(ids$SYMBOL),]
ids <- ids[!duplicated(ids$ENSEMBL),]
head(ids)
symbol_matrix <- exp[match(ids$ENSEMBL,rownames(exp)),]
rownames(symbol_matrix) = ids$SYMBOL
symbol_matrix[1:4,1:4]
y <- as.matrix(symbol_matrix)

# 基因集
geneSets <- read.gmt("h.all.v2024.1.Hs.symbols.gmt")
head(geneSets)
geneSets <- split(geneSets$gene, geneSets$term)


# 注意 gsvaParam 函数中不同 kcdf = c("Gaussian", "Poisson", "none") 的选择
# 如果是logarithmic scale, RNA-seq log-CPMs, log-RPKMs or log-TPMs, kcdf="Gaussian"
# 如果是integer counts, kcdf="Poisson"
gsvapar <- gsvaParam(y, geneSets, maxDiff=TRUE,kcdf="Poisson")

## 运行GSVA打分
gsva_es <- gsva(gsvapar)
head(gsva_es)
dim(gsva_es)
```

得到的打分结果如下：

![文章图片 2](assets/049_顶刊杂志Nat%20Med.(IF=58.7)同款GSVA打分结果可视化/002.png)

## limma差异分析

gsva打分可以像基因表达矩阵一样，做一些常规分析如差异分析：

```r
## 使用limma进行差异分析
library(limma)
group_list <- group[match(colnames(exp), group$run_accession),2]
group_list <- factor( group_list, levels = c("untreated","Dex"))
group_list

# 差异分析
design <- model.matrix(~group_list)
fit <- lmFit(gsva_es,design)
fit <- eBayes(fit)
## 上面是limma包用法的一种方式
options(digits = 4) #设置全局的数字有效位数为4
diff <- topTable(fit,coef=2,adjust='BH', n=Inf)
head(diff)
```

![文章图片 3](assets/049_顶刊杂志Nat%20Med.(IF=58.7)同款GSVA打分结果可视化/003.png)

## 绘制双向条形图

有了上面的差异结果就可以做文献中的那个图啦，还是使用ggplot2进行定制化：

```r
####### 3.双向条形图
library(tidyverse)
library(ggthemes)
library(ggprism)

# 载入gsva的差异分析结果
dat_plot <- data.frame(id=row.names(diff), p=diff$P.Value, tvalue= diff$t)
dat_plot$group <- ifelse(dat_plot$tvalue >0 ,1,-1)    # 将上调设为组1，下调设为组-1

# 阈值自己的项目需要调整，我这里因为显著的pvalue比较少，使用了0.2, 没有统计学意义
dat_plot$g <- "Not"
dat_plot$g[ dat_plot$tvalue>0 & dat_plot$p < 0.2 ] <- "Up"
dat_plot$g[ dat_plot$tvalue<0 & dat_plot$p < 0.2 ] <- "Down"
table(dat_plot$g)
dat_plot$g <- factor(dat_plot$g, levels=c('Up','Down','Not'))

# 添加label颜色
dat_plot$color <- ifelse(dat_plot$g=="Not", '#cccccc',"black")

# 排个序
dat_plot <- dat_plot[order(dat_plot$tvalue,decreasing = T), ]
dat_plot$id <- factor(dat_plot$id,levels = rev(dat_plot$id))

# 调整添加的y轴方向通路的对其方式
dat_plot$lable_hjust <- ifelse(dat_plot$tvalue>0, 1, 0)

# 对其的x轴起点，上调通路在x轴右边，起点隔0.05, 避免与柱子粘在一起
dat_plot$lable_xloc <- ifelse(dat_plot$tvalue>0, -0.05, 0.05)

# 虚线阈值
t_up <- min(dat_plot[dat_plot$g=="Up","tvalue"]);t_up
t_down <- max(dat_plot[dat_plot$g=="Down","tvalue"]);t_down

p <- ggplot(data = dat_plot,aes(x = id, y = tvalue, fill = g)) +
  geom_col() +
  coord_flip() +
  scale_fill_manual(values = c('Up'= '#36648b','Not'='#cccccc','Down'='#7ccd7c')) +
  geom_hline(yintercept = c(t_down,t_up), color = 'white', size = 0.5,lty='dashed') +
  xlab('') +
  ylab('t value of GSVA score, treat \n versus control') +
  guides(fill="none") +
  theme_prism(border = T) +
  theme( axis.text.y = element_blank(),
         axis.ticks.y = element_blank() ) +
  geom_text(data = dat_plot, aes(x=id, y = lable_xloc, label = id, hjust = lable_hjust),
            color=dat_plot$color, size = 4.2) #+  # 添加通路名称

p
# 保存
ggsave("GSVA_barplot_tvalue.pdf",p,width = 6,height  = 10)
```

结果如下：

![文章图片 4](assets/049_顶刊杂志Nat%20Med.(IF=58.7)同款GSVA打分结果可视化/004.png)

#### 每日一画，勤修苦练~

### 文末友情宣传

- [生信入门&数据挖掘线上直播课4月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247539788&idx=1&sn=62a09c7af6373658bf81c149eb0b4026&scene=21#wechat_redirect)

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](http://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247524148&idx=1&sn=7806da6feb41a36493c519c1cfc1d3ac&chksm=9b4bdf8fac3c569960369602f1ef26639cb366b250f233b2297d1f059471c0458335bfc0b829&scene=21#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247535760&idx=2&sn=1e02a2e982a046ecf6389231e6768d5b&scene=21#wechat_redirect)

<!-- wechat-article-fetcher: complete -->
