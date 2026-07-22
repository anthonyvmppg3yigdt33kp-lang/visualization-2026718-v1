---
name: visualization-2026718-v1
description: >-
  可视化2026718V1 public formal-Recipe runtime：面向生物医学、临床研究、统计分析和多组学，选择证据相容的正式图形 Recipe，适配或组合 R/Python 实现，按需渲染并完成原生像素复核。Use when users ask for 科研绘图、UMAP、dot/bubble plot、heatmap、volcano、GSEA/ORA、CellChat、survival、ROC、genomics、spatial 或 multipanel figures. Executable work requires an explicit backend and a formal Recipe.
---

# 可视化2026718V1：public formal-Recipe runtime

本安装由 `public-install-profile.json` 定义，只提供可公开分发的正式 Recipe
运行层。先读 [manifest.yaml](manifest.yaml)、`always_load` 契约和
[NOTICE.md](NOTICE.md)。

## 权利与能力边界

本 runtime 保留原创正式 Recipe、执行脚本、fixtures、渲染预览、科学与 QA
契约。以下内容不会被下载或安装：上游文章/图片快照、含抽取源码的完整
catalog、reference-only source-code candidates，以及第三方 curated previews。
这些排除项不得自动补下载、重建或从其他本机路径复制。

因此本 profile 支持：

1. 从正式 Recipe 和已净化索引中选择证据相容图形；
2. 在明确的 R 或 Python 后端中适配与组合正式 Recipe；
3. preflight、render/export、原图/终稿哈希绑定图审；
4. Seurat/Visium、单细胞、差异表达、富集、网络和多面板等已登记正式实现。

不支持上游 source archive 的全文检索、审计、摄取或更新，也不执行
`reference_only`、`visual_only` 或缺失 callable code 的候选。若请求依赖这些
能力，明确说明 public runtime 不包含该材料，并停止该分支。

## 工作流

`解析证据问题 -> 选择正式 Recipe -> 明确 backend -> preflight -> 适配/组合 -> 按需渲染 -> 打开像素 -> 核对声明`

### 选择

- 先核对分析单位、变量、统计量、声明强度和所需视觉通道。
- 只接受 `assets/recipes/<recipe-id>/recipe.json` 中具有 callable code、相容输入
  契约和可接受验证层级的正式 Recipe。
- 最多给三个真正不同且科学相容的方案；科学相容性优先于外观相似。
- 如果净化索引指向已排除 candidate/source path，将其视为不可用，不尝试恢复。

### 适配与执行

执行前读取 [references/recipe-schema.md](references/recipe-schema.md) 与
[references/qa-contract.md](references/qa-contract.md)。仅组合声明链：

`adapter -> base_recipe -> semantic_modifier -> aesthetic_modifier -> layout -> export`

- R/Python backend 必须在执行前明确，选定后禁止跨后端重绘。
- 运行前验证 `requires`、`provides`、`compatible_with` 和 `conflicts`。
- 不执行 install/download、workspace clearing、`setwd()`、私有路径或隐藏写入。
- 不为“让图跑起来”而改变过滤、归一化、阈值、检验、聚合或声明含义。
- Seurat Visium 使用 `seurat-spatial-overlay-r-v1`，先检查 Spatial assay、image、
  scale factors 与 barcode-coordinate 对账，并保留 Seurat 坐标绘图接口。
- 该 Recipe 的 `verified` 证据边界是独立 upstream harness 在一个可信 Seurat
  对象上的执行，不是对生成对象的工作流或外层 CLI wrapper 的背书。11 个标签仅作
  expression-derived spot clusters，Hpca/Ttr overlay 仅作描述性展示。

### 图审与交付

读取 [references/visual-review-protocol.md](references/visual-review-protocol.md)。
生成图仅代表 `rendered_pending_native_review`；必须实际打开 original/final PNG，
记录当前 SHA-256、发现和 `keep|revise|reselect|blocked`。最多三轮纯视觉修订；
每轮都保持数据和分析参数不变。任何子进程非零、warning/error gate、对象契约
失败或未完成图审都必须明确阻断。

交付时报告实际命令、环境、输入/参数边界、输出、验证状态、仍未验证假设和
允许/禁止的科学声明。MIT 仅覆盖原创代码与文档；第三方或数据衍生素材遵循
本包 NOTICE 和各自许可。
