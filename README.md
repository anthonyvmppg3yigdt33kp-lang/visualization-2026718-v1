# 可视化2026718V1

`可视化2026718V1` 是一个面向生物医学、临床研究、统计分析和多组学场景的离线科研可视化技能。它不只“找一张像的图”，而是先判断科学问题、分析单位、统计前提和证据角色，再检索可追踪的 Scheme，选择或组合已验证的 R/Python Recipe，并在用户明确要求后执行渲染和原生视觉复核。

当前发布版本：`V1.0.0`。机器可识别的 skill name 为 `visualization-2026718-v1`，Codex UI 显示名称为“可视化2026718V1”。

## 核心能力

- 科学图形决策：从研究问题和数据结构出发推荐主图、保守替代图和补充图。
- 双通道检索：同时返回科学证据设计与外观样式匹配，避免“好看但答非所问”。
- 离线图册浏览：按 scientific、modifier、resource、excluded 等 scope 检索本地图谱。
- R/Python 代码适配：将正式 Recipe 映射到用户对象、字段、分组和统计参数。
- 契约化组合：按 adapter → base recipe → modifier → layout → export 组合，拒绝任意代码拼接。
- 按需执行：只有用户明确要求时才 preflight、render 和 export，保留物化代码、参数与哈希。
- 科学结果解读：区分像素可见、图例/代码可解释、数据统计已确认和目前不能断言。
- 原生视觉 QA：检查原图与最终尺寸图片，支持最多三轮受控视觉修订。
- 图库维护：支持来源审计、dry-run 更新、Scheme/Recipe 验证、图册导出和显式 promotion。

## 工作流

```text
研究问题/外观描述
        ↓
FigureIntent（问题、分析单位、变量、统计、视觉通道、后端）
        ↓
scientific_decisions + appearance_matches
        ↓
Scheme（证据设计与来源谱系）
        ↓
adapter → base Recipe → modifiers → layout → export
        ↓
preflight → 按需 render → 原生像素复核 → keep/revise/reselect
```

## 仓库结构

```text
README.md
skill/
└─ visualization-2026718-v1/
   ├─ SKILL.md                 核心使用说明、门禁与交付契约
   ├─ manifest.yaml            版本、模式/后端路由和资源索引
   ├─ agents/openai.yaml       UI 元数据与默认调用提示
   ├─ static/                  核心契约、模式和后端 fragments
   ├─ references/              Scheme/Recipe schema、目录、索引和 QA 协议
   ├─ assets/                  Recipe、候选代码、来源快照、预览和 fixtures
   ├─ scripts/                 检索、组合、渲染、审计和视觉复核 CLI
   └─ tests/                   意图、runtime 与视觉复核测试
```

这种结构把“轻量路由说明”和“大型离线知识资产”分开：Codex 默认只加载 `SKILL.md`、manifest 和 `always_load`，其余资料按任务模式逐步加载。

## 安装

```powershell
git clone https://github.com/anthonyvmppg3yigdt33kp-lang/visualization-2026718-v1.git
Copy-Item -Recurse -Force `
  .\visualization-2026718-v1\skill\visualization-2026718-v1 `
  "$env:USERPROFILE\.codex\skills\visualization-2026718-v1"
```

重新启动或刷新 Codex 技能列表后，通过 `$visualization-2026718-v1` 显式调用。

核心检索、审计和验证 CLI 仅使用 Python 标准库。执行具体 Recipe 时，`preflight` 会按所选链检查依赖：Python Recipe 常用 `numpy`、`pandas`、`matplotlib`；R Recipe 可能需要 `ggplot2`、`ggrepel`、`patchwork`、`pROC`、`ComplexHeatmap`、`circlize` 或 `SeuratObject`。不建议预先安装全部依赖，应以实际 Recipe 的 `requires.packages` 为准。

## 使用示例

### 选择最合适的科研图

```text
使用 $visualization-2026718-v1。我的问题是比较肿瘤与邻近组织的细胞组成差异，数据有 donor、condition、cell_type。请先推荐证据设计，不要运行代码。
```

### 检索某种视觉样式

```text
使用 $visualization-2026718-v1。帮我找“带分组标签和重点基因标注的火山图”样式，给出最匹配的 Scheme、所需输入和不能支持的结论。
```

### 适配并运行 Python Recipe

```text
使用 $visualization-2026718-v1。Python。将 UMAP Recipe 适配到我的 DataFrame（umap1、umap2、cell_type），先 preflight，运行后检查原图和最终尺寸图。
```

### 解释已有结果图

```text
使用 $visualization-2026718-v1。请按 pixels_only / image_code / image_code_data 的证据层级解释这张图，并列出目前不能据此断言的内容。
```

### 审计与扩展图谱

```text
使用 $visualization-2026718-v1。只读审计这个来源归档的 Scheme 覆盖率、排除项和来源谱系；先不要 apply 或 promote。
```

## 常用命令

```text
python scripts/plot_library.py search --query "<request>" --top-k 3 --format json
python scripts/plot_library.py atlas --scope scientific --query "<appearance>" --top-k 5 --format json
python scripts/plot_library.py inspect --id <scheme-id> --include-lineage --include-visual
python scripts/plot_library.py preflight --recipe-id <recipe-id>
python scripts/plot_library.py render --recipe-id <recipe-id> --input <data> --output-dir <dir> --params-json <json> --review-state <state.json>
python scripts/plot_library.py validate --all --strict
```

详细规则、后端门禁、视觉复核和更新协议见 [SKILL.md](skill/visualization-2026718-v1/SKILL.md)。

## 关键原则与限制

- Discovery 可以比较 R 与 Python；执行、导出和 QA 必须先明确一个后端，并全程保持后端纯净。
- `visual_only`、`reference_only` 和候选源码不能冒充可执行正式 Recipe。
- render 成功只代表生成了待复核图片，不代表图形科学有效或可直接发表。
- 未经授权不改变过滤、归一化、聚合、分母、阈值、检验或声明强度。
- 该技能提供研究工程支持；最终统计、临床、伦理、隐私与发表判断仍需相应负责人复核。

## V1.0.0 发布重点

- 将用户可见名称统一为“可视化2026718V1”，机器名统一为 `visualization-2026718-v1`。
- 修复原说明中的中文编码损坏和 UI 元数据问题。
- 重写能力简介、工作流、结构框架、安装说明和典型用法。
- 保留原有离线 Scheme/Recipe 图谱、执行门禁、哈希绑定视觉复核和严格 QA 能力。

## 许可与素材说明

仓库原创代码与文档按 [MIT License](LICENSE) 提供。`skill/visualization-2026718-v1/assets/source_archive/`、来源图像、文章快照和由第三方来源衍生的素材不因进入本仓库而被重新授权；其权利仍归原作者或权利人所有，详见 [NOTICE.md](NOTICE.md)。公开仓库便于完整下载和本地复现，但使用者仍需自行确认特定素材的转载、公开展示和商业使用权限。
