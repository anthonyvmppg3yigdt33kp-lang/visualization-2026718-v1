#!/usr/bin/env python3
"""Build the deterministic Scheme v2 data layer for visualization-2026718-v1.

The source archive is immutable.  This builder classifies every catalogued code
fence and image exactly once, then derives visualization schemes from plotting
calls, object lineage, explicit scientific subtypes, and a small audited
override table.  Generated candidate snippets are reference/parse candidates;
they are never promoted to formal Recipes by this script.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_ROOT / "references"
CATALOG_PATH = REFERENCES / "catalog.jsonl"
CURATION_PATH = REFERENCES / "image-curation.json"
SCHEME_PATH = REFERENCES / "scheme-catalog.jsonl"
BLOCK_PATH = REFERENCES / "block-dispositions.jsonl"
IMAGE_PATH = REFERENCES / "image-dispositions.jsonl"
ALIASES_PATH = REFERENCES / "scheme-aliases.json"
INDEX_PATH = REFERENCES / "retrieval-index.json"
COVERAGE_PATH = REFERENCES / "scheme-coverage.json"
OVERRIDES_PATH = REFERENCES / "scheme-overrides.json"
CANDIDATE_ROOT = SKILL_ROOT / "assets" / "scheme-candidates"
DEFAULT_SOURCE = SKILL_ROOT / "assets" / "source_archive"
DEFAULT_NATIVE_REVIEWS = REFERENCES / "native-visual-reviews"

SCHEMA_VERSION = "2.0"
GENERATOR = "scripts/build_scheme_catalog.py"

BLOCK_DISPOSITIONS = {
    "setup",
    "install_download",
    "data_prep",
    "plot_base",
    "semantic_modifier",
    "aesthetic_modifier",
    "layout",
    "export",
    "analysis_only",
    "prompt_non_code",
    "decorative",
    "nonplot_output",
}

IMAGE_ROLES = {
    "scientific_result",
    "published_reference",
    "intermediate_step",
    "data_or_console_output",
    "cover_or_web_screenshot",
    "code_screenshot",
    "promotion_or_qr",
    "decorative_result",
    "uncertain",
}

ELIGIBILITIES = {
    "scientific_scheme",
    "semantic_modifier",
    "aesthetic_modifier",
    "layout_resource",
    "visual_reference",
    "excluded",
}


FAMILY_SEMANTICS: dict[str, dict[str, Any]] = {
    "embedding": {
        "question": "展示样本或细胞在预计算低维空间中的局部结构与标签分布。",
        "unit": "cell_or_sample",
        "topology": "embedding",
        "channels": {"x_y": "预计算嵌入坐标", "color": "类别或连续特征", "annotation": "标签、圈选或坐标提示"},
        "required": ["两列嵌入坐标", "类别或连续特征"],
        "supports": ["低维空间中的局部邻域、标签分布和可见混合模式。"],
        "limits": ["不能单独证明丰度差异、统计显著性、轨迹方向、全局距离或因果关系。"],
        "companion": "比较条件差异时配合 donor/sample-level 组成或效应量图。",
    },
    "dotplot": {
        "question": "在分组与特征之间同时比较两个已声明的汇总量。",
        "unit": "group_by_feature",
        "topology": "tidy_table",
        "channels": {"x_y": "分组×特征", "color": "平均值、效应或方向", "size": "比例、计数或显著性"},
        "required": ["分组", "特征", "颜色变量", "大小变量"],
        "supports": ["两个已声明汇总量在分组和特征间的模式。"],
        "limits": ["不能仅凭颜色或点大小宣称 marker 显著或因果机制。"],
        "companion": "配合效应量、FDR 或独立样本汇总。",
    },
    "heatmap": {
        "question": "展示矩阵的相对模式、聚类、方向或多层注释。",
        "unit": "feature_by_sample_or_group",
        "topology": "matrix",
        "channels": {"row_column": "特征×样本/分组", "color": "声明尺度下的数值", "annotation": "临床、分组或通路信息"},
        "required": ["数值矩阵", "行列标签", "缩放与聚类规则"],
        "supports": ["给定缩放和聚类规则下的相对高低、共变和分组模式。"],
        "limits": ["行缩放颜色不等于绝对表达，不能从像素推断显著性。"],
        "companion": "配合色标、转换说明、效应量与不确定性。",
    },
    "volcano": {
        "question": "联合展示差异效应方向、大小与统计证据。",
        "unit": "feature",
        "topology": "differential_results",
        "channels": {"x": "效应量/log2 fold-change", "y": "-log10(P/FDR)", "color_label": "阈值分组与重点特征"},
        "required": ["效应量", "P值或FDR", "特征名", "明确阈值"],
        "supports": ["声明阈值下的差异效应与统计证据分布。"],
        "limits": ["显著不自动等于生物学重要、可重复或因果。"],
        "companion": "配合样本级分布和独立验证。",
    },
    "enrichment": {
        "question": "展示通路或基因集的方向、强度、显著性、排序位置或类别结构。",
        "unit": "pathway_or_gene_set",
        "topology": "enrichment_results",
        "channels": {"position": "通路/排序位置", "length_or_y": "效应或富集强度", "color_size": "方向、FDR、GeneRatio或计数"},
        "required": ["通路名称", "方法匹配的效应或比例", "FDR"],
        "supports": ["声明富集方法和背景下的通路方向与统计证据。"],
        "limits": ["不能自动解释为每个细胞的通路活性、机制或因果关系。"],
        "companion": "配合 leading-edge、表达证据或正交实验。",
    },
    "composition": {
        "question": "展示类别组成、数量或比例在样本、条件或空间生态位间的变化。",
        "unit": "sample_or_region",
        "topology": "composition_table",
        "channels": {"x": "样本/条件/生态位", "y": "计数或比例", "fill": "类别"},
        "required": ["独立样本ID", "条件", "类别", "计数或明确分母的比例"],
        "supports": ["声明分母下的类别组成和样本间变化。"],
        "limits": ["堆积高度不能替代组成统计模型；细胞数不是样本重复。"],
        "companion": "配合 sample-level 点、区间或 composition-aware 模型。",
    },
    "correlation": {
        "question": "展示两个或多个连续变量的关联、回归趋势或三元组成。",
        "unit": "independent_sample",
        "topology": "tidy_table",
        "channels": {"x_y": "变量或组成轴", "point": "样本", "line": "拟合或参考线", "color_size": "分组或附加变量"},
        "required": ["成对数值", "独立样本ID", "声明的关联方法"],
        "supports": ["样本级关联方向和声明模型下的拟合趋势。"],
        "limits": ["相关不等于因果；需处理离群值、重复测量和多重检验。"],
        "companion": "配合效应量、置信区间、样本量与敏感性分析。",
    },
    "genomics": {
        "question": "展示突变位点、蛋白结构域、样本突变谱、CNV、LOH或基因组轨道。",
        "unit": "mutation_or_sample_or_genomic_interval",
        "topology": "genomic_events",
        "channels": {"position": "基因/蛋白/基因组位置", "height_or_track": "频率、拷贝数或样本", "color_shape": "事件类型"},
        "required": ["坐标", "事件", "样本ID", "注释类别"],
        "supports": ["已检测事件的分布、频率和注释结构。"],
        "limits": ["不能从图形本身推断功能影响、克隆演化或驱动因果。"],
        "companion": "配合统计富集、功能注释和验证。",
    },
    "cellchat": {
        "question": "展示模型推断的细胞通讯网络、方向、权重或配体受体结构。",
        "unit": "cell_group_or_interaction",
        "topology": "weighted_network",
        "channels": {"node": "细胞群或分子类别", "edge": "推断互作", "width_color": "权重、方向或类型"},
        "required": ["节点", "互作矩阵或边表", "权重"],
        "supports": ["计算模型推断的通讯结构或汇总得分。"],
        "limits": ["不能表述为已证实的物理通讯、分子通量或因果机制。"],
        "companion": "配合配体受体表达、空间邻近与扰动验证。",
    },
    "spatial": {
        "question": "将细胞、表达、分割或区域标签叠加到组织或荧光图像。",
        "unit": "cell_or_spot_or_region",
        "topology": "registered_image_and_coordinates",
        "channels": {"background": "组织/荧光图像", "position": "空间坐标", "color_shape": "标签、表达或分割"},
        "required": ["组织图像", "配准坐标", "标签或表达", "尺度信息"],
        "supports": ["声明配准和分割下的可见空间定位或共定位。"],
        "limits": ["不能仅凭像素证明分子互作、显著富集或因果。"],
        "companion": "配合区域定量、空间统计和不确定性。",
    },
    "distribution": {
        "question": "比较连续变量在分组间的分布、中心与离散程度。",
        "unit": "independent_sample_or_cell",
        "topology": "tidy_table",
        "channels": {"x": "分组", "y": "连续测量", "shape_width": "点、箱体或密度"},
        "required": ["连续变量", "分组", "明确分析单位"],
        "supports": ["给定分析单位下的分布形状和可见组间差异。"],
        "limits": ["图形本身不证明显著；细胞行不能替代 donor 重复。"],
        "companion": "配合样本点、效应量和置信区间。",
    },
    "set_intersection": {
        "question": "比较多个集合的交集、独有元素和组合规模。",
        "unit": "set_member",
        "topology": "set_membership",
        "channels": {"set_axis": "集合", "intersection_bar": "交集大小", "matrix_or_region": "集合组合"},
        "required": ["集合成员关系", "集合名称"],
        "supports": ["明确集合定义下的交集和独有元素规模。"],
        "limits": ["交集不代表统计富集、功能相似或因果联系。"],
        "companion": "推断时配合背景集合和 Fisher/超几何检验。",
    },
    "flow": {
        "question": "展示类别、状态、通路与基因之间的多阶段映射或流向。",
        "unit": "node_or_flow",
        "topology": "weighted_edges",
        "channels": {"node": "阶段/类别", "flow_width": "数量或权重", "color": "来源或目标类别"},
        "required": ["源节点", "目标节点", "权重"],
        "supports": ["声明节点之间的映射结构和相对流量。"],
        "limits": ["流向不自动代表时间、因果或真实物质通量。"],
        "companion": "配合节点级定量或统计比较。",
    },
    "roc": {
        "question": "评估连续评分对二分类结局的区分能力。",
        "unit": "independent_subject",
        "topology": "binary_outcome_and_score",
        "channels": {"x": "FPR", "y": "TPR", "curve": "模型/标志物", "annotation": "AUC及区间"},
        "required": ["真实二分类结局", "连续预测分数", "独立验证划分"],
        "supports": ["指定队列和划分中的区分能力。"],
        "limits": ["ROC不自动证明校准、临床效用、外部泛化或因果获益。"],
        "companion": "配合校准、PR曲线、决策曲线和外部验证。",
    },
    "survival": {
        "question": "展示随访时间内的事件过程、风险集和组间生存关联。",
        "unit": "independent_subject",
        "topology": "time_to_event",
        "channels": {"x": "时间", "y": "生存/累积事件概率", "curve": "组别", "risk_table": "在险人数"},
        "required": ["随访时间", "事件状态", "分组或协变量", "删失信息"],
        "supports": ["声明模型下的时间结局模式和组间关联。"],
        "limits": ["不能自动证明因果、比例风险假设或外部泛化。"],
        "companion": "配合风险表、HR/CI、PH诊断和调整模型。",
    },
    "trajectory": {
        "question": "展示算法推断的状态连续性、分支结构和拟时序变化。",
        "unit": "cell",
        "topology": "trajectory_object",
        "channels": {"position": "嵌入或轨迹坐标", "line_graph": "推断主干/分支", "color": "拟时序、状态或表达"},
        "required": ["轨迹对象", "拟时序或状态", "根节点/方向假设"],
        "supports": ["指定算法和根节点下的相对状态顺序与分支结构。"],
        "limits": ["不能自动证明真实时间方向、谱系祖先或因果分化。"],
        "companion": "配合时间点、RNA velocity、谱系追踪或扰动证据。",
    },
}

DEFAULT_SEMANTICS = {
    "question": "展示声明数据结构中的可见模式。",
    "unit": "declared_unit",
    "topology": "declared_input",
    "channels": {"declared": "必须由代码和图例确认"},
    "required": ["绘图输入", "变量含义", "分析单位"],
    "supports": ["仅支持代码与图例明确声明的可见模式。"],
    "limits": ["未经统计与研究设计核验不能升级结论。"],
    "companion": "先核对数据、图例和统计前提。",
}


@dataclass(frozen=True)
class SubtypeSpec:
    name: str
    family: str
    aliases_zh: tuple[str, ...]
    aliases_en: tuple[str, ...]
    visual_terms: tuple[str, ...]


SUBTYPES: dict[str, SubtypeSpec] = {
    "radial_bar_lollipop": SubtypeSpec("radial_bar_lollipop", "enrichment", ("富集玫瑰图", "极坐标柱点图", "环形棒棒图"), ("radial bar lollipop", "enrichment rose plot"), ("极坐标", "放射柱", "圆点", "环形标签")),
    "mirrored_dual_metric_lollipop": SubtypeSpec("mirrored_dual_metric_lollipop", "correlation", ("背靠背棒棒图", "双向棒棒图"), ("mirrored lollipop", "back-to-back lollipop"), ("中心共享标签", "左右镜像", "细柱", "圆点大小")),
    "enrichment_comet_link_dot": SubtypeSpec("enrichment_comet_link_dot", "enrichment", ("富集彗星图", "富集流星图"), ("enrichment comet plot", "link-dot enrichment"), ("连线", "尾迹", "终点圆点", "分面")),
    "enrichment_dendrogram_bar_composite": SubtypeSpec("enrichment_dendrogram_bar_composite", "enrichment", ("富集聚类树条形组合图", "通路树条形图"), ("enrichment dendrogram bar composite",), ("聚类树", "横向条形", "对齐拼接", "显著性标记")),
    "go_enrichment_circle": SubtypeSpec("go_enrichment_circle", "enrichment", ("GO富集圈图", "功能富集圆环图"), ("GO enrichment circle", "GOCircle"), ("圆环", "通路扇区", "基因表达", "z-score")),
    "ternary_composition_scatter": SubtypeSpec("ternary_composition_scatter", "correlation", ("三元图", "三元组成散点图"), ("ternary plot", "ternary composition scatter"), ("三角坐标", "三组分", "点大小", "类别颜色")),
    "two_contrast_foldchange_concordance": SubtypeSpec("two_contrast_foldchange_concordance", "correlation", ("双对比fold-change一致性图", "多对比差异散点图"), ("fold-change concordance", "two-contrast scatter"), ("两个log2FC轴", "象限", "第三对比颜色", "基因标签")),
    "mutation_lollipop_domain": SubtypeSpec("mutation_lollipop_domain", "genomics", ("突变棒棒糖图", "蛋白结构域突变图"), ("mutation lollipop", "protein-domain lollipop"), ("蛋白位置", "突变频次", "结构域", "突变标签")),
    "mutation_waterfall_oncoprint": SubtypeSpec("mutation_waterfall_oncoprint", "genomics", ("突变瀑布图", "肿瘤突变矩阵"), ("mutation waterfall", "oncoprint"), ("基因×样本矩阵", "突变类型", "边际频率")),
    "transition_transversion_spectrum": SubtypeSpec("transition_transversion_spectrum", "genomics", ("转换颠换图", "TiTv图"), ("transition transversion", "TiTv spectrum"), ("替换类型", "频率", "样本")),
    "cohort_cnv_spectrum": SubtypeSpec("cohort_cnv_spectrum", "genomics", ("队列CNV谱", "拷贝数队列图"), ("cohort CNV spectrum", "cnSpec"), ("染色体", "样本", "扩增缺失")),
    "single_sample_cnv_profile": SubtypeSpec("single_sample_cnv_profile", "genomics", ("单样本CNV图",), ("single-sample CNV profile", "cnView"), ("基因组坐标", "拷贝数", "片段")),
    "loh_spectrum": SubtypeSpec("loh_spectrum", "genomics", ("LOH谱图", "杂合性缺失图"), ("LOH spectrum", "lohSpec"), ("染色体", "LOH事件", "样本")),
    "genomic_coverage_tracks": SubtypeSpec("genomic_coverage_tracks", "genomics", ("基因组覆盖轨道图",), ("genomic coverage tracks", "genCov"), ("基因组坐标", "覆盖度", "多轨道")),
    "somatic_interaction_matrix": SubtypeSpec("somatic_interaction_matrix", "genomics", ("体细胞突变互斥共现图",), ("somatic interaction matrix",), ("基因对", "共现", "互斥", "显著性")),
    "mutation_rainfall": SubtypeSpec("mutation_rainfall", "genomics", ("突变雨图",), ("mutation rainfall",), ("基因组位置", "相邻突变距离", "染色体")),
    "oncodrive_score": SubtypeSpec("oncodrive_score", "genomics", ("驱动基因评分图",), ("oncodrive score plot",), ("基因", "评分", "显著性")),
    "apobec_enrichment": SubtypeSpec("apobec_enrichment", "genomics", ("APOBEC富集差异图",), ("APOBEC enrichment plot",), ("样本分组", "富集", "差异")),
    "he_whole_slide": SubtypeSpec("he_whole_slide", "spatial", ("HE全景图", "组织切片全景图"), ("whole-slide H&E",), ("组织背景", "全景", "ROI框")),
    "he_roi_zoom": SubtypeSpec("he_roi_zoom", "spatial", ("HE局部放大图", "ROI放大图"), ("H&E ROI zoom",), ("组织背景", "局部区域", "尺度")),
    "fluorescence_multichannel": SubtypeSpec("fluorescence_multichannel", "spatial", ("多通道荧光图",), ("multichannel fluorescence",), ("荧光通道", "组织区域", "归一化")),
    "segmentation_boundary_overlay": SubtypeSpec("segmentation_boundary_overlay", "spatial", ("细胞分割边界图",), ("segmentation boundary overlay",), ("组织背景", "细胞边界", "类别填色")),
    "spatial_spot_overlay": SubtypeSpec("spatial_spot_overlay", "spatial", ("空间位点组织叠加图", "SpatialDimPlot"), ("spatial spot overlay",), ("组织背景", "spot坐标", "cluster颜色", "空间配准")),
    "spatial_cell_overlay": SubtypeSpec("spatial_cell_overlay", "spatial", ("空间细胞映射图", "CellTrek组织叠加图"), ("spatial cell overlay", "CellTrek cell map"), ("组织背景", "细胞坐标", "细胞类型颜色", "空间映射")),
    "cellchat_circle_network": SubtypeSpec("cellchat_circle_network", "cellchat", ("细胞通讯圆形网络图", "贝壳图"), ("CellChat circle network",), ("圆形节点", "有向边", "边宽", "节点大小")),
    "cellchat_chord": SubtypeSpec("cellchat_chord", "cellchat", ("细胞通讯弦图",), ("CellChat chord diagram",), ("扇区", "弦带", "方向", "权重")),
    "cellchat_bubble": SubtypeSpec("cellchat_bubble", "cellchat", ("细胞通讯气泡图",), ("CellChat bubble plot",), ("发送接收细胞", "配体受体", "点大小", "颜色")),
    "marker_dotplot": SubtypeSpec("marker_dotplot", "dotplot", ("marker气泡图", "基因表达点图"), ("marker dot plot",), ("基因×细胞群", "平均表达颜色", "表达比例大小")),
    "marker_dotplot_group_boxes": SubtypeSpec("marker_dotplot_group_boxes", "dotplot", ("带marker分组框气泡图",), ("marker dot plot with group boxes",), ("平均表达颜色", "表达比例大小", "分组矩形框")),
    "embedding_scatter": SubtypeSpec("embedding_scatter", "embedding", ("UMAP散点图", "降维图"), ("embedding scatter", "UMAP"), ("二维嵌入", "类别颜色", "标签")),
    "embedding_feature": SubtypeSpec("embedding_feature", "embedding", ("特征表达UMAP",), ("feature embedding", "FeaturePlot"), ("二维嵌入", "连续表达颜色")),
    "embedding_density_cloud": SubtypeSpec("embedding_density_cloud", "embedding", ("云雾UMAP", "密度UMAP"), ("density cloud UMAP",), ("二维嵌入", "密度云", "类别轮廓")),
    "embedding_outline": SubtypeSpec("embedding_outline", "embedding", ("加圈UMAP", "轮廓UMAP"), ("outlined UMAP",), ("二维嵌入", "群集轮廓", "标签")),
    "embedding_arrow_axis": SubtypeSpec("embedding_arrow_axis", "embedding", ("箭头坐标UMAP",), ("UMAP arrow axes",), ("二维嵌入", "左下角箭头坐标")),
    "pca_scatter": SubtypeSpec("pca_scatter", "embedding", ("PCA散点图",), ("PCA scatter",), ("主成分坐标", "分组颜色", "置信椭圆")),
    "pca_3d_scatter": SubtypeSpec("pca_3d_scatter", "embedding", ("三维PCA散点图", "PCA三维图"), ("3D PCA scatter",), ("PC1/PC2/PC3", "三维坐标", "分组颜色", "视角")),
    "pcoa_scatter": SubtypeSpec("pcoa_scatter", "embedding", ("PCoA图", "Beta多样性排序图"), ("PCoA scatter",), ("主坐标", "分组颜色", "解释度")),
    "pca_magnified_inset": SubtypeSpec("pca_magnified_inset", "embedding", ("带局部放大的PCA图", "PCA局部放大图"), ("PCA with magnified inset",), ("主成分坐标", "局部放大框", "连接线", "分组颜色")),
    "annotated_heatmap": SubtypeSpec("annotated_heatmap", "heatmap", ("注释热图", "复杂热图"), ("annotated heatmap",), ("矩阵颜色", "聚类", "注释条", "文本框")),
    "volcano_scatter": SubtypeSpec("volcano_scatter", "volcano", ("火山图",), ("volcano plot",), ("log2FC", "-log10显著性", "方向颜色", "标签")),
    "gsea_running_score": SubtypeSpec("gsea_running_score", "enrichment", ("GSEA运行富集曲线",), ("GSEA running score",), ("基因排序", "运行ES", "命中刻度", "NES/FDR")),
    "gsea_rank_track": SubtypeSpec("gsea_rank_track", "enrichment", ("多通路GSEA基因排序轨道图",), ("multi-pathway GSEA rank track",), ("基因排序位置", "通路轨道", "命中线段", "方向")),
    "gsea_rank_score_dot": SubtypeSpec("gsea_rank_score_dot", "enrichment", ("GSEA通路得分排序气泡图",), ("GSEA rank score dot plot",), ("通路排序", "NES或得分", "FDR大小", "方向颜色")),
    "enrichment_bar": SubtypeSpec("enrichment_bar", "enrichment", ("富集条形图",), ("enrichment bar plot",), ("通路", "GeneRatio或-log10FDR", "方向或类别颜色")),
    "enrichment_dotplot": SubtypeSpec("enrichment_dotplot", "enrichment", ("富集气泡图",), ("enrichment dot plot",), ("通路", "GeneRatio", "FDR颜色", "Count大小")),
    "enrichment_text_rank": SubtypeSpec("enrichment_text_rank", "enrichment", ("富集通路文字排序图", "富集文字云式排名图"), ("enrichment text rank",), ("通路文字", "排序位置", "显著性颜色", "参考线")),
    "ranked_differential_dotplot": SubtypeSpec("ranked_differential_dotplot", "dotplot", ("差异基因排序气泡图",), ("ranked differential dot plot",), ("差异排序", "效应方向", "显著性颜色", "基因标签")),
    "gsva_score_bar": SubtypeSpec("gsva_score_bar", "enrichment", ("GSVA得分条形图",), ("GSVA score bar plot",), ("样本或通路", "GSVA score", "方向颜色", "标签")),
    "stacked_composition_bar": SubtypeSpec("stacked_composition_bar", "composition", ("组成堆积柱状图",), ("stacked composition bar",), ("样本/条件", "比例或计数", "类别填色")),
    "summary_mean_dot_bar": SubtypeSpec("summary_mean_dot_bar", "distribution", ("均值点柱图",), ("mean dot/bar summary",), ("分组", "均值", "点或柱", "数值标签")),
    "summary_bar_error": SubtypeSpec("summary_bar_error", "distribution", ("均值柱误差图",), ("mean bar with error",), ("分组", "均值", "SEM误差条", "原始点")),
    "mean_line_ribbon": SubtypeSpec("mean_line_ribbon", "distribution", ("均值趋势置信带图",), ("mean line with ribbon",), ("顺序轴", "均值线", "SEM或CI带")),
    "box_jitter": SubtypeSpec("box_jitter", "distribution", ("箱线散点图",), ("box jitter plot",), ("分组", "连续值", "箱体", "样本点")),
    "violin_distribution": SubtypeSpec("violin_distribution", "distribution", ("小提琴图",), ("violin plot",), ("分组", "连续值", "核密度宽度")),
    "mirrored_violin": SubtypeSpec("mirrored_violin", "distribution", ("背靠背小提琴图", "双向小提琴图"), ("mirrored violin",), ("中心轴", "双侧密度", "两个条件")),
    "ridgeline_distribution": SubtypeSpec("ridgeline_distribution", "distribution", ("山脊图", "山峦图"), ("ridgeline plot",), ("分组偏移", "密度曲线", "连续值")),
    "correlation_scatter": SubtypeSpec("correlation_scatter", "correlation", ("相关性散点图",), ("correlation scatter",), ("两个连续轴", "样本点", "回归线", "相关系数")),
    "upset_intersection": SubtypeSpec("upset_intersection", "set_intersection", ("UpSet交集图",), ("UpSet plot",), ("集合矩阵", "交集柱", "集合大小")),
    "venn_intersection": SubtypeSpec("venn_intersection", "set_intersection", ("韦恩图",), ("Venn diagram",), ("集合区域", "交集标签")),
    "sankey_alluvial": SubtypeSpec("sankey_alluvial", "flow", ("桑基图", "冲积图"), ("Sankey", "alluvial"), ("阶段节点", "流带宽度", "类别颜色")),
    "roc_curve": SubtypeSpec("roc_curve", "roc", ("ROC曲线",), ("ROC curve",), ("FPR", "TPR", "AUC")),
    "kaplan_meier": SubtypeSpec("kaplan_meier", "survival", ("生存曲线", "KM曲线"), ("Kaplan-Meier",), ("时间", "生存概率", "删失", "风险表")),
    "trajectory_pseudotime": SubtypeSpec("trajectory_pseudotime", "trajectory", ("拟时序轨迹图",), ("pseudotime trajectory",), ("嵌入", "轨迹主干", "拟时序颜色")),
    "grid_grob_layout": SubtypeSpec("grid_grob_layout", "unknown", ("Grid/Grob布局组件", "底层图形布局"), ("grid grob layout",), ("viewport", "grob", "多面板对齐", "表格嵌入")),
    "palette_resource": SubtypeSpec("palette_resource", "unknown", ("科研配色资源", "图片取色资源"), ("scientific palette resource",), ("离散配色", "连续配色", "图片取色", "跨面板一致")),
    "semantic_annotation_modifier": SubtypeSpec("semantic_annotation_modifier", "unknown", ("语义标注组件", "证据强调组件"), ("semantic annotation modifier",), ("标签", "参考线", "高亮", "显著性", "注释框")),
    "group_box_annotation": SubtypeSpec("group_box_annotation", "unknown", ("分组矩形框组件", "marker分组框"), ("group-box annotation",), ("矩形框", "marker分组", "边界强调")),
    "aesthetic_style_modifier": SubtypeSpec("aesthetic_style_modifier", "unknown", ("视觉样式组件", "主题配色组件"), ("aesthetic style modifier",), ("主题", "配色", "图例", "字体", "留白")),
    "layout_composition_modifier": SubtypeSpec("layout_composition_modifier", "unknown", ("布局拼接组件", "多面板组合组件"), ("layout composition modifier",), ("拼图", "共享图例", "面板对齐", "viewport", "patchwork")),
    "maf_summary": SubtypeSpec("maf_summary", "genomics", ("MAF突变汇总图",), ("MAF summary plot",), ("突变分类", "样本负荷", "碱基替换", "汇总面板")),
    "generic_scientific_plot": SubtypeSpec("generic_scientific_plot", "unknown", ("科研结果图",), ("scientific plot",), ("需逐项核对",)),
}


HARD_SCHEME_OVERRIDES: dict[str, list[dict[str, Any]]] = {
    "article-3792985494804332545-007": [{
        "subtype": "radial_bar_lollipop",
        "block_ids": [
            "article-3792985494804332545-007-b005",
            "article-3792985494804332545-007-b006",
            "article-3792985494804332545-007-b007",
        ],
        "object_chain": ["plt", "p1", "p2"],
        "image_ids": {
            "published_reference": ["article-3792985494804332545-007-i001"],
            "intermediate_step": [
                "article-3792985494804332545-007-i006",
                "article-3792985494804332545-007-i007",
            ],
            "scientific_result": ["article-3792985494804332545-007-i008"],
        },
        "source_semantics": {
            "question": "比较 hiking region 的累计路线长度、平均爬升和路线数量。",
            "unit": "region",
            "data_topology": "one_row_per_region",
            "variables": {"angle": "region", "radius_bar": "sum_length", "radius_point": "mean_gain", "fill": "n"},
            "statistical_intent": "descriptive",
        },
        "target_application": {
            "question": "通过显式 adapter 将多指标通路表映射为富集玫瑰图。",
            "adapter_required": True,
            "compatible_analysis_methods": ["ora"],
            "variable_mapping": {"angle": "pathway", "radius_bar": "declared enrichment magnitude", "radius_point": "declared second metric", "fill": "FDR, direction, or count (choose one and label it)"},
        },
    }],
    "article-3792985494804332545-032": [
        {
            "subtype": "venn_intersection",
            "block_ids": [
                "article-3792985494804332545-032-b003",
                "article-3792985494804332545-032-b005",
            ],
            "object_chain": ["p1"],
        },
        {
            "subtype": "venn_intersection",
            "block_ids": [
                "article-3792985494804332545-032-b004",
                "article-3792985494804332545-032-b005",
            ],
            "object_chain": ["p2"],
        },
    ],
    "article-3792985494804332545-056": [{
        "subtype": "enrichment_dendrogram_bar_composite",
        "block_ids": [
            "article-3792985494804332545-056-b004",
            "article-3792985494804332545-056-b005",
            "article-3792985494804332545-056-b006",
        ],
        "object_chain": ["p1", "p2", "p"],
    }],
    "article-3792985494804332545-060": [{
        "subtype": "enrichment_comet_link_dot",
        "block_ids": [
            "article-3792985494804332545-060-b004",
            "article-3792985494804332545-060-b005",
        ],
        "object_chain": ["p", "p1", "p2"],
    }],
    "article-3792985494804332545-063": [{
        "subtype": "ternary_composition_scatter",
        "block_ids": ["article-3792985494804332545-063-b001"],
        "object_chain": ["p"],
    }],
    "article-4329102050694250504-006": [{
        "subtype": "go_enrichment_circle",
        "block_ids": [
            "article-4329102050694250504-006-b003",
            "article-4329102050694250504-006-b004",
            "article-4329102050694250504-006-b005",
            "article-4329102050694250504-006-b006",
        ],
        "object_chain": ["circ", "GOCircle"],
    }],
    "article-4329102050694250504-008": [{
        "subtype": "mirrored_dual_metric_lollipop",
        "block_ids": [
            "article-4329102050694250504-008-b004",
            "article-4329102050694250504-008-b005",
            "article-4329102050694250504-008-b006",
            "article-4329102050694250504-008-b007",
        ],
        "object_chain": ["p1", "p2", "p"],
    }],
    "article-4329102050694250504-016": [{
        "subtype": "two_contrast_foldchange_concordance",
        "block_ids": [
            "article-4329102050694250504-016-b003",
            "article-4329102050694250504-016-b004",
            "article-4329102050694250504-016-b005",
        ],
        "object_chain": ["p", "p1", "p2", "p3"],
    }],
    "article-3792985494804332545-064": [
        {
            "subtype": "mutation_lollipop_domain",
            "block_ids": [
                "article-3792985494804332545-064-b002",
                "article-3792985494804332545-064-b003",
                "article-3792985494804332545-064-b004",
                "article-3792985494804332545-064-b005",
                "article-3792985494804332545-064-b006",
            ],
            "object_chain": ["gp"],
        },
        {
            "subtype": "mutation_lollipop_domain",
            "block_ids": ["article-3792985494804332545-064-b008"],
            "object_chain": ["ggraph"],
        },
        {
            "subtype": "mutation_lollipop_domain",
            "block_ids": ["article-3792985494804332545-064-b010"],
            "object_chain": ["gp"],
        },
    ],
    "article-3792985494804332545-077": [{
        "subtype": "volcano_scatter",
        "block_ids": ["article-3792985494804332545-077-b006"],
        "object_chain": [],
    }],
}

HARD_IMAGE_OVERRIDES: dict[str, dict[str, Any]] = {
    "article-3792985494804332545-007-i001": {"role": "published_reference", "reviewed": True, "note": "published design reference; not the tutorial output"},
    "article-3792985494804332545-007-i006": {"role": "intermediate_step", "reviewed": True, "note": "rectangular pre-polar implementation"},
    "article-3792985494804332545-007-i007": {"role": "intermediate_step", "reviewed": True, "note": "initial polar intermediate"},
    "article-3792985494804332545-007-i008": {"role": "scientific_result", "reviewed": True, "note": "final tutorial implementation"},
}

DECORATIVE_ARTICLE_IDS = {"article-3792985494804332545-002"}
LAYOUT_RESOURCE_ARTICLE_IDS = {"article-3792985494804332545-040"}
AESTHETIC_RESOURCE_ARTICLE_IDS = {"article-3792985494804332545-046"}


CALL_RE = re.compile(r"(?<![\w.])([A-Za-z][A-Za-z0-9_.]*(?:::[A-Za-z][A-Za-z0-9_.]*)?)\s*\(")
ASSIGN_RE = re.compile(r"(?m)^\s*([A-Za-z.][A-Za-z0-9_.]*)\s*(?:<-|=(?!=))\s*(.+)$")
CHAIN_RE = re.compile(r"(?m)^\s*([A-Za-z.][A-Za-z0-9_.]*)\s*(?:<-|=(?!=))\s*([A-Za-z.][A-Za-z0-9_.]*)\s*\+")

INSTALL_RE = re.compile(r"(?i)(install\.packages|BiocManager::install|install_github|pak::pkg_install|remotes::install|devtools::install|download\.file|wget|curl::|requests\.get|urlretrieve|git\s+clone)")
EXPORT_RE = re.compile(r"(?i)(ggsave\s*\(|\b(?:pdf|png|jpeg|tiff|svg|bmp)\s*\(|dev\.off\s*\(|savefig\s*\(|plt\.savefig\s*\(|write\.(?:csv|table)\s*\(|to_csv\s*\()")
# A package import such as ``library(patchwork)`` is setup, not a layout
# operation.  Require an actual composition call/operator so data-preparation
# fences are not promoted into fake layout resources.
LAYOUT_RE = re.compile(
    r"(?i)(patchwork::|wrap_plots\s*\(|plot_spacer\s*\(|plot_layout\s*\(|plot_annotation\s*\(|"
    r"plot_grid\s*\(|grid\.arrange\s*\(|grid\.draw\s*\(|ggarrange\s*\(|"
    r"insert_(?:left|right|top|bottom)\s*\(|viewport\s*\(|pushViewport\s*\(|drawPlot\s*\(|"
    r"\b(?:p|plot|fig)[A-Za-z0-9_.]*\s*[|&/]\s*(?:p|plot|fig)[A-Za-z0-9_.]*\b)"
)
AESTHETIC_RE = re.compile(r"(?i)(theme(?:_[a-z]+)?\s*\(|scale_(?:color|colour|fill)_(?:manual|gradient|gradientn|brewer)\s*\(|guides\s*\(|labs\s*\(|xlab\s*\(|ylab\s*\(|ggtitle\s*\(|NoLegend\s*\()")
SEMANTIC_MODIFIER_RE = re.compile(r"(?i)(geom_(?:text|label|text_repel|label_repel|rect|segment|hline|vline)\s*\(|annotate\s*\(|stat_compare_means\s*\(|geom_signif\s*\(|highlight|encircle|ellipse|add_(?:label|annotation))")
SETUP_RE = re.compile(r"(?i)^\s*(?:library|require|options|set\.seed|import\s|from\s+\S+\s+import|palette\s*<-|cols?\s*<-)")
DATA_PREP_RE = re.compile(r"(?i)(read\.(?:csv|table|delim|xlsx|rds)|readRDS|load\s*\(|merge\s*\(|mutate\s*\(|group_by\s*\(|summari[sz]e\s*\(|pivot_|melt\s*\(|CreateSeuratObject|FindAllMarkers|enrichGO|enrichKEGG|enricher\s*\(|fgsea\s*\(|scanpy\.|pd\.read_)")
ANALYSIS_RE = re.compile(r"(?i)(cor\.test|wilcox\.test|t\.test|lm\s*\(|coxph|survfit|FindMarkers|RunUMAP|RunPCA|hclust|dist\s*\(|roc\s*\(|compareCluster)")

PLOT_CALLS = {
    "ggplot", "ggtern", "ggraph", "tidyplot", "DimPlot", "FeaturePlot", "DotPlot", "VlnPlot",
    "CellDimPlot", "CellFeaturePlot", "Heatmap", "pheatmap", "ComplexHeatmap", "chordDiagram",
    "netVisual_circle", "netVisual_bubble", "netVisual_chord_gene", "upset", "ggvenn", "VennDiagram", "venn.diagram",
    "ggsurvplot", "gseaplot", "gseaplot2", "GOCircle", "GOChord", "GOBubble", "g3Lollipop",
    "lollipopPlot", "oncoplot", "plotmafSummary", "somaticInteractions", "rainfallPlot", "titv",
    "plotOncodrive", "plotApobecDiff", "waterfall", "Waterfall", "TvTi", "cnSpec", "cnView",
    "lohSpec", "genCov", "ggtree", "corrplot", "ggscatter", "ggroc", "ggalluvial",
    # Base-R graphics are real plot constructors too.  Keeping them here is
    # important for source fences that open/close a graphics device around a
    # complete plot; those fences must not be reduced to export-only records.
    "plot", "barplot", "hist", "boxplot", "image", "matplot", "stripchart", "pairs",
    "mosaicplot", "dotchart", "bwplot", "xyplot", "levelplot", "UMAPPlot",
    "scatterplot3d", "SpatialDimPlot", "celltrek_vis", "FeaturePlot_scCustom",
}
BASE_R_MODIFIER_CALLS = {
    "points", "lines", "segments", "arrows", "text", "axis", "abline", "mtext",
    "title", "rect", "grid", "rug", "polygon", "legend",
}
PLOT_PREFIXES = ("geom_", "stat_", "do_", "plt.", "ax.", "sns.")

FORBIDDEN_CANDIDATE_RE = re.compile(
    r"(?i)(rm\s*\(\s*list\s*=\s*ls\s*\(|setwd\s*\(|install\.packages|BiocManager::install|"
    r"install_github|download\.file|\b(?:ggsave|pdf|png|jpeg|tiff|svg|bmp)\s*\(|dev\.off\s*\(|"
    r"savefig\s*\(|\b(?:save|qsave|write\.csv|write\.table)\s*\(|to_csv\s*\(|"
    r"read\.(?:csv|table|xlsx|delim|rds)\s*\(|readRDS\s*\(|read_(?:csv|table|excel|parquet)\s*\(|"
    r"read_xlsx\s*\(|\bfread\s*\(|pd\.read_|np\.load\s*\(|qread\s*\(|load\s*\(|source\s*\(|"
    r"system\.file\s*\(|Sys\.glob\s*\(|file\.path\s*\(|dir\.create\s*\(|"
    r"requests\.(?:get|post|put|patch|delete)|urllib\.|urlretrieve|httpx\.|curl::|httr::|"
    r"getMutationsFromCbioportal\s*\(|subprocess\.|os\.(?:system|popen|chdir|remove|unlink)\s*\(|"
    r"system2?\s*\(|shell\s*\(|unlink\s*\(|file\.remove\s*\(|shutil\.(?:rmtree|move)\s*\(|"
    r"\bopen\s*\([^\n]+[\"'](?:w|a|x|wb|ab|xb)[\"']|writeLines\s*\(|saveRDS\s*\(|"
    r"output\.filename\s*=|filename\s*=|file\s*=)"
)
ABSOLUTE_PATH_RE = re.compile(r"(?i)(?:[A-Z]:[\\/]|(?:^|[\"'])/(?:home|Users|usr|var|tmp|data)/)")
# These complete, one-line side-effect wrappers can be removed without
# changing the in-memory plotting expression that follows.  More complex or
# multiline unsafe statements still cause the whole source block to be
# withheld from candidate export.
SAFE_STANDALONE_DROP_RE = re.compile(
    r"(?i)^\s*(?:rm|setwd|getwd|dir\.create|ggsave|pdf|png|jpeg|tiff|svg|bmp|"
    r"dev\.off|savefig|plt\.savefig|qsave|saveRDS|write\.csv|write\.table|"
    r"writeLines|file\.remove|unlink)\s*\(.*\)\s*;?\s*$"
)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Expected JSON object at {path}:{line_number}")
            result.append(value)
    return result


def load_native_reviews(directory: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load optional, appendable native visual-review batches deterministically."""
    if not directory.exists():
        return {}, []
    if not directory.is_dir():
        raise ValueError(f"Native review path is not a directory: {directory}")
    reviews: dict[str, dict[str, Any]] = {}
    files: list[str] = []
    for path in sorted(directory.glob("*.jsonl"), key=lambda item: item.name):
        files.append(path.name)
        for row in load_jsonl(path):
            image_id = str(row.get("image_id") or "")
            if not image_id:
                raise ValueError(f"Native review missing image_id: {path}")
            role = row.get("role")
            if role is not None and role not in IMAGE_ROLES:
                raise ValueError(f"Invalid native-review role {role!r} for {image_id}")
            previous = reviews.get(image_id)
            if previous is not None and previous != row:
                raise ValueError(f"Conflicting native reviews for {image_id}")
            reviews[image_id] = row
    return reviews, files


def normalize_consistency(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        value = (
            value.get("overall")
            or value.get("scheme_vs_image")
            or value.get("code_vs_image")
            or value.get("status")
        )
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "pass": "confirmed",
        "verified": "confirmed",
        "reviewed": "confirmed",
        "fail": "mismatch",
        "failed": "mismatch",
        "n/a": "not_applicable",
        "na": "not_applicable",
    }
    return aliases.get(text, text or None)


def flatten_strings(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            result.extend(flatten_strings(child))
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            result.extend(flatten_strings(child))
    elif value not in (None, ""):
        result.append(str(value))
    return result


def jsonl_text(records: Iterable[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n" for row in records)


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_calls(code: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for call in CALL_RE.findall(re.sub(r"(?m)#.*$", "", code)):
        bare = call.split("::")[-1]
        if bare not in seen:
            seen.add(bare)
            result.append(bare)
    return result


def infer_block_backend(block: dict[str, Any]) -> str:
    """Resolve mislabeled fences from the code itself before candidate export."""
    code = str(block.get("code") or "")
    python_score = 0
    r_score = 0
    python_score += 4 * len(re.findall(r"(?m)^\s*(?:from\s+\w|import\s+\w|def\s+\w+\s*\()", code))
    python_score += 3 * len(re.findall(r"\b(?:plt|sns|pd|np|sc|ax|fig)\.", code))
    python_score += 2 * len(re.findall(r"\.value_counts\s*\(|\.copy\s*\(|f[\"']", code))
    r_score += 4 * len(re.findall(r"<-|%>%|\|>", code))
    r_score += 3 * len(re.findall(r"\b(?:library|require)\s*\(|\b\w+::\w+", code))
    r_score += 2 * len(re.findall(r"\b(?:ggplot|pheatmap|Heatmap|geom_[A-Za-z0-9_]+)\s*\(|\$[A-Za-z_.]", code))
    if python_score >= 3 and python_score > r_score:
        return "python"
    if r_score >= 2 and r_score >= python_score:
        return "r"
    backend = str(block.get("backend") or "").lower()
    return backend if backend in {"r", "python"} else ""


def plot_calls(code: str) -> list[str]:
    result = []
    for call in normalized_calls(code):
        if call in PLOT_CALLS or call in BASE_R_MODIFIER_CALLS or call.startswith(PLOT_PREFIXES) or call.startswith("circos."):
            result.append(call)
    return result


def assigned_objects(code: str) -> list[str]:
    return list(dict.fromkeys(match.group(1) for match in ASSIGN_RE.finditer(code)))


def assigned_plot_objects(code: str) -> list[str]:
    """Return assignment targets whose right-hand side constructs a plot.

    Data objects are often assigned before the plot in the same fence.  Using
    the first arbitrary assignment as a Scheme root merges independent plots
    whenever common names such as ``df`` or ``p`` are reused later.
    """
    result: list[str] = []
    for match in ASSIGN_RE.finditer(code):
        target, expression = match.group(1), match.group(2)
        if plot_calls(expression) and target not in result:
            result.append(target)
    return result


def object_chains(code: str) -> list[tuple[str, str]]:
    return [(match.group(1), match.group(2)) for match in CHAIN_RE.finditer(code)]


def only_setup(code: str) -> bool:
    meaningful = [line.strip() for line in code.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return bool(meaningful) and all(SETUP_RE.search(line) or line in {"", "}"} for line in meaningful)


def classify_block(block: dict[str, Any], article: dict[str, Any]) -> tuple[str, str]:
    article_id = str(article["id"])
    code = str(block.get("code") or "")
    role = str(block.get("role") or "")
    calls = plot_calls(code)
    chains = object_chains(code)
    if article_id in DECORATIVE_ARTICLE_IDS or re.search(r"(?i)christmas|圣诞树", str(article.get("title") or "")):
        return "decorative", "article is an explicitly excluded decorative demonstration"
    if role == "non_code":
        if re.search(r"(?i)(请|prompt|codex|chatgpt|复现|生成|绘制|代码)", code):
            return "prompt_non_code", "natural-language prompt stored in a code fence"
        return "nonplot_output", "non-code fence without executable plotting syntax"
    if INSTALL_RE.search(code) and not calls:
        return "install_download", "installation or download code without a plot call"
    if EXPORT_RE.search(code) and not [c for c in calls if c not in {"plt.savefig"}]:
        return "export", "export/write-only fence"
    if re.search(r"(?i)par\s*\([^)]*new\s*=\s*(?:T|TRUE)", code) and re.search(r"(?i)\bplot\s*\(", code):
        return "aesthetic_modifier", "overlays a blank base-R frame to change border/axis appearance"
    if calls:
        base_calls = [c for c in calls if c in PLOT_CALLS or c.startswith(("do_", "plt.figure", "plt.subplots", "sns."))]
        geometry_calls = [c for c in calls if c in BASE_R_MODIFIER_CALLS or c.startswith(("geom_", "stat_", "ax."))]
        if geometry_calls and not base_calls and not chains:
            return "semantic_modifier", "adds base-R or layered evidence marks to an existing canvas"
        if chains and not base_calls:
            if SEMANTIC_MODIFIER_RE.search(code) or geometry_calls:
                return "semantic_modifier", "incremental object chain adds evidence-bearing marks or annotations"
            if AESTHETIC_RE.search(code):
                return "aesthetic_modifier", "incremental object chain changes appearance only"
        if LAYOUT_RE.search(code) and not base_calls and not geometry_calls:
            return "layout", "combines existing plot objects"
        if base_calls or geometry_calls or role == "plot":
            return "plot_base", "contains a recognized plotting constructor or mark"
    if LAYOUT_RE.search(code):
        return "layout", "layout/grob/patchwork operation"
    if EXPORT_RE.search(code):
        return "export", "explicit file or device export"
    if SEMANTIC_MODIFIER_RE.search(code) and chains:
        return "semantic_modifier", "incremental evidence-bearing annotation"
    if AESTHETIC_RE.search(code) and chains:
        return "aesthetic_modifier", "incremental theme or scale modification"
    if role == "install" or INSTALL_RE.search(code):
        return "install_download", "installation or download code"
    if role == "data_prep" or DATA_PREP_RE.search(code):
        return "data_prep", "input preparation or analysis result shaping"
    if only_setup(code):
        return "setup", "package/options/palette setup"
    if ANALYSIS_RE.search(code):
        return "analysis_only", "analysis or statistical computation without a plotting call"
    if role == "other_code":
        return "analysis_only", "executable support code without a recognized plot call"
    return "nonplot_output", "no recognized plotting, analysis, setup, or export operation"


def subtype_from_text(article: dict[str, Any], block: dict[str, Any]) -> list[str]:
    title = str(article.get("title") or "")
    heading = str(block.get("heading") or "")
    code = str(block.get("code") or "")
    text = "\n".join((title, heading, code))
    calls = set(normalized_calls(code))
    result: list[str] = []

    call_map = {
        "GOCircle": "go_enrichment_circle",
        "g3Lollipop": "mutation_lollipop_domain",
        "lollipopPlot": "mutation_lollipop_domain",
        "waterfall": "mutation_waterfall_oncoprint",
        "Waterfall": "mutation_waterfall_oncoprint",
        "oncoplot": "mutation_waterfall_oncoprint",
        "TvTi": "transition_transversion_spectrum",
        "titv": "transition_transversion_spectrum",
        "cnSpec": "cohort_cnv_spectrum",
        "cnView": "single_sample_cnv_profile",
        "lohSpec": "loh_spectrum",
        "genCov": "genomic_coverage_tracks",
        "somaticInteractions": "somatic_interaction_matrix",
        "rainfallPlot": "mutation_rainfall",
        "plotOncodrive": "oncodrive_score",
        "plotApobecDiff": "apobec_enrichment",
        "plotmafSummary": "maf_summary",
        "netVisual_circle": "cellchat_circle_network",
        "netVisual_bubble": "cellchat_bubble",
        "chordDiagram": "cellchat_chord",
        "netVisual_chord_gene": "cellchat_chord",
        "DotPlot": "marker_dotplot",
        "do_DotPlot": "marker_dotplot",
        "FeaturePlot": "embedding_feature",
        "do_FeaturePlot": "embedding_feature",
        "FeaturePlot_scCustom": "embedding_feature",
        "do_NebulosaPlot": "embedding_density_cloud",
        "scatterplot3d": "pca_3d_scatter",
        "SpatialDimPlot": "spatial_spot_overlay",
        "celltrek_vis": "spatial_cell_overlay",
        "do_ViolinPlot": "violin_distribution",
        "do_BarPlot": "stacked_composition_bar",
        "do_AlluvialPlot": "sankey_alluvial",
        "do_VolcanoPlot": "volcano_scatter",
        "Heatmap": "annotated_heatmap",
        "pheatmap": "annotated_heatmap",
        "ggsurvplot": "kaplan_meier",
        "gseaplot": "gsea_running_score",
        "gseaplot2": "gsea_running_score",
        "upset": "upset_intersection",
    }
    for call, subtype in call_map.items():
        if call in calls and subtype not in result:
            result.append(subtype)

    if re.search(r"(?i)ggtern|ternary|三元图", text): result.append("ternary_composition_scatter")
    if re.search(r"(?i)coord_polar", code) and re.search(r"(?i)geom_(?:col|bar)", code): result.append("radial_bar_lollipop")
    if re.search(r"(?i)geom_link", code): result.append("enrichment_comet_link_dot")
    if re.search(r"(?i)背靠背.*棒棒|scale_x_reverse", text) and re.search(r"(?i)geom_(?:col|segment).+geom_point", code, re.S): result.append("mirrored_dual_metric_lollipop")
    if re.search(r"(?i)(avg_log2FC|log2FoldChange).*(avg_log2FC|log2FoldChange)", code, re.S) and re.search(r"(?i)geom_point", code): result.append("two_contrast_foldchange_concordance")
    if re.search(r"(?i)marker.*(框|rect)|geom_rect", text) and ("DotPlot" in calls or re.search(r"(?i)avg\.exp|pct\.exp", code)): result.append("marker_dotplot_group_boxes")
    if re.search(r"(?i)DimPlot|CellDimPlot|do_DimPlot|UMAPPlot|umap|t-?sne", text):
        feature_encoding = (
            any(call in calls for call in {"FeaturePlot", "do_FeaturePlot", "FeaturePlot_scCustom"})
            or bool(
                re.search(r"(?is)FetchData\s*\([^)]*vars\s*=\s*c\s*\([^)]*,[^)]*,", code)
                and re.search(r"(?i)filter\s*\(\s*[A-Za-z][A-Za-z0-9_.]*\s*(?:==|!=|>=|<=|>|<)", code)
            )
        )
        density_encoding = bool(re.search(r"(?i)stat_density_2d|geom_pointdensity|Nebulosa|density_2d", code))
        if feature_encoding:
            result.append("embedding_feature")
        elif density_encoding or re.search(r"云雾|密度|nebula|density|cloud", title, re.I):
            result.append("embedding_density_cloud")
        elif re.search(r"加圈|圈款|outline|encircle|hull", title, re.I): result.append("embedding_outline")
        elif re.search(r"箭头|arrow", title, re.I): result.append("embedding_arrow_axis")
        else: result.append("embedding_scatter")
    # RunPCA() is an analysis step, not evidence that a PCA panel was drawn.
    # Require an actual PCA plotting call or PC-coordinate mapping so a block
    # that computes PCA and later draws only UMAP does not create a false
    # pca_scatter Scheme.
    if re.search(
        r"(?is)(?:PCAPlot\s*\(|DimPlot\s*\([^)]*reduction\s*=\s*['\"]pca['\"]|"
        r"ggplot\s*\([^)]*(?:PC[_ .]?1|PC1)[^)]*(?:PC[_ .]?2|PC2)|"
        r"aes\s*\([^)]*(?:PC[_ .]?1|PC1)[^)]*(?:PC[_ .]?2|PC2))",
        code,
    ):
        result.append("pca_scatter")
    if re.search(r"(?i)PCA.*(局部放大|magnif)|geom_magnify", text): result.append("pca_magnified_inset")
    if re.search(r"(?i)\bPCoA\b|beta多样性", text): result.append("pcoa_scatter")
    if re.search(r"(?i)ComplexHeatmap|geom_tile|heatmap|热图", text) and any(c in calls for c in {"Heatmap", "pheatmap", "ggplot", "geom_tile", "corrplot"}): result.append("annotated_heatmap")
    volcano_context = bool(
        re.search(r"(?i)volcano|火山图", heading)
        or (
            re.search(r"(?i)volcano|火山图", title)
            and re.search(r"(?i)log(?:2)?FC|fold.?change", code)
        )
    )
    # Grouped single-cell volcano tutorials often use jittered points and add
    # background columns in a later object (p -> p1 -> p2), rather than calling
    # geom_point() in every block.  The title/effect-size gate above keeps these
    # marks specific to a true volcano context.
    if volcano_context and re.search(
        r"(?i)geom_(?:point|jitter|col)|ggscatter|\bplot\s*\(", code
    ):
        result.append("volcano_scatter")
    if re.search(r"(?i)GSEA|NES|running enrichment", text) and re.search(r"(?i)gseaplot|geom_line|geom_path", code): result.append("gsea_running_score")
    if re.search(r"(?i)GSEA.*(?:rank|排序)", title) and re.search(r"(?i)geom_segment|wrap_plots", code): result.append("gsea_rank_track")
    if re.search(r"(?i)GSEA.*(?:打分|score|排序)", title) and re.search(r"(?i)geom_point", code): result.append("gsea_rank_score_dot")
    if re.search(r"(?i)富集|enrichment|KEGG|\bGO\b", title) and re.search(r"(?i)geom_(?:bar|col)|\bbarplot\s*\(", code): result.append("enrichment_bar")
    if re.search(r"(?i)富集|enrichment|KEGG|\bGO\b", title) and re.search(r"(?i)geom_point|dotplot", code): result.append("enrichment_dotplot")
    if re.search(r"(?i)Fold\.Enrichment|LogFDR", code) and re.search(r"(?i)ggscatter|geom_point", code): result.append("enrichment_dotplot")
    if re.search(r"(?i)富集|enrichment|KEGG|\bGO\b", title) and re.search(r"(?i)geom_text", code) and not re.search(r"(?i)geom_(?:bar|col|point)", code): result.append("enrichment_text_rank")
    if re.search(r"(?i)GSVA", title) and re.search(r"(?i)geom_col", code): result.append("gsva_score_bar")
    if re.search(r"(?i)(差异基因排序|ranked.*differential)", title) and re.search(r"(?i)geom_point", code): result.append("ranked_differential_dotplot")
    if re.search(r"(?i)position\s*=\s*['\"]fill|堆积|组成|比例", text) and re.search(r"(?i)geom_(?:bar|col)|tidyplot", code): result.append("stacked_composition_bar")
    if re.search(r"(?i)geom_boxplot|ggboxplot|boxplot\s*\(|bwplot\s*\(", code): result.append("box_jitter")
    if re.search(r"(?i)背靠背.*小提琴|双向小提琴", title): result.append("mirrored_violin")
    elif re.search(r"(?i)geom_violin|VlnPlot", code): result.append("violin_distribution")
    if re.search(r"(?i)ggridges|geom_density_ridges|山脊图|山峦图", text): result.append("ridgeline_distribution")
    if re.search(r"(?i)add_mean_(?:dot|bar)|add_mean_value", code): result.append("summary_mean_dot_bar")
    if re.search(r"(?i)add_sem_errorbar", code): result.append("summary_bar_error")
    if re.search(r"(?i)add_mean_line|add_sem_ribbon", code): result.append("mean_line_ribbon")
    if re.search(r"(?i)add_violin", code): result.append("violin_distribution")
    if re.search(r"(?i)add_barstack_(?:absolute|relative)", code): result.append("stacked_composition_bar")
    if re.search(r"(?i)add_data_points", code) and re.search(r"(?i)add_reference_lines", code): result.append("correlation_scatter")
    if re.search(r"(?i)add_data_labels_repel", code) and re.search(r"(?i)log10|fold", code): result.append("volcano_scatter")
    if re.search(r"(?i)stat_cor|geom_smooth|cor\.test|相关性", text) and re.search(r"(?i)geom_point|ggscatter", code): result.append("correlation_scatter")
    if re.search(r"(?i)相关性散点|correlation.*scatter", title) and re.search(r"(?i)\bplot\s*\(|\bpoints\s*\(", code): result.append("correlation_scatter")
    if re.search(r"(?i)ComplexUpset|upset\s*\(", code): result.append("upset_intersection")
    if re.search(r"(?i)VennDiagram|ggvenn|venn", text) and plot_calls(code): result.append("venn_intersection")
    if re.search(r"(?i)geom_alluvium|ggalluvial|sankey|桑基|冲积", text): result.append("sankey_alluvial")
    if re.search(
        r"(?i)ggroc\s*\(|pROC::roc\s*\(|\broc\s*\(|roc_curve|"
        r"1\s*-\s*Specificity|Sensitivity",
        code,
    ) and plot_calls(code):
        result.append("roc_curve")
    if re.search(r"(?i)ggsurvplot|Kaplan|生存曲线", text) and plot_calls(code): result.append("kaplan_meier")
    if re.search(r"(?i)pseudotime|plot_cells|拟时序|trajectory", text) and plot_calls(code): result.append("trajectory_pseudotime")
    if re.search(r"(?i)plt\.imshow|ax\d*\.imshow", code):
        if re.search(r"(?i)fluores|IF_image|荧光", text): result.append("fluorescence_multichannel")
        elif re.search(r"(?i)ROI|zoom|局部", text): result.append("he_roi_zoom")
        else: result.append("he_whole_slide")
    if re.search(r"(?i)add_patch|Polygon|alphashape|segmentation|分割边界", text) and re.search(r"(?i)plot|imshow|add_patch", code): result.append("segmentation_boundary_overlay")
    if re.search(r"(?i)geom_segment", code) and re.search(r"(?i)mutation|protein|突变|结构域|AA", text): result.append("mutation_lollipop_domain")
    if re.search(r"(?i)ggraph|geom_edge_elbow|突变|棒棒糖", text) and re.search(r"(?i)geom_(?:segment|edge|node)", code): result.append("mutation_lollipop_domain")
    if re.search(r"(?i)grid\.|grob|viewport", text) and str(article.get("id")) == "article-3792985494804332545-040": result.append("grid_grob_layout")
    if re.search(r"(?i)细胞通讯.*气泡图|cellchat.*bubble", title) and re.search(r"(?i)geom_point", code): result.append("cellchat_bubble")
    if re.search(r"(?i)基因表达气泡图|marker.*气泡图", title) and re.search(r"(?i)geom_point", code): result.append("marker_dotplot")
    if volcano_context and re.search(r"(?i)geom_(?:point|jitter|col)|ggscatter", code):
        result.append("volcano_scatter")

    return list(dict.fromkeys(sub for sub in result if sub in SUBTYPES))


def classify_image(
    image: dict[str, Any],
    article: dict[str, Any],
    curation: dict[str, Any],
) -> tuple[str, bool, str, str]:
    image_id = str(image["id"])
    if image_id in HARD_IMAGE_OVERRIDES:
        item = HARD_IMAGE_OVERRIDES[image_id]
        return str(item["role"]), bool(item["reviewed"]), str(item["note"]), "hard_override"
    curated = curation.get(str(image.get("archive_path") or ""))
    if isinstance(curated, dict):
        role = str(curated.get("role") or image.get("role") or "uncertain")
        return role if role in IMAGE_ROLES else "uncertain", bool(curated.get("reviewed")), str(curated.get("note") or ""), "curation_override"
    if str(article["id"]) in DECORATIVE_ARTICLE_IDS:
        return "decorative_result", True, "output of an excluded decorative article", "hard_article_rule"
    role = str(image.get("role") or "uncertain")
    if role not in IMAGE_ROLES:
        role = "uncertain"
    reviewed = bool(image.get("reviewed") is True)
    note = str(image.get("review_note") or "")
    return role, reviewed, note, "catalog_role"


@dataclass
class SchemeSeed:
    article_id: str
    subtype: str
    root: str
    block_ids: list[str] = field(default_factory=list)
    object_chain: list[str] = field(default_factory=list)
    forced: dict[str, Any] | None = None


def derive_scheme_seeds(
    article: dict[str, Any],
    blocks: list[dict[str, Any]],
    dispositions: dict[str, str],
) -> list[SchemeSeed]:
    article_id = str(article["id"])
    if article_id in DECORATIVE_ARTICLE_IDS:
        return [SchemeSeed(article_id, "generic_scientific_plot", "excluded", [str(b["id"]) for b in blocks], [], {"eligibility": "excluded"})]
    if article_id in HARD_SCHEME_OVERRIDES:
        forced_ids = {bid for item in HARD_SCHEME_OVERRIDES[article_id] for bid in item["block_ids"]}
        seeds = [
            SchemeSeed(article_id, item["subtype"], f"forced-{index:02d}", list(item["block_ids"]), list(item.get("object_chain") or []), item)
            for index, item in enumerate(HARD_SCHEME_OVERRIDES[article_id], 1)
        ]
    else:
        forced_ids = set()
        seeds = []

    object_to_seed: dict[str, SchemeSeed] = {}
    keyed: dict[tuple[str, str], SchemeSeed] = {}
    for seed in seeds:
        keyed[(seed.subtype, seed.root)] = seed
        for obj in seed.object_chain:
            object_to_seed[obj] = seed

    last_seed: SchemeSeed | None = seeds[-1] if seeds else None
    for block in blocks:
        block_id = str(block["id"])
        if block_id in forced_ids:
            continue
        disposition = dispositions[block_id]
        if disposition == "export":
            # Export/device blocks are not independent visual Schemes, but
            # when they explicitly reference the preceding Scheme object they
            # are part of its traceable lineage and populate export_block_ids.
            export_targets = ([last_seed.root] + list(last_seed.object_chain)) if last_seed is not None else []
            references_last = any(
                target and re.search(rf"(?<![A-Za-z0-9_.]){re.escape(target)}(?![A-Za-z0-9_.])", str(block.get("code") or ""))
                for target in export_targets
            )
            if last_seed is not None and references_last and block_id not in last_seed.block_ids:
                last_seed.block_ids.append(block_id)
            continue
        if disposition not in {"plot_base", "semantic_modifier", "aesthetic_modifier", "layout"}:
            continue
        code = str(block.get("code") or "")
        chains = object_chains(code)
        defs = assigned_objects(code)
        plot_defs = assigned_plot_objects(code)
        # If a block first resets ``p`` with a new constructor and later adds
        # ``p <- p + ...``, that local chain must not attach to an unrelated
        # ``p`` from an earlier Scheme.
        dependencies = [old for _, old in chains if old not in set(plot_defs)]
        parent = next((object_to_seed[obj] for obj in dependencies if obj in object_to_seed), None)
        subtypes = subtype_from_text(article, block)

        if disposition in {"semantic_modifier", "aesthetic_modifier", "layout"} and parent:
            if block_id not in parent.block_ids:
                parent.block_ids.append(block_id)
            for new, _old in chains:
                object_to_seed[new] = parent
                if new not in parent.object_chain:
                    parent.object_chain.append(new)
            last_seed = parent
            continue
        if disposition in {"semantic_modifier", "aesthetic_modifier", "layout"} and parent is None:
            # Base-R tutorials commonly build one canvas across consecutive
            # fences without assigning a plot object.  In that explicit
            # incremental case, attach the modifier to the immediately prior
            # scientific Scheme; otherwise keep it as a standalone resource.
            incremental_base_r_overlay = bool(re.search(r"(?i)par\s*\([^)]*new\s*=\s*(?:T|TRUE)", code))
            if last_seed is not None and (
                not any(call in PLOT_CALLS for call in plot_calls(code))
                or incremental_base_r_overlay
            ):
                if block_id not in last_seed.block_ids:
                    last_seed.block_ids.append(block_id)
                continue
            # Orphan components are indexed below as components/resources; they
            # must not be promoted to a scientific Scheme merely because the
            # article title names a scientific chart family.
            continue
        if not subtypes and disposition != "plot_base":
            if last_seed and block_id not in last_seed.block_ids:
                last_seed.block_ids.append(block_id)
            continue
        if not subtypes and disposition == "plot_base":
            subtypes = ["generic_scientific_plot"]

        for subtype in subtypes:
            if parent and parent.subtype == subtype:
                seed = parent
            else:
                base_root = plot_defs[0] if plot_defs else (defs[0] if defs else (plot_calls(code)[0] if plot_calls(code) else block_id.split("-")[-1]))
                root = base_root
                if disposition == "plot_base" and base_root in object_to_seed and parent is None:
                    root = f"{base_root}-{block_id.split('-')[-1]}"
                key = (subtype, root)
                seed = keyed.get(key)
                if seed is None:
                    seed = SchemeSeed(article_id, subtype, root)
                    keyed[key] = seed
                    seeds.append(seed)
            if block_id not in seed.block_ids:
                seed.block_ids.append(block_id)
            for obj in defs:
                object_to_seed[obj] = seed
                if obj not in seed.object_chain:
                    seed.object_chain.append(obj)
            last_seed = seed

    # Index modifiers as reusable auxiliary components as well as retaining them
    # inside their parent object's lineage.  This deliberately permits a block
    # to link to both its scientific Scheme and one component record.
    if article_id not in DECORATIVE_ARTICLE_IDS:
        for block in blocks:
            block_id = str(block["id"])
            disposition = dispositions[block_id]
            if disposition == "semantic_modifier":
                subtype = "group_box_annotation" if re.search(r"(?i)geom_rect|marker.*框|group.*box", str(block.get("code") or "") + str(block.get("heading") or "")) else "semantic_annotation_modifier"
                seeds.append(SchemeSeed(article_id, subtype, f"component-{block_id}", [block_id], assigned_objects(str(block.get("code") or "")), {"eligibility": "semantic_modifier"}))
            elif disposition == "aesthetic_modifier":
                seeds.append(SchemeSeed(article_id, "aesthetic_style_modifier", f"component-{block_id}", [block_id], assigned_objects(str(block.get("code") or "")), {"eligibility": "aesthetic_modifier"}))
            elif disposition == "layout":
                seeds.append(SchemeSeed(article_id, "layout_composition_modifier", f"component-{block_id}", [block_id], assigned_objects(str(block.get("code") or "")), {"eligibility": "layout_resource"}))

    # Visual-only article: index a reviewed/reference image without inventing code.
    if not seeds:
        seeds.append(SchemeSeed(article_id, infer_article_subtype(article), "visual-reference", [], [], {"eligibility": "visual_reference"}))
    return seeds


def infer_article_subtype(article: dict[str, Any]) -> str:
    visual_only_overrides = {
        # Native review of 020-i004 confirms a multi-pathway running-ES panel
        # with rank ticks and NES/P-value annotations.  The article contains no
        # target plotting source, so this remains visual_only rather than being
        # mislabeled as a coded enrichment dotplot.
        "article-4329102050694250504-020": "gsea_running_score",
    }
    article_id = str(article.get("id") or "")
    if article_id in visual_only_overrides:
        return visual_only_overrides[article_id]
    title = str(article.get("title") or "")
    if re.search(r"(?i)配色|取色|palette|color", title):
        return "palette_resource"
    dummy = {"heading": "", "code": title}
    found = subtype_from_text(article, dummy)
    if found:
        return found[0]
    family = str(article.get("family") or "")
    fallback = {
        "embedding": "embedding_scatter", "dotplot": "marker_dotplot", "heatmap": "annotated_heatmap",
        "volcano": "volcano_scatter", "gsea": "enrichment_dotplot", "boxplot": "box_jitter",
        "violin": "violin_distribution", "composition": "stacked_composition_bar", "correlation": "correlation_scatter",
        "set_intersection": "upset_intersection", "survival": "kaplan_meier", "roc": "roc_curve",
        "trajectory": "trajectory_pseudotime", "cellchat_chord": "cellchat_chord", "spatial_image": "he_whole_slide",
    }
    return fallback.get(family, "generic_scientific_plot")


def analysis_method(subtype: str, blocks: list[dict[str, Any]]) -> str:
    text = "\n".join(str(block.get("code") or "") for block in blocks)
    if subtype == "radial_bar_lollipop": return "descriptive_multimetric_radial"
    if subtype in {"gsea_running_score", "gsea_rank_track", "gsea_rank_score_dot"}: return "GSEA"
    if re.search(r"(?i)gseaplot|fgsea|\bNES\b|running enrichment", text): return "GSEA"
    if re.search(r"(?i)enrichGO|enrichKEGG|enricher\s*\(|GeneRatio|p\.adjust", text): return "ORA"
    if (subtype.startswith("enrichment_") or subtype == "go_enrichment_circle") and re.search(r"(?i)p(?:\.|_)?value|qvalue|fdr|\bGO\b|KEGG", text): return "ORA"
    if subtype in {"roc_curve"}: return "ROC"
    if subtype in {"kaplan_meier"}: return "Kaplan_Meier"
    if subtype == "correlation_scatter": return "correlation_or_regression"
    if subtype.startswith("mutation_") or subtype in {"transition_transversion_spectrum", "cohort_cnv_spectrum", "single_sample_cnv_profile", "loh_spectrum", "genomic_coverage_tracks"}: return "genomic_event_visualization"
    return "descriptive"


def required_statistics_for(family: str, method: str) -> list[str]:
    method_upper = method.upper()
    if method_upper == "ORA":
        return ["gene universe/background", "GeneRatio or Count", "adjusted p/FDR and correction method"]
    if method_upper == "GSEA":
        return ["ranked gene list and ranking statistic", "NES/ES", "FDR and leading-edge definition"]
    mapping = {
        "embedding": ["embedding method/parameters", "independent sample IDs for condition-level claims"],
        "dotplot": ["aggregation unit", "average-expression transform", "detected-cell denominator", "differential test/FDR if significance is claimed"],
        "heatmap": ["normalization/scaling direction", "distance and clustering method", "FDR if inferential annotations are shown"],
        "volcano": ["effect size", "raw and adjusted p/FDR", "threshold definitions"],
        "composition": ["independent sample ID", "denominator", "sample-level effect/uncertainty or composition-aware model"],
        "distribution": ["analysis unit and sample size", "effect size and uncertainty", "test/FDR if inference is claimed"],
        "correlation": ["independent sample size", "association estimate and confidence interval", "method and multiple-testing correction"],
        "roc": ["evaluation cohort", "AUC with uncertainty", "threshold policy and prevalence context"],
        "survival": ["time origin/event/censoring", "risk set", "effect estimate and confidence interval"],
        "cellchat": ["model/version and database", "interaction score/probability", "expression/spatial validation when claimed"],
        "genomics": ["event-calling definition", "sample denominator", "multiple-testing correction for driver/enrichment claims"],
        "spatial": ["scale and registration", "region/cell denominator", "spatial statistic and uncertainty when inferential"],
        "flow": ["node denominator", "flow/count definition", "sample-level uncertainty when comparing conditions"],
        "set_intersection": ["set definition", "universe", "intersection counts"],
        "trajectory": ["root/ordering method", "pseudotime uncertainty", "sample-aware validation"],
    }
    return mapping.get(family, ["analysis unit", "sample size", "declared transformation and uncertainty where applicable"])


CONFUSABLE_SUBTYPES: dict[str, list[str]] = {
    "radial_bar_lollipop": ["go_enrichment_circle", "enrichment_comet_link_dot", "gsea_running_score"],
    "mirrored_dual_metric_lollipop": ["mirrored_violin", "mutation_lollipop_domain"],
    "enrichment_comet_link_dot": ["radial_bar_lollipop", "enrichment_dotplot"],
    "enrichment_dendrogram_bar_composite": ["enrichment_bar", "annotated_heatmap"],
    "go_enrichment_circle": ["radial_bar_lollipop", "gsea_running_score"],
    "gsea_running_score": ["go_enrichment_circle", "radial_bar_lollipop"],
    "ternary_composition_scatter": ["correlation_scatter", "stacked_composition_bar"],
    "two_contrast_foldchange_concordance": ["volcano_scatter", "correlation_scatter"],
    "marker_dotplot_group_boxes": ["marker_dotplot", "cellchat_bubble"],
    "marker_dotplot": ["cellchat_bubble", "enrichment_dotplot"],
    "cellchat_bubble": ["marker_dotplot", "enrichment_dotplot"],
    "mutation_lollipop_domain": ["mirrored_dual_metric_lollipop", "mutation_rainfall"],
    "he_whole_slide": ["he_roi_zoom", "fluorescence_multichannel"],
    "he_roi_zoom": ["he_whole_slide", "segmentation_boundary_overlay"],
}


def clean_candidate_code(code: str) -> tuple[str, list[str]]:
    """Return an all-or-nothing safe source block.

    Removing only the line containing a forbidden call is unsafe for multiline
    Python/R expressions: argument lines can remain executable or make the
    embedded source unparsable.  Candidate modules are optional reference
    artifacts, so conservatively omit the complete source block instead.
    """
    findings: list[str] = []
    kept: list[str] = []
    for raw_line in code.splitlines():
        line = raw_line.rstrip()
        unsafe = (
            FORBIDDEN_CANDIDATE_RE.search(line)
            or ABSOLUTE_PATH_RE.search(line)
            or INSTALL_RE.search(line)
            or EXPORT_RE.search(line)
        )
        if unsafe:
            findings.append(line.strip()[:160])
            if (
                SAFE_STANDALONE_DROP_RE.fullmatch(line)
                and line.count("(") == line.count(")")
            ):
                continue
            # A partial multiline rewrite can leave invalid or misleading
            # code.  Withhold the complete block unless the unsafe statement
            # is one of the structurally safe wrappers above.
            return "", findings
        kept.append(line)
    cleaned = "\n".join(kept).strip() + "\n"
    return cleaned, findings


def candidate_payload(
    scheme_id: str,
    article: dict[str, Any],
    blocks: list[dict[str, Any]],
    block_dispositions: dict[str, str],
    required_inputs: list[str] | None = None,
    expected_object_chain: list[str] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Build traceable candidate modules after closing plot-object dependencies.

    A source fence can be globally classified as ``analysis_only`` while still
    being indispensable to a Scheme-specific plot chain (for example
    ``p1 <- plt + coord_polar()``).  Candidate construction therefore starts
    from plot/modifier/layout blocks and follows every declared object in the
    Scheme chain back to the fence that defines it.  An incomplete chain is
    retained for source audit, but it never receives ``build_candidate_plot``.
    """
    expected_chain = list(dict.fromkeys(expected_object_chain or []))
    available_by_backend: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for block in blocks:
        backend = infer_block_backend(block)
        if backend in {"r", "python"}:
            available_by_backend[backend].append(block)

    by_backend: dict[str, list[dict[str, Any]]] = {}
    closure_by_backend: dict[str, dict[str, Any]] = {}
    candidate_roles = {"plot_base", "semantic_modifier", "aesthetic_modifier", "layout"}
    for backend, available_blocks in sorted(available_by_backend.items()):
        definitions: dict[str, dict[str, Any]] = {}
        for block in available_blocks:
            for name in assigned_objects(str(block.get("code") or "")):
                definitions[name] = block

        initial_ids = {
            str(block["id"])
            for block in available_blocks
            if block_dispositions.get(str(block["id"])) in candidate_roles
        }
        # Only the backend that actually defines a declared chain object owns
        # that chain.  This avoids falsely failing an unrelated helper backend
        # in the rare mixed-language article.
        backend_chain = (
            expected_chain
            if len(available_by_backend) == 1
            else [name for name in expected_chain if name in definitions]
        )

        selected_ids = set(initial_ids)
        unresolved: list[str] = []
        dependency_ids: list[str] = []
        queue = list(reversed(backend_chain))
        visited: set[str] = set()
        while queue:
            name = queue.pop(0)
            if name in visited:
                continue
            visited.add(name)
            defining_block = definitions.get(name)
            if defining_block is None:
                unresolved.append(name)
                continue
            block_id = str(defining_block["id"])
            selected_ids.add(block_id)
            if block_id not in dependency_ids:
                dependency_ids.append(block_id)
            for new, parent in object_chains(str(defining_block.get("code") or "")):
                if new != name:
                    continue
                if parent in definitions:
                    queue.append(parent)
                else:
                    # A plot-object parent is not a normal data binding.  If its
                    # defining fence is absent, exposing a callable wrapper would
                    # only defer the broken chain to runtime.
                    unresolved.append(parent)

        source_blocks = [block for block in available_blocks if str(block["id"]) in selected_ids]
        if source_blocks:
            by_backend[backend] = source_blocks
            closure_by_backend[backend] = {
                "declared_object_chain": backend_chain,
                "dependency_block_ids": dependency_ids,
                "unresolved_objects": list(dict.fromkeys(unresolved)),
                "resolved": not unresolved,
            }
    files: dict[str, str] = {}
    removed_all: list[str] = []
    included_block_ids: list[str] = []
    omitted_block_ids: list[str] = []
    code_paths: dict[str, str] = {}
    entrypoints: dict[str, str] = {}
    for backend, source_blocks in sorted(by_backend.items()):
        fragments: list[str] = []
        included_for_backend: list[dict[str, Any]] = []
        for block in source_blocks:
            cleaned, removed = clean_candidate_code(str(block.get("code") or ""))
            removed_all.extend(f"{block['id']}: {line}" for line in removed)
            if cleaned.strip():
                marker = "#" if backend in {"r", "python"} else "//"
                fragments.append(f"{marker} source block: {block['id']}\n{cleaned}")
                included_block_ids.append(str(block["id"]))
                included_for_backend.append(block)
            else:
                omitted_block_ids.append(str(block["id"]))
        if not fragments:
            continue
        closure = closure_by_backend[backend]
        available_after_clean = {
            name
            for block in included_for_backend
            for name in assigned_objects(str(block.get("code") or ""))
        }
        removed_chain_objects = [
            name for name in closure["declared_object_chain"]
            if name not in available_after_clean
        ]
        if removed_chain_objects:
            closure["unresolved_objects"] = list(dict.fromkeys([
                *closure["unresolved_objects"], *removed_chain_objects,
            ]))
            closure["resolved"] = False
        extension = "R" if backend == "r" else "py"
        fragment_text = "\n".join(fragments).rstrip() + "\n"
        rel = f"assets/scheme-candidates/{scheme_id}/candidate.{extension}"
        encoded = json.dumps(fragment_text, ensure_ascii=False)
        expected_objects = [
            obj for obj in closure["declared_object_chain"]
            if obj and not obj.startswith(".")
        ] or list(
            dict.fromkeys(
                obj
                for block in included_for_backend
                for obj in assigned_plot_objects(str(block.get("code") or ""))
                if obj and not obj.startswith(".")
            )
        )
        callable_candidate = bool(closure["resolved"])
        if backend == "python":
            module = (
                "\"\"\"Import-safe candidate distilled from a traceable plotting chain.\"\"\"\n\n"
                f"CANDIDATE_SOURCE = {encoded}\n\n"
                "def get_candidate_source() -> str:\n"
                "    \"\"\"Return the sanitized source without executing it.\"\"\"\n"
                "    return CANDIDATE_SOURCE\n"
            )
            if callable_candidate:
                module += (
                "\ndef build_candidate_plot(bindings: dict | None = None):\n"
                "    \"\"\"Execute explicitly with caller-supplied bindings and return Figure/Axes.\n\n"
                "    This candidate is reference-only until its dependencies, input contract,\n"
                "    statistics, and native render have been validated.\n"
                "    \"\"\"\n"
                "    namespace = dict(bindings or {})\n"
                "    exec(compile(CANDIDATE_SOURCE, '<visualization-2026718-v1-candidate>', 'exec'), namespace, namespace)\n"
                f"    preferred = {list(reversed(expected_objects))!r}\n"
                "    try:\n"
                "        from matplotlib.axes import Axes\n"
                "        from matplotlib.figure import Figure\n"
                "        accepted = (Figure, Axes)\n"
                "    except Exception:\n"
                "        accepted = ()\n"
                "    for name in preferred:\n"
                "        value = namespace.get(name)\n"
                "        if accepted and isinstance(value, accepted):\n"
                "            return value\n"
                "        if hasattr(value, 'get_figure') or hasattr(value, 'savefig'):\n"
                "            return value\n"
                "    pyplot = namespace.get('plt')\n"
                "    if pyplot is not None and hasattr(pyplot, 'gcf'):\n"
                "        return pyplot.gcf()\n"
                "    raise RuntimeError('Candidate did not expose a Figure/Axes; supply the declared bindings and dependencies.')\n"
                )
                entrypoints[backend] = "build_candidate_plot"
            files[rel] = module
        else:
            module = (
                "# Source-safe candidate distilled from a traceable plotting chain.\n"
                f"CANDIDATE_SOURCE <- {encoded}\n\n"
                "candidate_source <- function() CANDIDATE_SOURCE\n"
            )
            if callable_candidate:
                preferred_r = "c(" + ", ".join(json.dumps(obj) for obj in reversed(expected_objects)) + ")"
                module += (
                "\nbuild_candidate_plot <- function(bindings = list()) {\n"
                "  if (!is.list(bindings)) stop('bindings must be a named list')\n"
                "  env <- list2env(bindings, parent = parent.frame())\n"
                "  result <- eval(parse(text = CANDIDATE_SOURCE), envir = env)\n"
                "  if (inherits(result, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(result)\n"
                f"  preferred <- {preferred_r}\n"
                "  for (name in preferred) {\n"
                "    if (!exists(name, envir = env, inherits = FALSE)) next\n"
                "    value <- get(name, envir = env, inherits = FALSE)\n"
                "    if (inherits(value, c('ggplot', 'Heatmap', 'HeatmapList', 'grob', 'gTree'))) return(value)\n"
                "  }\n"
                "  stop('Candidate did not expose a ggplot/Heatmap/grob; supply the declared bindings and dependencies.')\n"
                "}\n"
                )
                entrypoints[backend] = "build_candidate_plot"
            files[rel] = module
        code_paths[backend] = rel
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATOR,
        "scheme_id": scheme_id,
        "source_article_id": article["id"],
        "source_block_ids": sorted(set(included_block_ids)),
        "omitted_unsafe_source_block_ids": sorted(set(omitted_block_ids)),
        "candidate_code_path": code_paths,
        "entrypoints": entrypoints,
        "source_entrypoints": {backend: "get_candidate_source" if backend == "python" else "candidate_source" for backend in code_paths},
        "input_contract": {
            "bindings": "named objects required by the source chain; no file reads or hidden global state",
            "required_inputs": list(required_inputs or []),
            "expected_output_objects": expected_chain or list(dict.fromkeys(
                obj
                for block in blocks
                for obj in assigned_plot_objects(str(block.get("code") or ""))
                if obj and not obj.startswith(".")
            )),
        },
        "return_contract": {
            backend: (
                "ggplot, Heatmap/HeatmapList, grob/gTree"
                if backend == "r"
                else "matplotlib Figure or Axes"
            )
            for backend in code_paths
        },
        "validation_tier": "reference_only" if code_paths else "visual_only",
        "execution_validated": False,
        "callable": bool(entrypoints) and all(value.get("resolved") for value in closure_by_backend.values()),
        "object_chain_closure": closure_by_backend,
        "promotable": False,
        "safety": {
            "forbidden_operations_removed": len(removed_all),
            "forbidden_operation_examples": removed_all[:20],
            "requires_manual_input_contract": True,
            "requires_native_render_review": True,
        },
    }
    metadata_rel = f"assets/scheme-candidates/{scheme_id}/metadata.json"
    files[metadata_rel] = json_text(metadata)
    return files, metadata


def candidate_module_safe(relative: str, content: str) -> bool:
    """Validate the sanitized fragment embedded in an import/source-safe module."""
    if relative.endswith(".py"):
        match = re.search(r"(?m)^CANDIDATE_SOURCE = (.+)$", content)
    elif relative.endswith(".R"):
        match = re.search(r"(?m)^CANDIDATE_SOURCE <- (.+)$", content)
    else:
        return True
    if not match:
        return False
    try:
        fragment = json.loads(match.group(1))
    except json.JSONDecodeError:
        return False
    return not FORBIDDEN_CANDIDATE_RE.search(fragment) and not ABSOLUTE_PATH_RE.search(fragment)


def python_candidate_module_parseable(relative: str, content: str) -> bool:
    if not relative.endswith(".py"):
        return True
    try:
        ast.parse(content, filename=relative)
    except SyntaxError:
        return False
    match = re.search(r"(?m)^CANDIDATE_SOURCE = (.+)$", content)
    if not match:
        return False
    try:
        fragment = json.loads(match.group(1))
        ast.parse(fragment, filename=f"{relative}:CANDIDATE_SOURCE")
    except (json.JSONDecodeError, SyntaxError):
        return False
    return True


def tokenize(text: str) -> list[str]:
    text = text.lower()
    latin = re.findall(r"[a-z][a-z0-9_.+-]{1,}", text)
    cjk_runs = re.findall(r"[\u3400-\u9fff]+", text)
    cjk: list[str] = []
    for run in cjk_runs:
        for n in (2, 3, 4):
            cjk.extend(run[i:i+n] for i in range(max(0, len(run) - n + 1)))
    return sorted(set(latin + cjk))


def build_source_audit(source: Path, articles: list[dict[str, Any]], expected_blocks: int, expected_images: int) -> dict[str, Any]:
    matched = 0
    missing: list[str] = []
    manifest_parts: list[str] = []
    fence_total = 0
    for article in sorted(articles, key=lambda row: str(row["id"])):
        rel = str(article.get("article_path") or "")
        path = source / Path(rel)
        if not path.is_file():
            missing.append(str(article["id"]))
            continue
        data = path.read_bytes()
        matched += 1
        manifest_parts.append(f"{rel}\t{sha256_bytes(data)}")
        text = data.decode("utf-8-sig", errors="replace")
        fence_total += len(re.findall(r"(?m)^```[^\n]*\n.*?^```\s*$", text, re.S))
    image_files = [path for path in source.rglob("*") if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff", ".bmp"}]
    return {
        "mode": "bundled_snapshot" if source.resolve() == DEFAULT_SOURCE.resolve() else "external_read_only_audit",
        "articles_expected": len(articles),
        "articles_matched": matched,
        "missing_article_ids": missing,
        "markdown_fences_observed": fence_total,
        "catalog_blocks_expected": expected_blocks,
        "image_files_observed": len(image_files),
        "catalog_images_expected": expected_images,
        "article_manifest_sha256": sha256_bytes("\n".join(manifest_parts).encode("utf-8")),
    }


def unique_scheme_id(article: dict[str, Any], subtype: str, occurrence: int) -> str:
    base = str(article["id"]).removeprefix("article-")
    suffix = "" if occurrence == 1 else f"-{occurrence}"
    return f"scheme-{base}-{subtype}{suffix}-v1"


def legacy_ids_for(article_id: str, subtype: str, style_cards: list[dict[str, Any]]) -> list[str]:
    spec = SUBTYPES[subtype]
    if article_id in DECORATIVE_ARTICLE_IDS:
        return sorted(str(card["style_id"]) for card in style_cards if card.get("source_article_id") == article_id)
    result = []
    family_aliases = {
        "enrichment": {"gsea"}, "cellchat": {"cellchat_chord", "dotplot"}, "distribution": {"boxplot", "violin"},
        "spatial": {"spatial_image"}, "correlation": {"correlation"}, "embedding": {"embedding"},
        "dotplot": {"dotplot"}, "heatmap": {"heatmap"}, "volcano": {"volcano"}, "composition": {"composition"},
        "genomics": {"genomics"}, "set_intersection": {"set_intersection"}, "flow": {"flow"}, "roc": {"roc"},
        "survival": {"survival"}, "trajectory": {"trajectory"},
    }.get(spec.family, {spec.family})
    for card in style_cards:
        if card.get("source_article_id") == article_id and str(card.get("family")) in family_aliases:
            result.append(str(card["style_id"]))
    return sorted(set(result))


def build_all(
    records: list[dict[str, Any]],
    curation_data: dict[str, Any],
    source: Path,
    native_reviews: dict[str, dict[str, Any]] | None = None,
    native_review_files: list[str] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    articles = sorted((row for row in records if row.get("record_type") == "article"), key=lambda row: str(row["id"]))
    blocks = sorted((row for row in records if row.get("record_type") == "source_block"), key=lambda row: str(row["id"]))
    images = sorted((row for row in records if row.get("record_type") == "image"), key=lambda row: str(row["id"]))
    style_cards = load_jsonl(REFERENCES / "style-atlas.jsonl") if (REFERENCES / "style-atlas.jsonl").exists() else []
    article_by_id = {str(row["id"]): row for row in articles}
    blocks_by_article: dict[str, list[dict[str, Any]]] = defaultdict(list)
    images_by_article: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for block in blocks: blocks_by_article[str(block["article_id"])].append(block)
    for image in images: images_by_article[str(image["article_id"])].append(image)

    disposition_by_block: dict[str, str] = {}
    reason_by_block: dict[str, str] = {}
    for block in blocks:
        disposition, reason = classify_block(block, article_by_id[str(block["article_id"])])
        if disposition not in BLOCK_DISPOSITIONS:
            raise AssertionError(f"Invalid block disposition {disposition}")
        disposition_by_block[str(block["id"])] = disposition
        reason_by_block[str(block["id"])] = reason

    curation = dict((curation_data or {}).get("overrides") or {})
    native_reviews = native_reviews or {}
    native_review_files = native_review_files or []
    image_state: dict[str, dict[str, Any]] = {}
    for image in images:
        image_id = str(image["id"])
        role, reviewed, note, source_rule = classify_image(image, article_by_id[str(image["article_id"])], curation)
        native = native_reviews.get(image_id) or {}
        if native:
            role = str(native.get("role") or role)
            reviewed = bool(native.get("reviewed", True))
            note = str(native.get("note") or note)
            source_rule = "native_visual_review"
        if role not in IMAGE_ROLES:
            raise AssertionError(f"Invalid image role {role}")
        native_scheme_ids = native.get("scheme_ids") or []
        if isinstance(native_scheme_ids, str):
            native_scheme_ids = [native_scheme_ids]
        scheme_consistency_raw = native.get("scheme_consistency") or {}
        scheme_consistency = {
            str(key): normalize_consistency(value)
            for key, value in scheme_consistency_raw.items()
        } if isinstance(scheme_consistency_raw, dict) else {}
        explicit_rejected = native.get("rejected_scheme_ids") or []
        if isinstance(explicit_rejected, str):
            explicit_rejected = [explicit_rejected]
        rejected_scheme_ids = {
            str(value) for value in explicit_rejected
        } | {
            str(value)
            for value in native_scheme_ids
            if scheme_consistency.get(str(value)) in {"mismatch", "fail", "failed"}
        }
        positive_native_scheme_ids = [
            str(value) for value in native_scheme_ids
            if str(value) not in rejected_scheme_ids
        ]
        image_state[image_id] = {
            "role": role,
            "reviewed": reviewed,
            "note": note,
            "classification_source": source_rule,
            "scheme_ids": [],
            "native_scheme_ids": sorted(set(positive_native_scheme_ids)),
            "rejected_scheme_ids": sorted(rejected_scheme_ids),
            "scheme_consistency": scheme_consistency,
            "code_image_consistency": normalize_consistency(native.get("code_image_consistency")),
            "visual_fingerprint": native.get("visual_fingerprint"),
        }
    unknown_native_images = sorted(set(native_reviews) - set(image_state))
    if unknown_native_images:
        raise ValueError(f"Native reviews reference unknown image IDs: {unknown_native_images[:10]}")

    seeds_by_article: dict[str, list[SchemeSeed]] = {}
    for article in articles:
        aid = str(article["id"])
        seeds_by_article[aid] = derive_scheme_seeds(article, blocks_by_article[aid], disposition_by_block)

    scheme_rows: list[dict[str, Any]] = []
    candidate_files: dict[str, str] = {}
    occurrence_counter: Counter[tuple[str, str]] = Counter()
    scheme_ids_by_block: dict[str, list[str]] = defaultdict(list)
    legacy_to_schemes: dict[str, list[str]] = defaultdict(list)

    for article in articles:
        aid = str(article["id"])
        article_blocks = {str(block["id"]): block for block in blocks_by_article[aid]}
        for seed in seeds_by_article[aid]:
            occurrence_counter[(aid, seed.subtype)] += 1
            scheme_id = unique_scheme_id(article, seed.subtype, occurrence_counter[(aid, seed.subtype)])
            spec = SUBTYPES[seed.subtype]
            selected_blocks = [article_blocks[bid] for bid in seed.block_ids if bid in article_blocks]
            forced_eligibility = str((seed.forced or {}).get("eligibility") or "")
            if aid in LAYOUT_RESOURCE_ARTICLE_IDS:
                eligibility = "layout_resource"
            elif aid in AESTHETIC_RESOURCE_ARTICLE_IDS:
                eligibility = "aesthetic_modifier"
            elif forced_eligibility:
                eligibility = forced_eligibility
            elif selected_blocks:
                eligibility = "scientific_scheme"
            else:
                eligibility = "visual_reference"
            if eligibility not in ELIGIBILITIES:
                raise AssertionError(f"Invalid eligibility {eligibility}")

            image_ids_by_role: dict[str, list[str]] = defaultdict(list)
            forced_images = (seed.forced or {}).get("image_ids") or {}
            if forced_images:
                for role, ids in forced_images.items():
                    image_ids_by_role[str(role)].extend(str(value) for value in ids)
            else:
                linked_block_ids = set(seed.block_ids)
                for image in images_by_article[aid]:
                    iid = str(image["id"])
                    state = image_state[iid]
                    if state["classification_source"] == "native_visual_review":
                        scheme_consistency = state.get("scheme_consistency", {}).get(scheme_id) or state.get("code_image_consistency")
                        linked = (
                            scheme_id in state["native_scheme_ids"]
                            and scheme_consistency not in {"mismatch", "fail", "failed"}
                        )
                    else:
                        linked = (
                            image.get("nearest_block_id") in linked_block_ids
                            or (not selected_blocks and state["role"] in {"scientific_result", "published_reference"})
                        )
                    if linked:
                        image_ids_by_role[state["role"]].append(iid)

            final_ids = list(dict.fromkeys(image_ids_by_role.get("scientific_result", [])))
            reference_ids = list(dict.fromkeys(image_ids_by_role.get("published_reference", [])))
            intermediate_ids = list(dict.fromkeys(image_ids_by_role.get("intermediate_step", [])))
            primary_id = final_ids[-1] if final_ids else reference_ids[0] if reference_ids else None
            if primary_id is None and intermediate_ids:
                primary_id = intermediate_ids[-1]
            primary_state = image_state.get(primary_id or "", {})
            article_has_native_review = any(
                image_state[str(image["id"])]["classification_source"] == "native_visual_review"
                for image in images_by_article[aid]
            )
            if primary_state.get("reviewed") is True and primary_state.get("role") in {"scientific_result", "published_reference"}:
                review_status = "native_reviewed"
            elif primary_state.get("reviewed") is True:
                review_status = "native_reviewed_nonfinal"
            elif primary_id:
                review_status = "deterministic_only"
            elif article_has_native_review:
                review_status = "no_confirmed_native_image"
            else:
                review_status = "unreviewed"
            consistency = str(primary_state.get("scheme_consistency", {}).get(scheme_id) or primary_state.get("code_image_consistency") or (
                "confirmed" if (seed.forced and primary_id) or (primary_state.get("reviewed") is True and primary_id) else "pending"
            ))
            visual_fingerprint = (
                primary_state.get("visual_fingerprint")
                if isinstance(primary_state.get("visual_fingerprint"), dict)
                else {}
            )
            fingerprint_channels_value = visual_fingerprint.get("channels")
            precise_visual_channels = (
                fingerprint_channels_value
                if isinstance(fingerprint_channels_value, dict) and fingerprint_channels_value
                else None
            )
            appearance_subtype = str(visual_fingerprint.get("subtype") or "").strip() or None
            panel_locator = str(visual_fingerprint.get("panel_locator") or "").strip() or None
            fingerprint_marks = flatten_strings(visual_fingerprint.get("marks"))
            fingerprint_channels = flatten_strings(visual_fingerprint.get("channels"))
            fingerprint_layout = flatten_strings(visual_fingerprint.get("layout"))
            fingerprint_risks = flatten_strings(visual_fingerprint.get("risks"))
            native_visual_descriptions: list[str] = []
            if fingerprint_marks:
                native_visual_descriptions.append("图中主要由" + "、".join(fingerprint_marks[:6]) + "构成")
            if fingerprint_layout:
                native_visual_descriptions.append("布局为" + "、".join(fingerprint_layout[:3]))
            if fingerprint_channels:
                native_visual_descriptions.append("视觉通道包括" + "、".join(fingerprint_channels[:6]))

            semantics = dict(FAMILY_SEMANTICS.get(spec.family, DEFAULT_SEMANTICS))
            forced_source = (seed.forced or {}).get("source_semantics")
            source_semantics = forced_source or {
                "question": semantics["question"],
                "unit": semantics["unit"],
                "data_topology": semantics["topology"],
                "variables": precise_visual_channels or semantics["channels"],
                "statistical_intent": "descriptive_or_exploratory",
            }
            target_application = (seed.forced or {}).get("target_application") or {
                "question": semantics["question"],
                "adapter_required": False,
                "variable_mapping": precise_visual_channels or semantics["channels"],
            }
            declared_method = analysis_method(seed.subtype, selected_blocks)
            evidence_role = {
                "embedding": "overview",
                "distribution": "comparison",
                "composition": "comparison",
                "correlation": "comparison",
                "volcano": "discovery",
                "enrichment": "mechanism",
                "genomics": "discovery",
                "cellchat": "mechanism",
                "spatial": "overview",
                "roc": "validation",
                "survival": "validation",
            }.get(spec.family, "overview")
            block_calls = list(dict.fromkeys(call for block in selected_blocks for call in normalized_calls(str(block.get("code") or ""))))
            base_ids = [bid for bid in seed.block_ids if disposition_by_block.get(bid) == "plot_base"]
            modifier_ids = [bid for bid in seed.block_ids if disposition_by_block.get(bid) in {"semantic_modifier", "aesthetic_modifier"}]
            layout_ids = [bid for bid in seed.block_ids if disposition_by_block.get(bid) == "layout"]
            export_ids = [bid for bid in seed.block_ids if disposition_by_block.get(bid) == "export"]
            backends = sorted({backend for block in selected_blocks if (backend := infer_block_backend(block))})

            legacy_ids = legacy_ids_for(aid, seed.subtype, style_cards)
            for old_id in legacy_ids: legacy_to_schemes[old_id].append(scheme_id)

            candidate_metadata: dict[str, Any] = {"candidate_code_path": {}, "validation_tier": "visual-only"}
            if eligibility == "scientific_scheme" and base_ids:
                files, candidate_metadata = candidate_payload(
                    scheme_id,
                    article,
                    selected_blocks,
                    disposition_by_block,
                    required_inputs=list(semantics["required"]),
                    expected_object_chain=list(seed.object_chain),
                )
                candidate_files.update(files)
            candidate_code_path = candidate_metadata.get("candidate_code_path") or {}
            code_status = "reference_only" if candidate_code_path or selected_blocks else "visual_only"

            search_parts = [
                str(article.get("title") or ""), seed.subtype, spec.family, *spec.aliases_zh, *spec.aliases_en,
                *spec.visual_terms, *(str(block.get("heading") or "") for block in selected_blocks), *block_calls,
                semantics["question"], json.dumps(source_semantics.get("variables") or {}, ensure_ascii=False),
                *native_visual_descriptions,
                json.dumps(visual_fingerprint, ensure_ascii=False) if visual_fingerprint else "",
            ]
            search_document = " ".join(part for part in search_parts if part)
            row = {
                "schema_version": SCHEMA_VERSION,
                "scheme_id": scheme_id,
                "title": f"{article.get('title')} — {spec.aliases_zh[0]}",
                "eligibility": eligibility,
                "broad_family": spec.family,
                "geometry_subtype": seed.subtype,
                "analysis_method": declared_method,
                "evidence_role": evidence_role,
                "appearance_subtype": appearance_subtype,
                "source_semantics": source_semantics,
                "target_application": target_application,
                # Native pixels plus code/context provide the most specific
                # channel declaration.  Family defaults are only a fallback
                # for schemes that have not yet received a native fingerprint.
                "visual_channels": precise_visual_channels or semantics["channels"],
                "required_inputs": semantics["required"],
                "optional_inputs": ["分组、分面、标签或注释变量（按 Scheme 声明）"],
                "transformations": ["排序、缩放、Top-N、阈值和多重校正必须显式声明，不从图像猜测"],
                "required_statistics": required_statistics_for(spec.family, declared_method),
                "code_lineage": {
                    "block_ids": seed.block_ids,
                    "base_block_ids": base_ids,
                    "modifier_block_ids": modifier_ids,
                    "layout_block_ids": layout_ids,
                    "export_block_ids": export_ids,
                    "object_chain": seed.object_chain,
                    "calls": block_calls,
                },
                "image_evidence": {
                    "primary_image_id": primary_id,
                    "final_image_ids": final_ids,
                    "reference_image_ids": reference_ids,
                    "intermediate_image_ids": intermediate_ids,
                    "review_status": review_status,
                    "role_confirmed": bool(primary_state.get("reviewed") is True),
                    "scheme_link_confirmed": bool(seed.forced and primary_id) or scheme_id in primary_state.get("native_scheme_ids", []),
                    "code_image_consistency": consistency,
                    "evidence_level": (
                        "image_code" if primary_id and selected_blocks
                        else "image_metadata" if primary_id
                        else "none"
                    ),
                    "panel_locator": panel_locator,
                    "semantic_review": "native_reviewed" if primary_state.get("classification_source") == "native_visual_review" else "audited_override" if seed.forced else "pending_native_review",
                    "primary_visual_fingerprint": primary_state.get("visual_fingerprint"),
                },
                "visual_fingerprint": visual_fingerprint or None,
                "supported_claims": semantics["supports"],
                "claim_limits": semantics["limits"],
                "misread_risks": list(dict.fromkeys([
                    "不得把视觉相似性替代统计、分析单位或研究设计核验。",
                    *fingerprint_risks,
                ])),
                "recommended_companion": semantics["companion"],
                "aliases_zh": list(spec.aliases_zh),
                "aliases_en": list(spec.aliases_en),
                "fuzzy_descriptions": list(dict.fromkeys([
                    *[f"想要{term}的图" for term in spec.visual_terms[:3]],
                    *native_visual_descriptions,
                ])),
                "visual_feature_terms": list(dict.fromkeys([
                    *spec.visual_terms,
                    *fingerprint_marks,
                    *fingerprint_channels,
                    *fingerprint_layout,
                ])),
                "confusable_with": CONFUSABLE_SUBTYPES.get(seed.subtype, []),
                "negative_terms": (
                    ["圣诞树", "纯装饰", *CONFUSABLE_SUBTYPES.get(seed.subtype, [])]
                    if eligibility != "excluded"
                    else ["科研结果", "生信分析证据"]
                ),
                "backends": backends,
                "code_status": code_status,
                "candidate_code_path": candidate_code_path,
                "candidate_metadata_path": f"assets/scheme-candidates/{scheme_id}/metadata.json" if candidate_code_path else None,
                "candidate_entrypoints": candidate_metadata.get("entrypoints") or {},
                "candidate_callable": bool(candidate_metadata.get("callable")),
                "validation": {
                    "catalog_linkage": "pass",
                    "execution": "not_validated",
                    "source_code": candidate_metadata.get("validation_tier", "visual-only"),
                    "object_chain_closure": candidate_metadata.get("object_chain_closure") or {},
                    "visual": review_status,
                    "promotable": False,
                },
                "source": {
                    "article_id": aid,
                    "article_title": article.get("title"),
                    "article_path": article.get("article_path"),
                    "album_id": article.get("album_id"),
                    "sequence": article.get("sequence"),
                },
                "legacy_style_ids": legacy_ids,
                "search_document": search_document,
            }
            scheme_rows.append(row)
            for bid in seed.block_ids: scheme_ids_by_block[bid].append(scheme_id)
            for iid in set(final_ids + reference_ids + intermediate_ids):
                if iid in image_state and scheme_id not in image_state[iid]["scheme_ids"]:
                    image_state[iid]["scheme_ids"].append(scheme_id)

    scheme_rows.sort(key=lambda row: str(row["scheme_id"]))
    known_scheme_ids = {str(row["scheme_id"]) for row in scheme_rows}
    unknown_native_schemes = sorted({
        scheme_id
        for state in image_state.values()
        for scheme_id in state["native_scheme_ids"]
        if scheme_id not in known_scheme_ids
    })
    if unknown_native_schemes:
        raise ValueError(f"Native reviews reference unknown Scheme IDs: {unknown_native_schemes[:10]}")
    block_rows = []
    for block in blocks:
        bid = str(block["id"])
        block_rows.append({
            "schema_version": SCHEMA_VERSION,
            "block_id": bid,
            "article_id": block.get("article_id"),
            "disposition": disposition_by_block[bid],
            "reason": reason_by_block[bid],
            "language": block.get("language"),
            "backend": infer_block_backend(block) or None,
            "heading": block.get("heading"),
            "plot_calls": plot_calls(str(block.get("code") or "")),
            "assigned_objects": assigned_objects(str(block.get("code") or "")),
            "object_chains": [{"new": new, "parent": parent} for new, parent in object_chains(str(block.get("code") or ""))],
            "scheme_ids": sorted(set(scheme_ids_by_block.get(bid, []))),
            "source": block.get("source"),
            "fingerprint": block.get("fingerprint"),
        })

    image_rows = []
    for image in images:
        iid = str(image["id"])
        state = image_state[iid]
        image_rows.append({
            "schema_version": SCHEMA_VERSION,
            "image_id": iid,
            "article_id": image.get("article_id"),
            "role": state["role"],
            "reviewed": state["reviewed"],
            "review_note": state["note"],
            "classification_source": state["classification_source"],
            "scheme_ids": sorted(state["scheme_ids"]),
            "native_scheme_ids": state["native_scheme_ids"],
            "rejected_scheme_ids": state["rejected_scheme_ids"],
            "scheme_consistency": state["scheme_consistency"],
            "code_image_consistency": state["code_image_consistency"],
            "visual_fingerprint": state["visual_fingerprint"],
            "nearest_block_id": image.get("nearest_block_id"),
            "archive_path": image.get("archive_path"),
            "metadata": image.get("metadata"),
            "fingerprint": image.get("fingerprint"),
        })

    old_ids = sorted(str(card["style_id"]) for card in style_cards)
    aliases = {
        "schema_version": SCHEMA_VERSION,
        "aliases": {
            old_id: {
                "scheme_ids": sorted(set(legacy_to_schemes.get(old_id, []))),
                "status": "deprecated_excluded" if old_id.startswith("style-3792985494804332545-002-") else "one_to_many" if len(set(legacy_to_schemes.get(old_id, []))) > 1 else "mapped" if legacy_to_schemes.get(old_id) else "unmapped",
            }
            for old_id in old_ids
        },
    }

    inverted: dict[str, list[str]] = defaultdict(list)
    documents: dict[str, dict[str, Any]] = {}
    for scheme in scheme_rows:
        sid = str(scheme["scheme_id"])
        tokens = tokenize(str(scheme["search_document"]))
        documents[sid] = {
            "eligibility": scheme["eligibility"],
            "broad_family": scheme["broad_family"],
            "geometry_subtype": scheme["geometry_subtype"],
            "analysis_method": scheme["analysis_method"],
            "tokens": tokens,
        }
        for token in tokens: inverted[token].append(sid)
    retrieval_index = {
        "schema_version": SCHEMA_VERSION,
        "tokenization": {"latin": "lowercase words length>=2", "cjk": "2-4 character ngrams", "single_cjk_scored": False},
        "documents": documents,
        "inverted_index": {token: sorted(ids) for token, ids in sorted(inverted.items())},
    }

    source_audit = build_source_audit(source, articles, len(blocks), len(images))
    block_counts = Counter(disposition_by_block.values())
    image_counts = Counter(state["role"] for state in image_state.values())
    native_image_counts = Counter(
        state["role"] for state in image_state.values() if state.get("reviewed") is True
    )
    unreviewed_high_risk_images = sorted(
        image_id
        for image_id, state in image_state.items()
        if state["role"] in {"scientific_result", "published_reference", "uncertain"}
        and state.get("reviewed") is not True
    )
    eligibility_counts = Counter(row["eligibility"] for row in scheme_rows)
    eligibility_by_article: dict[str, set[str]] = defaultdict(set)
    for row in scheme_rows:
        eligibility_by_article[str(row["source"]["article_id"])].add(str(row["eligibility"]))
    article_tiers: dict[str, str] = {}
    for article in articles:
        aid = str(article["id"])
        values = eligibility_by_article.get(aid, set())
        if "scientific_scheme" in values:
            tier = "scientific_or_data_visualization_code"
        elif "visual_reference" in values:
            tier = "visual_or_workflow_reference"
        elif values & {"semantic_modifier", "aesthetic_modifier", "layout_resource"}:
            tier = "modifier_or_resource_only"
        else:
            tier = "excluded_decorative_or_nonplot"
        article_tiers[aid] = tier
    article_tier_counts = Counter(article_tiers.values())
    family_counts = Counter(row["broad_family"] for row in scheme_rows)
    subtype_counts = Counter(row["geometry_subtype"] for row in scheme_rows)
    code_counts = Counter(row["code_status"] for row in scheme_rows)
    candidate_metadata_records = [
        json.loads(content)
        for path, content in candidate_files.items()
        if path.endswith("/metadata.json")
    ]
    rose_candidate_metadata = next(
        (
            row for row in candidate_metadata_records
            if row.get("scheme_id") == "scheme-3792985494804332545-007-radial_bar_lollipop-v1"
        ),
        {},
    )
    hard_checks = {
        "blocks_exactly_once": len(block_rows) == 621 and len({row["block_id"] for row in block_rows}) == len(block_rows),
        "images_exactly_once": len(image_rows) == 709 and len({row["image_id"] for row in image_rows}) == len(image_rows),
        "christmas_excluded": all(row["eligibility"] == "excluded" for row in scheme_rows if row["source"]["article_id"] in DECORATIVE_ARTICLE_IDS),
        "christmas_not_scientific": not any(row["eligibility"] == "scientific_scheme" for row in scheme_rows if row["source"]["article_id"] in DECORATIVE_ARTICLE_IDS),
        "rose_lineage_exact": any(
            row["geometry_subtype"] == "radial_bar_lollipop"
            and row["code_lineage"]["block_ids"] == HARD_SCHEME_OVERRIDES["article-3792985494804332545-007"][0]["block_ids"]
            and row["image_evidence"]["primary_image_id"] == "article-3792985494804332545-007-i008"
            for row in scheme_rows
        ),
        "required_key_subtypes_present": all(name in subtype_counts for name in {
            "radial_bar_lollipop", "mirrored_dual_metric_lollipop", "enrichment_comet_link_dot",
            "enrichment_dendrogram_bar_composite", "go_enrichment_circle", "ternary_composition_scatter",
            "two_contrast_foldchange_concordance", "mutation_lollipop_domain",
        }),
        "candidate_safety": all(candidate_module_safe(path, text) for path, text in candidate_files.items() if path.endswith((".R", ".py"))),
        "candidate_object_chains_guarded": all(
            not row.get("entrypoints")
            or (
                row.get("callable") is True
                and all(state.get("resolved") is True for state in (row.get("object_chain_closure") or {}).values())
            )
            for row in candidate_metadata_records
        ),
        "rose_candidate_chain_closed": (
            rose_candidate_metadata.get("source_block_ids")
            == HARD_SCHEME_OVERRIDES["article-3792985494804332545-007"][0]["block_ids"]
            and rose_candidate_metadata.get("callable") is True
            and all(
                state.get("resolved") is True
                for state in (rose_candidate_metadata.get("object_chain_closure") or {}).values()
            )
        ),
        "python_candidate_modules_parse": all(
            python_candidate_module_parseable(path, text)
            for path, text in candidate_files.items()
            if path.endswith(".py")
        ),
        "high_risk_images_native_reviewed": not unreviewed_high_risk_images,
        "source_articles_present": source_audit["articles_matched"] == len(articles),
    }
    coverage = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATOR,
        "totals": {"articles": len(articles), "blocks": len(block_rows), "images": len(image_rows), "schemes": len(scheme_rows), "candidate_files": len(candidate_files)},
        "block_dispositions": dict(sorted(block_counts.items())),
        "image_roles": dict(sorted(image_counts.items())),
        "native_reviewed_image_roles": dict(sorted(native_image_counts.items())),
        "unreviewed_high_risk_images": unreviewed_high_risk_images,
        "eligibility": dict(sorted(eligibility_counts.items())),
        "article_tiers": {
            "counts": dict(sorted(article_tier_counts.items())),
            "by_article": dict(sorted(article_tiers.items())),
        },
        "families": dict(sorted(family_counts.items())),
        "subtypes": dict(sorted(subtype_counts.items())),
        "code_status": dict(sorted(code_counts.items())),
        "native_reviewed_scientific_schemes": sum(row["eligibility"] == "scientific_scheme" and row["image_evidence"]["review_status"] == "native_reviewed" for row in scheme_rows),
        "heuristic_or_missing_scientific_schemes": sum(row["eligibility"] == "scientific_scheme" and row["image_evidence"]["review_status"] != "native_reviewed" for row in scheme_rows),
        "source_audit": source_audit,
        "native_visual_reviews": {
            "directory_present": bool(native_review_files),
            "files": native_review_files,
            "records_applied": len(native_reviews),
            "reviewed_images_applied": sum(bool(row.get("reviewed", True)) for row in native_reviews.values()),
        },
        "hard_checks": hard_checks,
        "all_hard_checks_pass": all(hard_checks.values()),
    }
    overrides = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATOR,
        "decorative_article_ids": sorted(DECORATIVE_ARTICLE_IDS),
        "scheme_overrides": HARD_SCHEME_OVERRIDES,
        "image_overrides": HARD_IMAGE_OVERRIDES,
    }

    files = {
        str(SCHEME_PATH.relative_to(SKILL_ROOT)).replace("\\", "/"): jsonl_text(scheme_rows),
        str(BLOCK_PATH.relative_to(SKILL_ROOT)).replace("\\", "/"): jsonl_text(block_rows),
        str(IMAGE_PATH.relative_to(SKILL_ROOT)).replace("\\", "/"): jsonl_text(image_rows),
        str(ALIASES_PATH.relative_to(SKILL_ROOT)).replace("\\", "/"): json_text(aliases),
        str(INDEX_PATH.relative_to(SKILL_ROOT)).replace("\\", "/"): json_text(retrieval_index),
        str(COVERAGE_PATH.relative_to(SKILL_ROOT)).replace("\\", "/"): json_text(coverage),
        str(OVERRIDES_PATH.relative_to(SKILL_ROOT)).replace("\\", "/"): json_text(overrides),
        **candidate_files,
    }
    return files, coverage


def safe_remove_stale_candidates(expected: set[Path]) -> None:
    if not CANDIDATE_ROOT.exists():
        return
    root = CANDIDATE_ROOT.resolve()
    expected_dirs = {path.parent.resolve() for path in expected if root in path.resolve().parents}
    for child in CANDIDATE_ROOT.iterdir():
        if not child.is_dir() or child.resolve() in expected_dirs:
            continue
        metadata = child / "metadata.json"
        if not metadata.exists():
            continue
        try:
            value = load_json(metadata, {})
        except (ValueError, json.JSONDecodeError):
            continue
        if value.get("generated_by") == GENERATOR and root in child.resolve().parents:
            shutil.rmtree(child)


def write_or_check(files: dict[str, str], check: bool) -> tuple[bool, list[str]]:
    mismatches: list[str] = []
    expected_paths: set[Path] = set()
    for relative, content in sorted(files.items()):
        path = SKILL_ROOT / Path(relative)
        expected_paths.add(path)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            mismatches.append(relative)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
    if not check:
        safe_remove_stale_candidates(expected_paths)
    return not mismatches, mismatches


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Build Scheme v2 catalog, dispositions, aliases, index, coverage, and safe candidates")
    result.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    result.add_argument("--curation", type=Path, default=CURATION_PATH)
    result.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Read-only source root used for provenance audit")
    result.add_argument("--native-reviews-dir", type=Path, default=DEFAULT_NATIVE_REVIEWS, help="Optional directory of native visual-review JSONL batches")
    result.add_argument("--check", action="store_true", help="Compare all generated artifacts without writing")
    return result


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            except (OSError, ValueError):
                pass
    args = parser().parse_args()
    catalog = args.catalog.resolve()
    curation = args.curation.resolve()
    source = args.source.resolve()
    if not catalog.is_file():
        raise FileNotFoundError(catalog)
    if not source.is_dir():
        raise FileNotFoundError(source)
    records = load_jsonl(catalog)
    curation_data = load_json(curation, {"overrides": {}})
    native_reviews, native_review_files = load_native_reviews(args.native_reviews_dir.resolve())
    files, coverage = build_all(records, curation_data, source, native_reviews, native_review_files)
    up_to_date, mismatches = write_or_check(files, args.check)
    result = {
        "schema_version": SCHEMA_VERSION,
        "mode": "check" if args.check else "write",
        "up_to_date": up_to_date if args.check else True,
        "changed_or_mismatched_files": mismatches,
        "totals": coverage["totals"],
        "eligibility": coverage["eligibility"],
        "hard_checks": coverage["hard_checks"],
        "all_hard_checks_pass": coverage["all_hard_checks_pass"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not coverage["all_hard_checks_pass"]:
        return 2
    return 0 if (not args.check or up_to_date) else 1


if __name__ == "__main__":
    sys.exit(main())
