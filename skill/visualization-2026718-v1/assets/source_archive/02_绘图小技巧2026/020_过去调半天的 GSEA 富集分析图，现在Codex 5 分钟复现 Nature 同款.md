# 过去调半天的 GSEA 富集分析图，现在Codex 5 分钟复现 Nature 同款

- 专辑：绘图小技巧2026
- 公众号：生信技能树
- 发布时间：2026-07-07 22:36
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247552839&idx=1&sn=10c65712e67a395b873429c7cecf9680&chksm=9b4b4ffcac3cc6ea8f52bb98601735d03ba2e658a37c8c953b4d2891c33ad37f42402ae031f1)

---
> 我们今年的绘图小专辑还会继续，只不过会使用AI来做复现。今天复现一幅来自2024年发表在nature杂志上的图，文献为《Immune responses in checkpoint myocarditis acrossheart, blood and tumour》。图如下：配色什么的都比较和谐美观！是大家做功能富集分析的结果展示刚需。

![文章图片 1](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/001.png)

图注：

Fig 2. Cardiac T cell phenotypes in irMyocarditis.

d, Select pathways are shown from GSEA of  T/NK cell DEGs modeled by serum troponin T (adjusted empirical P value). Abbreviations: NES, normalized enrichment score.

## 1、下载文献

我用的zcode+glm5.2云端模型，下载文献超方便。

而且因为是月套餐，所以不用担心额度问题，可能只会使焦虑能不能用完！

配置见zcode：[Ollama：使用 Claude Code 与 GLM-5.2 进行 Vibe Coding 的配置指南](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng==&mid=2247552296&idx=1&sn=470d33c0fee6fc89541a0b15d71e9e7a&scene=21#wechat_redirect)

提示词：

```r
下载这篇文献以及文献附件：Immune responses in checkpoint myocarditis acrossheart, blood and tumour
```

很丝滑下载好了：

![文章图片 2](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/002.png)

## 2、AI解读我们需要复现的图

Fig 2. Cardiac T cell phenotypes in irMyocarditis.

d, Select pathways are shown from GSEA of  T/NK cell DEGs modeled by serum troponin T (adjusted empirical P value). Abbreviations: NES, normalized enrichment score.

```r
解读这个目录下文献@的fig2d,并做数据来源解读。
```

### 解读结果

Fig. 2d 来自这篇文献：CheckpointMyocarditis/Blum_2024_CheckpointMyocarditis_HeartBloodTumor_Nature_main.pdf，对应补充表： CheckpointMyocarditis/Blum_2024_CheckpointMyocarditis_HeartBloodTumor_Nature_supplementary_tables.xlsx 的 S8_GSEA results。

#### Fig. 2d 在讲什么

> Fig. 2d 是一个 GSEA 通路热图，不是空间图。它分析的是心脏组织单细胞数据里的 T/NK cells，看这些 T/NK 细胞的基因表达程序如何随血清 troponin T 升高而变化。troponin T 是心肌损伤严重程度指标，所以这里本质上是在问：心肌损伤越重，心脏内 T/NK 细胞更像在启动哪些转录程序？
>
> 图注原文意思是：Fig. 2c 先做“基因表达与 serum troponin T 的模型”，Fig. 2d 再把这些按 troponin 相关性排序的基因拿去做 GSEA。颜色表示 NES，即 normalized enrichment score。

#### 主要结论：

- troponin T 越高，心脏 T/NK 细胞越富集细胞周期、增殖、代谢激活相关通路。

- 正相关通路包括：

  - HALLMARK_E2F_TARGETS, NES 3.447, FDR 0.016

  - HALLMARK_G2M_CHECKPOINT, NES 3.180, FDR 0.016

  - KEGG_CELL_CYCLE, NES 2.359, FDR 0.0315

  - KEGG_DNA_REPLICATION, NES 2.471, FDR 0.0315

  - HALLMARK_MTORC1_SIGNALING, NES 1.824, FDR 0.016

- 负相关通路里比较醒目的是：

  - HALLMARK_TNFA_SIGNALING_VIA_NFKB, NES -1.476, FDR 0.0386

  - KEGG_NATURAL_KILLER_CELL_MEDIATED_CYTOTOXICITY, NES -1.961, FDR 0.0315

  - KEGG_NEUROACTIVE_LIGAND_RECEPTOR_INTERACTION, NES -2.298, FDR 0.0315

所以作者的解读是：更严重的 ICI 相关心肌炎中，心脏 T/NK 细胞并不是简单“炎症越强所有炎症通路都越高”，而是特别表现出增殖、细胞周期、DNA 复制和 mTORC1 代谢激活；同时一些 TNF/NF-kB 或 NK cytotoxicity 相关基因集反而随 troponin T 升高呈负相关。

### 数据来源

#### Fig. 2d 的输入数据链条是：

1.  心脏组织来源：ICI 相关心肌炎患者和对照的心肌组织，来自心内膜心肌活检或早期尸检。

2.  单细胞数据：作者自己的 MGH heart scRNA-seq 数据，共 33,145 个心脏细胞。

3.  对照补充：合并公开 Human Cell Atlas 心脏 scRNA-seq 数据，6 个非癌症、非 ICI 供体，51,431 个细胞。

4.  整合后心脏数据集：84,576 个 cardiac cells。

5.  Fig. 2 聚焦其中的心脏 T/NK 细胞：9,134 个 intracardiac T/NK cells。

6.  Fig. 2d 进一步只看 heart / global / 3. T and NK cells / contrast = by troponin 这一组 GSEA 结果。

#### 方法上，作者先用 DESeq2 建模：

gene ~ log(troponin)

troponin T 取的是接近组织采样时间的血清 troponin T，文中要求 troponin 测量时间距离组织采样不超过 ±2 天。然后用每个基因的 Wald statistic 排序，送入 fgsea 做 GSEA，10,000 permutations。补充表 S8 保存了每条通路的 pval, padj, ES, NES, leadingEdge, tissue, lineage, Subset, contrast。

#### 原始/再分析数据入口：

- 本研究 scRNA-seq count matrices、相关数据和 TCR sequencing：GEO GSE228597

- 受控原始人类测序数据：dbGaP phs003413.v1.p1

- 公开心脏对照 atlas：HCA / ENA ERP123138

- 分析代码：https://github.com/villani-lab/myocarditis

- 本地 Fig. 2d 直接对应结果表：S8_GSEA results 中 tissue=heart, Subset=3. T and NK cells, contrast=by troponin 的 517 条记录。

## 3、AI复现

现在数据来源，结果含义都非常清楚了，让AI读取数据给我们做一个复现吧。

因为GLM5.2没有视觉，所以这部分复现我使用的codex，接入的chatgpt pro模型。

提示词如下：

```r
你根据上面的信息使用原文的的数据复现一下这个fig2d吧。
```

这个过程中他发现少了些数据，于是自己去文献和代码里面找了：

![image-20260707205430462](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/003.png)

image-20260707205430462

复现结果如下：

![文章图片 4](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/004.png)

与原文的细节差异这里也做了说明：

![image-20260707210505823](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/005.jpg)


#### 可以说非常完美了！

#### 最后一点很重要，如果是拿到我自己的文献里面，这个代码应该怎么用？

#### 问下：

```r
如果是我自己的数据，我应该怎么准备输入数据，然后运行你的代码可以得到同款GSEA图呢？
```

#### 准备两个数据

> 你自己的数据要准备两类输入：**排序基因表** + **基因集 GMT**。核心不是必须有差异基因表，而是要有一个能把所有基因从“最正相关/最上调”排到“最负相关/最下调”的统计量。

![文章图片 6](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/006.png)

![文章图片 7](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/007.png)

![文章图片 8](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/008.png)

![文章图片 9](assets/020_过去调半天的%20GSEA%20富集分析图，现在Codex%205%20分钟复现%20Nature%20同款/009.png)

很贴心！

这次的复现：弱化了写代码的需求，但是需要比较强的对GSEA结果的解读和认知。

可能这就是AI时代大家需要加强的地方吧。

复现脚本放到了公众号后台，发送关键词即可获取：Nature同款GSEA图。

如果你对AI绘图感兴趣，欢迎来群里交流：jzhang0527。

<!-- wechat-article-fetcher: complete -->
