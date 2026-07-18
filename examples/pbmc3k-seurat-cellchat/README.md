# PBMC3K：Seurat + 可视化2026718V1 + CellChat 教学案例

这是一次真实端到端验收，不是静态代码示例。案例从 10x Genomics 官方 PBMC3K 计数矩阵开始，在独立 `renv` 环境中完成 Seurat 基本流程，再由 `$visualization-2026718-v1` 的正式 Recipe 生成 UMAP、marker dot plot 以及 CellChat circle、chord、bubble、heatmap，最后对原图和最终尺寸图执行哈希绑定的原生视觉复核。

## 已验证结果

| 阶段 | 结果 |
|---|---:|
| 官方原始矩阵 | 32,738 genes × 2,700 cells |
| `CreateSeuratObject` 后 | 13,714 genes × 2,700 cells |
| 官方教程式 QC 后 | 13,714 genes × 2,638 cells |
| Seurat 聚类/注释 | 9 clusters / 9 cell types |
| marker 展示 | 每群 3 个，共 27 个 positive features |
| CellChat | 441 条 `p <= 0.05` 通信记录，15 条通路，74 条非零聚合边 |
| Skill 产图 | 9 个图形设计，原图和 300 dpi 成图各一份 |
| 原生视觉 QA | 9/9 终态 `keep`，均通过 `validate --require-terminal` |

完整数字、参数和声明边界见 [结果解读](RESULTS.zh-CN.md)，可复制指令见 [提示词指南](PROMPT_GUIDE.zh-CN.md)，已遇到并解决的障碍见 [故障排查](TROUBLESHOOTING.zh-CN.md)。

## 环境与数据

- R 4.5.3
- Seurat 5.4.0 / SeuratObject 5.4.0
- CellChat 2.2.0.9001（commit `75253cd0c9e68410e6e721a6d3a0419a1d7e358f`）
- ggplot2 4.0.3 / ComplexHeatmap 2.26.1 / circlize 0.4.18
- 固定随机种子：`20260718`
- PBMC3K 官方归档 SHA-256：`847d6ebd9a1ec9a768f2be7e40ca42cbfe75ebeb6d76a4c24167041699dc28b5`

`renv.lock` 固定完整依赖。原始矩阵和中间 RDS 不提交；下载脚本会从 10x Genomics 官方地址获取数据并先校验 SHA-256。

克隆后可先用 Python 标准库验证已提交案例的 JSON、关键依赖版本、阶段完成标记，以及 9 组审图记录与原图/终稿 PNG 的 SHA-256 绑定关系：

```powershell
python validate_case.py
```

## 从干净克隆复现

在仓库根目录进入案例：

```powershell
Set-Location .\examples\pbmc3k-seurat-cellchat
$env:VIS_SKILL_ROOT = (Resolve-Path '..\..\skill\visualization-2026718-v1').Path
$env:PBMC3K_PROJECT = (Get-Location).Path
```

恢复隔离依赖。首次执行会下载 R 包，耗时取决于网络和是否需要本地编译：

```powershell
Rscript -e "renv::restore(prompt = FALSE)"
```

依次执行：

```powershell
Rscript R/00_preflight.R
Rscript R/00_download_pbmc3k.R
Rscript R/01_seurat_pbmc3k.R
Rscript R/02_skill_visualizations.R
Rscript R/03_cellchat_pbmc3k.R
Rscript R/04_cellchat_visualizations.R
```

数据已下载后，也可让 `run_all.R` 连续执行四个分析/绘图阶段：

```powershell
Rscript R/run_all.R
```

正常环境不要设置 `PBMC3K_WINDOWS_EXIT_WORKAROUND`。只有复现 [特定 Windows UCRT 退出崩溃](TROUBLESHOOTING.zh-CN.md#windows-0xc0000005--ucrtbasedll) 时才考虑可选 workaround。

## 分析链

```text
official PBMC3K archive + SHA-256 check
  -> Seurat QC / LogNormalize / VST / PCA / neighbours / clustering / UMAP
  -> canonical-signature one-to-one cluster annotation
  -> positive markers
  -> Skill Seurat adapters
  -> clean / arrow-axis / dark-nebula UMAP + marker dot plot
  -> CellChatDB.human / triMean / aggregate network
  -> Skill CellChat adapters
  -> circle / top-35 chord / top-30 LR bubble / full heatmap
  -> original + final PNG native review with bound hashes
```

注释不依赖数字 cluster ID。脚本按 canonical signatures 计算每群得分，并用一对一最大权重分配；如果聚类结构或最低得分不符合预期会停止，而不是静默套用旧教程标签。

## 目录

```text
R/                    下载、preflight、Seurat、Skill 绘图和 CellChat 脚本
renv.lock             固定依赖
runtime/              仅供特定 Windows 退出崩溃使用的可选源码
artifacts/figures/    原始尺寸与最终 300 dpi PNG
artifacts/tables/     QC、注释、marker、CellChat 矩阵与通信表
artifacts/manifests/  数据、参数、版本、Recipe 和声明边界
artifacts/review/     与已提交 PNG 哈希绑定的原生复核记录
artifacts/logs/       完成标记与 sessionInfo
```

## 最重要的科学边界

这是一个公开单数据集的功能教学案例，不是 donor-level 比较。UMAP 不能证明轨迹或全局距离；marker dot plot 是描述性汇总；CellChat 是基于表达和数据库的模型推断，不能证明物理结合、分子通量、空间接触、因果信号或跨供者复现。图题、manifest 和审图记录都保留了这些限制。
