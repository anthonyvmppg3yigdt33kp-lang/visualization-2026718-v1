---
name: visualization-2026718-v1
description: >-
  可视化2026718V1：面向生物医学、临床研究、统计分析和多组学的离线科研可视化决策与代码检索技能。支持从科学问题或模糊外观描述选择证据型图形，检索精确 Scheme，适配或组合 R/Python Recipe，按需渲染，原生像素复核，解释结果图，审计/更新本地图谱，并在严格 QA 后提升新 Recipe。Use when users ask for 科研绘图、绘图代码检索、匹配绘图模板、图册浏览、结果图解读、UMAP、dot/bubble plot、heatmap、volcano、GSEA/ORA、CellChat、survival、ROC、genomics、spatial 或 multipanel figures. Discovery can compare R and Python; executable adaptation, rendering, export, and QA require an explicit backend and remain backend-exclusive.
---

# 可视化2026718V1（V1.0.0）

把科研图形视为承载证据的视觉论证，而不是装饰。遵循：

`解析问题 -> 选择证据设计 -> 检索精确 Scheme -> 适配/组合 Recipe -> 按需渲染 -> 检查像素 -> 核对声明 -> 修订或重选`

## 能力边界

本技能提供七类能力：

1. `discover`：根据科学问题、数据结构、统计前提或外观描述推荐图形。
2. `adapt`：把已登记 Recipe 适配到用户的 R/Python 数据对象与字段。
3. `compose`：按契约组合 adapter、base recipe、modifier、layout 和 export。
4. `review`：基于实际像素、代码和可用数据解释结果图并执行视觉 QA。
5. `audit`：只读审计来源、Scheme、Recipe、覆盖率、谱系和导出状态。
6. `update`：确定性地摄取新来源并更新离线图谱，先 dry-run 后 apply。
7. `promote`：仅在代码、科学性、视觉、来源和导出 QA 均通过后提升候选 Recipe。

不把“相似图片”自动当作可执行代码，不把成功渲染自动当作科学结论，也不在未获授权时修改数据处理、阈值、统计检验或声明强度。

## 结构框架

```text
SKILL.md                         核心路由、执行门禁和交付规则
manifest.yaml                   版本、always_load、模式/后端路由和资源索引
agents/openai.yaml              UI 名称、简介和默认调用提示
static/core/                    始终加载的契约与科学立场
static/fragments/mode/          discover/adapt/compose/review/audit/update/promote
static/fragments/backend/       R 与 Python 的后端专属约束
references/                     本体、Scheme/Recipe schema、目录、索引和 QA 协议
assets/recipes/                 可调用、可验证的正式 Recipe
assets/scheme-candidates/       尚未提升的候选代码
assets/source_archive/          不可变来源快照
assets/previews-*/              人工复核参考图与精确渲染图
assets/fixtures/                测试数据与视觉缺陷样例
scripts/plot_library.py         统一检索、检查、组合、渲染、审计和更新 CLI
scripts/visual_review_controller.py  哈希绑定的视觉复核状态控制器
tests/                          意图解析、R/Python runtime 和视觉复核测试
../../examples/                 可复现的公开端到端教学案例
```

每次使用先读取 [manifest.yaml](manifest.yaml) 及 `always_load` 中的文件，再根据主模式与后端按需加载一个 fragment。需要 Scheme/Recipe、视觉复核、扩展或交付时，分别读取 manifest 指向的 reference；不要一次性加载全部大目录。

## 快速使用

### 1. 科学问题或样式检索

```text
python scripts/plot_library.py search --query "<request>" --top-k 3 --format json
python scripts/plot_library.py atlas --scope scientific --query "<appearance>" --top-k 5 --format json
python scripts/plot_library.py inspect --id <scheme-id> --include-lineage --include-visual
```

`search` 同时返回：

- `scientific_decisions`：问题、数据、统计与证据角色相容的设计；
- `appearance_matches`：图形 subtype、marks、channels、modifier 和 layout 的外观匹配。

优先科学相容性，再考虑外观。检查 `rejected_candidates`、`clarification`、`intent.action_intents`、`intent.review_after_execution`、`intent.source_lookup` 和 `intent.requires_executable`。若要求执行，只接受由正式 Recipe 支持的 `executable_plan`；不得执行 `visual_only`、`reference_only` 或非 callable 候选。

### 2. 适配与组合

执行前读取 [references/recipe-schema.md](references/recipe-schema.md)，仅使用声明链：

`adapter -> base_recipe -> semantic_modifier -> aesthetic_modifier -> layout -> export`

```text
python scripts/plot_library.py compose --backend <r|python> --adapter-id <id> --base-id <id> --modifier <id>
python scripts/plot_library.py preflight --backend <r|python> --base-id <id> --adapter-id <id> --modifier <id>
```

要求 `requires`、`provides`、`compatible_with` 和 `conflicts` 全部通过。不得任意拼接代码字符串。

- R：输出 callable function，并返回 plot、Heatmap 或 grob。
- Python：输出 importable function/module，并返回 Figure 或 Axes。
- 移除 install/download、workspace clearing、`setwd()`、私有路径、隐藏写入和来源专属对象。
- 保留过滤、归一化、阈值、检验和科学含义，除非用户明确批准改变。
- `compose` 必须返回 backend-pure 的 `build_plot` module 与 preflight 证据。
- 对 Seurat/CellChat RDS 仅接受用户明确确认可信的本地输入；未知来源 RDS 不得反序列化。
- 单细胞 marker 请求中的“表达比例”属于 marker 语义，不得仅凭“比例”误路由为细胞组成图。
- CellChat 语境优先解析 circle/chord/bubble/heatmap；只能连接声明兼容的 CellChat adapter 与 base Recipe。

### 3. 按需执行与导出

只有用户明确要求 run/render/export 时才执行。先读取 `executable_plan`，再对同一声明链运行 preflight 和 render：

```text
python scripts/plot_library.py preflight --recipe-id <recipe-id>
python scripts/plot_library.py render --recipe-id <recipe-id> --input <data> --output-dir <dir> --params-json <json> --review-state <state.json>
python scripts/plot_library.py render --scheme-id <scheme-id> --backend <r|python> --adapter-id <id> --base-id <id> --modifier <id> --input <data> --output-dir <dir> --params-json <json> --review-state <state.json>
```

显式绑定预聚合计数、分母、分组变量、阈值和科学参数。不得为了让图运行而猜测新的聚合方式。成功 render 仅表示 `rendered_pending_native_review`；若子进程非零退出、依赖缺失、绘图对象契约不支持或 runtime 崩溃，即使留下部分图片也视为阻断。

## 决策与科学门禁

### 构建 FigureIntent

记录已知值，未知字段写 `unknown`，不得猜测：

- 科学问题、暂定声明与证据角色；
- 分析单位与生物学重复层级；
- 数据对象、变量、分组、转换与统计量；
- marks、channels、高亮、标签、布局与输出场景；
- 后端（若已明确）。

缺失字段只有在会改变有效 Scheme、科学解释或后端时才追问。`p.adjust`、`GeneRatio`、`Count`、`avg.exp`、`pct.exp` 默认是变量名；只有用户明确索要源码、函数、标识符或包含某 token 的代码时才进入 source-code mode。严格区分 ORA 与 GSEA。

### 后端门禁

发现、只读审计和纯像素复核可保持 backend-neutral。任何可执行适配、组合、渲染、预览、导出或后端专属 QA 前，必须从用户选择或明确工件中解析出 Python/R。仍不明确时只问：**Python or R?** 然后停止。选定后，绘图、导出和 QA 全程保持该后端，禁止跨后端重绘。

### 推荐输出

最多返回三个真正不同的科学决策：

1. 主证据设计；
2. 最保守、最不易误读的替代方案；
3. 信息量更高的补充方案。

每项说明适配理由、视觉通道、所需输入/统计量、支持与禁止的声明、淘汰理由和伴随证据。例如，按条件着色的 UMAP 通常需要供体/样本层面的组成统计作为定量证据。

## 图像解释与原生视觉复核

读取 [references/visual-review-protocol.md](references/visual-review-protocol.md)。必须打开实际图片检查像素；只看代码不算视觉复核。声明证据层级：`pixels_only`、`image_metadata`、`image_code` 或 `image_code_data`，并依次报告：

1. 图中可见；
2. 结合图例或代码可解释为；
3. 经源数据或统计确认；
4. 目前不能据此断言；
5. `keep`、`revise` 或 `reselect`。

显式生成后，或 `review_after_execution=true` 时，同时打开 original 与 final-size PNG，填写哈希绑定的 review template，再执行：

```text
python scripts/visual_review_controller.py ingest-review --state <state.json> --review <review.json>
python scripts/visual_review_controller.py validate --state <state.json> --require-terminal
```

最多进行三轮已登记视觉参数修订，每轮都重新打开结果。改变数据、过滤、归一化、聚合/分母、阈值、检验、具有语义的 scale 或声明前必须征得用户同意。若无法原生查看图片，明确报告复核未完成。

## 审计、更新与提升

```text
python scripts/plot_library.py audit-source --source <archive>
python scripts/plot_library.py update --source <archive> --dry-run
python scripts/plot_library.py validate --all --strict
python scripts/plot_library.py validate --scheme-id <scheme-id>
python scripts/export_style_atlas.py --output-dir <dir> --scope all
python scripts/plot_library.py promote --candidate <id> --apply
```

添加来源或 Recipe 前读取 [references/extension-protocol.md](references/extension-protocol.md)，交付前读取 [references/qa-contract.md](references/qa-contract.md)。保持来源快照不可变；每个 block/image 必须有唯一 disposition；再生成时保留稳定 ID、别名、人工语义、排除项、Recipe 和 lineage。更新必须先 dry-run 后 apply。提升必须由用户明确要求，并且代码、科学、视觉、来源和导出均无 blocker/major finding。

## 交付契约

- 检索保持离线、确定性：不使用 embedding、网络、遥测或自动反馈学习。
- 默认隐藏本地路径、文件名、内部来源和用户历史；只有用户明确要求审计轨迹时披露。
- 区分 candidate、`parse_verified`、`reference_only`、`visual_only` 与正式 Recipe，不夸大验证级别。
- 报告实际运行的命令、通过/失败状态、阻断原因与仍未验证的假设。
- 图形声明不得超出分析单位、统计证据与可用数据支持的范围。
