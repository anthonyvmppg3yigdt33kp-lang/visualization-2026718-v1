# 如何给 `$visualization-2026718-v1` 指令

高质量指令至少说明：科学问题、后端、输入对象、分组字段、允许改变的内容、需要的视觉通道、是否执行、是否检查原图和最终尺寸图。

## 1. 先设计，不执行

```text
使用 $visualization-2026718-v1。R 后端。我有一个已经完成 QC、归一化、聚类和 UMAP 的 Seurat 对象，分组字段是 cell_type。请先给出 PBMC 单细胞结果的可视化方案，包括 UMAP、marker 展示和 CellChat 通信视图；说明每张图回答什么问题、需要什么输入、能支持和不能支持什么结论。先不要运行代码。
```

期望返回：`FigureIntent`、科学设计与外观匹配、正式 Recipe 链、输入契约、风险和保守替代图。

## 2. UMAP 多风格执行与复核

```text
使用 $visualization-2026718-v1。R 后端。读取可信的本地 Seurat RDS，使用对象中已有的 umap reduction 和 cell_type；不要重算 UMAP、聚类或注释。组合 seurat embedding adapter 与正式 UMAP Recipe，生成：
1) 白底直接标签版；
2) 带坐标箭头版，必须明确“箭头不是轨迹”；
3) 深色 nebula 风格，halo 只作装饰并明确“不代表密度”；
4) 三联图。
先 preflight，再执行；分别导出原图和 300 dpi 最终尺寸图，最后用原生查看器复核裁切、标签、点、图例和免责声明。
```

本案例实际使用链：

```text
seurat-embedding-adapter-r-v1
  -> umap-dataframe-r-v1
  -> arrow-axes-r-v1 / dark-nebula-r-v1
```

## 3. marker dot plot

```text
使用 $visualization-2026718-v1。R 后端。基于 Seurat RNA assay 的 data layer 和 cell_type 分组，为每个群选定的 marker 做 dot plot。点面积必须表示表达比例（0-100），颜色必须表示每个基因跨群 z-scaled 的平均线性表达；图例标题写清楚。不要把细胞当作独立生物学重复。执行并检查原图与最终尺寸图。
```

本案例实际使用链：

```text
seurat-marker-summary-adapter-r-v1 -> marker-dotplot-r-v1
```

若你只说“比例”，旧式关键词路由可能把请求理解为细胞组成图；应同时给出 `marker`、`gene`、`点面积` 和 `颜色` 的语义。本仓库已加入回归测试，marker 语境现在优先于泛化的“比例”。

## 4. CellChat 四视图

```text
使用 $visualization-2026718-v1。R 后端。输入是已经完成推断的可信本地 CellChat 对象。请从 aggregate net$weight 和 subsetCommunication 结果生成：
1) 全网络 circle：边宽为相对聚合推断权重，节点大小为 incoming + outgoing；
2) directional chord：只显示权重最高的 35 条正边，并导出显示矩阵；
3) sender-receiver heatmap：完整未变换的 aggregate weight；
4) ligand-receptor bubble：CellChat p <= 0.05 后按 probability 取前 30，颜色为 probability，面积为 -log10(model p)，声明 p floor。
先列出 adapter/base Recipe 链并 preflight，再执行、导出和原生复核。所有图必须标注模型推断边界，不能写成真实物理通信或因果信号。
```

本案例实际使用链：

```text
cellchat-matrix-adapter-r-v1 -> circle / chord / heatmap
cellchat-lr-adapter-r-v1     -> bubble
```

## 5. 请求结果解读

```text
使用 $visualization-2026718-v1。请基于已生成 PNG、对应 R 代码、导出的表格和 manifest，按以下层级解读：
- visible：像素直接可见；
- interpretable：结合图例/代码可解释；
- confirmed：由数据表或对象确认；
- cannot_assert：目前不能断言。
重点解释 UMAP、marker dot plot 和 CellChat 四视图；不要把模型 p 值解释成跨供者生物学复现。
```

## 6. 最小验收清单

- 明确后端是 R 或 Python。
- 明确对象类型、数据层、分组字段和变量语义。
- 指定是否允许重新计算分析结果。
- 区分统计过滤和仅影响展示的 top-N。
- 要求物化代码、参数、输入/输出和版本记录。
- 同时检查原图与最终尺寸图。
- 要求列出不能由当前图支持的结论。
