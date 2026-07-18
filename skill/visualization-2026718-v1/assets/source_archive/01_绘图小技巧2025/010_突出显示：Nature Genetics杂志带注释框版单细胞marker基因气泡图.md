# 突出显示：Nature Genetics杂志带注释框版单细胞marker基因气泡图

- 专辑：绘图小技巧2025
- 公众号：生信技能树
- 发布时间：2025-11-17 15:52
- 原文：[微信公众平台](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247547054&idx=1&sn=f87d661c8e4b8f90f793f3e3d4d7454b&chksm=9b4b7815ac3cf103afcb16bdf87490008664666acffcbe3c02d32c2327cb9fa3b3a5e110b2e1)

---
> 单细胞的marker基因气泡图，再来一个突出结果版本的。还是来自王凌华团队的最新文献，2025年10月21号发表在Nature Genetics杂志上，标题为《Multi-modal spatial characterization of tumor immune microenvironments identifies targetable inflammatory niches in diffuse large B cell lymphoma》。这个图上有带虚线的框框突出显示了作者想要强调的marker！来看看~

专辑里面的气泡图有：

- [Nature杂志同款高颜值单细胞基因表达气泡图（王凌华团队）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247545796&idx=1&sn=bb7ae79db9b3c3a0542187e1b6b31bc5#wechat_redirect)

- [高分杂志同款cellchat细胞通讯结果气泡图绘制（IF=25.083）](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247544734&idx=1&sn=afb7ead473e91445b695efea54807327#wechat_redirect)

- [Nature Genetics杂志特别版单细胞marker基因气泡图](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546635&idx=1&sn=8a9fbdb461f7c704e07e61f054b3e200#wechat_redirect)

- 绘图小技巧进群方式：添加微信 Biotree123，发18.8的进群门票，可以在群里交流学习绘图，并发布许愿绘图~

12月份的生信入门班已经开始报名，详细点击链接：[生信入门&数据挖掘线上直播课12月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247547012&idx=1&sn=f55923d9a6d9e04c3e923c2a3cae6e56#wechat_redirect)

Fig3中的a图：

![文章图片 1](assets/010_突出显示：Nature%20Genetics杂志带注释框版单细胞marker基因气泡图/001.png)

图注：

> Fig. 3 The expression of naive/ genes in APOE+ C1Q+ TAMs residing in different spatial niches. e, Summary of memory, cytotoxic and exhaustion markers in T cells from different spatial niches.

## 数据背景

作者利用78例大B细胞淋巴瘤切除活检样本及5例对照组织（4例扁桃体、1例淋巴结）构建了六组组织微阵列。作者抽取了部分示例数据以及代码放在github上面：https://github.com/Coolgenome/Lymphoma-spatial

下载好的： 链接: https://pan.baidu.com/s/1ISXLXLEmgdwtBrLTTdkPOQ?pwd=b49k 提取码: b49k

详细介绍见：[一行代码给你的单细胞UMAP图添加左下角小箭头坐标轴](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247546483&idx=1&sn=acea4ccfb046a373c767523ccc41a266#wechat_redirect)

## 数据处理

### 1.先读取绘图数据

数据为seurat对象，每一个CN中不同细胞类型的比例组成：

```r
### Figure 3 ###
rm(list=ls())
### load essential packages ###
library(Seurat)
library(tidyverse)
library(dplyr)
library(ggplot2)

### load data objects ###
Lymphoma_data <- readRDS("./demo_data/Lymphoma_data.rds") ### This is saved from Figure 1b.
spatial_niche <- readRDS("./demo_data/spatial_niche.rds")
spatial_niche <- column_to_rownames(spatial_niche, var="Barcode")
Lymphoma_data <- AddMetaData(Lymphoma_data, spatial_niche)
head(Lymphoma_data@meta.data)
table(Lymphoma_data$CN_cluster)
class(Lymphoma_data$CN_cluster)
```

Lymphoma_data 是一个seurat对象，里面有 细胞类型信息 CN_cluster列，总共有CN1-7七大类：

![文章图片 2](assets/010_突出显示：Nature%20Genetics杂志带注释框版单细胞marker基因气泡图/002.png)

数据处理一下因子变量：这样标签就能跟图片中的对应上了。

```r
library(dplyr)
Lymphoma_data@meta.data <- Lymphoma_data@meta.data %>%
  mutate(CN_cluster = recode(CN_cluster,
                           "CN1" = "CN1_T",
                           "CN2" = "CN2_PC",
                           "CN3" = "CN3_Myeloid",
                           "CN4" = "CN4_Stromal",
                           "CN5" = "CN5_Tumor-B",
                           "CN6" = "CN6_Diffuse",
                           "CN7" = "CN7_Mixed"))
table(Lymphoma_data$CN_cluster)
Lymphoma_data$CN_cluster <- factor(Lymphoma_data$CN_cluster, levels = rev(c("CN1_T","CN2_PC","CN3_Myeloid","CN4_Stromal","CN5_Tumor-B","CN6_Diffuse","CN7_Mixed")))
```

### 2.提取marker基因向量

使用deepseek从图片中提取：

```r
### for visualization of the expression of naive and memory markers ###
T_cell_naive_mem_markers = c("SELL","TCF7","CCR7","IL7R","ANXA1","GPR183")
T_cell_Cytotoxicity_markers = c("GZMK", "GZMB", "PRF1", "NKG7", "GZMH", "GNLY", "XCL1/2")
T_cell_exhaustion_markers = c("LAG3", "HAVCR2", "TNFRSF9", "TIGIT", "PDCD1", "ENTPD1", "TOX")
```

## 开始绘图

### 1、先来画左边的 naive_mem_markers

**基础气泡图**：

```r
## 绘制左边的图
p1 <- DotPlot(object = subset(Lymphoma_data, cell_state == "C5_T"),features = T_cell_naive_mem_markers, group.by="CN_cluster", scale.by = "size", scale=5, col.max = 1.3) +
  RotatedAxis() +
  scale_color_gradientn(values = seq(0,1,0.1),colours = c("#4575b4","#abd9e9","#e0f3f8","#ffffbf","#fdae61","#d73027","#800026"))
p1
range(p1@data$pct.exp)
```

结果如下：

![文章图片 3](assets/010_突出显示：Nature%20Genetics杂志带注释框版单细胞marker基因气泡图/003.png)

**添加方框**：使用geom_rect，来修饰一下：

```r
## 添加注释框
p1 <- p1 +
  xlab(label = "") + ylab(label = "") +
  scale_size_continuous( range = c(1.2, 10) ) +
# 第一列
  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=5.7,ymax=6.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=2.7,ymax=3.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第二列
  geom_rect(aes(xmin=2.7,xmax=3.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第三列
  geom_rect(aes(xmin=3.7,xmax=4.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black")
p1
```

![文章图片 4](assets/010_突出显示：Nature%20Genetics杂志带注释框版单细胞marker基因气泡图/004.png)

**添加底部的文字和横线：**

```r
## 添加底部文字
p1 <- p1 +
  geom_segment(x=0.5,xend=6.5,y=-0.8,yend=-0.8,linewidth = 0.45) +
  annotate(geom="text",x = 4, y = -Inf,label="Naive and memory",hjust = 0.5, vjust = 6,size=6.3) +
  coord_cartesian(clip="off")  +
  labs(title = "C5_T in different spatial niches") +
  theme( plot.margin = margin(r = 0,b = 30) ,
         plot.title = element_text(size = 15),
         axis.text = element_text(size = 14) )

p1
```

![文章图片 5](assets/010_突出显示：Nature%20Genetics杂志带注释框版单细胞marker基因气泡图/005.png)

### 2、绘制中间的marker

基础部分：

```r
##### 第二个marker图
p2 <- DotPlot(object = subset(Lymphoma_data, cell_state == "C5_T"),features = T_cell_Cytotoxicity_markers, group.by="CN_cluster", scale.by = "size", scale=5, col.max = 1.3) +
  RotatedAxis() +
  scale_color_gradientn(values = seq(0,1,0.1),colours = c("#4575b4","#abd9e9","#e0f3f8","#ffffbf","#fdae61","#d73027","#800026"))

p2
range(p2@data$pct.exp)
```

添加注释框：

```r
## 注释框
p2 <- p2 +
  xlab(label = "") + ylab(label = "") +
  scale_size_continuous( range = c(1.2, 10),breaks = c(10, 20,30, 40) ) +
# 第一竖排
  geom_rect(aes(xmin=0.7,xmax=1.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=0.7,xmax=1.3, ymin=4.7,ymax=5.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=0.7,xmax=1.3, ymin=2.7,ymax=3.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第二竖排
  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=4.7,ymax=5.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=1.7,xmax=2.3, ymin=1.7,ymax=2.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第三竖排
  geom_rect(aes(xmin=2.7,xmax=3.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=2.7,xmax=3.3, ymin=4.7,ymax=5.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第四竖排
  geom_rect(aes(xmin=3.7,xmax=4.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=3.7,xmax=4.3, ymin=4.7,ymax=5.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=3.7,xmax=4.3, ymin=2.7,ymax=3.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第五竖排
  geom_rect(aes(xmin=4.7,xmax=5.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=4.7,xmax=5.3, ymin=4.7,ymax=5.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第六竖排
  geom_rect(aes(xmin=5.7,xmax=6.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
  geom_rect(aes(xmin=5.7,xmax=6.3, ymin=4.7,ymax=5.3),fill=NA,linetype = 2,linewidth = 0.8,color="black") +
# 第7竖排
  geom_rect(aes(xmin=6.7,xmax=7.3, ymin=6.7,ymax=7.3),fill=NA,linetype = 2,linewidth = 0.8,color="black")
p2
```

其他修饰：

```r
## 其他修饰
p2 <- p2 +
  geom_segment(x=0.5,xend=7.5,y=-0.8,yend=-0.8,linewidth = 0.45) +
  annotate(geom="text",x = 4.5, y = -Inf,label="Cytotoxicity",hjust = 0.5, vjust = 6,size=6.3) +
  coord_cartesian(clip="off")  +
  theme(
    axis.text.y = element_blank(),  # 隐藏y轴标签
    axis.ticks.y = element_blank(), # 隐藏y轴刻度
    axis.title.y = element_blank(),  # 隐藏y轴标题
    axis.line.y = element_blank(),  # 移除Y轴线
    axis.text = element_text(size = 14),
    plot.margin = margin(l = 0,b = 30) )
p2
```

![文章图片 6](assets/010_突出显示：Nature%20Genetics杂志带注释框版单细胞marker基因气泡图/006.png)

### 3、拼图在一起

前面在绘制 p1 和 p2的时候设置了 plot.margn，p1的r=0， p2的l=0，**这样拼在一起的时候 隐藏p2的y轴线，就没有空格了！**

是不是我想的一个好方法！

```r
# 拼图并保持共有图例
library(patchwork)
p <- (p1 + p2 ) +
  plot_layout(guides = "collect",widths=c(1,1*(7/6))) &
  theme( legend.position = "bottom",
         legend.margin = margin(t = 26, r = 0, b = 0, l = 0) ) &
  guides(
    color = guide_colorbar(title.position = "top", title.hjust = 0.5,title = "Avg.exp."),
    size = guide_legend(title.position = "top", title.hjust = 0.5,
                        label.position = "bottom",
                        direction = "horizontal",
                        nrow = 1,
                        keywidth = unit(0.5, "cm"),
                        keyheight = unit(0.8, "cm"),
                        override.aes = list(color = "black")) )
p
ggsave(filename = "Figure3a.pdf",width = 11, height = 7, plot = p)
```

最终结果如下：

![文章图片 7](assets/010_突出显示：Nature%20Genetics杂志带注释框版单细胞marker基因气泡图/007.png)

完美！

如果上面的内容对你有帮助，欢迎一键三连！

友情转发：

- [生信入门&数据挖掘线上直播课12月班](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247547012&idx=1&sn=f55923d9a6d9e04c3e923c2a3cae6e56#wechat_redirect)，你的生物信息学入门课

- [时隔5年，我们的生信技能树VIP学徒继续招生啦](https://mp.weixin.qq.com/s?__biz=MzAxMDkxODM1Ng%3D%3D&mid=2247525079&idx=1&sn=0b997af16a58195b4192691373048fd5#wechat_redirect)

- [满足你生信分析计算需求的低价解决方案](https://mp.weixin.qq.com/s?__biz=MzUzMTEwODk0Ng%3D%3D&mid=2247530048&idx=1&sn=28aa7bbd5e00521f79e074496a5f5d66#wechat_redirect)

- [生信故事会](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=1679199708449144836#wechat_redirect)，来看看他们的生信入门故事

- [生信马拉松答疑专辑](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzAxMDkxODM1Ng%3D%3D&action=getalbum&album_id=3690970204957147140#wechat_redirect)，获取你的生信专属答疑

<!-- wechat-article-fetcher: complete -->
