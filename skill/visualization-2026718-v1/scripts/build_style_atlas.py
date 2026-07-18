#!/usr/bin/env python3
"""Build a deterministic article-by-style atlas from the bundled plot catalog.

The atlas is an index over private source material, not a promotion mechanism.
It links scientific use, source code blocks, one representative source image,
and the nearest formal Recipe without claiming that source-only code is safe or
directly executable.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "catalog.jsonl"
ATLAS_PATH = SKILL_ROOT / "references" / "style-atlas.jsonl"
SUMMARY_PATH = SKILL_ROOT / "references" / "style-coverage.json"


FAMILY_NORMALIZATION = {
    "axis_style": "embedding",
    "theme": "layout",
    "labeling": "layout",
    "dotplot_annotation": "dotplot",
    "multipanel": "layout",
    "export": "layout",
    "network": "cellchat_chord",
    "enrichment": "gsea",
}


FAMILY_LABELS = {
    "embedding": "降维与嵌入图",
    "dotplot": "气泡图与点图",
    "heatmap": "热图",
    "volcano": "火山图",
    "gsea": "富集分析图",
    "boxplot": "箱线图与散点叠加",
    "violin": "小提琴图、山脊图与分布图",
    "composition": "组成与比例图",
    "cellchat_chord": "细胞通讯与弦图",
    "flow": "桑基图与冲积图",
    "correlation": "相关性、散点与三元图",
    "set_intersection": "集合交集图",
    "survival": "生存分析图",
    "roc": "ROC与判别性能图",
    "genomics": "基因组与突变图",
    "spatial_image": "空间组学与组织图像叠加",
    "trajectory": "轨迹与拟时序图",
    "layout": "布局与注释组件",
    "palette": "配色资源",
    "decorative": "装饰性绘图",
    "unknown": "未归类绘图资源",
}


SEMANTICS: dict[str, dict[str, Any]] = {
    "embedding": {
        "analysis_use": "展示样本、细胞或特征在降维空间中的结构、分群、混合程度和标签分布。",
        "visual_channels": {"x_y": "预计算嵌入坐标", "color": "分组、细胞类型或连续特征", "annotation": "标签、圈选或箭头坐标"},
        "required_inputs": ["两列嵌入坐标", "分组或连续特征", "可选标签/分面变量"],
        "supported_claims": ["展示降维空间中的局部邻域、标签分布和可见混合模式。"],
        "claim_limits": ["不能单独证明组间丰度差异、统计显著性、轨迹方向、全局距离或因果关系。"],
        "recommended_companion": "若比较条件差异，搭配 donor/sample-level 组成或效应量图。",
        "keywords": ["UMAP", "t-SNE", "PCA", "PCoA", "降维", "分群", "云雾", "星云", "圈选", "箭头坐标"],
    },
    "dotplot": {
        "analysis_use": "同时比较多个分组和多个基因、通路或互作的两个汇总量。",
        "visual_channels": {"x_y": "分组×特征", "color": "平均值、效应或方向", "size": "比例、计数或显著性"},
        "required_inputs": ["分组", "特征", "颜色变量", "大小变量", "可选显著性/marker分组"],
        "supported_claims": ["展示两个已声明的汇总量在分组和特征间的模式。"],
        "claim_limits": ["不能仅凭颜色或点大小宣称 marker 显著、独立重复或因果机制。"],
        "recommended_companion": "搭配差异分析效应量/FDR表或独立样本汇总。",
        "keywords": ["DotPlot", "bubble", "气泡图", "点图", "marker", "平均表达", "表达比例"],
    },
    "heatmap": {
        "analysis_use": "展示矩阵中的相对模式、聚类、方向、共变结构及多层注释。",
        "visual_channels": {"row_column": "特征×样本/分组", "color": "声明尺度下的数值", "annotation": "临床、分组或通路信息"},
        "required_inputs": ["数值矩阵", "行列标签", "缩放/聚类方法", "可选注释表"],
        "supported_claims": ["展示在明确缩放和聚类规则下的相对高低、共变和分组模式。"],
        "claim_limits": ["行缩放颜色不等同绝对表达；不能从像素推断显著性或未声明的标准化。"],
        "recommended_companion": "搭配色标、转换说明及效应量/不确定性图。",
        "keywords": ["heatmap", "ComplexHeatmap", "pheatmap", "热图", "聚类", "注释条", "相关性热图"],
    },
    "volcano": {
        "analysis_use": "同时展示差异效应方向/大小与统计证据，并突出目标特征。",
        "visual_channels": {"x": "效应量或 log2 fold-change", "y": "-log10(P/FDR)", "color_label": "阈值分组和重点特征"},
        "required_inputs": ["效应量", "P值或FDR", "特征名", "明确阈值"],
        "supported_claims": ["展示声明阈值下的差异效应和统计证据分布。"],
        "claim_limits": ["显著不自动等于生物学重要、可重复或因果。"],
        "recommended_companion": "搭配标注效应表、独立验证或样本级分布图。",
        "keywords": ["volcano", "火山图", "log2FC", "FDR", "差异表达", "分组火山图", "标签"],
    },
    "gsea": {
        "analysis_use": "展示基因集/通路富集方向、强度、显著性、排序位置或类别结构。",
        "visual_channels": {"x": "排序位置、NES或效应", "y": "通路/类别或运行富集分数", "color_size": "方向、FDR、基因数"},
        "required_inputs": ["通路名称", "富集方向/分数", "FDR", "可选 leading-edge/基因数"],
        "supported_claims": ["展示在已声明富集方法和背景下的通路方向与统计证据。"],
        "claim_limits": ["不能自动解释为每个细胞的通路活性、机制或因果关系。"],
        "recommended_companion": "搭配 leading-edge、表达证据或正交实验。",
        "keywords": ["GSEA", "GO", "KEGG", "富集", "NES", "FDR", "玫瑰图", "流星图", "条形图"],
    },
    "boxplot": {
        "analysis_use": "比较连续变量在组间、时间点或独立样本中的分布与差异。",
        "visual_channels": {"x": "组别/时间点", "y": "连续测量", "point_line": "独立样本或配对关系"},
        "required_inputs": ["数值变量", "分组", "独立样本ID", "可选配对ID和统计结果"],
        "supported_claims": ["展示样本级分布、中心趋势和离散程度；有统计输入时可支持声明的比较。"],
        "claim_limits": ["细胞行不能替代 donor/sample 独立重复；箱体本身不证明显著。"],
        "recommended_companion": "优先叠加原始样本点、效应量和置信区间。",
        "keywords": ["boxplot", "箱线图", "jitter", "散点", "组间差异", "配对", "样本级"],
    },
    "violin": {
        "analysis_use": "展示连续变量的密度形状、亚群分布、偏态或多峰结构。",
        "visual_channels": {"x_y": "组别×连续测量", "width": "核密度", "color_facet": "分组或特征"},
        "required_inputs": ["连续变量", "分组", "明确分析单位", "可选样本点"],
        "supported_claims": ["展示在给定带宽和尺度下的分布形状及组间可见差异。"],
        "claim_limits": ["密度宽度不是样本量；不能把细胞当作生物学独立重复。"],
        "recommended_companion": "搭配样本级点、箱线/区间或正式模型。",
        "keywords": ["violin", "小提琴图", "ridge", "ridgeline", "山脊图", "山峦图", "密度"],
    },
    "composition": {
        "analysis_use": "展示类别组成、比例、数量及其在条件、样本或空间生态位间的变化。",
        "visual_channels": {"x": "样本/条件/生态位", "y": "计数或比例", "fill": "类别", "line": "可选对应关系"},
        "required_inputs": ["样本ID", "条件", "类别", "计数或明确分母的比例"],
        "supported_claims": ["展示声明分母下的类别组成及样本间变化。"],
        "claim_limits": ["堆积高度不能替代组成统计模型；细胞数不是样本重复。"],
        "recommended_companion": "搭配 donor/sample-level 点图、区间或 composition-aware 模型。",
        "keywords": ["stacked bar", "堆积柱状图", "组成", "比例", "生态位", "连线堆积", "双向条形图"],
    },
    "cellchat_chord": {
        "analysis_use": "展示 CellChat 等模型推断的细胞通讯网络、方向、权重和汇总结构。",
        "visual_channels": {"node_sector": "细胞群/配体受体类别", "edge": "推断互作", "width_color": "权重、方向或类型"},
        "required_inputs": ["节点/细胞群", "有向或无向互作矩阵", "权重", "可选通路/配体受体"],
        "supported_claims": ["展示计算模型推断的通讯结构或汇总得分。"],
        "claim_limits": ["不能表述为已证实的物理通讯、分子通量或因果机制。"],
        "recommended_companion": "搭配配体受体表达、空间邻近和扰动验证。",
        "keywords": ["CellChat", "弦图", "chord", "细胞通讯", "网络", "互作", "贝壳图"],
    },
    "flow": {
        "analysis_use": "展示类别、状态、通路与基因之间的多阶段映射或流向。",
        "visual_channels": {"axis_node": "阶段/类别", "flow_width": "数量或权重", "color": "来源或目标类别"},
        "required_inputs": ["源节点", "目标节点", "权重", "可选多阶段路径"],
        "supported_claims": ["展示声明节点之间的映射结构和相对流量。"],
        "claim_limits": ["流向不自动代表时间、因果或真实物质通量。"],
        "recommended_companion": "搭配节点级定量表或统计比较。",
        "keywords": ["Sankey", "桑基图", "alluvial", "冲积图", "流图", "通路-基因"],
    },
    "correlation": {
        "analysis_use": "展示两个或多个连续变量的关系、相关趋势、回归或三元组成。",
        "visual_channels": {"x_y": "变量或组成轴", "point": "样本", "line": "拟合趋势", "color": "分组/第三变量"},
        "required_inputs": ["成对数值", "独立样本ID", "相关/回归方法", "可选分组"],
        "supported_claims": ["展示样本级关联、方向和声明模型的拟合趋势。"],
        "claim_limits": ["相关不等于因果；离群点、重复测量和多重检验必须另行处理。"],
        "recommended_companion": "搭配效应量、置信区间、样本量和敏感性分析。",
        "keywords": ["correlation", "scatter", "相关性", "散点图", "回归", "ternary", "三元图"],
    },
    "set_intersection": {
        "analysis_use": "比较多个集合的交集、独有元素和组合规模。",
        "visual_channels": {"set_axis": "集合", "intersection_bar": "交集大小", "matrix_or_region": "集合组合"},
        "required_inputs": ["集合成员关系或逻辑矩阵", "集合名称", "可选交集权重"],
        "supported_claims": ["展示明确集合定义下的交集和独有元素规模。"],
        "claim_limits": ["交集不代表统计富集、功能相似或因果联系。"],
        "recommended_companion": "需要推断时搭配超几何/Fisher检验及背景集合。",
        "keywords": ["UpSet", "Venn", "韦恩图", "交集", "集合", "ComplexUpset"],
    },
    "survival": {
        "analysis_use": "展示随访时间内的事件发生、风险集和组间生存差异。",
        "visual_channels": {"x": "时间", "y": "生存/累积事件概率", "curve": "组别", "risk_table": "在险人数"},
        "required_inputs": ["随访时间", "事件状态", "分组/协变量", "删失信息", "可选调整模型"],
        "supported_claims": ["展示时间结局模式及声明模型下的组间关联。"],
        "claim_limits": ["不能自动证明因果、比例风险假设或外部泛化。"],
        "recommended_companion": "搭配风险表、HR及CI、PH诊断和调整模型。",
        "keywords": ["Kaplan-Meier", "survival", "生存曲线", "风险表", "Cox", "HR"],
    },
    "roc": {
        "analysis_use": "评价连续评分或模型对二分类结局的区分能力。",
        "visual_channels": {"x": "1-specificity/FPR", "y": "sensitivity/TPR", "curve": "模型/标志物", "annotation": "AUC及CI"},
        "required_inputs": ["真实二分类结局", "连续预测分数", "独立验证划分", "可选AUC置信区间"],
        "supported_claims": ["展示指定队列和划分中的区分能力。"],
        "claim_limits": ["ROC不能自动证明校准、临床效用、外部泛化或因果获益。"],
        "recommended_companion": "搭配校准曲线、PR曲线、决策曲线和外部验证。",
        "keywords": ["ROC", "AUC", "敏感度", "特异度", "诊断", "判别能力"],
    },
    "genomics": {
        "analysis_use": "展示突变位点、蛋白结构域、样本突变谱或基因组轨道。",
        "visual_channels": {"x": "基因/蛋白/基因组位置", "y": "频率/样本/轨道", "shape_color": "突变类型或功能类别"},
        "required_inputs": ["基因/蛋白坐标", "突变或事件", "样本ID", "注释类别"],
        "supported_claims": ["展示已检测事件的分布、频率和注释结构。"],
        "claim_limits": ["不能从图形本身推断功能影响、克隆演化或驱动因果。"],
        "recommended_companion": "搭配统计富集、功能注释和正交验证。",
        "keywords": ["lollipop", "棒棒糖图", "MAF", "oncoplot", "maftools", "GenVisR", "突变"],
    },
    "spatial_image": {
        "analysis_use": "将细胞、分割、表达或区域标签叠加到 H&E、荧光或空间组织图像。",
        "visual_channels": {"background": "组织/荧光图像", "position": "空间坐标", "color_shape": "细胞类型、表达或分割"},
        "required_inputs": ["组织图像", "对齐空间坐标", "细胞/spot标签", "尺度和分割信息"],
        "supported_claims": ["展示声明配准和分割下的可见空间定位或共定位。"],
        "claim_limits": ["不能仅凭像素证明分子互作、区域富集显著性或因果。"],
        "recommended_companion": "搭配区域级定量、空间统计和不确定性。",
        "keywords": ["Xenium", "spatial", "H&E", "HE切片", "荧光", "空间定位", "segmentation"],
    },
    "trajectory": {
        "analysis_use": "展示算法推断的细胞状态连续性、分支结构和拟时序变化。",
        "visual_channels": {"position": "嵌入或轨迹坐标", "line_graph": "推断主干/分支", "color": "拟时序、状态或基因表达"},
        "required_inputs": ["细胞嵌入/轨迹对象", "拟时序或状态", "根节点/方向假设", "可选特征动态"],
        "supported_claims": ["展示指定算法和根节点下的相对状态顺序与分支结构。"],
        "claim_limits": ["不能自动证明真实时间方向、谱系祖先或因果分化。"],
        "recommended_companion": "搭配时间点、RNA velocity、谱系追踪或扰动证据。",
        "keywords": ["pseudotime", "trajectory", "拟时序", "轨迹", "Monocle", "分支"],
    },
    "layout": {
        "analysis_use": "组织多面板、共享图例、注释或底层 grid/grob 元素，不单独承担科学结论。",
        "visual_channels": {"layout": "面板层级与对齐", "legend": "共享映射", "annotation": "标题、标注和强调"},
        "required_inputs": ["一个或多个现有图形对象", "目标尺寸", "共享图例/面板规则"],
        "supported_claims": ["改善证据顺序、对齐和跨面板可读性。"],
        "claim_limits": ["布局和美化不能补偿数据、统计或科学设计不足。"],
        "recommended_companion": "与能够回答科学问题的 base Recipe 组合。",
        "keywords": ["patchwork", "grid", "grob", "多面板", "拼图", "共享图例", "布局"],
    },
    "palette": {
        "analysis_use": "选择或提取配色并保持跨面板类别一致性。",
        "visual_channels": {"color": "类别、方向或连续数值"},
        "required_inputs": ["变量类型", "类别数或数值范围", "背景/期刊约束"],
        "supported_claims": ["改善辨识度、风格一致性和视觉层级。"],
        "claim_limits": ["配色不改变证据强度；不得使用颜色作为唯一关键信息载体。"],
        "recommended_companion": "结合色盲、灰度和最终尺寸检查。",
        "keywords": ["palette", "配色", "取色", "动漫配色", "期刊配色", "color"],
    },
    "decorative": {
        "analysis_use": "装饰性或演示性绘图，不作为科研结果证据。",
        "visual_channels": {"position_color_shape": "装饰元素"},
        "required_inputs": ["装饰目标和输出尺寸"],
        "supported_claims": ["可用于演示绘图语法或节日视觉。"],
        "claim_limits": ["不支持科研或统计结论。"],
        "recommended_companion": "科研任务应重新选择证据型图形。",
        "keywords": ["装饰", "圣诞树", "动画", "demonstration"],
    },
    "unknown": {
        "analysis_use": "尚未稳定归入受控图形家族的来源资源，使用前需先审计代码与图像语义。",
        "visual_channels": {"unknown": "需逐项核对"},
        "required_inputs": ["原始文章上下文", "代码", "结果图", "预期科学问题"],
        "supported_claims": ["仅作为检索线索。"],
        "claim_limits": ["未审计前不应作为正式可执行模板或科学结论依据。"],
        "recommended_companion": "先执行 inspect 和视觉审阅，再决定是否蒸馏。",
        "keywords": ["未归类", "reference-only", "待审计"],
    },
}


PLOT_CALL_RE = re.compile(
    r"(?i)(ggplot\s*\(|geom_[a-z_]+\s*\(|\bplot\s*\(|DimPlot\s*\(|FeaturePlot\s*\(|"
    r"DotPlot\s*\(|VlnPlot\s*\(|Heatmap\s*\(|pheatmap\s*\(|ggsurvplot\s*\(|"
    r"chordDiagram\s*\(|circos\.|upset\s*\(|ggsave\s*\(|imshow\s*\(|scatter\s*\()"
)


FAMILY_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("survival", re.compile(r"(?i)survfit|ggsurvplot|coxph|kaplan|risk\s*table|生存曲线")),
    ("roc", re.compile(r"(?i)\bggroc\b|pROC::roc|\broc\s*\(|roc_curve|receiver operating|\bauc\b|ROC曲线")),
    ("trajectory", re.compile(r"(?i)pseudotime|monocle|plot_cells|learn_graph|order_cells|拟时序|轨迹")),
    ("spatial_image", re.compile(r"(?i)xenium|spatial|h\s*&\s*e|he切片|荧光|segmentation|imshow")),
    ("set_intersection", re.compile(r"(?i)complexupset|upset\s*\(|venn\.?diagram|ggvenn|韦恩|交集")),
    ("flow", re.compile(r"(?i)ggalluvial|geom_alluvium|geom_stratum|sankey|桑基|冲积")),
    ("dotplot", re.compile(r"(?i)dotplot\s*\(|netvisual_bubble|avg\.?(?:exp|expr)|pct\.?(?:exp|expr)|气泡图|泡泡图|bubble\s*plot")),
    ("cellchat_chord", re.compile(r"(?i)chorddiagram|circos\.link|netvisual|cellchat|弦图|细胞通讯|互作")),
    ("genomics", re.compile(r"(?i)maftools|genvisr|lollipop|oncoplot|plotmaf|棒棒糖|突变谱")),
    ("heatmap", re.compile(r"(?i)complexheatmap|\bheatmap\s*\(|pheatmap|geom_tile|热图")),
    ("volcano", re.compile(r"(?i)volcano|log2?fc|fold.?change|火山图|significance.*geom_point")),
    ("violin", re.compile(r"(?i)geom_violin|vlnplot|ggridges|geom_density_ridges|小提琴|山脊|山峦")),
    ("boxplot", re.compile(r"(?i)geom_boxplot|ggboxplot|boxplot\s*\(|箱线图|箱图")),
    ("composition", re.compile(r"(?i)position\s*=\s*[\"']fill|geom_bar|geom_col|stacked|堆积|组成|比例|双向.*条形|背靠背")),
    ("gsea", re.compile(r"(?i)gseaplot|fgsea|enrichplot|\bNES\b|gene.?set|enrichment|kegg|go富集|通路|富集")),
    ("correlation", re.compile(r"(?i)stat_cor|geom_smooth|corrplot|ggscatter|ternary|三元图|相关性|散点图|cor\.test")),
    ("embedding", re.compile(r"(?i)dimpl?ot|featureplot|runumap|umap|t-?sne|\bpca\b|\bpcoa\b|nmds|降维|主成分")),
    ("layout", re.compile(r"(?i)patchwork|plot_grid|grid\.arrange|grob|viewport|共享图例|拼图|布局")),
    ("palette", re.compile(r"(?i)palette|scale_(?:color|colour|fill)_manual|配色|取色|调色")),
    ("decorative", re.compile(r"(?i)christmas|圣诞树|gganimate")),
)


RESOURCE_TITLE_RE = re.compile(r"(?i)(版本发布|图片配色|动漫配色|圣诞树|绘图大全|一键美化|不要被ggplot2洗脑|工具介绍)")


def canonical_family(value: Any) -> str:
    family = str(value or "unknown").strip().lower().replace(" ", "_")
    return FAMILY_NORMALIZATION.get(family, family)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Expected an object at {path}:{line_number}")
            records.append(value)
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def block_family(block: dict[str, Any], article_title: str = "") -> str:
    text = "\n".join((str(block.get("heading") or ""), str(block.get("code") or "")))
    # Resolve two common visual ambiguities before generic code-term matching:
    # Chinese "散点图" contains "点图", and CellChat bubble calls also contain
    # the broader CellChat/network vocabulary.
    if re.search(r"(?i)散点图|scatter", article_title) and not re.search(r"(?i)火山图|volcano", article_title):
        if re.search(r"(?i)geom_point|scatter\s*\(|ggplot\s*\(", text):
            return "correlation"
    if re.search(r"(?i)气泡图|泡泡图|dotplot|bubble", article_title):
        if re.search(r"(?i)dotplot\s*\(|netvisual_bubble|geom_point|bubble", text):
            return "dotplot"
    for family, pattern in FAMILY_RULES:
        if pattern.search(text):
            return family
    for family, pattern in FAMILY_RULES:
        if pattern.search(article_title):
            return family
    return canonical_family(block.get("family"))


def plot_like(block: dict[str, Any]) -> bool:
    if block.get("role") == "plot":
        return True
    if block.get("role") in {"install", "non_code", "data_prep"}:
        return False
    return bool(PLOT_CALL_RE.search(str(block.get("code") or "")))


def source_recipe_ids(recipe: dict[str, Any]) -> set[str]:
    articles = (recipe.get("source") or {}).get("articles") or []
    result = set()
    for item in articles:
        if isinstance(item, dict) and item.get("source_id"):
            result.add(str(item["source_id"]))
    return result


def image_score(image: dict[str, Any], family_block_ids: set[str], family: str) -> tuple[float, str]:
    role_score = {
        "scientific_result": 100.0,
        "published_reference": 70.0,
        "intermediate_step": 35.0,
        "uncertain": 15.0,
    }.get(str(image.get("role")), -1000.0)
    if role_score < 0:
        return role_score, str(image.get("id"))
    score = role_score
    if image.get("reviewed") is True:
        score += 30.0
    if image.get("nearest_block_id") in family_block_ids:
        score += 25.0
    if canonical_family(image.get("family")) == family:
        score += 10.0
    metadata = image.get("metadata") or {}
    if metadata.get("readable") is True:
        score += 5.0
    area = int(metadata.get("width") or 0) * int(metadata.get("height") or 0)
    score += min(area / 10_000_000, 2.0)
    score += min(float(image.get("line") or 0) / 100_000, 0.01)
    return score, str(image.get("id"))


def coverage_status(
    family: str,
    article_title: str,
    exact_recipe_ids: list[str],
    family_recipe_ids: list[str],
    code_available: bool,
    image_available: bool,
) -> str:
    if exact_recipe_ids:
        return "formal_exact"
    if family_recipe_ids:
        return "formal_family"
    if family in {"palette", "decorative", "unknown"}:
        return "resource_only"
    if RESOURCE_TITLE_RE.search(article_title):
        return "source_only" if code_available and image_available else "resource_only"
    if code_available and image_available:
        return "source_only"
    if code_available:
        return "code_only"
    if image_available:
        return "visual_only"
    return "resource_only"


def build_cards(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    articles = {record["id"]: record for record in records if record.get("record_type") == "article"}
    blocks_by_article: dict[str, list[dict[str, Any]]] = defaultdict(list)
    images_by_article: dict[str, list[dict[str, Any]]] = defaultdict(list)
    recipes = [record for record in records if record.get("record_type") == "recipe"]
    for record in records:
        if record.get("record_type") == "source_block":
            blocks_by_article[str(record.get("article_id"))].append(record)
        elif record.get("record_type") == "image":
            images_by_article[str(record.get("article_id"))].append(record)

    recipe_sources = {recipe["id"]: source_recipe_ids(recipe) for recipe in recipes}
    base_recipes_by_family: dict[str, list[str]] = defaultdict(list)
    all_recipes_by_family: dict[str, list[str]] = defaultdict(list)
    for recipe in recipes:
        family = canonical_family(recipe.get("family"))
        all_recipes_by_family[family].append(str(recipe["id"]))
        if recipe.get("kind") == "base_recipe":
            base_recipes_by_family[family].append(str(recipe["id"]))

    cards: list[dict[str, Any]] = []
    for article_id, article in sorted(articles.items()):
        article_blocks = sorted(blocks_by_article.get(article_id, []), key=lambda item: (int(item.get("line_start") or 0), str(item.get("id"))))
        plot_blocks = [block for block in article_blocks if plot_like(block)]
        family_to_blocks: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for block in plot_blocks:
            family_to_blocks[block_family(block, str(article.get("title") or ""))].append(block)

        primary_family = canonical_family(article.get("family"))
        if not family_to_blocks:
            family_to_blocks[primary_family] = [block for block in article_blocks if block.get("role") not in {"install", "non_code"}]
        elif primary_family not in {"unknown", "palette", "decorative"} and primary_family not in family_to_blocks:
            same_family = [block for block in article_blocks if canonical_family(block.get("family")) == primary_family and block.get("role") not in {"install", "non_code"}]
            if same_family:
                family_to_blocks[primary_family] = same_family

        for family, family_blocks in sorted(family_to_blocks.items()):
            family = canonical_family(family)
            semantics = SEMANTICS.get(family, SEMANTICS["unknown"])
            block_ids = [str(block["id"]) for block in family_blocks]
            block_id_set = set(block_ids)
            eligible_images = [
                image for image in images_by_article.get(article_id, [])
                if image.get("role") in {"scientific_result", "published_reference", "intermediate_step", "uncertain"}
            ]
            selected_image = None
            if eligible_images:
                selected_image = max(eligible_images, key=lambda item: image_score(item, block_id_set, family))

            exact = sorted(
                recipe_id for recipe_id, source_ids in recipe_sources.items()
                if article_id in source_ids
                and canonical_family(
                    next(recipe for recipe in recipes if recipe["id"] == recipe_id).get("family")
                ) == family
            )
            family_recipe_ids = sorted(base_recipes_by_family.get(family, []))
            matched_recipe_ids = exact or family_recipe_ids
            backends = sorted({
                str(block.get("backend")) for block in family_blocks
                if block.get("backend") in {"r", "python"}
            })
            if not backends:
                backends = [
                    str(recipe.get("backend")) for recipe in recipes
                    if recipe.get("id") in matched_recipe_ids and recipe.get("backend") in {"r", "python"}
                ]
                backends = sorted(set(backends))
            code_available = bool(block_ids)
            image_available = selected_image is not None
            status = coverage_status(
                family,
                str(article.get("title") or ""),
                exact,
                family_recipe_ids,
                code_available,
                image_available,
            )
            style_id = f"style-{article_id.removeprefix('article-')}-{family}-v1"
            title = str(article.get("title") or style_id)
            family_label = FAMILY_LABELS.get(family, family)
            source_block_families = sorted({block_family(block, title) for block in plot_blocks})
            keywords = list(dict.fromkeys([
                family_label,
                title,
                *semantics["keywords"],
                *(str(block.get("heading")) for block in family_blocks if block.get("heading")),
            ]))
            card = {
                "schema_version": "1.0",
                "style_id": style_id,
                "title": title,
                "family": family,
                "family_label": family_label,
                "description": f"来源文章《{title}》中的{family_label}样式；保留原库索引，并区分正式 Recipe、同家族模板和仅供参考源码。",
                "analysis_use": semantics["analysis_use"],
                "visual_channels": semantics["visual_channels"],
                "required_inputs": semantics["required_inputs"],
                "supported_claims": semantics["supported_claims"],
                "claim_limits": semantics["claim_limits"],
                "recommended_companion": semantics["recommended_companion"],
                "keywords": keywords,
                "backends": backends,
                "source_article_id": article_id,
                "source_article_path": article.get("article_path"),
                "source_block_ids": block_ids,
                "source_block_count": len(block_ids),
                "article_plot_families": source_block_families,
                "sample_image_id": selected_image.get("id") if selected_image else None,
                "sample_image": selected_image.get("path") if selected_image else None,
                "sample_image_role": selected_image.get("role") if selected_image else None,
                "sample_image_reviewed": bool(selected_image and selected_image.get("reviewed") is True),
                "recipe_ids": matched_recipe_ids,
                "exact_recipe_ids": exact,
                "family_recipe_ids": family_recipe_ids,
                "coverage_status": status,
                "coverage_note": {
                    "formal_exact": "该来源直接进入正式 Recipe 或组件 lineage；仍需按 Recipe 输入契约使用。",
                    "formal_family": "已有同家族正式 Recipe，但该文章的具体造型尚未逐项蒸馏。",
                    "source_only": "原代码和结果图可检索，但尚无同家族正式可执行 Recipe。",
                    "code_only": "存在相关代码，但缺少合格的科学结果样板图。",
                    "visual_only": "存在结果样板图，但没有可可靠配对的绘图代码。",
                    "resource_only": "工具、配色、装饰或未归类资源，不作为正式科学结果模板。",
                }[status],
                "prompt_example": (
                    f"使用 $visualization-2026718-v1，参考样式 `{style_id}` 做{semantics['analysis_use']}"
                    "先核对我的分析单位、输入字段和统计前提，再给主方案及必要伴随证据；适配或运行前确认 Python or R。"
                ),
                "validation": {
                    "catalog_linkage": "pass",
                    "sample_selection": (
                        "native_reviewed"
                        if selected_image and selected_image.get("reviewed") is True
                        else "heuristic_scientific_result"
                        if selected_image and selected_image.get("role") in {"scientific_result", "published_reference"}
                        else "heuristic_intermediate_candidate"
                        if selected_image
                        else "missing"
                    ),
                    "recipe_match": "exact" if exact else "family" if family_recipe_ids else "none",
                    "execution": "recipe_contract" if exact else "not_validated_for_source_code",
                },
            }
            cards.append(card)
    return sorted(cards, key=lambda item: (item["family"], item["source_article_id"], item["style_id"]))


def summarize(cards: list[dict[str, Any]]) -> dict[str, Any]:
    family_counts = Counter(card["family"] for card in cards)
    coverage_counts = Counter(card["coverage_status"] for card in cards)
    backend_counts = Counter(backend for card in cards for backend in card.get("backends") or ["unspecified"])
    exact_articles = {card["source_article_id"] for card in cards if card["coverage_status"] == "formal_exact"}
    source_articles = {card["source_article_id"] for card in cards}
    missing_samples = [card["style_id"] for card in cards if not card.get("sample_image")]
    missing_code = [card["style_id"] for card in cards if not card.get("source_block_ids")]
    source_only_by_family = Counter(
        card["family"] for card in cards if card["coverage_status"] in {"source_only", "code_only", "visual_only"}
    )
    return {
        "schema_version": "1.0",
        "articles_indexed": len(source_articles),
        "style_cards": len(cards),
        "families": dict(sorted(family_counts.items())),
        "coverage_status": dict(sorted(coverage_counts.items())),
        "backends": dict(sorted(backend_counts.items())),
        "articles_with_exact_formal_lineage": len(exact_articles),
        "exact_formal_article_ids": sorted(exact_articles),
        "missing_sample_count": len(missing_samples),
        "missing_sample_style_ids": missing_samples,
        "missing_code_count": len(missing_code),
        "missing_code_style_ids": missing_code,
        "source_only_priority_families": [
            {"family": family, "count": count}
            for family, count in source_only_by_family.most_common()
        ],
        "interpretation": {
            "formal_exact": "direct source lineage to a formal Recipe/component",
            "formal_family": "formal base Recipe exists for the family; article-specific style remains undistilled",
            "source_only": "source code and sample image are indexed but not generalized/validated",
            "code_only": "indexed code without a qualified sample image",
            "visual_only": "qualified image without linked code",
            "resource_only": "non-evidence style/tool/palette/uncategorized resource",
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the offline plot style atlas")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=ATLAS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--check", action="store_true", help="Compare generated content without writing")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    records = load_jsonl(args.catalog.resolve())
    cards = build_cards(records)
    summary = summarize(cards)
    jsonl_text = "".join(json.dumps(card, ensure_ascii=False, separators=(",", ":")) + "\n" for card in cards)
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        mismatches = []
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != jsonl_text:
            mismatches.append(str(args.output))
        if not args.summary.exists() or args.summary.read_text(encoding="utf-8") != summary_text:
            mismatches.append(str(args.summary))
        print(json.dumps({"cards": len(cards), "up_to_date": not mismatches, "mismatches": mismatches}, ensure_ascii=False, indent=2))
        return 0 if not mismatches else 1
    write_jsonl(args.output.resolve(), cards)
    args.summary.resolve().write_text(summary_text, encoding="utf-8", newline="\n")
    print(json.dumps({"atlas": str(args.output), "summary": str(args.summary), **summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
