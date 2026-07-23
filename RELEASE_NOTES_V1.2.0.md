# 可视化2026718V1 — V1.2.0

V1.2.0 增加了面向研究者在环单细胞/空间教学工作流的声明式 R Recipe，同时保留
既有 v1 ID 作为显式兼容接口。本技能辅助科研绘图决策、代码执行和结果图复核，不
自动完成科研判断，也不替代统计、临床、伦理或发表责任。

## 新增

- `seurat-embedding-adapter-r-v2 -> umap-dataframe-r-v2`：读取既有 Seurat UMAP 与
  metadata group，不重算坐标或改写组别。
- `seurat-marker-summary-adapter-r-v2 -> marker-dotplot-r-v2`：显式绑定 assay、
  layer、average transform、group、scaling 和 percent denominator。
- `seurat-spatial-overlay-r-v2`：在 assay/image/scale/barcode-coordinate 门禁后，
  使用官方 Seurat spatial plot 路径绘制 identity 或已有 feature values。
- `declared-only` runtime gate：拒绝未声明参数、输入对象重绑定和未登记的视觉修订。
- `build_public_runtime.py build|verify`：确定性应用公开安装 profile、拒绝覆盖，生成
  相对路径/大小/内容 SHA-256 清单。

## 真实数据证据

- PBMC3K：hash-bound 2,638-cell Seurat 对象、9 个 descriptive teaching labels；
  UMAP round 1 `KEEP`。
- PBMC3K marker：12 个声明 marker；round 1 发现 `axis_label_clipped` major，只有
  label rotation（60°→90°）与画布高度（125→140 mm）发生改变，round 2 `KEEP`。
- Visium Mouse Brain Sagittal-Anterior：2,695 spots，Spatial assay、image 与
  coordinates 六向差集均为 0；identity 与 Hpca/Ttr original/final 四图均 `KEEP`。

全部成功证据绑定 Recipe、materialized code、输入对象、环境 lock 与 PNG SHA-256。
pre-fix palette 类型错误、未限定 `ave()`、不兼容的 `SpatialFeaturePlot(cols=...)` 和
warning-emitting 中间实现均明确排除，未复用为成功证据。

## 兼容与升级

- 不静默迁移已有 v1 plan/provenance；需要 v2 契约时必须显式选择 v2 ID。
- 从 clean clone 运行 public-runtime builder，再执行 `verify`。升级时先生成新的
  versioned 目录并校验，保留当前安装备份后再替换，避免叠加 stale assets。
- Windows PowerShell 调用 `render` 时优先传入 UTF-8 参数 JSON 文件，避免内联 JSON
  的 shell 引号歧义。
- 上游 audit checkout 含 mixed-rights 来源材料；Codex task-local 安装以
  `public-install-profile.json` 为唯一边界，不自动恢复被排除内容。

## 科学边界

- UMAP 不支持 abundance、trajectory 或 significance 结论。
- marker dot plot 是描述性 cell-group summary，不是 differential-expression 检验。
- Visium cluster 是 expression-derived spot clusters，不是已验证 cell types 或
  anatomical regions；feature overlay 不建立 enrichment、机制或因果。
- 所有结果仍需研究者检查输入、参数、像素、统计假设和声明强度。
