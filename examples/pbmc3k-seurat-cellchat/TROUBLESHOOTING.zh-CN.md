# 故障排查与本次修复

## Skill 路由误判

本次真实请求暴露并修复了三个路由问题，并加入回归测试：

1. “生成后复核”原先只进入 render，没有保留 review 动作；现在 `review_after_execution` 会被识别。
2. marker 请求包含“表达比例”时曾被泛化为细胞组成图；现在 marker/gene/dotplot 语境优先。
3. CellChat 多视图请求曾误配 marker dotplot/heatmap；现在 CellChat context 和 circle/chord/bubble/heatmap subtype 优先，adapter 兼容性也限制到真实 CellChat 链。

验证入口：

```powershell
Set-Location ..\..\skill\visualization-2026718-v1
python -m pytest -q
python scripts/plot_library.py validate --all --strict
```

## CellChat 要求 `presto`

症状：

```text
For a faster implementation of the Wilcoxon Test, please install the presto package
Otherwise, please set do.fast = FALSE
```

`presto` 是可选加速依赖。案例使用标准 Wilcoxon 路径：

```r
cellchat <- CellChat::identifyOverExpressedGenes(cellchat, do.fast = FALSE)
```

这样不改变检验类型，只牺牲部分速度，并减少一个非必要依赖。

## `CellChatDB.human` 不是 namespace export

不要假定 `CellChat::CellChatDB.human` 可用。开发版中稳妥写法是：

```r
utils::data("CellChatDB.human", package = "CellChat", envir = environment())
cellchat@DB <- CellChatDB.human
```

preflight 会确认数据库对象存在。

## Seurat 数字 cluster ID 与旧教程不一致

聚类 ID 只是当前图上的任意编号，版本、随机算法和参数都可能改变其顺序。禁止按 `0:8` 直接硬编码旧教程的细胞类型。本案例：

- 用 canonical signatures 对每个群计算平均表达和 z-score；
- 用 `clue::solve_LSAP(..., maximum = TRUE)` 做一对一最大权重分配；
- 检查聚类集合和最低分配得分；
- 输出完整 score/mapping 表。

若新版本产生不同聚类数或低分配得分，脚本会停止，要求人工检查。

## Windows `0xC0000005` / `ucrtbase.dll`

本次宿主机上，R 4.5.2 和 4.5.3 在加载 `rlang`/`ggplot2`/Seurat/CellChat 后，分析可完成但进程退出时以 Windows exception `0xC0000005` 崩溃；事件日志把 faulting module 指向 `ucrtbase.dll`。从源码重装 `rlang`/`cli` 仍复现，因此判断为宿主 C runtime 退出路径问题，而非本 Skill 的绘图逻辑。

优先处理：

1. 在另一台干净机器或 CI 中复现；
2. 更新/修复 Windows 与 Visual C++ Runtime；
3. 尝试与锁文件兼容的独立 R 安装；
4. 确认分析阶段有没有真实 R error，不能只看最终异常码。

只有精确复现“输出已全部写完、completion marker 已写、随后 shutdown 崩溃”的情况，才可按 `runtime/README.md` 编译并启用可选 workaround。它用 Windows API 在成功标记后终止进程，会跳过正常 R shutdown，绝不能作为默认设置，也不能掩盖分析中途错误。

## `renv` out-of-sync

如修改脚本但没有改变依赖，可先运行：

```r
renv::status()
```

如依赖确实改变，审查后再 `renv::snapshot()`。不要在未审查差异时盲目重写锁文件。Linux/macOS 可能需要系统编译器和字体/图形库；Windows 需要与 R 对应的 Rtools 才能编译源码包。

## RDS 安全

RDS 反序列化不是安全的通用数据交换方式。本 Skill runtime 只允许明确可信的本地 `.rds` 输入。不要运行从未知来源下载的 Seurat/CellChat RDS；公开案例通过官方下载原始计数并本地生成对象。
