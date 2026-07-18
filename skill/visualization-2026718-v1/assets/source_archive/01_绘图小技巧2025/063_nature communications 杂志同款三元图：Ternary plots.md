# nature communications 杂志同款三元图：Ternary plots

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-01-31 20:01
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247537683&idx=1&sn=2efed317d095c95f03700804d4b8cefa&chksm=9b4b14a8ac3c9dbe4eef2991dcc1d6190f84372b9d7a043332ebdb4c02e840bfd2704d064035)

---
> 前面我们已经给大家介绍过来自 nature communicattions 杂志的高颜值小提琴图：《[NC杂志同款高颜值小提琴图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537553&idx=1&sn=d60bcf0ec06858a21c2e0eb52e55fea3&scene=21#wechat_redirect)》，这篇文章里面还有很多其他高颜值科研绘图，**今天来看看这个三元图吧！文献还是《A highly conserved core bacterial microbiota with nitrogen-fixation capacity inhabits the xylem sap in maize plants》**，图片如下：

![文章图片 1](assets/063_nature%20communications%20杂志同款三元图：Ternary%20plots/001.png)

图注：

> 图2 玉米细菌群落沿土壤-植物连续体的组成。
>
> f\. **三种施肥处理下木质部汁液中OTU的三元图**。每个**点的大小**表示OTU的相对丰度。**位置**由三种施肥处理对总相对丰度的贡献决定，靠近某个顶点表示该OTU在该施肥处理下富集。**圆圈的颜色**对应不同的属。灰色圆圈表示丰度没有显著差异的OTU。

## 数据背景

### 总共有10种不同微生物群落细菌：

> 1.  **克雷伯氏菌属（Klebsiella）**：一种常见的革兰氏阴性细菌，广泛存在于环境中，部分种类可致病。
>
> 2.  **假单胞菌属（Pseudomonas）**：一种广泛分布的革兰氏阴性细菌，具有很强的代谢能力，部分种类对植物有益，部分种类可致病。
>
> 3.  **肠杆菌科未分类（Enterobacteriaceae_unclassified）**：属于肠杆菌科，但尚未明确分类到具体属或种的细菌。
>
> 4.  **罗森贝吉氏菌属（Rosenbergiella）**：一种相对较少被研究的细菌属，通常与海洋或淡水环境相关。
>
> 5.  **草酸杆菌科未分类（Oxalobacteraceae_unclassified）**：属于草酸杆菌科，但尚未明确分类到具体属或种的细菌。
>
> 6.  **鞘氨醇单胞菌属（Sphingobacterium）**：一种革兰氏阴性细菌，通常存在于土壤和水体中，部分种类与植物共生。
>
> 7.  **乳酸球菌属（Lactococcus）**：一种革兰氏阳性细菌，广泛用于发酵工业，如奶酪和酸奶的制作。
>
> 8.  **欧文氏菌属（Erwinia）**：一种革兰氏阴性细菌，部分种类是植物病原菌，可引起植物软腐病。
>
> 9.  **其他（Others）**：指除上述分类之外的其他细菌。
>
> 10. **无显著差异（NotSig）**：指在统计分析中未表现出显著差异的细菌。

### OUTs含义

全称：操作分类单元（Operational Taxonomic Units，OTUs）

> #### 1. **定义**
>
> 操作分类单元（OTUs）是一种在微生物生态学和分子生物学中常用的术语，用于对微生物群落中的微生物进行分类和分析。OTUs是基于微生物的遗传特征（通常是16S rRNA基因序列）将微生物划分为不同的“分类单元”，而不是基于传统的形态学分类。
>
> #### 2. **背景**
>
> 在微生物生态学研究中，直接观察和鉴定微生物的种类往往非常困难，因为许多微生物无法在实验室中培养，或者其形态特征不足以区分不同的物种。因此，科学家们通常通过分析微生物的基因序列来推断其种类和多样性。16S rRNA基因是细菌和古菌中高度保守的基因，其序列的差异可以用来区分不同的微生物种类。
>
> #### 3. **OTUs的划分方法**
>
> OTUs通常是通过将微生物的基因序列进行聚类分析来划分的。具体步骤如下：
>
> - **序列比对**：将从样本中获得的微生物基因序列（如16S rRNA基因序列）与已知的参考数据库进行比对。
>
> - **相似性阈值**：选择一个相似性阈值（如97%），将相似度高于该阈值的序列归为同一个OTU。例如，如果两个序列的相似度达到97%，则认为它们属于同一个OTU。
>
> - **聚类分析**：使用聚类算法（如UPGMA、Neighbor-Joining等）将所有序列划分为不同的OTU。
>
> #### 4. **OTUs的意义**
>
> OTUs在微生物生态学研究中具有重要意义：
>
> - **多样性分析**：OTUs可以用来评估微生物群落的多样性，包括物种丰富度（Species Richness）和均匀度（Evenness）。
>
> - **群落结构分析**：通过比较不同样本中的OTUs组成，可以研究微生物群落的结构和功能差异。
>
> - **生态学研究**：OTUs可以帮助科学家理解微生物在不同环境中的分布和生态功能，例如在土壤、水体、人体肠道等生态系统中的作用。
>
> #### 5. **OTUs的局限性**
>
> 尽管OTUs是一种非常有用的工具，但它也有一些局限性：
>
> - **阈值选择的主观性**：OTUs的划分依赖于相似性阈值的选择，不同的阈值可能导致不同的结果。
>
> - **无法完全反映物种差异**：OTUs是基于序列相似性划分的，可能无法完全反映微生物的生物学差异。例如，两个序列相似度为97%的微生物可能在生态功能上存在显著差异。
>
> - **依赖于参考数据库**：OTUs的划分依赖于已知的参考数据库，如果数据库不完整或不准确，可能会影响OTUs的划分结果。
>
> #### 6. **OTUs与其他分类方法的比较**
>
> - **物种（Species）**：OTUs与传统生物学中的“物种”概念不同。物种是基于形态学、生理学和遗传学特征综合定义的，而OTUs主要是基于基因序列的相似性。
>
> - **ASVs（Amplicon Sequence Variants）**：近年来，ASVs逐渐成为一种替代OTUs的新方法。ASVs是基于单个核苷酸变异来划分微生物种类，能够更精确地反映微生物的多样性。

### 三种实验条件

不同施肥处理下的微生物相对丰度：

- **CK对照组**（Control）：未施肥；

- **NPK**：施用氮肥、磷肥和钾肥的化肥；

- **NPKM**：施用有机肥料加化肥。

### 数据地址：https://github.com/PlantNutrition/Liyu

Fig2/Tern_data.txt数据每列的含义：

- `size`：每个OTU（操作分类单元）的相对丰度或大小

- `Kingdom`：表示微生物所属的界（Kingdom）。如，`Bacteria`表示细菌界。

- `Phylum`：表示微生物所属的门（Phylum）。如，`Gammaproteobacteria`表示γ-变形菌门。

- `Class`：表示微生物所属的纲（Class）。如，`Gammaproteobacteria`表示γ-变形菌纲。

- `Order`：表示微生物所属的目（Order）。如，`Burkholderiales`表示伯克霍尔德菌目。

- `Family`：表示微生物所属的科（Family）。如，`Burkholderiaceae`表示伯克霍尔德菌科。

- `Genus`：表示微生物所属的属（Genus）。如，`NotSig`可能表示该OTU在属的分类上没有显著差异或未被明确分类。

- `enrich`：表示该OTU在不同施肥处理下的富集情况。如，`NotSig`可能表示该OTU在不同处理下没有显著的富集差异。

这个数据展示了微生物分类信息和相对丰度，从界（Kingdom）到属（Genus）的分类信息，用于描述每个OTU的分类地位。`enrich`标记OTU在不同处理下的富集情况。

## 三元图：Ternary plots绘制

```r
rm(list=ls())
library(ggtern)

plot_data = read.table("Fig2/Tern_data.txt", header=T, row.names= 1, sep="\t", comment.char = "")
head(plot_data)
str(plot_data)

p <- ggtern(data=plot_data, aes(x=CK, y=NPK, z=NPKM)) +
  geom_mask() +  # 创建手动裁剪蒙版
  geom_point(aes(size=size, color=Genus),alpha=0.8) +
  scale_size(range = c(0, 10)) +
  scale_color_manual(values  = c('#E31A1C','#228B22','#1F78B4', '#FDB462', '#8B658B',  '#4876FF', '#00BFFF', '#EE82EE','#8B8682','#CDC9C9'),
                     limits = c('Klebsiella','Pseudomonas','Enterobacteriaceae_unclassified','Rosenbergiella','Oxalobacteraceae_unclassified','Sphingobacterium','Lactococcus','Erwinia','Others','NotSig')
                     ) +
  guides(size="none") +
  theme_bw() +
  theme(axis.text=element_blank(), axis.ticks=element_blank())

p

ggsave(filename = "Fig2f.pdf", width = 9, height = 8)
```

结果如下：

![文章图片 2](assets/063_nature%20communications%20杂志同款三元图：Ternary%20plots/002.png)

### 往期精彩

[绘制NC杂志同款高颜值小提琴图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537553&idx=1&sn=d60bcf0ec06858a21c2e0eb52e55fea3&scene=21#wechat_redirect)

[给你的单细胞umap图加个cell杂志同款的圈](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537290&idx=1&sn=ad76831349df67bb5236370dab088536&scene=21#wechat_redirect)

[高颜值复杂热图绘制小技巧](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537091&idx=1&sn=23f4aa643cf8c731221c3abe857ce150&scene=21#wechat_redirect)

[一种很新的功能富集结果展示方法](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247537055&idx=1&sn=26544d5687fbe6001391e869ea84e692&scene=21#wechat_redirect)

[KEGG富集结果7大分类展示](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247536875&idx=2&sn=67fe96abc9c8a139edebfa8a89728df8&scene=21#wechat_redirect)

[5种方式美化你的单细胞umap散点图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247536822&idx=1&sn=5f695d4ee6d8ba00a0961c02c4cf83bd&scene=21#wechat_redirect)

<!-- wechat-article-fetcher: complete -->
