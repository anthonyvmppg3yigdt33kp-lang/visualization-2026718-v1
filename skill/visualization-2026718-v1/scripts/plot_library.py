#!/usr/bin/env python3
"""Offline catalog, retrieval, composition, and validation for visualization-2026718-v1."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = SKILL_ROOT / "assets" / "source_archive"
RECIPES_ROOT = SKILL_ROOT / "assets" / "recipes"
CANDIDATES_ROOT = SKILL_ROOT / "assets" / "candidates"
CATALOG_PATH = SKILL_ROOT / "references" / "catalog.jsonl"
COVERAGE_PATH = SKILL_ROOT / "references" / "coverage.json"
IMAGE_CURATION_PATH = SKILL_ROOT / "references" / "image-curation.json"
BENCHMARK_PATH = SKILL_ROOT / "references" / "benchmark-prompts.jsonl"
DECISION_CARDS_PATH = SKILL_ROOT / "references" / "decision-cards.json"
STABLE_IDS_PATH = SKILL_ROOT / "references" / "stable-ids.json"
VISUAL_BENCHMARK_PATH = SKILL_ROOT / "references" / "visual-review-benchmark.jsonl"
VISUAL_RESULTS_PATH = SKILL_ROOT / "references" / "visual-review-results.jsonl"
EXACT_RENDER_REVIEW_PATH = SKILL_ROOT / "references" / "exact-render-review.jsonl"
STYLE_ATLAS_PATH = SKILL_ROOT / "references" / "style-atlas.jsonl"
STYLE_COVERAGE_PATH = SKILL_ROOT / "references" / "style-coverage.json"
SCHEME_CATALOG_PATH = SKILL_ROOT / "references" / "scheme-catalog.jsonl"
BLOCK_DISPOSITIONS_PATH = SKILL_ROOT / "references" / "block-dispositions.jsonl"
IMAGE_DISPOSITIONS_PATH = SKILL_ROOT / "references" / "image-dispositions.jsonl"
SCHEME_ALIASES_PATH = SKILL_ROOT / "references" / "scheme-aliases.json"
RETRIEVAL_INDEX_PATH = SKILL_ROOT / "references" / "retrieval-index.json"
SCHEME_COVERAGE_PATH = SKILL_ROOT / "references" / "scheme-coverage.json"
SCHEME_BENCHMARK_PATH = SKILL_ROOT / "references" / "scheme-benchmark-prompts.jsonl"
SCHEME_CANDIDATE_ROOT = SKILL_ROOT / "assets" / "scheme-candidates"
SOURCE_CHECKSUMS_NAME = "SHA256SUMS.csv"

SCIENTIFIC_SCHEME_ELIGIBILITY = {
    "scientific",
    "scientific_scheme",
    "scientific_result",
    "evidence_scheme",
    "analysis_visualization",
}
NON_SCIENTIFIC_SCHEME_ELIGIBILITY = {
    "aesthetic_modifier",
    "layout",
    "layout_resource",
    "palette",
    "resource",
    "resource_only",
    "visual_reference",
    "decorative",
    "decorative_result",
    "excluded",
    "nonplot",
    "non_plot",
    "prompt_non_code",
}
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
IMAGE_DISPOSITIONS = {
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

_JSONL_CACHE: dict[Path, tuple[int, int, list[dict[str, Any]]]] = {}
_JSON_CACHE: dict[Path, tuple[int, int, Any]] = {}
_SCHEME_RECORD_CACHE: tuple[int, int, list[dict[str, Any]]] | None = None
_SCHEME_FEATURE_CACHE: dict[str, dict[str, Any]] = {}
_QUERY_TOKEN_CACHE: dict[str, set[str]] = {}
_FORMAL_RECIPE_INDEX_CACHE: dict[str, dict[str, Any]] | None = None

EXPECTED = {
    "articles": 97,
    "source_blocks": 621,
    "images": 709,
    "raw_languages": {"r": 604, "python": 16, "bash": 1},
}

# Deterministic Scheme -> formal Recipe routing.  These IDs are deliberately
# explicit: a visually similar source Scheme must not be called "executable"
# unless an installed, backend-matched formal Recipe implements its target
# contract.  Candidate source code remains a separate, lower-assurance state.
FORMAL_BASE_RECIPE_CANDIDATES: dict[tuple[str, str], tuple[str, ...]] = {
    ("sample_level_composition", "python"): ("sample-composition-python-v1",),
    ("stacked_composition_bar", "python"): ("sample-composition-python-v1",),
    ("embedding_scatter", "python"): ("umap-dataframe-python-v1",),
    ("embedding_scatter", "r"): ("umap-dataframe-r-v1",),
    ("radial_bar_lollipop", "r"): ("enrichment-rose-r-v1",),
    ("enrichment_rose", "r"): ("enrichment-rose-r-v1",),
    ("marker_dotplot", "r"): ("marker-dotplot-r-v1",),
    ("marker_dotplot_group_boxes", "r"): ("marker-dotplot-r-v1",),
    ("annotated_heatmap", "r"): ("complex-heatmap-r-v1",),
    ("grouped_volcano", "r"): ("grouped-volcano-r-v1",),
    ("gsea_rank_score_dot", "r"): ("gsea-summary-r-v1",),
    ("roc_curve", "r"): ("roc-curve-r-v1",),
    ("cellchat_chord", "r"): ("cellchat-chord-r-v1",),
    ("cellchat_circle_network", "r"): ("cellchat-circle-r-v1",),
    ("cellchat_bubble", "r"): ("cellchat-bubble-r-v1",),
    ("cellchat_heatmap", "r"): ("cellchat-heatmap-r-v1",),
    ("box_jitter", "r"): ("box-jitter-r-v1",),
    ("he_cell_overlay", "python"): ("xenium-he-overlay-python-v1",),
    ("spatial_spot_overlay", "r"): ("seurat-spatial-overlay-r-v1",),
}

FORMAL_FAMILY_RECIPE_CANDIDATES: dict[tuple[str, str], tuple[str, ...]] = {
    ("sample_level_composition", "python"): ("sample-composition-python-v1",),
    ("embedding", "python"): ("umap-dataframe-python-v1",),
    ("embedding", "r"): ("umap-dataframe-r-v1",),
    ("dotplot", "r"): ("marker-dotplot-r-v1",),
    ("heatmap", "r"): ("complex-heatmap-r-v1",),
    ("volcano", "r"): ("grouped-volcano-r-v1",),
    ("roc", "r"): ("roc-curve-r-v1",),
    ("cellchat_chord", "r"): ("cellchat-chord-r-v1",),
    ("boxplot", "r"): ("box-jitter-r-v1",),
    ("spatial_image", "python"): ("xenium-he-overlay-python-v1",),
    ("spatial_image", "r"): ("seurat-spatial-overlay-r-v1",),
}

FORMAL_MODIFIER_RECIPE_IDS: dict[tuple[str, str], str] = {
    ("label-repel", "python"): "label-repel-python-v1",
    ("label-repel", "r"): "label-repel-r-v1",
    ("borderless", "python"): "borderless-python-v1",
    ("borderless", "r"): "borderless-r-v1",
    ("marker-box", "r"): "marker-box-r-v1",
    ("arrow-axes", "r"): "arrow-axes-r-v1",
    ("shared-legend", "r"): "shared-legend-r-v1",
    ("dark-nebula", "r"): "dark-nebula-r-v1",
}

FENCE_RE = re.compile(r"^\s*```([A-Za-z0-9_+.-]*)\s*$")
# Match through the image suffix so balanced parentheses inside local filenames
# (common in article titles) are not mistaken for the closing Markdown token.
IMAGE_RE = re.compile(
    r"!\[[^\]]*\]\((.+\.(?:png|jpe?g|gif|webp|tiff?))(?:\s+[\"'][^\"']*[\"'])?\)",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

FAMILY_TERMS: dict[str, tuple[str, ...]] = {
    "embedding": ("umap", "t-sne", "tsne", "pca", "pcoa", "nmds", "降维", "嵌入", "星云", "云雾"),
    "dotplot": ("dotplot", "dot plot", "bubble", "气泡图", "泡泡图", "marker基因气泡"),
    "heatmap": ("heatmap", "complexheatmap", "pheatmap", "热图", "聚类热图"),
    "volcano": ("volcano", "火山图", "log2fc", "logfc", "fold change"),
    "gsea": ("gsea", "fgsea", "富集", "enrichment", "kegg", "gene set", "通路"),
    "boxplot": ("boxplot", "box plot", "箱线图", "箱图", "jitter", "雨云图", "raincloud"),
    "violin": ("violin", "小提琴", "ridge", "ridgeline", "山脊", "山峦"),
    "composition": ("stacked bar", "stacked", "barplot", "堆积", "柱状图", "组成", "比例", "composition"),
    "cellchat_chord": ("cellchat", "chord", "弦图", "细胞通讯", "interaction", "互作", "贝壳图"),
    "flow": ("sankey", "alluvial", "桑基", "河流图", "冲积图"),
    "correlation": ("correlation", "corrplot", "相关", "scatter", "散点", "ternary", "三元图"),
    "set_intersection": ("upset", "venn", "韦恩", "交集", "集合"),
    "survival": ("survival", "kaplan", "cox", "生存", "森林图", "forest"),
    "roc": ("roc", "auc", "receiver operating", "诊断曲线"),
    "genomics": ("maftools", "genvisr", "lollipop", "棒棒糖", "maf", "突变", "基因组"),
    "spatial_image": ("xenium", "spatial", "空间", "he图片", "h&e", "he切片", "荧光", "segmentation"),
    "trajectory": ("pseudotime", "trajectory", "monocle", "拟时序", "轨迹"),
    "layout": ("patchwork", "multipanel", "multi-panel", "拼图", "排版", "布局", "共享图例"),
    "palette": ("palette", "color", "配色", "调色", "颜色"),
    "decorative": ("圣诞树", "christmas tree", "装饰"),
}

FAMILY_NORMALIZATION = {
    "axis_style": "embedding",
    "theme": "layout",
    "labeling": "layout",
    "dotplot_annotation": "dotplot",
    "multipanel": "layout",
    "export": "layout",
    "network": "cellchat_chord",
    "cellchat": "cellchat_chord",
    "enrichment": "gsea",
    "spatial": "spatial_image",
}

DOMAIN_TERMS = {
    "single_cell": ("single cell", "single-cell", "单细胞", "seurat", "scanpy", "anndata"),
    "spatial": ("spatial", "空间", "xenium", "visium", "he切片"),
    "bulk_omics": ("bulk", "bulk rna", "deseq", "limma", "转录组"),
    "clinical": ("patient", "clinical", "survival", "roc", "患者", "临床", "生存"),
    "microbiome": ("microbiome", "pcoa", "beta diversity", "微生物", "物种"),
    "pathway": ("gsea", "enrichment", "kegg", "go", "富集", "通路"),
}

VISUAL_TERMS = {
    "highlight": ("highlight", "突出", "高亮", "框", "圈"),
    "arrow_axes": ("arrow", "箭头", "左下角坐标"),
    "borderless": ("borderless", "no border", "去边框", "不要边框"),
    "direct_labels": ("direct label", "repel", "直接标签", "标注", "标签避让"),
    "annotation": ("annotation", "注释", "临床注释", "marker分组"),
    "journal_style": ("nature", "science", "cell", "期刊", "发表", "高分杂志"),
}

OBJECT_TERMS: dict[str, tuple[str, ...]] = {
    "Seurat": ("seurat",),
    "AnnData": ("anndata", "scanpy"),
    "CellChat": ("cellchat",),
    "data.frame": ("data.frame", "dataframe", "data frame", "表格", "长表"),
    "matrix": ("matrix", "矩阵"),
    "image": ("image", "h&e", "he底图", "图像", "荧光图"),
}

UNIT_TERMS: dict[str, tuple[str, ...]] = {
    "cell": ("cell", "细胞", "cluster"),
    "donor": ("donor", "供者"),
    "sample": ("sample", "样本"),
    "patient": ("patient", "subject", "病人", "患者", "受试者"),
    "gene": ("gene", "marker", "基因"),
    "pathway": ("pathway", "gsea", "通路"),
    "interaction": ("interaction", "communication", "通讯", "互作"),
    "spatial_spot": ("spot", "xenium", "visium", "空间点"),
}

TOPOLOGY_TERMS: dict[str, tuple[str, ...]] = {
    "embedding": ("umap", "tsne", "t-sne", "embedding", "嵌入", "降维"),
    "matrix": ("matrix", "heatmap", "矩阵", "热图"),
    "long_table": ("data.frame", "dataframe", "long table", "长表", "表格"),
    "network": ("network", "cellchat", "chord", "网络", "弦图", "通讯"),
    "binary_outcome_scores": ("roc", "auc", "precision", "recall", "binary", "阳性率", "分类模型"),
    "spatial_image": ("xenium", "h&e", "he底图", "荧光", "空间图像"),
    "repeated_measures": ("paired", "pre/post", "pre post", "repeated", "配对", "治疗前后"),
}

ALTERNATIVE_FAMILIES: dict[str, tuple[str, str]] = {
    "sample_level_composition": ("boxplot", "embedding"),
    "composition": ("boxplot", "embedding"),
    "embedding": ("sample_level_composition", "dotplot"),
    "dotplot": ("boxplot", "heatmap"),
    "heatmap": ("dotplot", "gsea"),
    "volcano": ("boxplot", "heatmap"),
    "gsea": ("heatmap", "dotplot"),
    "boxplot": ("data_audit", "violin"),
    "paired_plot": ("data_audit", "boxplot"),
    "roc": ("precision_recall", "calibration"),
    "precision_recall": ("roc", "calibration"),
    "calibration": ("roc", "precision_recall"),
    "cellchat_chord": ("cellchat_dotplot", "heatmap"),
    "cellchat_dotplot": ("heatmap", "cellchat_chord"),
    "spatial_image": ("layout", "embedding"),
    "layout": ("visual_review", "visual_examples"),
    "visual_review": ("layout", "data_audit"),
    "intent_clarification": ("data_audit", "visual_examples"),
    "data_audit": ("intent_clarification", "visual_examples"),
    "violin": ("boxplot", "heatmap"),
    "correlation": ("boxplot", "heatmap"),
    "set_intersection": ("composition", "flow"),
    "survival": ("data_audit", "roc"),
    "flow": ("composition", "heatmap"),
    "genomics": ("volcano", "heatmap"),
    "trajectory": ("embedding", "heatmap"),
    "palette": ("visual_review", "visual_examples"),
    "decorative": ("intent_clarification", "visual_examples"),
    "unknown": ("intent_clarification", "data_audit"),
}

CLAIM_BOUNDARIES = {
    "embedding": {
        "supports": "Shows the displayed local embedding neighborhoods and label or expression distribution.",
        "does_not_support": "Does not by itself establish abundance differences, significance, trajectory, global distance, or causality.",
    },
    "dotplot": {
        "supports": "Shows two declared visual quantities, commonly average expression and detected-cell proportion.",
        "does_not_support": "Does not by itself establish differential significance, independent replication, or causality.",
    },
    "heatmap": {
        "supports": "Shows relative patterns, direction, co-variation, ordering, or clustering under the declared transformation.",
        "does_not_support": "Scaled colors are not absolute abundance; significance and transformation details cannot be guessed from pixels.",
    },
    "volcano": {
        "supports": "Jointly displays an effect-size axis and a declared significance measure.",
        "does_not_support": "Statistical significance alone is not biological importance or causality.",
    },
    "gsea": {
        "supports": "Shows gene-set enrichment direction and magnitude under the declared ranking and FDR method.",
        "does_not_support": "Does not establish single-gene causality or direct pathway activity without orthogonal evidence.",
    },
    "cellchat_chord": {
        "supports": "Shows a computationally inferred interaction network or aggregate communication score.",
        "does_not_support": "Does not prove physical molecular communication, flux, or causal signaling.",
    },
    "roc": {
        "supports": "Shows discrimination under the declared evaluation data and threshold sweep.",
        "does_not_support": "Does not establish calibration, external generalization, treatment benefit, or clinical utility.",
    },
    "survival": {
        "supports": "Shows time-to-event patterns or fitted effects under the declared censoring and model assumptions.",
        "does_not_support": "Does not establish causal treatment benefit or adequate confounding control by itself.",
    },
    "boxplot": {
        "supports": "Shows visible distribution, center, and spread for the plotted observations.",
        "does_not_support": "Does not establish independence, significance, or confounding control without the analysis design.",
    },
    "spatial_image": {
        "supports": "Shows spatial localization, morphology, overlays, or segmentation visible in the selected image region.",
        "does_not_support": "Representative imagery alone does not establish population-level differences; scale and processing must be documented.",
    },
}

PLOT_PATTERNS = re.compile(
    r"\b(?:ggplot|geom_[A-Za-z0-9_]+|DimPlot|FeaturePlot|DotPlot|VlnPlot|DoHeatmap|"
    r"Heatmap|pheatmap|chordDiagram|netVisual_[A-Za-z0-9_]+|EnhancedVolcano|ggsurvplot|"
    r"ggroc|plotEnrichment|plotGseaTable|CellDimPlot|FeaturePlot_scCustom|upset|venn|"
    r"geom_alluvium|geom_density_ridges|plt\.|sns\.|sc\.pl\.|imshow|scatter)\b",
    re.I,
)

INSTALL_PATTERNS = re.compile(
    r"\b(?:install\.packages|BiocManager::install|remotes::install_github|pak::pkg_install|pip\s+install|conda\s+install)\b",
    re.I,
)

SAFETY_PATTERNS = {
    "workspace_clear": re.compile(r"rm\s*\(\s*list\s*=\s*ls\s*\(", re.I),
    "working_directory": re.compile(r"\bsetwd\s*\(", re.I),
    "installer": INSTALL_PATTERNS,
    "download": re.compile(r"\bdownload\.file\s*\(|requests\.get\s*\(|urllib\.request", re.I),
    "absolute_path": re.compile(r"(?:[A-Za-z]:[\\/]|/home/|/Users/|~/)"),
    "session_secret": re.compile(r"pass_ticket|exportkey|sessionid=|wx_header=|\bkey=[0-9a-f]{32,}", re.I),
}

# Source snippets are reference material, so hidden file writes are a cleanup
# requirement even though explicit export Recipes may legitimately save output.
SOURCE_ONLY_SAFETY_PATTERNS = {
    "implicit_file_write": re.compile(
        r"\b(?:ggsave|saveRDS|write\.csv|write\.table|fwrite|pdf|png|tiff|svg)\s*\(|"
        r"(?:plt|fig|figure|ax)\.savefig\s*\(|\.to_csv\s*\(",
        re.I,
    ),
}

CANDIDATE_SAFETY_PATTERNS = {
    **SAFETY_PATTERNS,
    **SOURCE_ONLY_SAFETY_PATTERNS,
    "network_or_remote_data": re.compile(
        r"requests\.(?:get|post|put|patch|delete)|urllib\.|urlretrieve|httpx\.|curl::|httr::|"
        r"getMutationsFromCbioportal\s*\(",
        re.I,
    ),
    "process_or_shell": re.compile(
        r"subprocess\.|os\.(?:system|popen|chdir)\s*\(|system2?\s*\(|shell\s*\(",
        re.I,
    ),
    "destructive_or_hidden_write": re.compile(
        r"os\.(?:remove|unlink)\s*\(|shutil\.(?:rmtree|move)\s*\(|unlink\s*\(|"
        r"file\.remove\s*\(|writeLines\s*\(|saveRDS\s*\(|"
        r"\bopen\s*\([^\n]+[\"'](?:w|a|x|wb|ab|xb)[\"']",
        re.I,
    ),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=path.parent) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    _JSON_CACHE.pop(path.resolve(), None)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=path.parent) as tmp:
        for row in rows:
            tmp.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    _JSONL_CACHE.pop(path.resolve(), None)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    resolved = path.resolve()
    stat = resolved.stat()
    cached = _JSONL_CACHE.get(resolved)
    if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return cached[2]
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(read_text(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    _JSONL_CACHE[resolved] = (stat.st_mtime_ns, stat.st_size, rows)
    return rows


def load_json_object(path: Path, default: Any = None) -> Any:
    """Load a generated JSON artifact without triggering source-tree scans."""
    if not path.exists():
        return {} if default is None else default
    resolved = path.resolve()
    stat = resolved.stat()
    cached = _JSON_CACHE.get(resolved)
    if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return cached[2]
    try:
        value = json.loads(read_text(path))
        _JSON_CACHE[resolved] = (stat.st_mtime_ns, stat.st_size, value)
        return value
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON at {path}: {exc}") from exc


def as_list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def flatten_text(value: Any) -> str:
    """Flatten nested generated metadata into deterministic searchable text."""
    if value in (None, ""):
        return ""
    if isinstance(value, dict):
        return " ".join(
            part
            for key, item in value.items()
            for part in (str(key), flatten_text(item))
            if part
        )
    if isinstance(value, (list, tuple, set)):
        return " ".join(filter(None, (flatten_text(item) for item in value)))
    return str(value)


def formal_recipe_scheme_records() -> list[dict[str, Any]]:
    """Expose reviewed original Recipes that have no source-derived Scheme.

    The source-derived Scheme catalog remains immutable and authoritative for
    article-backed designs.  A small explicit bridge prevents an exact,
    reviewed formal Recipe from disappearing only because the bundled source
    archive lacks that exact subtype.  These records never claim article
    provenance and remain tied to the formal Recipe validation contract.
    """
    specs = (
        {
            "recipe_id": "cellchat-heatmap-r-v1",
            "scheme_id": "formal-recipe-scheme-cellchat-heatmap-r-v1",
            "geometry_subtype": "cellchat_heatmap",
            "family": "cellchat_chord",
            "backend": "r",
            "aliases_zh": ["CellChat热图", "细胞通讯热图", "sender-receiver热图"],
            "aliases_en": ["CellChat heatmap", "sender receiver communication heatmap"],
        },
    )
    records: list[dict[str, Any]] = []
    for spec in specs:
        recipe_path = RECIPES_ROOT / spec["recipe_id"] / "recipe.json"
        recipe = load_json_object(recipe_path, {})
        checks = (recipe.get("validation") or {}).get("checks") or {}
        if (
            recipe.get("kind") != "base_recipe"
            or recipe.get("backend") != spec["backend"]
            or any(checks.get(name) != "pass" for name in ("schema", "syntax", "safety", "render", "visual"))
        ):
            continue
        preview = (recipe.get("files") or {}).get("preview")
        preview_path = (
            (RECIPES_ROOT / spec["recipe_id"] / str(preview)).resolve()
            if preview
            else None
        )
        final_path = (
            preview_path.with_name(preview_path.stem + "-final" + preview_path.suffix)
            if preview_path
            else None
        )
        if not preview_path or not preview_path.is_file() or not final_path or not final_path.is_file():
            continue
        semantic = recipe.get("semantic_card") if isinstance(recipe.get("semantic_card"), dict) else {}
        fingerprint = recipe.get("visual_fingerprint") if isinstance(recipe.get("visual_fingerprint"), dict) else {}
        record = {
            "schema_version": "2.0",
            "scheme_id": spec["scheme_id"],
            "id": spec["scheme_id"],
            "record_type": "scheme",
            "title": recipe.get("name") or spec["scheme_id"],
            "eligibility": "scientific_scheme",
            "family": spec["family"],
            "broad_family": spec["family"],
            "source_broad_family": spec["family"],
            "geometry_subtype": spec["geometry_subtype"],
            "analysis_method": "descriptive",
            "evidence_role": "comparison",
            "aliases_zh": spec["aliases_zh"],
            "aliases_en": spec["aliases_en"],
            "semantic_card": semantic,
            "visual_channels": semantic.get("visual_channels") or {},
            "required_inputs": semantic.get("required_variables") or [],
            "supported_claims": semantic.get("supports_claims") or [],
            "claim_limits": semantic.get("does_not_support") or [],
            "required_statistics": semantic.get("required_statistics") or [],
            "visual_fingerprint": fingerprint,
            "image_evidence": {
                "review_status": "formal_recipe_reviewed",
                "original_asset": rel_posix(preview_path),
                "final_asset": rel_posix(final_path),
                "evidence_level": "image_code_data",
                "code_image_consistency": "confirmed",
                "scheme_link_confirmed": True,
            },
            "recipe_ids": [spec["recipe_id"]],
            "backends": [spec["backend"]],
            "code_status": "formal_recipe",
            "validation": {
                "tier": (recipe.get("validation") or {}).get("tier") or "parse-verified",
                "recipe_ids": [spec["recipe_id"]],
                "review_status": "formal_recipe_reviewed",
            },
            "source": {
                "status": "original_formal_recipe",
                "recipe_id": spec["recipe_id"],
                "article_id": None,
            },
        }
        record["search_text"] = " ".join(
            filter(
                None,
                (
                    str(record["title"]),
                    str(record["family"]),
                    str(record["geometry_subtype"]),
                    flatten_text(record["aliases_zh"]),
                    flatten_text(record["aliases_en"]),
                    flatten_text(semantic),
                    flatten_text(fingerprint),
                ),
            )
        )
        records.append(record)
    return records


def load_scheme_records() -> list[dict[str, Any]]:
    """Load Scheme-v2 records while retaining every generated contract field.

    The Scheme catalog is authoritative for normal v2 retrieval.  Loading it is
    intentionally a small file operation: it never fingerprints or walks the
    immutable source archive.
    """
    global _SCHEME_RECORD_CACHE
    if not SCHEME_CATALOG_PATH.exists():
        return []
    stat = SCHEME_CATALOG_PATH.stat()
    if (
        _SCHEME_RECORD_CACHE
        and _SCHEME_RECORD_CACHE[0] == stat.st_mtime_ns
        and _SCHEME_RECORD_CACHE[1] == stat.st_size
    ):
        return _SCHEME_RECORD_CACHE[2]
    rows = load_jsonl(SCHEME_CATALOG_PATH)
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Scheme catalog record {index} must be a JSON object")
        scheme_id = str(row.get("scheme_id") or row.get("id") or "").strip()
        if not scheme_id:
            raise ValueError(f"Scheme catalog record {index} is missing scheme_id")
        record = dict(row)
        record["scheme_id"] = scheme_id
        record["id"] = scheme_id
        record["record_type"] = "scheme"
        record["geometry_subtype"] = normalize_text(
            row.get("geometry_subtype") or row.get("subtype") or "unknown"
        ).replace(" ", "_")
        source_family = normalize_text(row.get("broad_family") or row.get("family") or "unknown").replace(" ", "_")
        if source_family == "cellchat":
            normalized_family = "cellchat_chord"
        elif source_family == "enrichment":
            normalized_family = "gsea"
        elif source_family == "spatial":
            normalized_family = "spatial_image"
        elif source_family == "distribution" and "violin" in record["geometry_subtype"]:
            normalized_family = "violin"
        elif source_family == "distribution" and any(
            term in record["geometry_subtype"] for term in ("box", "raincloud", "jitter")
        ):
            normalized_family = "boxplot"
        else:
            normalized_family = canonical_family(source_family)
        record["source_broad_family"] = source_family
        record["family"] = normalized_family
        record["broad_family"] = normalized_family
        record["analysis_method"] = normalize_analysis_method(row.get("analysis_method"))
        semantic = row.get("semantic_card") if isinstance(row.get("semantic_card"), dict) else {}
        fingerprint = row.get("visual_fingerprint") if isinstance(row.get("visual_fingerprint"), dict) else {}
        record["title"] = (
            row.get("title")
            or row.get("name")
            or semantic.get("title")
            or semantic.get("name")
            or scheme_id
        )
        record["search_text"] = " ".join(
            filter(
                None,
                (
                    str(record["title"]),
                    str(record["family"]),
                    str(record["geometry_subtype"]),
                    str(record["analysis_method"]),
                    flatten_text(row.get("aliases")),
                    flatten_text(row.get("aliases_zh")),
                    flatten_text(row.get("aliases_en")),
                    flatten_text(row.get("fuzzy_phrases")),
                    flatten_text(row.get("fuzzy_descriptions")),
                    flatten_text(row.get("visual_signature_tokens")),
                    flatten_text(row.get("visual_feature_terms")),
                    flatten_text(row.get("contrastive_discriminators")),
                    flatten_text(row.get("source_semantics")),
                    flatten_text(row.get("target_application")),
                    flatten_text(row.get("visual_channels")),
                    flatten_text(semantic),
                    flatten_text(fingerprint),
                    flatten_text(row.get("search_document")),
                ),
            )
        )
        records.append(record)
    existing_ids = {str(record.get("scheme_id")) for record in records}
    records.extend(
        record
        for record in formal_recipe_scheme_records()
        if str(record.get("scheme_id")) not in existing_ids
    )
    _SCHEME_FEATURE_CACHE.clear()
    for record in records:
        subtype = str(record.get("geometry_subtype") or "unknown")
        specific_alias_values = [
            subtype,
            *GEOMETRY_SUBTYPE_TERMS.get(subtype, ()),
            *[str(item) for item in as_list(record.get("aliases"))],
            *[str(item) for item in as_list(record.get("aliases_zh"))],
            *[str(item) for item in as_list(record.get("aliases_en"))],
        ]
        generic_alias_values: list[str] = []
        if "lollipop" in subtype:
            generic_alias_values.extend(("棒棒图", "lollipop"))
        if any(term in subtype for term in ("circle", "circular", "radial", "chord")):
            generic_alias_values.extend(("圆形图", "circle plot", "circular plot"))
        if scheme_eligibility(record) in {"decorative", "decorative_result", "excluded"}:
            specific_alias_values.extend(("圣诞树", "christmas tree", "decorative"))
        alias_values = [*specific_alias_values, *generic_alias_values]
        fuzzy_values = [
            *as_list(record.get("fuzzy_phrases")),
            *as_list(record.get("fuzzy_descriptions")),
        ]
        fingerprint = record.get("visual_fingerprint") if isinstance(record.get("visual_fingerprint"), dict) else {}
        signature = (
            record.get("visual_signature_tokens")
            or record.get("visual_feature_terms")
            or fingerprint.get("visual_signature_tokens")
            or fingerprint
        )
        modifiers = {
            "semantic": record.get("semantic_modifiers"),
            "aesthetic": record.get("aesthetic_modifiers"),
            "fingerprint": fingerprint,
        }
        _SCHEME_FEATURE_CACHE[str(record.get("scheme_id"))] = {
            "search_tokens": text_tokens(record.get("search_text") or ""),
            "aliases": [normalize_text(item) for item in alias_values if normalize_text(item)],
            "specific_aliases": [
                normalize_text(item) for item in specific_alias_values if normalize_text(item)
            ],
            "generic_aliases": [
                normalize_text(item) for item in generic_alias_values if normalize_text(item)
            ],
            "signature_tokens": text_tokens(flatten_text(signature)),
            "modifier_tokens": text_tokens(flatten_text(modifiers)),
            "fuzzy_tokens": text_tokens(flatten_text(fuzzy_values)),
            "fuzzy_phrases": [normalize_text(item) for item in fuzzy_values if normalize_text(item)],
        }
    _SCHEME_RECORD_CACHE = (stat.st_mtime_ns, stat.st_size, records)
    return records


def load_catalog_fast() -> list[dict[str, Any]]:
    """Load the generated legacy catalog without a full source freshness walk."""
    if not CATALOG_PATH.exists():
        return []
    return load_jsonl(CATALOG_PATH)


def refresh_style_atlas(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Rebuild the derived style atlas whenever the authoritative catalog changes."""
    from build_style_atlas import build_cards, summarize, write_jsonl as write_atlas_jsonl

    cards = build_cards(records)
    summary = summarize(cards)
    write_atlas_jsonl(STYLE_ATLAS_PATH, cards)
    STYLE_COVERAGE_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return summary


def rel_posix(path: Path, root: Path = SKILL_ROOT) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def catalog_input_fingerprint(source_root: Path = SOURCE_ROOT) -> dict[str, Any]:
    """Fingerprint every input that can change catalog records or ranking metadata.

    Source binaries are represented by portable path/size inventory entries plus
    the archive checksum index, while the comparatively small generator, curation,
    decision, and Recipe files are hashed directly. File mtimes are intentionally
    excluded because a clean clone preserves bytes but assigns new timestamps.
    This keeps normal searches fast enough while still refusing a silently stale
    catalog after code or curated metadata changes.
    """
    digest = hashlib.sha256()
    entries = 0

    def add_bytes(label: str, path: Path) -> None:
        nonlocal entries
        digest.update(label.encode("utf-8"))
        if path.exists() and path.is_file():
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        else:
            digest.update(b"<missing>")
        entries += 1

    add_bytes("generator", Path(__file__).resolve())
    add_bytes("style-atlas-generator", SKILL_ROOT / "scripts" / "build_style_atlas.py")
    add_bytes("image-curation", IMAGE_CURATION_PATH)
    add_bytes("decision-cards", DECISION_CARDS_PATH)
    for path in sorted(RECIPES_ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix.lower() == ".pyc":
            continue
        add_bytes("recipe:" + path.relative_to(RECIPES_ROOT).as_posix(), path)

    # The checksum index is the content authority for the immutable archive.
    add_bytes("source-checksums", source_root / SOURCE_CHECKSUMS_NAME)
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or ".state" in path.parts or "_tools" in path.parts:
            continue
        rel = path.relative_to(source_root).as_posix()
        stat = path.stat()
        digest.update(f"source-stat:{rel}\0{stat.st_size}".encode("utf-8"))
        entries += 1
    return {"algorithm": "sha256-v2-portable", "sha256": digest.hexdigest(), "entries": entries}


def catalog_freshness(source_root: Path = SOURCE_ROOT) -> dict[str, Any]:
    if not CATALOG_PATH.exists() or not COVERAGE_PATH.exists():
        return {"fresh": False, "reason": "catalog_or_coverage_missing"}
    try:
        coverage = json.loads(read_text(COVERAGE_PATH))
    except (OSError, json.JSONDecodeError) as exc:
        return {"fresh": False, "reason": f"invalid_coverage:{type(exc).__name__}"}
    expected = coverage.get("catalog_input_fingerprint")
    current = catalog_input_fingerprint(source_root)
    return {
        "fresh": bool(expected and expected.get("sha256") == current.get("sha256")),
        "expected": expected,
        "current": current,
        "reason": None if expected and expected.get("sha256") == current.get("sha256") else "catalog_inputs_changed",
    }


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = re.sub(r"[_/\\|:;,.()\[\]{}<>+*=!?\"'`~—–-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def text_tokens(value: Any) -> set[str]:
    text = normalize_text(value)
    tokens = set(re.findall(r"[a-z][a-z0-9.+-]*|\d+(?:\.\d+)?", text))
    for seq in re.findall(r"[\u3400-\u9fff]+", text):
        # Single Han characters are too noisy for a 97-article plotting corpus.
        # Keep only 2--4 character n-grams; exact phrases are scored separately.
        for width in (2, 3, 4):
            if len(seq) < width:
                continue
            tokens.update(seq[i : i + width] for i in range(len(seq) - width + 1))
    return {token for token in tokens if token}


def query_tokens_cached(value: Any) -> set[str]:
    normalized = normalize_text(value)
    cached = _QUERY_TOKEN_CACHE.get(normalized)
    if cached is not None:
        return cached
    tokens = text_tokens(normalized)
    if len(_QUERY_TOKEN_CACHE) >= 256:
        _QUERY_TOKEN_CACHE.clear()
    _QUERY_TOKEN_CACHE[normalized] = tokens
    return tokens


def explicit_source_lookup(query: str) -> bool:
    """Return True only for an explicit request to locate source text.

    Calling, adapting, running, or rendering code is an action request, not a
    request to search the archive for an identifier.  Keeping those concepts
    separate prevents phrases such as ``调用代码并运行`` from bypassing
    scientific/Recipe ranking and entering raw-source mode.
    """
    normalized = normalize_text(query)
    return bool(
        re.search(
            r"(?:源码|源代码|代码块|标识符|"
            r"(?:查找|搜索|检索|定位|哪里|哪个|包含|含有).{0,32}(?:函数|标识符|代码)|"
            r"(?:函数|标识符).{0,20}(?:源码|源代码|在哪里)|"
            r"source\s*code|code\s*block|"
            r"(?:find|search|locate|where\s+is|contains?).{0,32}(?:function|identifier|code)|"
            r"(?:function|identifier).{0,20}(?:source|location))",
            normalized,
            re.I,
        )
    )


def detect_action_requests(query: str) -> dict[str, bool]:
    """Detect independent action flags for a possibly compound request.

    A caller can ask to execute/render *and then* review the result.  Review is
    therefore not mutually exclusive with execution and must never disable the
    executable/backend gates.
    """
    normalized = normalize_text(query)
    return {
        "review": bool(re.search(
            r"(?:复核|审阅|检查|看图|理解|解释).{0,16}(?:这张?图|结果图|成图|原图|投稿图|图片|图像)|"
            r"(?:结果图|成图|原图|投稿图|图片|图像).{0,24}(?:复核|审阅|检查|看图|理解|解释)|"
            r"(?:科学|结果|图形|图像).{0,8}(?:解释|解读)|(?:解释|解读).{0,8}(?:科学|结果|图形|图像)|"
            r"(?:review|inspect|interpret).{0,24}(?:figure|image|plot)|"
            r"(?:figure|image|plot).{0,24}(?:review|inspect|interpret)|"
            r"(?:生成|绘制|渲染|运行|执行)(?:完成)?(?:后|之后).{0,8}(?:复核|审阅|检查|看图|解读|解释)|"
            r"(?:复核|审阅|检查|看图|解读|解释).{0,8}(?:生成|绘制|渲染|运行|执行)(?:后|之后)?|"
            r"(?:之后|随后|最后)?(?:复核|审阅)(?:并)?(?:解释|解读)?",
            normalized,
            re.I,
        )),
        "render": bool(re.search(
            r"(?:生成|绘制|制作|输出|导出|渲染|预览).{0,12}(?:结果图|成图|图片|图像|figure|image|plot)|"
            r"(?:结果图|成图|图片|图像|figure|image|plot).{0,12}(?:生成|绘制|制作|输出|导出|渲染|预览)|"
            r"(?:生成|绘制|制作|输出|渲染|预览)(?!.{0,12}(?:代码|函数|模块)).{0,16}(?:图|plot)|"
            r"\brender\b|\bexport\b",
            normalized,
            re.I,
        )),
        "execute": bool(re.search(
            r"调用.{0,8}(?:代码|函数|模块|recipe)|(?:运行|执行).{0,12}(?:代码|函数|模块|recipe|绘图)?|"
            r"(?:代码|函数|模块|recipe).{0,12}(?:运行|执行)|\bexecute\b|\brun\s+(?:the\s+)?(?:code|recipe|module)\b",
            normalized,
            re.I,
        )),
        "adapt": bool(re.search(
            r"(?:适配|改写|封装|组合|拼接|返回|提供|生成).{0,16}(?:代码|函数|模块|recipe)|"
            r"(?:代码|函数|模块|recipe).{0,16}(?:适配|改写|封装|组合|拼接)|"
            r"\badapt\b|\bcompose\b|\bgenerate\s+(?:code|module|function)\b",
            normalized,
            re.I,
        )),
    }


def detect_action_intent(query: str) -> str:
    """Return the primary action while preserving compound flags elsewhere."""
    requested = detect_action_requests(query)
    # Execution-producing actions take precedence over their requested
    # post-render review.  The review flag is retained in FigureIntent.
    for action in ("render", "execute", "adapt", "review"):
        if requested[action]:
            return action
    return "discover"


def code_identifier_terms(query: str) -> list[str]:
    """Extract explicit function/object identifiers without treating UMAP-like
    scientific keywords as raw-code lookup requests.
    """
    if not explicit_source_lookup(query):
        return []
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9_.]*(?:::[A-Za-z][A-Za-z0-9_.]*)?", query)
    identifiers: list[str] = []
    for candidate in candidates:
        has_structure = any(marker in candidate for marker in ("_", ".", "::"))
        has_camel_case = bool(re.search(r"[a-z][A-Z]", candidate))
        token_only = bool(re.fullmatch(r"\s*" + re.escape(candidate) + r"\s*(?:\(\s*\))?\s*", query))
        function_context = bool(
            re.search(re.escape(candidate) + r".{0,8}(?:函数|function|调用|代码|code)", query, re.I)
            or re.search(r"(?:函数|function|调用|代码|code).{0,8}" + re.escape(candidate), query, re.I)
        )
        if has_structure or (has_camel_case and (token_only or function_context)):
            identifiers.append(candidate)
    return list(dict.fromkeys(identifiers))


def detect_terms(text: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    normalized = normalize_text(text)
    found = []
    for canonical, aliases in mapping.items():
        if any(normalize_text(alias) in normalized for alias in aliases):
            found.append(canonical)
    return found


def canonical_family(value: str | None) -> str:
    family = normalize_text(value).replace(" ", "_") if value else "unknown"
    return FAMILY_NORMALIZATION.get(family, family)


def normalize_analysis_method(value: Any) -> str:
    text = normalize_text(value).replace("-", "_").replace(" ", "_")
    if not text:
        return "unknown"
    if any(term in text for term in ("gsea", "fgsea", "preranked", "ranked_enrichment", "running_score")):
        return "gsea"
    if any(
        term in text
        for term in (
            "ora",
            "over_representation",
            "overrepresentation",
            "hypergeometric",
            "enrichgo",
            "enrichkegg",
        )
    ):
        return "ora"
    return text


GEOMETRY_SUBTYPE_TERMS: dict[str, tuple[str, ...]] = {
    "enrichment_rose": (
        "富集玫瑰图",
        "玫瑰图",
        "通路围成一圈",
        "通路像花瓣",
        "花瓣一样围成一圈",
        "外圈写通路",
        "扇叶长度",
        "中间留空",
        "极坐标柱",
        "polar bar",
        "radial bar",
        "radial bar lollipop",
    ),
    "radial_bar_lollipop": (
        "radial lollipop",
        "极坐标棒棒图",
        "圆形柱点图",
        "富集玫瑰图",
        "玫瑰图",
        "通路围成一圈",
        "通路像花瓣",
        "花瓣一样围成一圈",
        "外圈写通路",
        "扇叶长度",
        "极坐标柱形加棒棒糖",
    ),
    "mirrored_dual_metric_lollipop": (
        "背靠背棒棒图",
        "双向棒棒图",
        "mirrored lollipop",
        "dual metric lollipop",
        "左右镜像",
        "左右两半",
        "两边同时显示",
        "线长表示impact",
        "点大小表示ec score",
    ),
    "mirrored_violin": (
        "背靠背小提琴图",
        "镜像小提琴图",
        "双向小提琴图",
        "mirrored violin",
        "back to back violin",
    ),
    "enrichment_comet_link_dot": (
        "富集彗星图",
        "富集流星图",
        "彗星图",
        "流星图",
        "comet link dot",
        "连线点图",
        "末端有圆点",
        "线长显示负log10",
    ),
    "enrichment_dendrogram_bar_composite": (
        "富集树状柱图",
        "聚类树柱状图",
        "富集聚类树和条形图",
        "通路聚类树",
        "dendrogram and bar",
        "dendrogram bar",
    ),
    "go_enrichment_circle": (
        "gocircle",
        "go circle",
        "go富集圈图",
        "富集圆环图",
        "go term在圆环外层",
        "基因logfc和p.adjust",
    ),
    "ternary_composition_scatter": (
        "三元图",
        "ternary",
        "三角坐标组成",
        "三个比例之和固定为1",
        "点在三角形坐标",
    ),
    "two_contrast_foldchange_concordance": (
        "fold change concordance",
        "foldchange concordance",
        "双对比fold change",
        "两组差异倍数一致性",
        "log2fc一致性散点图",
        "两个contrast的fold change",
        "颜色和大小是第三个contrast",
        "两个logfc比较",
    ),
    "marker_dotplot_group_boxes": (
        "marker分组框",
        "加分组框",
        "框出每群marker",
        "add boxes",
        "marker boxes",
    ),
    "embedding_density_cloud": (
        "云雾密度umap",
        "单细胞云雾",
        "二维密度云",
        "高密区域",
        "nebulosa",
        "density umap",
    ),
    "mutation_lollipop_domain": ("突变棒棒糖", "蛋白结构域棒棒糖", "mutation lollipop", "protein lollipop"),
    "mutation_rainfall": ("rainfall plot", "maftools rainfall", "突变雨滴图", "突变降雨图"),
    "mutation_waterfall_oncoprint": ("突变瀑布图", "oncoplot", "oncoprint", "mutation waterfall"),
    "transition_transversion_spectrum": ("transition transversion", "ti tv spectrum", "tstv", "转换颠换谱"),
    "single_sample_cnv_profile": ("单样本cnv", "single sample cnv", "cnview", "染色体cnv谱"),
    "cohort_cnv_spectrum": ("队列cnv", "cohort cnv", "cnspec", "cnv频率谱"),
    "trajectory_pseudotime": ("拟时序", "pseudotime", "trajectory", "monocle轨迹"),
    "cellchat_bubble": ("cellchat通讯气泡图", "cellchat气泡图", "cellchat bubble"),
    "cellchat_chord": ("cellchat弦图", "chord diagram", "cellchat chord"),
    "cellchat_circle_network": ("cellchat圆形网络", "netvisual_circle", "cellchat circle network"),
    "cellchat_heatmap": ("cellchat热图", "cellchat heatmap", "netvisual_heatmap"),
    "sankey_alluvial": ("桑基图", "sankey", "alluvial", "通路与基因连接"),
    "he_whole_slide": ("he全景图", "h&e全景", "whole slide", "he whole slide"),
    "he_roi_zoom": ("he局部roi", "roi放大图", "he roi zoom"),
    "segmentation_boundary_overlay": ("分割边界叠加", "segmentation boundary", "细胞边界叠加"),
    "fluorescence_multichannel": ("多通道荧光图", "multichannel fluorescence", "fluorescence image"),
    "gsea_running_score": (
        "running score",
        "running enrichment score",
        "rank ticks",
        "运行富集分数",
        "gsea曲线",
        "gsea running",
    ),
}


def detect_geometry_subtypes(query: str) -> list[str]:
    normalized = normalize_text(query)
    matches: list[tuple[int, int, str]] = []
    for subtype, aliases in GEOMETRY_SUBTYPE_TERMS.items():
        positions = [normalized.find(normalize_text(alias)) for alias in aliases]
        positions = [position for position in positions if position >= 0]
        if positions:
            matches.append((min(positions), len(matches), subtype))

    # A CellChat request usually declares the context once, then lists panels
    # such as "圈图、弦图、气泡图与热图". Resolve each panel inside that context
    # and retain the user's textual order instead of dictionary order.
    if re.search(r"cellchat|细胞通讯|细胞簇.*通讯|communication", normalized, re.I):
        contextual = {
            "cellchat_circle_network": r"圈图|圆形网络|circle\s*(?:network|plot)|netvisual_circle",
            "cellchat_chord": r"弦图|chord(?:\s*diagram)?",
            "cellchat_bubble": r"气泡图|bubble(?:\s*plot)?",
            "cellchat_heatmap": r"热图|heatmap|netvisual_heatmap",
        }
        present = {subtype for _, _, subtype in matches}
        for subtype, pattern in contextual.items():
            hit = re.search(pattern, normalized, re.I)
            if hit and subtype not in present:
                matches.append((hit.start(), len(matches), subtype))
                present.add(subtype)
    matches.sort(key=lambda item: (item[0], item[1]))
    return [subtype for _, _, subtype in matches]


def detect_analysis_method(query: str) -> str:
    normalized = normalize_text(query)
    gsea = bool(
        re.search(
            r"\b(?:gsea|fgsea|nes|preranked)\b|running\s*score|ranked\s*(?:gene|list)|"
            r"leading\s*edge|core\s*enrichment|排序基因|运行富集分数|核心富集",
            normalized,
            re.I,
        )
    )
    ora = bool(
        re.search(
            r"\bora\b|over[ -]?representation|hypergeometric|enrichgo|enrichkegg|"
            r"generatio|p\.adjust|\bcount\b|过度富集|超几何",
            normalized,
            re.I,
        )
    )
    if gsea and ora:
        return "ambiguous_enrichment"
    if gsea:
        return "gsea"
    if ora:
        return "ora"
    return "unknown"


def infer_family(text: str) -> str:
    families = detect_terms(text, FAMILY_TERMS)
    return families[0] if families else "unknown"


def infer_domain(text: str) -> str:
    domains = detect_terms(text, DOMAIN_TERMS)
    return domains[0] if domains else "general"


def normalize_language(raw: str, code: str) -> tuple[str, str | None]:
    raw = normalize_text(raw).replace(" ", "") or "text"
    if raw == "py":
        raw = "python"
    python_score = 0
    r_score = 0
    python_score += 3 * len(re.findall(r"(?m)^\s*(?:from\s+\w+\s+import|import\s+\w+|def\s+\w+\s*\(|class\s+\w+)", code))
    python_score += 2 * len(re.findall(r"\b(?:plt|pd|np|sns|sc|ax|fig)\.", code))
    python_score += 2 * len(re.findall(r"\.copy\s*\(|\.value_counts\s*\(|f[\"']", code))
    python_score += len(re.findall(r"(?m)^\s*(?:for|if|while)\s+[^\n]+:\s*$", code))
    r_score += 3 * len(re.findall(r"<-|%>%|\|>", code))
    r_score += 2 * len(re.findall(r"\b(?:library|require)\s*\(|\b\w+::\w+|\bggplot\s*\(", code))
    r_score += len(re.findall(r"\$[A-Za-z_.][\w.]*|\b(?:TRUE|FALSE|NULL|NA)\b", code))
    detected = raw
    reason = None
    if raw == "r" and python_score >= 4 and python_score > r_score + 1:
        detected = "python"
        reason = f"content-language correction (python_score={python_score}, r_score={r_score})"
    elif raw == "python" and r_score >= 4 and r_score > python_score + 1:
        detected = "r"
        reason = f"content-language correction (r_score={r_score}, python_score={python_score})"
    return detected, reason


def classify_block(code: str) -> str:
    nonblank = [line for line in code.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    has_call = bool(re.search(r"[A-Za-z_.][\w.]*\s*\(", code))
    has_assign = bool(re.search(r"<-|(?<![=!<>])=(?!=)", code))
    if INSTALL_PATTERNS.search(code) and not PLOT_PATTERNS.search(code):
        return "install"
    if PLOT_PATTERNS.search(code):
        return "plot"
    if re.search(r"\b(?:read\.|readRDS|load\s*\(|mutate\s*\(|filter\s*\(|group_by\s*\(|pivot_|melt\s*\(|CreateSeuratObject|NormalizeData|RunUMAP)\b", code, re.I):
        return "data_prep"
    if len(nonblank) <= 3 and not has_call and not has_assign:
        return "non_code"
    if not has_call and not has_assign and len(code) < 240:
        return "non_code"
    return "other_code"


def latest_heading(headings: list[tuple[int, str]], line_no: int) -> str:
    for heading_line, heading in reversed(headings):
        if heading_line < line_no:
            return heading
    return ""


def load_manifest_rows(source_root: Path) -> dict[str, dict[str, str]]:
    path = source_root / "manifest.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row.get("md_file", "").replace("\\", "/"): row for row in rows}


def load_image_overrides() -> dict[str, dict[str, Any]]:
    if not IMAGE_CURATION_PATH.exists():
        return {}
    data = json.loads(read_text(IMAGE_CURATION_PATH))
    return data.get("overrides", {})


def image_metadata(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"readable": False, "qr_like": False}
    try:
        from PIL import Image, ImageStat

        with Image.open(path) as image:
            result.update(
                {
                    "readable": True,
                    "width": image.width,
                    "height": image.height,
                    "format": image.format,
                    "mode": image.mode,
                    "bytes": path.stat().st_size,
                    "orientation": "landscape" if image.width > image.height else "portrait" if image.height > image.width else "square",
                }
            )
            gray = image.convert("L")
            gray.thumbnail((256, 256))
            get_pixels = getattr(gray, "get_flattened_data", gray.getdata)
            pixels = list(get_pixels())
            if pixels:
                near_binary = sum(value <= 28 or value >= 227 for value in pixels) / len(pixels)
                transitions = 0
                samples = 0
                width, height = gray.size
                for y in range(0, height, max(1, height // 32)):
                    row = [pixels[y * width + x] < 128 for x in range(width)]
                    transitions += sum(a != b for a, b in zip(row, row[1:]))
                    samples += max(1, len(row) - 1)
                transition_rate = transitions / max(1, samples)
                result["near_binary_fraction"] = round(near_binary, 4)
                result["transition_rate"] = round(transition_rate, 4)
                result["mean_luminance"] = round(float(ImageStat.Stat(gray).mean[0]), 2)
                result["qr_like"] = bool(near_binary > 0.88 and transition_rate > 0.08)
    except Exception as exc:  # optional image metadata must degrade cleanly
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def extract_markdown(path: Path, source_root: Path, manifest: dict[str, str], overrides: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    text = read_text(path)
    lines = text.splitlines()
    rel_md = path.relative_to(source_root).as_posix()
    title = manifest.get("actual_title") or next((line[2:].strip() for line in lines if line.startswith("# ")), path.stem)
    album_id = manifest.get("album_id") or "local"
    sequence_text = manifest.get("sequence") or re.match(r"(\d+)", path.stem).group(1) if re.match(r"(\d+)", path.stem) else "0"
    try:
        sequence = int(sequence_text)
    except ValueError:
        sequence = 0
    article_id = f"article-{album_id}-{sequence:03d}"

    headings: list[tuple[int, str]] = []
    image_mentions: list[tuple[int, str, Path]] = []
    for line_no, line in enumerate(lines, 1):
        heading_match = HEADING_RE.match(line)
        if heading_match:
            headings.append((line_no, heading_match.group(2).strip()))
        for match in IMAGE_RE.finditer(line):
            target = match.group(1).strip().strip("<>")
            target = re.sub(r'\s+["\'].*["\']\s*$', "", target)
            if re.match(r"https?://", target, re.I):
                continue
            decoded = unquote(target)
            resolved = (path.parent / decoded).resolve()
            image_mentions.append((line_no, target, resolved))

    block_rows: list[dict[str, Any]] = []
    i = 0
    block_no = 0
    while i < len(lines):
        match = FENCE_RE.match(lines[i])
        if not match or not match.group(1):
            i += 1
            continue
        raw_language = match.group(1).lower()
        start_line = i + 1
        i += 1
        buffer: list[str] = []
        while i < len(lines) and not re.match(r"^\s*```\s*$", lines[i]):
            buffer.append(lines[i])
            i += 1
        end_line = i + 1 if i < len(lines) else len(lines)
        i += 1
        block_no += 1
        code = "\n".join(buffer).rstrip()
        language, correction = normalize_language(raw_language, code)
        heading = latest_heading(headings, start_line)
        context = " ".join(line.strip() for line in lines[max(0, start_line - 7) : start_line - 1] if line.strip() and not line.lstrip().startswith("!["))[-500:]
        role = classify_block(code)
        family = infer_family(" ".join((title, heading, context, code[:2000])))
        domain = infer_domain(" ".join((title, heading, context)))
        nearest_image = None
        if image_mentions:
            nearest = min(image_mentions, key=lambda item: abs(item[0] - end_line))
            nearest_image = {"line": nearest[0], "distance": abs(nearest[0] - end_line)}
        safety = [
            name
            for name, pattern in {**SAFETY_PATTERNS, **SOURCE_ONLY_SAFETY_PATTERNS}.items()
            if pattern.search(code)
        ]
        boundary = CLAIM_BOUNDARIES.get(family, {})
        block_rows.append(
            {
                "record_type": "source_block",
                "id": f"{article_id}-b{block_no:03d}",
                "article_id": article_id,
                "title": f"{title} — {heading or f'block {block_no}'}",
                "article_title": title,
                "heading": heading,
                "backend": language if language in {"r", "python"} else None,
                "raw_language": raw_language,
                "language": language,
                "language_correction": correction,
                "role": role,
                "family": family,
                "domain": domain,
                "line_start": start_line,
                "line_end": end_line,
                "line_count": len(buffer),
                "code": code,
                "safety_flags": safety,
                "nearest_image": nearest_image,
                "source": {
                    "article_path": rel_md,
                    "source_url": manifest.get("source_url", ""),
                    "album_id": album_id,
                    "sequence": sequence,
                },
                "supports_claims": [boundary.get("supports")] if boundary.get("supports") else [],
                "does_not_support": [boundary.get("does_not_support")] if boundary.get("does_not_support") else [],
                "validation": {"tier": "reference-only"},
                "fingerprint": "sha256:" + hashlib.sha256((article_id + "\0" + raw_language + "\0" + heading + "\0" + code).encode("utf-8")).hexdigest(),
                "search_text": " ".join((title, heading, context, family, domain, language, code[:3000])),
            }
        )

    image_rows: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for image_no, (line_no, raw_target, resolved) in enumerate(image_mentions, 1):
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        try:
            archive_rel = resolved.relative_to(source_root.resolve()).as_posix()
        except ValueError:
            continue
        meta = image_metadata(resolved) if resolved.exists() else {"readable": False, "error": "missing"}
        override = overrides.get(archive_rel, {})
        nearest_block = min(block_rows, key=lambda row: abs(row["line_end"] - line_no)) if block_rows else None
        image_context = normalize_text(" ".join(lines[max(0, line_no - 4) : min(len(lines), line_no + 3)]))
        if override:
            image_role = override.get("role", "uncertain")
        elif meta.get("qr_like") or re.search(r"二维码|扫码|wechat\s*qr|qr\s*code", image_context, re.I):
            image_role = "promotion_or_qr"
        elif re.search(r"代码截图|code\s*screenshot|截图.*代码", image_context, re.I):
            image_role = "code_screenshot"
        elif re.search(r"文献原图|原论文|原文图|paper\s*figure|original\s*figure|文献中.*图", image_context, re.I):
            image_role = "published_reference"
        elif nearest_block and nearest_block.get("role") == "plot" and abs(nearest_block["line_end"] - line_no) <= 12:
            image_role = "scientific_result"
        elif nearest_block and abs(nearest_block["line_end"] - line_no) <= 25:
            image_role = "intermediate_step"
        elif line_no < 35:
            image_role = "cover_or_web_screenshot"
        else:
            image_role = "uncertain"
        family = nearest_block.get("family") if nearest_block else infer_family(title)
        image_rows.append(
            {
                "record_type": "image",
                "id": f"{article_id}-i{image_no:03d}",
                "article_id": article_id,
                "title": f"{title} — image {image_no}",
                "article_title": title,
                "family": family,
                "domain": infer_domain(title),
                "role": image_role,
                "reviewed": bool(override.get("reviewed", False)),
                "review_note": override.get("note"),
                "line": line_no,
                "path": rel_posix(resolved) if resolved.exists() else f"assets/source_archive/{archive_rel}",
                "archive_path": archive_rel,
                "raw_markdown_target": raw_target,
                "metadata": meta,
                "nearest_block_id": nearest_block.get("id") if nearest_block else None,
                "validation": {"tier": "visual-only"},
                "fingerprint": "sha256:" + hashlib.sha256((article_id + "\0" + archive_rel).encode("utf-8")).hexdigest(),
                "search_text": " ".join((title, family, image_role, override.get("note", ""))),
            }
        )

    article_row = {
        "record_type": "article",
        "id": article_id,
        "title": title,
        "author": manifest.get("author", ""),
        "published_at": manifest.get("published_at", ""),
        "family": infer_family(title),
        "domain": infer_domain(title),
        "article_path": rel_md,
        "source_url": manifest.get("source_url", ""),
        "album_id": album_id,
        "sequence": sequence,
        "block_count": len(block_rows),
        "image_count": len(image_rows),
        "validation": {"tier": "reference-only" if block_rows else "visual-only"},
        "search_text": " ".join((title, manifest.get("album_title", ""), manifest.get("author", ""))),
    }
    return article_row, block_rows, image_rows


def load_recipe_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not RECIPES_ROOT.exists():
        return records
    for metadata_path in sorted(RECIPES_ROOT.rglob("recipe.json")):
        try:
            recipe = json.loads(read_text(metadata_path))
        except Exception as exc:
            records.append({"record_type": "recipe_error", "id": metadata_path.parent.name, "error": str(exc)})
            continue
        record = dict(recipe)
        record["record_type"] = "recipe"
        record["title"] = recipe.get("name") or recipe.get("title") or recipe.get("id")
        record["family"] = canonical_family(recipe.get("family"))
        record["recipe_path"] = rel_posix(metadata_path.parent)
        files = recipe.get("files") or {}
        code_rel = files.get("code") or recipe.get("code_path")
        if code_rel:
            code_path = (metadata_path.parent / code_rel).resolve()
            if code_path.exists():
                record["code"] = read_text(code_path)
                record["code_path"] = rel_posix(code_path)
        preview_rel = files.get("preview") or recipe.get("preview_path")
        if preview_rel:
            preview_path = (metadata_path.parent / preview_rel).resolve()
            record["preview_path"] = rel_posix(preview_path) if preview_path.exists() else str(preview_rel).replace("\\", "/")
        semantic = recipe.get("semantic_card") or {}
        searchable = [
            record.get("title", ""),
            record.get("description", ""),
            record.get("family", ""),
            record.get("backend", ""),
            " ".join(recipe.get("tags") or recipe.get("aliases") or []),
            " ".join(semantic.get("questions_answered") or semantic.get("scientific_questions") or []),
            " ".join(semantic.get("evidence_roles") or []),
            " ".join(semantic.get("units") or []),
            " ".join(semantic.get("data_topologies") or []),
            " ".join(semantic.get("supports_claims") or []),
            " ".join(semantic.get("does_not_support") or semantic.get("does_not_support_claims") or []),
        ]
        record["search_text"] = " ".join(str(value) for value in searchable if value)
        records.append(record)
    return records


def load_decision_records() -> list[dict[str, Any]]:
    """Load code-independent scientific decision cards used before recipe choice."""
    if not DECISION_CARDS_PATH.exists():
        return []
    payload = json.loads(read_text(DECISION_CARDS_PATH))
    records: list[dict[str, Any]] = []
    for card in payload.get("cards", []):
        record = dict(card)
        record["record_type"] = "strategy"
        record["title"] = card.get("name") or card.get("id")
        semantic = card.get("semantic_card") or {}
        record["search_text"] = " ".join(
            str(value)
            for value in (
                record.get("title", ""),
                record.get("description", ""),
                record.get("family", ""),
                " ".join(card.get("tags") or []),
                " ".join(semantic.get("questions_answered") or []),
                " ".join(semantic.get("supports_claims") or []),
                " ".join(semantic.get("does_not_support") or []),
            )
            if value
        )
        records.append(record)
    return records


def build_catalog(source_root: Path = SOURCE_ROOT, write: bool = True) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_rows = load_manifest_rows(source_root)
    overrides = load_image_overrides()
    article_files = [path for path in sorted(source_root.rglob("*.md")) if path.parent != source_root and path.name.lower() != "readme.md"]
    records: list[dict[str, Any]] = []
    for path in article_files:
        rel = path.relative_to(source_root).as_posix()
        article, blocks, images = extract_markdown(path, source_root, manifest_rows.get(rel, {}), overrides)
        records.append(article)
        records.extend(blocks)
        records.extend(images)
    stable_payload = json.loads(read_text(STABLE_IDS_PATH)) if STABLE_IDS_PATH.exists() else {"schema_version": 1, "records": {}}
    stable_map: dict[str, str] = dict(stable_payload.get("records") or {})
    used_ids = set(stable_map.values())
    occurrence: Counter[str] = Counter()
    id_rewrites: dict[str, str] = {}
    for record in records:
        if record.get("record_type") not in {"source_block", "image"}:
            continue
        base_fingerprint = record.get("fingerprint")
        occurrence[base_fingerprint] += 1
        stable_key = f"{base_fingerprint}#{occurrence[base_fingerprint]}"
        old_id = record["id"]
        stable_id = stable_map.get(stable_key)
        if not stable_id:
            stable_id = old_id
            if stable_id in used_ids:
                stable_id = old_id + "-h" + base_fingerprint.split(":", 1)[-1][:8]
            stable_map[stable_key] = stable_id
            used_ids.add(stable_id)
        record["id"] = stable_id
        id_rewrites[old_id] = stable_id
    for record in records:
        if record.get("record_type") == "image" and record.get("nearest_block_id") in id_rewrites:
            record["nearest_block_id"] = id_rewrites[record["nearest_block_id"]]
    records.extend(load_recipe_records())
    records.extend(load_decision_records())

    record_types = Counter(record.get("record_type") for record in records)
    raw_languages = Counter(record.get("raw_language") for record in records if record.get("record_type") == "source_block")
    normalized_languages = Counter(record.get("language") for record in records if record.get("record_type") == "source_block")
    families = Counter(canonical_family(record.get("family")) for record in records)
    image_roles = Counter(record.get("role") for record in records if record.get("record_type") == "image")
    corrections = [record["id"] for record in records if record.get("record_type") == "source_block" and record.get("language_correction")]
    coverage = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "source_root": "assets/source_archive",
        "catalog_input_fingerprint": catalog_input_fingerprint(source_root),
        "records": dict(record_types),
        "raw_languages": dict(raw_languages),
        "normalized_languages": dict(normalized_languages),
        "language_corrections": corrections,
        "stable_ids": {"registered": len(stable_map), "rewritten_this_build": sum(old != new for old, new in id_rewrites.items())},
        "families": dict(families),
        "image_roles": dict(image_roles),
        "expectations": EXPECTED,
        "expectations_pass": {
            "articles": record_types.get("article", 0) == EXPECTED["articles"],
            "source_blocks": record_types.get("source_block", 0) == EXPECTED["source_blocks"],
            "images": record_types.get("image", 0) == EXPECTED["images"],
            "raw_languages": dict(raw_languages) == EXPECTED["raw_languages"],
        },
    }
    if write:
        write_jsonl(CATALOG_PATH, records)
        write_json(STABLE_IDS_PATH, {"schema_version": 1, "records": stable_map})
        atlas_summary = refresh_style_atlas(records)
        coverage["style_atlas"] = {
            "style_cards": atlas_summary.get("style_cards"),
            "articles_indexed": atlas_summary.get("articles_indexed"),
            "coverage_status": atlas_summary.get("coverage_status"),
            "missing_sample_count": atlas_summary.get("missing_sample_count"),
        }
        write_json(COVERAGE_PATH, coverage)
    return records, coverage


def ensure_catalog() -> list[dict[str, Any]]:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError("Catalog is missing. Run: python scripts/plot_library.py build")
    freshness = catalog_freshness()
    if not freshness.get("fresh"):
        raise FileNotFoundError(
            "Catalog is stale because generator, source, curation, or Recipe inputs changed. "
            "Run: python scripts/plot_library.py build"
        )
    return load_jsonl(CATALOG_PATH)


def infer_primary_family(query: str, detected: list[str], visual_intents: list[str]) -> str:
    """Resolve the scientific decision before lexical recipe ranking."""
    text = normalize_text(query)
    has = lambda pattern: bool(re.search(pattern, text, re.I))

    if (
        has(r"marker|经典基因|特征基因|feature\s*gene")
        and has(r"平均\s*表达|average\s*expression|avg[_ ]?expression")
        and has(r"表达\s*比例|检出\s*比例|percent(?:age)?\s*express|pct[_ ]?expression|detection\s*(?:rate|frequency)|比例")
        and has(r"点\s*大小|point\s*size|dot\s*(?:size|plot)|dotplot|气泡图|bubble")
    ):
        return "dotplot"
    if has(r"cellchat|细胞通讯|配体.{0,8}受体.{0,20}通讯|ligand.{0,8}receptor.{0,20}communication"):
        return "cellchat_chord"
    if has(r"(?:marker|表达|expression).*(?:平均|average).*(?:比例|percent|percentage|大小|size|detection|frequency)|average\s*expression.*(?:detection|frequency|percent)|(?:颜色|color).*(?:平均表达|average expression).*(?:大小|size).*(?:比例|percent|detection)"):
        return "dotplot"
    if has(r"(?:marker|经典基因).*(?:加框|框选|highlight|box)"):
        return "dotplot"
    if has(r"(?:donor|sample|patient|subject|供者|样本|患者|受试者)(?:\s*[- ]?\s*(?:level|级|层面))?[^。；]{0,40}(?:组成|比例|丰度|composition|fraction|proportion|abundance)|(?:组成|比例|丰度|composition|fraction|proportion|abundance)[^。；]{0,40}(?:donor|sample|patient|subject|供者|样本|患者|受试者)"):
        return "sample_level_composition"
    if has(r"(?:umap|细胞).*(?:组成|比例|丰度|更多|扩增|composition|fraction|proportion|abundance)|(?:组成|比例|丰度|composition|fraction|proportion|abundance).*(?:条件|组|condition|cell)"):
        return "sample_level_composition"
    if has(r"paired|pre\s*post|before\s*after|within\s*subject|配对|治疗前后|前后变化"):
        return "paired_plot"
    if has(r"precision\s*recall|pr\s*curve|阳性率.*低|rare\s*positive|class\s*imbalance|imbalanced"):
        return "precision_recall"
    if has(r"(?:通讯|communication|cellchat).*(?:很多|太乱|拥挤|dense|clutter|换)|(?:弦图|chord).*(?:太乱|拥挤|dense|clutter|换)"):
        return "cellchat_dotplot"
    if has(r"(?:rendered|figure|成图|这张图).*(?:legend.*clip|labels?.*overlap|图例.*裁|标签.*(?:重叠|遮挡))|read.*p\s*value|看图.*(?:p值|样本量)"):
        return "visual_review"
    if has(r"(?:he|h&e|荧光|全景|局部).*(?:panel|拼|组合|排版)"):
        return "layout"
    if has(r"(?:panel|图例|legend).*(?:颜色.*不一致|inconsistent|共享|共用)"):
        return "layout"
    if has(r"(?:标签|label).*(?:遮挡|overlap|repel)|(?:remove|去掉).*(?:frame|border|边框)|(?:frame|border).*(?:remove|去掉)"):
        return "layout"
    if has(r"log\s*2?\s*fc|logfc|fold\s*change"):
        return "volcano"
    if has(r"export|editable\s*vector|one.column|two.column|600\s*dpi|导出|可编辑版本|单栏|双栏|\btiff\b|\bsvg\b|\bpdf\b"):
        return "layout"
    if not detected and has(r"好看|直接选|nature\s*style|nature-style|recommend.*figure.*results"):
        return "intent_clarification"
    if not detected and has(r"看图|理解这张图|review.*figure|interpret.*figure"):
        return "visual_review"
    return canonical_family(detected[0]) if detected else "intent_clarification"


def query_intent(query: str, backend: str | None = None, family: str | None = None, domain: str | None = None) -> dict[str, Any]:
    query_normalized = normalize_text(query)
    action_requests = detect_action_requests(query)
    action_intent = detect_action_intent(query)
    source_lookup = explicit_source_lookup(query)
    geometry_subtypes = detect_geometry_subtypes(query)
    analysis_method = detect_analysis_method(query)
    explicit_backend = backend
    if not explicit_backend:
        if re.search(r"\bpython\b|scanpy|matplotlib|anndata", query_normalized):
            explicit_backend = "python"
        elif re.search(
            r"(?<![a-z0-9])r(?![a-z0-9])|r\s*语言|用\s*r(?:\s*(?:绘图|作图|运行|代码))?|"
            r"ggplot|seurat|complexheatmap",
            query_normalized,
            re.I,
        ):
            explicit_backend = "r"

    detected_families = [canonical_family(item) for item in detect_terms(query, FAMILY_TERMS)]
    visuals = detect_terms(query, VISUAL_TERMS)
    primary_family = canonical_family(family) if family else infer_primary_family(query, detected_families, visuals)
    subtype_family_hints = {
        "enrichment_rose": "gsea",
        "radial_bar_lollipop": "gsea",
        "enrichment_comet_link_dot": "gsea",
        "enrichment_dendrogram_bar_composite": "gsea",
        "go_enrichment_circle": "gsea",
        "gsea_running_score": "gsea",
        "mirrored_dual_metric_lollipop": "correlation",
        "ternary_composition_scatter": "correlation",
        "two_contrast_foldchange_concordance": "correlation",
        "marker_dotplot_group_boxes": "dotplot",
        "mutation_lollipop_domain": "genomics",
        "mutation_rainfall": "genomics",
        "mutation_waterfall_oncoprint": "genomics",
        "transition_transversion_spectrum": "genomics",
        "single_sample_cnv_profile": "genomics",
        "cohort_cnv_spectrum": "genomics",
        "trajectory_pseudotime": "trajectory",
        "cellchat_bubble": "cellchat_chord",
        "cellchat_chord": "cellchat_chord",
        "cellchat_circle_network": "cellchat_chord",
        "cellchat_heatmap": "cellchat_chord",
        "sankey_alluvial": "flow",
        "he_whole_slide": "spatial_image",
        "he_roi_zoom": "spatial_image",
        "segmentation_boundary_overlay": "spatial_image",
        "fluorescence_multichannel": "spatial_image",
    }
    if analysis_method in {"ora", "gsea", "ambiguous_enrichment"}:
        primary_family = "gsea"
    elif geometry_subtypes:
        primary_family = subtype_family_hints.get(geometry_subtypes[0], primary_family)
    families = [primary_family] + [item for item in detected_families if item != primary_family]
    domains = [domain] if domain else detect_terms(query, DOMAIN_TERMS)
    objects = detect_terms(query, OBJECT_TERMS)
    units = detect_terms(query, UNIT_TERMS)
    topologies = detect_terms(query, TOPOLOGY_TERMS)
    component_targets: list[str] = []
    component_patterns = (
        ("label-repel", r"标签.*(?:遮挡|重叠|避让)|labels?.*(?:overlap|repel)|repel.*label|top.*genes?.*label"),
        ("marker-box", r"marker.*(?:加框|框选|box)|(?:加框|框选).*marker"),
        ("arrow-axes", r"箭头.*坐标|arrow.*ax"),
        ("borderless", r"remove.*(?:frame|border)|去掉.*(?:边框|外框)|去边框|borderless"),
        ("shared-legend", r"共享.*图例|共用.*图例|shared.*legend|collect.*guide"),
        ("dark-nebula", r"深色|暗色|星云|云雾|nebula|glow"),
        ("publication-export", r"export|导出|editable\s*vector|可编辑版本|\btiff\b|\bsvg\b|\bpdf\b|\bdpi\b"),
    )
    for target, pattern in component_patterns:
        if re.search(pattern, query_normalized, re.I):
            component_targets.append(target)
    component_target = component_targets[0] if component_targets else None

    if re.search(r"p\s*value|p值|fdr|adjusted|显著|confidence interval|置信区间", query_normalized):
        statistical_intent = "inferential"
    elif re.search(r"explor|探索|overview|概览|看看|展示", query_normalized):
        statistical_intent = "exploratory"
    else:
        statistical_intent = "descriptive"
    if primary_family == "visual_review":
        evidence_role = "robustness"
    elif statistical_intent == "inferential" or primary_family in {"roc", "precision_recall", "calibration"}:
        evidence_role = "validation"
    elif re.search(r"compare|comparison|比较|不同条件|两组|pre\s*post|配对", query_normalized):
        evidence_role = "comparison"
    else:
        evidence_role = "overview"

    variables: list[str] = []
    for name, pattern in {
        "log_fold_change": r"log\s*2?\s*fc|logfc|fold\s*change",
        "adjusted_p_or_fdr": r"fdr|adjusted|p\s*value|p值",
        "nes": r"\bnes\b",
        "sample_id": r"sample|donor|patient|subject|样本|供者|患者|病人",
        "condition": r"condition|group|treatment|组别|条件|治疗|(?:实验|疾病|处理|病例|对照)组",
        "binary_outcome": r"roc|auc|binary|positive|阳性|二分类|classification|"
        r"病例[^。；]{0,16}对照|对照[^。；]{0,16}病例",
        "numeric_score": r"score|probability|risk|模型|评分|概率",
    }.items():
        if re.search(pattern, query_normalized, re.I):
            variables.append(name)

    composition_plus_structure = primary_family == "sample_level_composition" and bool(
        re.search(r"cluster.*(?:结构|structure)|(?:结构|structure).*cluster|umap|embedding", query_normalized, re.I)
    )
    output_context = {
        "multi_panel": bool(re.search(r"panel|拼图|多面板|组合图", query_normalized)) or composition_plus_structure,
        "journal": "nature" if "nature" in query_normalized else None,
        "export": next((item for item in ("tiff", "svg", "pdf", "png") if item in query_normalized), None),
        "final_size_declared": bool(re.search(r"one.column|two.column|single.column|单栏|双栏|\bmm\b|\bcm\b|\binch", query_normalized)),
    }
    if re.search(r"两组|two\s+groups?", query_normalized):
        group_count: int | None = 2
    elif re.search(r"四组|four\s+groups?", query_normalized):
        group_count = 4
    else:
        group_match = re.search(r"\b(\d{1,2})\s+groups?\b", query_normalized)
        group_count = int(group_match.group(1)) if group_match else None
    repeated = "paired" if primary_family == "paired_plot" else "sample_level" if primary_family == "sample_level_composition" else "unknown"
    if repeated == "sample_level":
        units = ["sample", *[unit for unit in units if unit != "sample"]]
        if "long_table" not in topologies:
            topologies.append("long_table")
    semantic_core_question = (
        "pathway_enrichment"
        if analysis_method in {"ora", "gsea", "ambiguous_enrichment"}
        else primary_family
    )
    action_sequence = [
        action
        for action in ("adapt", "execute", "render", "review")
        if action_requests.get(action)
    ]
    return {
        "query": query,
        "core_question": semantic_core_question,
        "retrieval_family": primary_family,
        "scientific_claim": {"text": query, "status": "provisional"},
        "evidence_role": evidence_role,
        "unit_of_analysis": units,
        "data_topology": topologies,
        "statistical_intent": statistical_intent,
        "backend": explicit_backend,
        "input_objects": objects,
        "variables": variables,
        "group_count": group_count,
        "repeat_structure": repeated,
        "families": families,
        "domains": domains,
        "visual_intents": visuals,
        "component_target": component_target,
        "component_targets": component_targets,
        "geometry_subtypes": geometry_subtypes,
        "analysis_method": analysis_method,
        "action_intent": action_intent,
        "action_intents": action_sequence or ["discover"],
        "review_requested": bool(action_requests.get("review")),
        "review_after_execution": bool(
            action_requests.get("review")
            and action_intent in {"execute", "render"}
        ),
        "source_lookup": source_lookup,
        "requires_code": action_intent in {"adapt", "execute", "render"} or source_lookup,
        "requires_executable": action_intent in {"execute", "render"},
        "requires_backend_choice": action_intent in {"adapt", "execute", "render"} and not explicit_backend,
        "nonplot_request": bool(
            re.search(r"(?:下载|download|ascp|wget|curl|获取数据).{0,24}(?:数据|文件|命令|command)?", query_normalized, re.I)
        ),
        "output_context": output_context,
        "tokens": text_tokens(query),
    }


def intent_retrieval_family(intent: dict[str, Any]) -> str:
    """Return the internal broad family without weakening FigureIntent semantics."""
    return canonical_family(intent.get("retrieval_family") or intent.get("core_question"))


def get_validation_tier(record: dict[str, Any]) -> str:
    validation = record.get("validation") or {}
    return validation.get("tier") if isinstance(validation, dict) else str(validation)


def compatibility_assessment(record: dict[str, Any], intent: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    """Apply deterministic hard gates and report unresolved, non-fatal inputs."""
    gate_notes: list[str] = []
    missing: list[str] = []
    backend = intent.get("backend")
    record_backend = record.get("backend")
    if backend and record_backend and backend != record_backend:
        return False, [f"backend mismatch: selected {backend}, record {record_backend}"], missing

    requested_objects = set(intent.get("input_objects") or [])
    required_objects = set((record.get("requires") or {}).get("object_types") or [])
    normalized_required = {normalize_text(item).replace(" ", "") for item in required_objects}
    adapter_targets = {
        "Seurat": {"data.frame", "dataframe", "long_table", "longtable", "embedding"},
        "AnnData": {"data.frame", "dataframe", "pandasdataframe", "long_table", "longtable", "embedding"},
        "CellChat": {"data.frame", "dataframe", "long_table", "longtable", "matrix"},
        "image": {"numpyndarray", "array", "image"},
    }
    if requested_objects and required_objects:
        direct = any(normalize_text(item).replace(" ", "") in normalized_required for item in requested_objects)
        bridge = any(adapter_targets.get(item, set()) & normalized_required for item in requested_objects)
        if direct:
            gate_notes.append("input object directly compatible")
        elif bridge:
            gate_notes.append("input object compatible through an explicit adapter")
            missing.append("select and declare the input adapter or conversion before adaptation")
        elif record.get("record_type") == "strategy":
            missing.append("confirm an adapter or derived summary for the declared input object")
        else:
            return False, [f"input object incompatible: {sorted(requested_objects)} -> {sorted(required_objects)}"], missing

    required_variables = list((record.get("requires") or {}).get("variables") or [])
    if required_variables:
        missing.append("confirm variables: " + ", ".join(str(item) for item in required_variables))
    required_statistics = list((record.get("semantic_card") or {}).get("required_statistics") or [])
    if required_statistics and required_statistics != ["none"]:
        missing.append("confirm statistics: " + "; ".join(str(item) for item in required_statistics))
    return True, gate_notes or ["no known hard-gate conflict"], missing


def score_record(record: dict[str, Any], intent: dict[str, Any]) -> tuple[float, list[str], dict[str, float], list[str]]:
    record_type = record.get("record_type")
    if record_type not in {"recipe", "strategy", "source_block", "article", "image"}:
        return -1.0, [], {}, []
    if record_type == "source_block" and record.get("role") in {"install", "non_code"}:
        return -1.0, [], {}, []
    if record_type == "image" and record.get("role") in {"promotion_or_qr", "cover_or_web_screenshot", "code_screenshot", "published_reference"}:
        return -1.0, [], {}, []
    compatible_record, gate_notes, missing_inputs = compatibility_assessment(record, intent)
    if not compatible_record:
        return -1.0, gate_notes, {}, missing_inputs

    reasons: list[str] = []
    record_family = canonical_family(record.get("family"))
    primary_family = intent_retrieval_family(intent)
    requested_families = intent.get("families") or []
    query_tokens = intent.get("tokens") or set()
    record_tokens = text_tokens(record.get("search_text") or record.get("title") or "")
    lexical = len(query_tokens & record_tokens) / max(1, len(query_tokens)) if query_tokens else 0.0
    if record_family == primary_family:
        question_score = 30.0
        reasons.append(f"scientific_question={record_family}")
    elif record_family in requested_families[1:]:
        question_score = min(24.0, 18.0 + lexical * 6.0)
        reasons.append(f"complementary_family={record_family}")
    else:
        question_score = min(14.0, lexical * 20.0)

    semantic = record.get("semantic_card") or {}
    requested_units = set(intent.get("unit_of_analysis") or [])
    record_units = set(semantic.get("units") or [])
    requested_topologies = set(intent.get("data_topology") or [])
    record_topologies = set(semantic.get("data_topologies") or [])
    requested_objects = set(intent.get("input_objects") or [])
    required_objects = set((record.get("requires") or {}).get("object_types") or [])
    data_score = 8.0
    if requested_units and record_units:
        data_score += 5.0 if requested_units & record_units else 0.0
    elif record_units:
        data_score += 2.0
    if requested_topologies and record_topologies:
        topology_text = normalize_text(" ".join(record_topologies))
        data_score += 4.0 if any(normalize_text(item) in topology_text for item in requested_topologies) else 0.0
    elif record_topologies:
        data_score += 2.0
    if requested_objects and required_objects:
        data_score += 3.0 if "directly compatible" in " ".join(gate_notes) else 1.0
    data_score = min(20.0, data_score)

    channels = semantic.get("visual_channels") or {}
    encoding_score = 10.0 if channels else 3.0
    if record_family == primary_family:
        encoding_score += 5.0
    encoding_score = min(15.0, encoding_score)

    visuals = intent.get("visual_intents") or []
    searchable = normalize_text(record.get("search_text", ""))
    component_target = str(intent.get("component_target") or "")
    compatible_ids = (record.get("compatible_with") or {}).get("ids", []) if isinstance(record.get("compatible_with"), dict) else []
    if component_target and (
        str(record.get("id") or "").startswith(component_target)
        or any(str(item).startswith(component_target) for item in compatible_ids)
    ):
        visual_score = 10.0
        reasons.append("component=" + component_target)
    elif visuals:
        visual_hits = [item for item in visuals if item in searchable or any(normalize_text(alias) in searchable for alias in VISUAL_TERMS.get(item, ()))]
        visual_score = min(10.0, 5.0 * len(visual_hits))
        if visual_hits:
            reasons.append("visual=" + ",".join(visual_hits))
    else:
        visual_score = 5.0

    tier = get_validation_tier(record)
    if record_type == "recipe":
        executability_score = {"verified": 10.0, "parse-verified": 8.0, "reference-only": 3.0}.get(tier, 2.0)
        reasons.append(f"recipe:{tier or 'unrated'}")
    elif record_type == "strategy":
        executability_score = 4.0
        reasons.append("decision strategy; derive only after backend selection")
    elif record_type == "source_block" and record.get("role") == "plot":
        executability_score = 3.0
        reasons.append("source plot candidate")
    else:
        executability_score = 1.0

    fingerprint = record.get("visual_fingerprint") or {}
    if fingerprint.get("reviewed"):
        readability_score = 10.0
    elif record_type == "strategy" and semantic:
        readability_score = 7.0
    elif record_type == "image" and record.get("role") == "scientific_result":
        readability_score = 6.0
    else:
        readability_score = 3.0

    source = record.get("source") or {}
    if record_type == "strategy":
        source_score = 4.0
    elif source.get("status") in {"original", "internal_distillation", "derived"}:
        source_score = 5.0
    elif record_type in {"source_block", "image"}:
        source_score = 3.0
    else:
        source_score = 1.0

    breakdown = {
        "question_evidence": round(question_score, 3),
        "data_compatibility": round(data_score, 3),
        "visual_encoding": round(encoding_score, 3),
        "visual_intent": round(visual_score, 3),
        "executability": round(executability_score, 3),
        "readability": round(readability_score, 3),
        "source_diversity": round(source_score, 3),
    }
    score = sum(breakdown.values())
    record_domain = normalize_text(record.get("domain") or "general").replace(" ", "_")
    requested_domains = intent.get("domains") or []
    if requested_domains:
        if record_domain in requested_domains or any(value in normalize_text(record.get("search_text", "")) for value in requested_domains):
            reasons.append(f"domain={requested_domains[0]}")
    overlap = query_tokens & record_tokens
    if overlap:
        reasons.append("terms=" + ",".join(sorted(overlap, key=len, reverse=True)[:5]))
    if intent.get("backend") and record.get("backend") == intent.get("backend"):
        reasons.append(f"backend={intent['backend']}")
    if record.get("safety_flags"):
        score -= min(12, 3 * len(record["safety_flags"]))
        reasons.append("requires safety cleanup")
    return round(max(0.0, min(100.0, score)), 3), reasons, breakdown, missing_inputs


def recommendation_tradeoff(primary_family: str, candidate_family: str, role: str) -> str:
    specific = {
        ("sample_level_composition", "boxplot", "conservative"): "按 sample/donor 展示观察值与分布，最能避免把细胞误当独立重复；代价是不能呈现 cluster 的嵌入几何。",
        ("sample_level_composition", "embedding", "information_dense"): "补充所有细胞的 cluster 结构和标签分布，适合作为概览面板；但它不是条件间细胞比例差异的定量证据。",
        ("composition", "boxplot", "conservative"): "显示独立样本层面的比例分布，解释边界最稳健；代价是牺牲整体组成概览。",
        ("composition", "embedding", "information_dense"): "增加细胞状态与局部邻域信息；代价是不能凭嵌入密度推断组成差异。",
        ("dotplot", "boxplot", "conservative"): "回到独立分析单位的原始或聚合值，便于核对重复和离群值；代价是不能在一张图中总览大量 marker。",
        ("dotplot", "heatmap", "information_dense"): "可容纳更多基因、分组和聚类结构；代价是失去“颜色=均值、大小=比例”的双通道直读。",
        ("volcano", "boxplot", "conservative"): "直接显示重点特征在独立样本中的分布与效应方向；代价是不能总览全量检验结果。",
        ("volcano", "heatmap", "information_dense"): "展示多个候选特征的样本模式和共变结构；代价是更依赖缩放、排序和聚类说明。",
        ("embedding", "sample_level_composition", "conservative"): "把细胞级几何降为背景，改用 sample/donor 作为独立点检验组成差异；代价是看不到局部邻域结构。",
        ("embedding", "dotplot", "information_dense"): "同时概览多个 marker 的平均量和检测比例，用于解释 cluster 身份；代价是失去单细胞位置与局部异质性。",
        ("heatmap", "dotplot", "conservative"): "用明确的颜色与大小双通道替代聚类色块，较少依赖行缩放和树状排序；代价是难以容纳大型矩阵。",
        ("heatmap", "gsea", "information_dense"): "把特征模式提升到通路方向和 FDR 层面；信息更综合，但必须新增排名统计、基因集版本和多重检验前提。",
        ("gsea", "heatmap", "conservative"): "回看 leading-edge 或预先指定基因在独立样本中的实际模式，避免把通路分数当作直接活性；但不能替代富集检验。",
        ("gsea", "dotplot", "information_dense"): "可在一图比较更多通路、方向、显著性和集合大小；代价是通路重叠与多通道解码负担更高。",
        ("boxplot", "data_audit", "conservative"): "先核对分析单位、独立性、缺失值、配对和样本量，避免一个整洁箱体掩盖设计错误；代价是暂不增加视觉概览。",
        ("boxplot", "violin", "information_dense"): "增加核密度形状以展示多峰或偏态；代价是带宽会制造视觉结构，小样本尤其容易误读。",
        ("paired_plot", "data_audit", "conservative"): "先验证配对 ID、时间顺序和缺失配对，防止错误连线制造个体变化；代价是暂不展示轨迹。",
        ("paired_plot", "boxplot", "information_dense"): "补充各时间点的边际分布与全部观察值；代价是箱体本身隐藏配对关系，不能替代配对效应分析。",
        ("roc", "precision_recall", "conservative"): "在阳性稀少或类别不平衡时直接呈现 precision/recall，较少被大量真阴性美化；代价是数值依赖患病率。",
        ("roc", "calibration", "information_dense"): "补充预测概率与实际风险的一致性，回答 ROC 未涉及的校准问题；代价是需要可靠概率、分箱或平滑方案及独立验证。",
        ("precision_recall", "roc", "conservative"): "补充完整敏感度—特异度权衡并便于跨阈值比较；代价是类别极不平衡时 ROC 可能显得过于乐观。",
        ("precision_recall", "calibration", "information_dense"): "增加概率准确性而非只看排序性能；代价是需要更大样本和预先声明的校准评估。",
        ("calibration", "roc", "conservative"): "分别核对区分能力，避免把校准良好误写成能区分个体；代价是 ROC 不回答概率是否准确。",
        ("calibration", "precision_recall", "information_dense"): "在不平衡结局中补充阳性预测表现；代价是引入患病率依赖，且仍不等于临床效用。",
        ("cellchat_chord", "cellchat_dotplot", "conservative"): "把每条推断连接拆成可排序的来源—靶点项目，减少弦线遮挡；代价是失去网络整体拓扑。",
        ("cellchat_chord", "heatmap", "information_dense"): "可容纳完整来源×靶点矩阵并比较多个条件；代价是依赖聚合、缩放和色标，方向性不如逐边图直观。",
        ("cellchat_dotplot", "heatmap", "conservative"): "以规则矩阵保留全部来源—靶点格点，降低大小/颜色双通道误读；代价是单条连接细节较弱。",
        ("cellchat_dotplot", "cellchat_chord", "information_dense"): "恢复网络拓扑与连接汇聚关系；代价是边多时遮挡严重，且推断网络不能被写成物理通讯或因果。",
        ("spatial_image", "layout", "conservative"): "保留同一视野、比例尺和配准信息，仅用多面板并列 H&E/荧光/分割结果；代价是定量汇总较少。",
        ("spatial_image", "embedding", "information_dense"): "补充细胞状态空间与标签分布以解释区域异质性；代价是嵌入不保留真实组织距离，不能替代空间图。",
        ("layout", "visual_review", "conservative"): "先在原始与投稿尺寸核对裁切、图例、色标和跨面板一致性，风险最低；代价是不会新增科学信息。",
        ("layout", "visual_examples", "information_dense"): "并列更多视觉样例以探索 panel hierarchy 和图例方案；代价是样例相似不代表数据或语义兼容。",
        ("visual_review", "layout", "conservative"): "只修复已确认的排版缺陷并保持映射不变；代价是不能解决图形家族选错或证据不足。",
        ("visual_review", "data_audit", "information_dense"): "加入代码、数据和统计核对，把证据从像素提升到 image_code_data；代价是需要完整可审计输入。",
        ("intent_clarification", "data_audit", "conservative"): "先确认分析单位、字段和统计目标，防止按风格词误选图；代价是需要补充信息后才能出代码。",
        ("intent_clarification", "visual_examples", "information_dense"): "用多个样例帮助明确视觉偏好和论文角色；代价是样例只能澄清外观，不能决定科学有效性。",
        ("data_audit", "intent_clarification", "conservative"): "把尚未明确的 claim、单位和输出角色重新问清，避免对错误 estimand 做完整审计；代价是流程暂时停在决策层。",
        ("data_audit", "visual_examples", "information_dense"): "用候选图预览暴露字段缺失和编码冲突；代价是预览不能替代数据完整性和统计检查。",
        ("violin", "boxplot", "conservative"): "显示全部观察值与中位数/IQR，避免核密度在小样本中制造多峰；代价是分布形状更粗略。",
        ("violin", "heatmap", "information_dense"): "同时比较更多特征和组别的模式；代价是失去单变量密度与独立样本点。",
        ("correlation", "boxplot", "conservative"): "按预先定义的组展示原始分布，避免把相关性误作组间机制；代价是不能直接呈现连续关系。",
        ("correlation", "heatmap", "information_dense"): "扩展为多变量相关矩阵并显示模块结构；代价是多重比较、聚类和共线性解释负担更高。",
        ("set_intersection", "composition", "conservative"): "先展示各集合及交集的可核对计数/比例，减少复杂交集编码误读；代价是高阶交集细节有限。",
        ("set_intersection", "flow", "information_dense"): "展示成员跨集合或阶段的流向；代价是宽度与路径拥挤会弱化精确计数。",
        ("survival", "data_audit", "conservative"): "先核对时间起点、事件、删失、风险集和比例风险假设，避免漂亮曲线掩盖偏倚；代价是暂不形成展示图。",
        ("survival", "roc", "information_dense"): "补充指定时间点的区分能力；代价是必须处理删失和时间依赖，且不能替代生存效应与风险集。",
        ("flow", "composition", "conservative"): "用阶段或类别比例直接报告数量变化，较易精确比较；代价是失去个体路径和转移结构。",
        ("flow", "heatmap", "information_dense"): "把大量来源—去向关系压缩为矩阵；代价是路径连续性不再直观且需要清楚色标。",
        ("genomics", "volcano", "conservative"): "先用效应量与多重校正显著性筛查候选事件，避免只凭突变图案讲故事；代价是失去样本共现结构。",
        ("genomics", "heatmap", "information_dense"): "展示基因×样本事件、注释和共现模式；代价是排序、缺失和多种事件编码更复杂。",
        ("trajectory", "embedding", "conservative"): "只报告可见的嵌入邻域与状态标签，不把几何自动解释为方向；代价是不能声称伪时间进程。",
        ("trajectory", "heatmap", "information_dense"): "沿已审计的伪时间展示多基因动态模块；代价是排序、平滑和根节点选择都会影响图形。",
        ("palette", "visual_review", "conservative"): "在最终尺寸、灰度和色觉缺陷条件下验证现有映射，避免只凭审美换色；代价是不会增加类别容量。",
        ("palette", "visual_examples", "information_dense"): "比较更多候选配色与图例组合；代价是必须保持类别身份和连续尺度语义一致。",
        ("decorative", "intent_clarification", "conservative"): "先确认装饰是否服务论文角色，避免视觉噱头压过证据；代价是可能放弃用户最初的样式设想。",
        ("decorative", "visual_examples", "information_dense"): "提供多个装饰强度层级供选择；代价是信息更杂，且不能改善统计或科学有效性。",
        ("unknown", "intent_clarification", "conservative"): "先把科学问题、分析单位和数据结构问清，避免随机返回热门图；代价是暂不生成代码。",
        ("unknown", "data_audit", "information_dense"): "检查现有字段、对象和重复层级以缩小候选空间；代价是需要可审计的数据模式。",
    }
    if (primary_family, candidate_family, role) in specific:
        return specific[(primary_family, candidate_family, role)]
    if role == "primary":
        return "最直接回答已解析的核心科学问题；若输入契约未满足，先完成所列数据与统计检查。"
    if role == "conservative":
        return "解释边界更稳健或更贴近独立分析单位，但通常牺牲整体结构概览或视觉压缩效率。"
    return "增加互补变量、结构或探索细节，代价是信息密度、阅读负担或额外统计前提更高。"


def scheme_eligibility(record: dict[str, Any]) -> str:
    return normalize_text(record.get("eligibility") or "scientific_scheme").replace(" ", "_")


def scheme_review_status(record: dict[str, Any]) -> str:
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    fingerprint = record.get("visual_fingerprint") if isinstance(record.get("visual_fingerprint"), dict) else {}
    image_evidence = record.get("image_evidence") if isinstance(record.get("image_evidence"), dict) else {}
    candidates = (
        image_evidence.get("review_status"),
        validation.get("review_status"),
        validation.get("visual_review"),
        validation.get("visual"),
        (validation.get("checks") or {}).get("visual") if isinstance(validation.get("checks"), dict) else None,
        fingerprint.get("review_status"),
        "reviewed" if fingerprint.get("reviewed") is True else None,
    )
    for value in candidates:
        if value not in (None, ""):
            return normalize_text(value).replace(" ", "_")
    return "unreviewed"


def scheme_validation_tier(record: dict[str, Any]) -> str:
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    value = validation.get("tier") or validation.get("code_status") or record.get("code_status") or "unrated"
    return normalize_text(value).replace(" ", "_")


def scheme_is_visual_only(record: dict[str, Any]) -> bool:
    tier = scheme_validation_tier(record)
    availability = normalize_text(
        record.get("code_availability")
        or (record.get("validation") or {}).get("code_availability")
        or ""
    ).replace(" ", "_")
    return tier in {"visual_only", "visual-only"} or availability in {"visual_only", "none", "no_code"}


def disposition_record_id(row: dict[str, Any], kind: str) -> str:
    keys = (
        ("block_id", "source_block_id", "block_record_id", "record_id", "source_id", "id")
        if kind == "block"
        else ("image_id", "source_image_id", "image_record_id", "record_id", "source_id", "id")
    )
    return str(next((row.get(key) for key in keys if row.get(key)), ""))


def disposition_value(row: dict[str, Any], kind: str) -> str:
    keys = ("disposition", "role", "block_disposition") if kind == "block" else ("role", "disposition", "image_disposition")
    return normalize_text(next((row.get(key) for key in keys if row.get(key)), "")).replace(" ", "_")


def load_disposition_map(path: Path, kind: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in load_jsonl(path):
        record_id = disposition_record_id(row, kind)
        if record_id:
            result[record_id] = disposition_value(row, kind)
    return result


def lineage_block_ids(record: dict[str, Any]) -> set[str]:
    found: set[str] = set()

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, (list, tuple, set)):
            for child in value:
                visit(child, key)
        elif isinstance(value, str):
            if "block" in key.lower() or re.search(r"-b\d{3}(?:\b|$)", value):
                found.add(value)

    visit(record.get("code_lineage") or {})
    return found


def scheme_scope_matches(record: dict[str, Any], scope: str | None) -> bool:
    scope = normalize_text(scope or "scientific").replace(" ", "_")
    eligibility = scheme_eligibility(record)
    if scope == "all":
        return True
    if scope == "scientific":
        return eligibility in SCIENTIFIC_SCHEME_ELIGIBILITY
    if scope == "modifier":
        return eligibility in {"semantic_modifier", "aesthetic_modifier"}
    if scope == "resource":
        return eligibility in {
            "aesthetic_modifier",
            "layout",
            "layout_resource",
            "palette",
            "resource",
            "resource_only",
            "visual_reference",
        }
    if scope == "excluded":
        return eligibility in {"decorative", "decorative_result", "excluded", "nonplot", "non_plot", "prompt_non_code"}
    return eligibility == scope


def scheme_analysis_method(record: dict[str, Any]) -> str:
    method = normalize_analysis_method(record.get("analysis_method"))
    if method != "unknown":
        return method
    subtype = str(record.get("geometry_subtype") or "")
    if subtype == "gsea_running_score":
        return "gsea"
    return "unknown"


def formal_recipe_index() -> dict[str, dict[str, Any]]:
    """Load installed formal Recipes once per process for deterministic plans."""
    global _FORMAL_RECIPE_INDEX_CACHE
    if _FORMAL_RECIPE_INDEX_CACHE is None:
        _FORMAL_RECIPE_INDEX_CACHE = {
            str(record.get("id")): record
            for record in load_recipe_records()
            if record.get("record_type") == "recipe" and record.get("id")
        }
    return _FORMAL_RECIPE_INDEX_CACHE


def formal_recipe_ready(recipe: dict[str, Any] | None, expected_kind: str | None = None) -> bool:
    if not recipe or not recipe.get("code"):
        return False
    if expected_kind and normalize_text(recipe.get("kind")).replace(" ", "_") != expected_kind:
        return False
    validation = recipe.get("validation") if isinstance(recipe.get("validation"), dict) else {}
    tier = normalize_text(validation.get("tier") or "").replace(" ", "_")
    if tier not in {"parse_verified", "parse-verified", "verified", "executed", "formal"}:
        return False
    checks = validation.get("checks") if isinstance(validation.get("checks"), dict) else {}
    return not any(
        normalize_text(checks.get(name)) in {"fail", "failed", "error", "blocker"}
        for name in ("schema", "syntax", "safety", "fixture")
    )


def formal_recipe_runtime_blockers(recipe: dict[str, Any], action_intent: str) -> list[str]:
    """Report explicit environment/runtime failures without hiding the plan."""
    validation = recipe.get("validation") if isinstance(recipe.get("validation"), dict) else {}
    checks = validation.get("checks") if isinstance(validation.get("checks"), dict) else {}
    names = ["fixture"]
    if action_intent == "render" and recipe.get("kind") == "base_recipe":
        names.append("render")
    blockers: list[str] = []
    for name in names:
        value = normalize_text(checks.get(name)).replace(" ", "_")
        if value.startswith("blocked") or value in {"fail", "failed", "error", "blocker"}:
            blockers.append(f"{recipe.get('id')} {name}={checks.get(name)} in the current environment")
    return blockers


def recipe_object_types(recipe: dict[str, Any], field: str) -> set[str]:
    contract = recipe.get(field) if isinstance(recipe.get(field), dict) else {}
    return {
        normalize_text(value).replace(" ", "").replace("_", "")
        for value in as_list(contract.get("object_types"))
        if value not in (None, "")
    }


def scheme_base_recipe_candidates(
    record: dict[str, Any], intent: dict[str, Any], backend: str
) -> list[str]:
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    declared = [
        str(value)
        for value in as_list(
            record.get("recipe_ids")
            or record.get("formal_recipe_ids")
            or validation.get("recipe_ids")
        )
        if value
    ]
    subtype = str(record.get("geometry_subtype") or "unknown")
    requested_subtypes = [str(value) for value in as_list(intent.get("geometry_subtypes")) if value]
    family = canonical_family(record.get("broad_family") or record.get("family"))
    core_question = intent_retrieval_family(intent)
    candidates = list(declared)
    if requested_subtypes and intent_retrieval_family(intent) == "cellchat_chord":
        # A multi-panel CellChat request declares several exact subtypes at
        # once. Route each Scheme through its own subtype, not through the
        # first panel in the user's list.
        contextual_subtype = subtype if subtype in requested_subtypes else requested_subtypes[0]
        candidates.extend(FORMAL_BASE_RECIPE_CANDIDATES.get((contextual_subtype, backend), ()))
    record_backends = {
        normalize_text(value).replace(" ", "_")
        for value in as_list(record.get("backends", record.get("backend")))
        if value
    }
    article_id = str(
        (record.get("source") or {}).get("article_id")
        if isinstance(record.get("source"), dict)
        else ""
    )
    recipes = formal_recipe_index()

    def recipe_cites_source(recipe_id: str) -> bool:
        recipe = recipes.get(recipe_id) or {}
        articles = (recipe.get("source") or {}).get("articles") or []
        return bool(
            article_id
            and any(
                isinstance(article, dict) and str(article.get("source_id")) == article_id
                for article in articles
            )
        )

    subtype_candidates = FORMAL_BASE_RECIPE_CANDIDATES.get((subtype, backend), ())
    candidates.extend(
        recipe_id
        for recipe_id in subtype_candidates
        if backend in record_backends or recipe_cites_source(recipe_id)
    )
    if core_question == "sample_level_composition" and family == "composition":
        candidates.extend(FORMAL_BASE_RECIPE_CANDIDATES.get(("sample_level_composition", backend), ()))
    candidates.extend(
        recipe_id
        for recipe_id in FORMAL_FAMILY_RECIPE_CANDIDATES.get((family, backend), ())
        if recipe_cites_source(recipe_id)
    )
    return list(dict.fromkeys(candidates))


def scheme_execution_plan(record: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    """Resolve a Scheme to an installed formal execution chain.

    Source candidates and visual references are intentionally not promoted by
    this function.  The returned plan distinguishes a callable formal chain,
    an adaptation-only source candidate, and a genuinely unavailable design.
    """
    scheme_id = str(record.get("scheme_id") or record.get("id") or "")
    selected_backend = normalize_text(intent.get("backend")).replace(" ", "_") or None
    candidate_paths = record.get("candidate_code_path") if isinstance(record.get("candidate_code_path"), dict) else {}
    candidate_backends = sorted(
        normalize_text(value).replace(" ", "_")
        for value in candidate_paths
        if value
    )
    if scheme_is_visual_only(record):
        return {
            "status": "unavailable",
            "availability": "visual_only",
            "scheme_id": scheme_id,
            "backend": selected_backend,
            "adapter_id": None,
            "base_recipe_id": None,
            "modifier_ids": [],
            "export_id": None,
            "recipe_ids": [],
            "parameter_bindings": {},
            "direct_execution": False,
            "preflight_required": False,
            "blockers": ["visual-only Scheme has no target plotting code"],
            "reason": "Visual evidence may guide design, but it cannot be executed.",
        }

    recipes = formal_recipe_index()
    if not selected_backend:
        executable_backends: list[str] = []
        for backend in ("python", "r"):
            if any(
                formal_recipe_ready(recipes.get(recipe_id), "base_recipe")
                and recipes[recipe_id].get("backend") == backend
                for recipe_id in scheme_base_recipe_candidates(record, intent, backend)
                if recipe_id in recipes
            ):
                executable_backends.append(backend)
        availability = "backend_choice_required" if executable_backends or candidate_backends else "unavailable"
        return {
            "status": availability,
            "availability": availability,
            "scheme_id": scheme_id,
            "backend": None,
            "executable_backends": executable_backends,
            "candidate_backends": candidate_backends,
            "adapter_id": None,
            "base_recipe_id": None,
            "modifier_ids": [],
            "export_id": None,
            "recipe_ids": [],
            "parameter_bindings": {},
            "direct_execution": False,
            "preflight_required": bool(executable_backends),
            "blockers": ["select Python or R before adaptation or execution"],
            "reason": "A backend-exclusive execution chain has not been selected.",
        }

    base_candidates = scheme_base_recipe_candidates(record, intent, selected_backend)
    base_id = next(
        (
            recipe_id
            for recipe_id in base_candidates
            if formal_recipe_ready(recipes.get(recipe_id), "base_recipe")
            and recipes[recipe_id].get("backend") == selected_backend
        ),
        None,
    )
    if not base_id:
        has_candidate = selected_backend in candidate_backends
        return {
            "status": "adaptable_candidate" if has_candidate else "unavailable",
            "availability": "adaptable_candidate" if has_candidate else "no_executable_implementation",
            "scheme_id": scheme_id,
            "backend": selected_backend,
            "adapter_id": None,
            "base_recipe_id": None,
            "modifier_ids": [],
            "export_id": None,
            "recipe_ids": [],
            "candidate_code_path": candidate_paths.get(selected_backend) if has_candidate else None,
            "parameter_bindings": {},
            "direct_execution": False,
            "preflight_required": has_candidate,
            "blockers": [
                "source candidate requires adaptation, dependency preflight, and fixture execution before running"
                if has_candidate
                else f"no installed formal {selected_backend} Recipe implements this Scheme"
            ],
            "reason": (
                "Source code is available for adaptation but is not a callable formal Recipe."
                if has_candidate
                else "No backend-matched executable implementation is installed."
            ),
        }

    base = recipes[base_id]
    blockers: list[str] = []
    adapter_id: str | None = None
    requested_objects = set(intent.get("input_objects") or [])
    base_requires = recipe_object_types(base, "requires")
    normalized_objects = {
        normalize_text(value).replace(" ", "").replace("_", "")
        for value in requested_objects
    }
    parameter_bindings: dict[str, Any] = {}
    subtype = str(record.get("geometry_subtype") or "unknown")
    core_question = intent_retrieval_family(intent)

    if (
        base_id == "enrichment-rose-r-v1"
        and intent.get("analysis_method") == "ora"
    ):
        candidate_adapter = "ora-enrichment-adapter-r-v1"
        if formal_recipe_ready(recipes.get(candidate_adapter), "adapter"):
            adapter_id = candidate_adapter
        else:
            blockers.append("ORA enrichment adapter is not installed or validated")

    direct_object_match = bool(normalized_objects & base_requires) or not normalized_objects
    if "anndata" in normalized_objects and not direct_object_match:
        if base_id == "umap-dataframe-python-v1":
            candidate_adapter = "anndata-embedding-adapter-python-v1"
            if formal_recipe_ready(recipes.get(candidate_adapter), "adapter"):
                adapter_id = candidate_adapter
                parameter_bindings.update({"adata": "caller AnnData", "basis": "X_umap", "group": "caller obs cluster column"})
            else:
                blockers.append("AnnData embedding adapter is not installed or validated")
        elif base_id == "sample-composition-python-v1":
            # This Recipe accepts an AnnData-compatible object directly and
            # copies ``.obs`` internally, so no adapter or hidden mutation is
            # needed.  Bind the public Recipe parameter names exactly.
            parameter_bindings.update(
                {
                    "data": "caller AnnData-compatible object",
                    "sample": "caller sample/donor column",
                    "group": "caller condition column",
                    "cell_type": "caller cell-type/cluster column",
                }
            )
        else:
            blockers.append(f"no declared AnnData adapter for {base_id}")
    elif "seurat" in normalized_objects and not direct_object_match:
        candidate_adapter = {
            "umap-dataframe-r-v1": "seurat-embedding-adapter-r-v1",
            "marker-dotplot-r-v1": "seurat-marker-summary-adapter-r-v1",
        }.get(base_id)
        if candidate_adapter and formal_recipe_ready(recipes.get(candidate_adapter), "adapter"):
            adapter_id = candidate_adapter
            if base_id == "umap-dataframe-r-v1":
                parameter_bindings.update({"object": "caller Seurat object", "reduction": "umap", "group": "caller metadata column"})
            else:
                parameter_bindings.update({"object": "caller Seurat object", "features": "caller marker vector", "group": "caller metadata column"})
        else:
            blockers.append(f"no declared Seurat adapter for {base_id}")
    elif "cellchat" in normalized_objects and not direct_object_match:
        candidate_adapter = (
            "cellchat-lr-adapter-r-v1"
            if base_id == "cellchat-bubble-r-v1"
            else "cellchat-matrix-adapter-r-v1"
        )
        adapter_recipe = recipes.get(candidate_adapter) or {}
        adapter_targets = set(as_list((adapter_recipe.get("compatible_with") or {}).get("ids")))
        if base_id not in adapter_targets:
            blockers.append(f"no declared CellChat adapter for {base_id}")
        elif formal_recipe_ready(adapter_recipe, "adapter"):
            adapter_id = candidate_adapter
        else:
            blockers.append("CellChat matrix adapter is not installed or validated")
    elif normalized_objects and not direct_object_match:
        blockers.append(
            "input object is not accepted by the formal base Recipe and no explicit adapter is mapped"
        )

    if subtype in {"radial_bar_lollipop", "enrichment_rose"}:
        parameter_bindings.update(
            {
                "pathway": "pathway/term column",
                "gene_ratio": "GeneRatio or declared radial metric",
                "count": "Count or declared point-size metric",
                "padj": "p.adjust/FDR column",
            }
        )
    elif subtype == "spatial_spot_overlay" and base_id == "seurat-spatial-overlay-r-v1":
        parameter_bindings.update(
            {
                "object": "caller trusted Seurat object",
                "assay": "Spatial",
                "image": "caller-selected image when more than one is present",
                "mode": "identity or feature",
                "group_by/features": "caller metadata column or existing assay features",
            }
        )

    modifier_ids: list[str] = []
    export_id: str | None = None
    compatible_ids = set(as_list((base.get("compatible_with") or {}).get("ids")))
    for target in intent.get("component_targets") or as_list(intent.get("component_target")):
        if target == "publication-export":
            candidate_export = f"publication-export-{selected_backend}-v1"
            if formal_recipe_ready(recipes.get(candidate_export), "export"):
                export_id = candidate_export
            else:
                blockers.append(f"requested export component is unavailable: {candidate_export}")
            continue
        modifier_id = FORMAL_MODIFIER_RECIPE_IDS.get((str(target), selected_backend))
        if not modifier_id or not formal_recipe_ready(recipes.get(modifier_id)):
            blockers.append(f"requested modifier is unavailable for {selected_backend}: {target}")
            continue
        if compatible_ids and modifier_id not in compatible_ids:
            blockers.append(f"requested modifier is not declared compatible with {base_id}: {modifier_id}")
            continue
        modifier_ids.append(modifier_id)

    chain_ids = [value for value in (adapter_id, base_id, *modifier_ids, export_id) if value]
    validation_tiers = {
        recipe_id: normalize_text((recipes[recipe_id].get("validation") or {}).get("tier")).replace(" ", "_")
        for recipe_id in chain_ids
    }
    runtime_blockers = [
        blocker
        for recipe_id in chain_ids
        for blocker in formal_recipe_runtime_blockers(
            recipes[recipe_id], str(intent.get("action_intent") or "discover")
        )
    ]
    source_article_id = str(
        (record.get("source") or {}).get("article_id")
        if isinstance(record.get("source"), dict)
        else ""
    )
    base_source_articles = {
        str(article.get("source_id"))
        for article in ((base.get("source") or {}).get("articles") or [])
        if isinstance(article, dict) and article.get("source_id")
    }
    if source_article_id and source_article_id in base_source_articles:
        mapping_level = "formal_exact_source"
    elif core_question == "sample_level_composition" and canonical_family(record.get("broad_family")) == "composition":
        mapping_level = "formal_target_application"
    else:
        mapping_level = "formal_subtype"
    mapped = not blockers
    execution_status = (
        "unavailable"
        if not mapped
        else "preflight_blocked"
        if runtime_blockers
        else "executable"
    )
    return {
        "status": execution_status,
        "execution_status": execution_status,
        "availability": "formal_recipe" if mapped else "formal_recipe_blocked",
        "scheme_id": scheme_id,
        "backend": selected_backend,
        "adapter_id": adapter_id,
        "base_recipe_id": base_id,
        "modifier_ids": modifier_ids,
        "export_id": export_id,
        "recipe_ids": chain_ids,
        "mapping_level": mapping_level,
        "parameter_bindings": parameter_bindings,
        "validation_tiers": validation_tiers,
        "direct_execution": execution_status == "executable",
        "preflight_required": True,
        "blockers": [*blockers, *runtime_blockers],
        "reason": (
            "Installed backend-matched formal Recipe chain; dependency and input preflight remains mandatory."
            if execution_status == "executable"
            else "A callable formal Recipe chain is mapped, but current-environment preflight blocks execution."
            if execution_status == "preflight_blocked"
            else "A formal base Recipe exists, but the requested input/component chain is incomplete."
        ),
        "evidence_design": (
            "sample-level composition is primary quantitative evidence; UMAP is a companion overview"
            if core_question == "sample_level_composition"
            else None
        ),
    }


def scheme_hard_gate(
    record: dict[str, Any],
    intent: dict[str, Any],
    block_dispositions: dict[str, str] | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Return eligibility, hard-rejection reasons, and unresolved requirements."""
    reasons: list[str] = []
    missing: list[str] = []
    if intent.get("nonplot_request"):
        return False, ["non-plot request: download/setup commands are outside scientific Scheme retrieval"], missing
    eligibility = scheme_eligibility(record)
    # Visual-only references are legitimate decision/appearance anchors, but
    # they must remain explicitly non-code-bearing.  They are rejected later
    # only by adapt/render operations, not by pure discovery.
    if eligibility not in SCIENTIFIC_SCHEME_ELIGIBILITY and eligibility != "visual_reference":
        return False, [f"eligibility={eligibility}: not a standalone scientific visualization"], missing
    execution_plan = scheme_execution_plan(record, intent)
    if intent.get("requires_executable"):
        if not intent.get("backend"):
            return False, ["execution/render request requires an explicit backend: Python or R"], missing
        if scheme_is_visual_only(record):
            return False, ["requires_executable=true: visual-only Scheme is not callable"], missing
        if execution_plan.get("status") not in {"executable", "preflight_blocked"}:
            blockers = execution_plan.get("blockers") or [execution_plan.get("reason")]
            return False, [
                "requires_executable=true: " + "; ".join(str(item) for item in blockers if item)
            ], missing
        plan_label = (
            "executable_plan" if execution_plan.get("status") == "executable" else "formal_plan_preflight_blocked"
        )
        reasons.append(plan_label + "=" + str(execution_plan.get("base_recipe_id") or "formal_recipe"))
    elif scheme_is_visual_only(record):
        missing.append("visual-only reference: no target plotting source; choose a coded Scheme before adaptation or rendering")

    backend = intent.get("backend")
    raw_backends = record.get("backends", record.get("backend"))
    scheme_backends = {
        normalize_text(value).replace(" ", "_")
        for value in as_list(raw_backends)
        if value not in (None, "")
    }
    executable_target_bridge = bool(
        execution_plan.get("status") in {"executable", "preflight_blocked"}
        and execution_plan.get("backend") == backend
    )
    if (
        backend
        and scheme_backends
        and backend not in scheme_backends
        and "neutral" not in scheme_backends
        and not executable_target_bridge
    ):
        return False, [f"backend mismatch: selected {backend}, scheme {sorted(scheme_backends)}"], missing

    requested_method = intent.get("analysis_method") or "unknown"
    method = scheme_analysis_method(record)
    family = canonical_family(record.get("broad_family") or record.get("family"))
    subtype = str(record.get("geometry_subtype") or "unknown")
    enrichment_like = family == "gsea" or subtype.startswith("enrichment_") or subtype in {
        "radial_bar_lollipop",
        "go_enrichment_circle",
        "gsea_running_score",
        "gsea_rank_track",
        "gsea_rank_score_dot",
    }
    target_application = record.get("target_application") if isinstance(record.get("target_application"), dict) else {}
    adapter_methods = {
        normalize_analysis_method(item)
        for item in as_list(target_application.get("compatible_analysis_methods"))
    }
    if requested_method in {"ora", "gsea"} and enrichment_like and method != requested_method:
        if requested_method in adapter_methods:
            missing.append(
                f"explicit adapter required: source method is {method}, target accepts {requested_method.upper()} fields"
            )
        else:
            return False, [f"analysis_method mismatch: requested {requested_method}, scheme {method}"], missing
    if requested_method in {"ora", "gsea"} and method == "unknown" and record.get("broad_family") == "gsea":
        missing.append(f"confirm that the scheme accepts {requested_method.upper()} fields")
    if requested_method == "ambiguous_enrichment":
        missing.append("choose ORA (GeneRatio/Count/p.adjust) or GSEA (NES/ranked list/leading edge)")

    requested_subtypes = set(intent.get("geometry_subtypes") or [])
    exact_subtype_match = subtype in requested_subtypes
    if requested_subtypes and subtype not in requested_subtypes:
        compatible_pairs = {
            ("enrichment_rose", "radial_bar_lollipop"),
            ("radial_bar_lollipop", "enrichment_rose"),
        }
        if not any((requested, subtype) in compatible_pairs for requested in requested_subtypes):
            reasons.append(f"geometry_subtype differs: requested {sorted(requested_subtypes)}, scheme {subtype}")
            if intent.get("requires_executable"):
                return False, [
                    "requires_executable=true: exact requested geometry is not implemented by this Recipe mapping "
                    f"({sorted(requested_subtypes)} != {subtype})"
                ], missing
        else:
            exact_subtype_match = True

    negative_terms = [normalize_text(item) for item in as_list(record.get("negative_terms")) if item]
    query_normalized = normalize_text(intent.get("query") or "")
    matched_negative = [
        term
        for term in negative_terms
        if term
        and term in query_normalized
        and not re.search(rf"(?:不要|排除|避免|不是|非|without|exclude|not)\s*{re.escape(term)}", query_normalized, re.I)
    ]
    # Confusable subtype names often occur inside a more specific exact request
    # (for example marker_dotplot inside marker_dotplot_group_boxes).  The exact
    # geometry detector is stronger evidence than that lexical negative term.
    if matched_negative and not exact_subtype_match:
        return False, ["negative discriminator matched: " + ", ".join(matched_negative[:4])], missing

    if block_dispositions:
        linked = lineage_block_ids(record)
        known = [block_dispositions[item] for item in linked if item in block_dispositions]
        plot_roles = {"plot_base", "semantic_modifier", "aesthetic_modifier", "layout", "export"}
        if known and not any(role in plot_roles for role in known):
            return False, ["code lineage contains no plotting block after disposition gating"], missing

    return True, reasons or ["passed scientific eligibility and compatibility gates"], missing


def scheme_scientific_score(
    record: dict[str, Any], intent: dict[str, Any]
) -> tuple[float, dict[str, float], list[str], list[str]]:
    semantic = record.get("semantic_card") if isinstance(record.get("semantic_card"), dict) else {}
    source_semantics = record.get("source_semantics") if isinstance(record.get("source_semantics"), dict) else {}
    query = normalize_text(intent.get("query") or "")
    query_tokens = intent.get("tokens") or set()
    features = _SCHEME_FEATURE_CACHE.get(str(record.get("scheme_id")), {})
    record_tokens = features.get("search_tokens") or text_tokens(record.get("search_text") or "")
    lexical = len(query_tokens & record_tokens) / max(1, len(query_tokens)) if query_tokens else 0.0
    reasons: list[str] = []
    missing: list[str] = []

    subtype = str(record.get("geometry_subtype") or "unknown")
    requested_subtypes = set(intent.get("geometry_subtypes") or [])
    family = canonical_family(record.get("broad_family") or record.get("family"))
    requested_family = intent_retrieval_family(intent)
    if subtype in requested_subtypes:
        question = 30.0
        reasons.append(f"exact_subtype={subtype}")
    elif requested_subtypes and {subtype, *requested_subtypes} >= {"enrichment_rose", "radial_bar_lollipop"}:
        question = 28.0
        reasons.append(f"compatible_subtype={subtype}")
    elif family == requested_family or (requested_family == "sample_level_composition" and family == "composition"):
        # Keep a real margin between an exact Scheme-level request and a broad
        # family hit; otherwise a generic volcano/dotplot can outrank an exact
        # concordance/modifier subtype on incidental lexical overlap.
        question = min(25.0, 20.0 + lexical * 5.0)
        reasons.append(f"scientific_question={family}")
    else:
        question = min(18.0, lexical * 24.0)

    method = scheme_analysis_method(record)
    requested_method = intent.get("analysis_method") or "unknown"
    if requested_method in {"ora", "gsea"}:
        if method == requested_method:
            question = min(30.0, question + 4.0)
            reasons.append(f"analysis_method={method}")
        elif method == "unknown":
            missing.append(f"scheme analysis method is not declared; confirm {requested_method}")

    requested_units = set(intent.get("unit_of_analysis") or [])
    units = set(as_list(semantic.get("unit_of_analysis") or semantic.get("units") or source_semantics.get("unit")))
    requested_topologies = set(intent.get("data_topology") or [])
    topologies = set(
        as_list(
            semantic.get("data_topology")
            or semantic.get("data_topologies")
            or source_semantics.get("data_topology")
        )
    )
    data = 8.0
    if requested_units:
        data += 6.0 if requested_units & units else (1.0 if not units else 0.0)
    elif units:
        data += 3.0
    if requested_topologies:
        data += 6.0 if requested_topologies & topologies else (1.0 if not topologies else 0.0)
    elif topologies:
        data += 3.0
    data = min(20.0, data)

    channels = semantic.get("visual_channels") or record.get("visual_channels") or {}
    signature_tokens = features.get("signature_tokens") or text_tokens(
        flatten_text(
            record.get("visual_signature_tokens")
            or record.get("visual_feature_terms")
            or (record.get("visual_fingerprint") or {}).get("visual_signature_tokens")
            or []
        )
    )
    signature_overlap = query_tokens & signature_tokens
    encoding = min(15.0, (10.0 if channels else 4.0) + min(5.0, len(signature_overlap) * 1.5))
    if signature_overlap:
        reasons.append("visual_channels=" + ",".join(sorted(signature_overlap, key=len, reverse=True)[:5]))

    modifier_text = flatten_text(
        {
            "semantic": record.get("semantic_modifiers"),
            "aesthetic": record.get("aesthetic_modifiers"),
            "fingerprint": record.get("visual_fingerprint"),
        }
    )
    modifier_overlap = query_tokens & (features.get("modifier_tokens") or text_tokens(modifier_text))
    visual_intent = 5.0 if not intent.get("visual_intents") else min(10.0, 4.0 + 2.0 * len(modifier_overlap))
    if modifier_overlap:
        reasons.append("modifiers=" + ",".join(sorted(modifier_overlap, key=len, reverse=True)[:4]))

    tier = scheme_validation_tier(record)
    resolved_plan = scheme_execution_plan(record, intent)
    if intent.get("requires_executable") and resolved_plan.get("status") in {"executable", "preflight_blocked"}:
        executable = 10.0 if resolved_plan.get("status") == "executable" else 7.0
        reasons.append(
            ("formal_executable_plan=" if resolved_plan.get("status") == "executable" else "formal_plan_preflight_blocked=")
            + str(resolved_plan.get("base_recipe_id"))
        )
    else:
        executable = {
            "verified": 10.0,
            "executed": 10.0,
            "parse_verified": 8.0,
            "parse-verified": 8.0,
            "reference_only": 4.0,
            "reference-only": 4.0,
        }.get(tier, 3.0)
    review = scheme_review_status(record)
    readability = 10.0 if review in {"pass", "reviewed", "native_reviewed", "verified"} else 6.0 if "review" in review else 3.0
    source_status = normalize_text((record.get("source") or {}).get("status") if isinstance(record.get("source"), dict) else "")
    source = 5.0 if source_status in {"original", "internal distillation", "derived", "traceable"} else 3.0

    breakdown = {
        "question_evidence": round(question, 3),
        "data_compatibility": round(data, 3),
        "visual_encoding": round(encoding, 3),
        "visual_intent": round(visual_intent, 3),
        "executability": round(executable, 3),
        "readability": round(readability, 3),
        "source_diversity": round(source, 3),
    }
    score = sum(breakdown.values())
    if not requested_subtypes and family != requested_family:
        score -= 8.0
    if query and query in normalize_text(record.get("search_text") or ""):
        score += 3.0
        reasons.append("exact_phrase")
    return round(max(0.0, min(100.0, score)), 3), breakdown, reasons, missing


def scheme_appearance_score(record: dict[str, Any], query: str) -> tuple[float, dict[str, float], list[str]]:
    query_normalized = normalize_text(query)
    query_tokens = query_tokens_cached(query_normalized)
    subtype = str(record.get("geometry_subtype") or "unknown")
    features = _SCHEME_FEATURE_CACHE.get(str(record.get("scheme_id")), {})
    specific_aliases_raw = [
        subtype,
        *GEOMETRY_SUBTYPE_TERMS.get(subtype, ()),
        *[str(item) for item in as_list(record.get("aliases"))],
        *[str(item) for item in as_list(record.get("aliases_zh"))],
        *[str(item) for item in as_list(record.get("aliases_en"))],
    ]
    generic_aliases_raw: list[str] = []
    if "lollipop" in subtype:
        generic_aliases_raw.extend(("棒棒图", "lollipop"))
    if any(term in subtype for term in ("circle", "circular", "radial", "chord")):
        generic_aliases_raw.extend(("圆形图", "circle plot", "circular plot"))
    if scheme_eligibility(record) in {"decorative", "decorative_result", "excluded"}:
        specific_aliases_raw.extend(("圣诞树", "christmas tree", "decorative"))
    aliases = [*specific_aliases_raw, *generic_aliases_raw]
    fuzzy = [
        str(item)
        for item in [
            *as_list(record.get("fuzzy_phrases")),
            *as_list(record.get("fuzzy_descriptions")),
        ]
    ]
    fingerprint = record.get("visual_fingerprint") if isinstance(record.get("visual_fingerprint"), dict) else {}
    signature = (
        record.get("visual_signature_tokens")
        or record.get("visual_feature_terms")
        or fingerprint.get("visual_signature_tokens")
        or fingerprint
    )
    modifiers = {
        "semantic": record.get("semantic_modifiers"),
        "aesthetic": record.get("aesthetic_modifiers"),
        "fingerprint": fingerprint,
    }
    reasons: list[str] = []

    normalized_aliases = features.get("aliases") or [normalize_text(alias) for alias in aliases if normalize_text(alias)]
    specific_aliases = features.get("specific_aliases") or [
        normalize_text(alias) for alias in specific_aliases_raw if normalize_text(alias)
    ]
    generic_aliases = features.get("generic_aliases") or [
        normalize_text(alias) for alias in generic_aliases_raw if normalize_text(alias)
    ]
    exact_specific = [alias for alias in specific_aliases if alias in query_normalized]
    exact_generic = [alias for alias in generic_aliases if alias in query_normalized]
    # A controlled Scheme alias carries the full 40% appearance weight.  A
    # generic shape word (for example “棒棒图”) is only an anchor: otherwise it
    # ties mutation, radial and mirrored encodings and lets review bonuses
    # overturn the user's exact “背靠背棒棒图” request.
    exact = 40.0 if exact_specific else 12.0 if exact_generic else 0.0
    if exact_specific:
        reasons.append("exact subtype/alias=" + ",".join(exact_specific[:3]))
    elif exact_generic:
        reasons.append("generic shape anchor=" + ",".join(exact_generic[:3]))

    signature_overlap = query_tokens & (features.get("signature_tokens") or text_tokens(flatten_text(signature)))
    signature_score = min(25.0, 5.0 * len(signature_overlap))
    if signature_overlap:
        reasons.append("visual signature=" + ",".join(sorted(signature_overlap, key=len, reverse=True)[:5]))

    modifier_overlap = query_tokens & (features.get("modifier_tokens") or text_tokens(flatten_text(modifiers)))
    modifier_score = min(15.0, 3.0 * len(modifier_overlap))
    if modifier_overlap:
        reasons.append("modifier/layout=" + ",".join(sorted(modifier_overlap, key=len, reverse=True)[:4]))

    fuzzy_text = " ".join(fuzzy)
    fuzzy_overlap = query_tokens & (features.get("fuzzy_tokens") or text_tokens(fuzzy_text))
    normalized_fuzzy = features.get("fuzzy_phrases") or [normalize_text(item) for item in fuzzy if normalize_text(item)]
    fuzzy_phrase = any(item in query_normalized for item in normalized_fuzzy)
    fuzzy_score = 10.0 if fuzzy_phrase else min(10.0, 2.0 * len(fuzzy_overlap))
    if fuzzy_score:
        reasons.append("personalized phrase match")

    review = scheme_review_status(record)
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    image_evidence = record.get("image_evidence") if isinstance(record.get("image_evidence"), dict) else {}
    consistency = (
        validation.get("code_image_consistency")
        or validation.get("image_code_consistency")
        or image_evidence.get("code_image_consistency")
    )
    quality = 0.0
    if review in {"pass", "reviewed", "native_reviewed", "verified"}:
        quality += 5.0
    if consistency in {True, "pass", "verified", "reviewed"}:
        quality += 5.0
    if query_normalized and not (exact or signature_score or modifier_score or fuzzy_score):
        quality = 0.0
    if quality:
        reasons.append("native visual/code evidence")

    if not query_normalized:
        exact = 1.0
    breakdown = {
        "exact_subtype_alias": exact,
        "visual_signature": signature_score,
        "modifier_layout": modifier_score,
        "personalized_description": fuzzy_score,
        "visual_code_evidence": quality,
    }
    return round(sum(breakdown.values()), 3), breakdown, reasons


def index_candidate_ids(query: str) -> set[str] | None:
    """Read common retrieval-index layouts; return None when the layout is unknown."""
    if not RETRIEVAL_INDEX_PATH.exists():
        return None
    payload = load_json_object(RETRIEVAL_INDEX_PATH, {})
    postings = (
        payload.get("postings")
        or payload.get("token_postings")
        or payload.get("inverted_index")
        or payload.get("tokens")
    )
    if not isinstance(postings, dict):
        return None
    ids: set[str] = set()
    for token in query_tokens_cached(query):
        values = postings.get(token)
        if isinstance(values, dict):
            values = values.get("scheme_ids") or values.get("ids")
        for value in as_list(values):
            if isinstance(value, str):
                ids.add(value)
    return ids or None


def rank_scheme_appearance(
    schemes: list[dict[str, Any]],
    query: str,
    top_k: int = 5,
    include_excluded: bool = False,
) -> list[dict[str, Any]]:
    candidate_ids = index_candidate_ids(query)
    # Score the in-memory catalog completely.  The inverted index is loaded for
    # diagnostics/cache warm-up but never allowed to reduce visual recall.
    pool = schemes
    ranked: list[tuple[float, str, dict[str, Any], dict[str, float], list[str]]] = []
    for record in pool:
        eligibility = scheme_eligibility(record)
        if not include_excluded and eligibility in {"decorative", "decorative_result", "excluded", "nonplot", "non_plot", "prompt_non_code"}:
            continue
        score, breakdown, reasons = scheme_appearance_score(record, query)
        if query and score <= 0:
            continue
        ranked.append((score, str(record.get("scheme_id")), record, breakdown, reasons))
    requested_subtypes = set(detect_geometry_subtypes(query))
    ranked.sort(
        key=lambda item: (
            0 if str(item[2].get("geometry_subtype") or "unknown") in requested_subtypes else 1,
            -item[0],
            normalize_text(item[2].get("title")),
            item[1],
        )
    )
    results: list[dict[str, Any]] = []
    seen_subtypes: set[str] = set()
    for score, scheme_id, record, breakdown, reasons in ranked:
        subtype = str(record.get("geometry_subtype") or "unknown")
        if subtype in seen_subtypes:
            continue
        seen_subtypes.add(subtype)
        results.append(
            {
                "scheme_id": scheme_id,
                "id": scheme_id,
                "title": record.get("title"),
                "eligibility": scheme_eligibility(record),
                "broad_family": record.get("broad_family"),
                "geometry_subtype": record.get("geometry_subtype"),
                "analysis_method": scheme_analysis_method(record),
                "review_status": scheme_review_status(record),
                "score": score,
                "score_breakdown": breakdown,
                "why_match": "; ".join(reasons) or "visual browse order",
                "image_evidence": record.get("image_evidence"),
                "validation_tier": scheme_validation_tier(record),
            }
        )
        if len(results) >= max(1, top_k):
            break
    return results


def scheme_result_row(
    record: dict[str, Any],
    score: float,
    breakdown: dict[str, float],
    reasons: list[str],
    missing: list[str],
    rank: int,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intent = intent or {}
    semantic = record.get("semantic_card") if isinstance(record.get("semantic_card"), dict) else {}
    family = canonical_family(record.get("broad_family") or record.get("family"))
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    recipe_ids = (
        record.get("recipe_ids")
        or record.get("formal_recipe_ids")
        or validation.get("recipe_ids")
        or []
    )
    code_lineage = record.get("code_lineage") or {}
    has_lineage = bool(
        not scheme_is_visual_only(record)
        and (
            lineage_block_ids(record)
            or as_list(code_lineage.get("object_chain"))
            or as_list(code_lineage.get("calls"))
            or record.get("candidate_code_path")
        )
    )
    execution_plan = scheme_execution_plan(record, intent)
    source_analysis_method = scheme_analysis_method(record)
    target_analysis_method = (
        intent.get("analysis_method")
        if execution_plan.get("availability") == "formal_recipe"
        and intent.get("analysis_method") in {"ora", "gsea"}
        else source_analysis_method
    )
    legacy_availability = "scheme_with_code_lineage" if has_lineage else "scheme_without_code_lineage"
    availability = (
        execution_plan.get("availability")
        if intent.get("action_intent") in {"adapt", "execute", "render"}
        else legacy_availability
    )
    role = ("primary", "conservative", "information_dense")[rank - 1] if rank <= 3 else "additional"
    return {
        "rank": rank,
        "recommendation_role": role,
        "id": record.get("scheme_id"),
        "scheme_id": record.get("scheme_id"),
        "record_type": "scheme",
        "title": record.get("title"),
        "score": score,
        "score_breakdown": breakdown,
        "why_match": "; ".join(reasons[:8]) or "Scheme-v2 semantic match",
        "tradeoff": recommendation_tradeoff(family, family, role),
        "priority_rationale": "Scientific and data compatibility control ranking; appearance is reported separately.",
        "family": family,
        "broad_family": family,
        "geometry_subtype": record.get("geometry_subtype"),
        "analysis_method": target_analysis_method,
        "source_analysis_method": source_analysis_method,
        "backend": execution_plan.get("backend") or record.get("backend"),
        "backends": (
            [execution_plan.get("backend")]
            if execution_plan.get("status") in {"executable", "preflight_blocked"} and execution_plan.get("backend")
            else record.get("backends") or as_list(record.get("backend"))
        ),
        "source_backends": record.get("backends") or as_list(record.get("backend")),
        "eligibility": scheme_eligibility(record),
        "validation_tier": scheme_validation_tier(record),
        "review_status": scheme_review_status(record),
        "input_contract": semantic.get("required_variables") or record.get("required_inputs") or record.get("requires") or {},
        "visual_channels": semantic.get("visual_channels") or record.get("visual_channels") or {},
        "supports_claims": semantic.get("supports_claims") or semantic.get("can_support") or record.get("supported_claims") or [],
        "does_not_support": semantic.get("does_not_support") or semantic.get("cannot_support") or record.get("claim_limits") or [],
        "required_statistics": semantic.get("required_statistics") or record.get("required_statistics") or [],
        "missing_inputs": list(dict.fromkeys(missing)),
        "companion_evidence": semantic.get("preferred_companions") or semantic.get("companion_evidence") or record.get("recommended_companion") or [],
        "recipe_ids": execution_plan.get("recipe_ids") or as_list(recipe_ids),
        "availability": availability,
        "execution_availability": execution_plan.get("availability"),
        "executable_plan": execution_plan,
        "requires_backend_choice_before_adapt_or_render": not bool(intent.get("backend")),
        "source_semantics": record.get("source_semantics"),
        "target_application": record.get("target_application"),
        "code": record.get("code") or record.get("candidate_code"),
    }


def clarification_for_query(
    intent: dict[str, Any], appearance: list[dict[str, Any]]
) -> dict[str, Any] | None:
    query = normalize_text(intent.get("query") or "")
    if intent.get("requires_backend_choice"):
        return {
            "needed": True,
            "reason": "Executable adaptation and rendering are backend-exclusive.",
            "question": "Python or R?",
            "options": [
                {"backend": "python"},
                {"backend": "r"},
            ],
        }
    if intent.get("source_lookup"):
        return None
    if intent.get("analysis_method") == "ambiguous_enrichment":
        return {
            "needed": True,
            "reason": "The query mixes ORA and GSEA field contracts.",
            "question": "Are the inputs ORA fields (GeneRatio/Count/p.adjust) or GSEA fields (NES/ranked list/leading edge)?",
            "options": [
                {"analysis_method": "ora", "required_fields": ["term", "GeneRatio or Count", "p.adjust/FDR"]},
                {"analysis_method": "gsea", "required_fields": ["term", "NES", "FDR", "ranked list"]},
            ],
        }
    generic_shape = bool(re.search(r"(?:圆形图|圆圈图|circle\s*plot|circular\s*plot|棒棒图|lollipop)", query, re.I))
    contextual = bool(
        re.search(
            r"(?:富集|通路|gsea|ora|gene\s*ratio|p\.adjust|nes|突变|mutation|protein|"
            r"通讯|cellchat|组成|composition|fold\s*change)",
            query,
            re.I,
        )
    )
    if generic_shape and not contextual and not intent.get("geometry_subtypes"):
        options = []
        seen: set[str] = set()
        for item in appearance:
            subtype = str(item.get("geometry_subtype") or "unknown")
            if subtype in seen:
                continue
            seen.add(subtype)
            options.append({
                "scheme_id": item.get("scheme_id"),
                "title": item.get("title"),
                "geometry_subtype": subtype,
            })
            if len(options) >= 3:
                break
        if len(options) >= 2:
            return {
                "needed": True,
                "reason": "The shape term maps to multiple scientific encodings.",
                "question": "Which data meaning should the circular/lollipop marks encode?",
                "options": options,
            }
    if (
        intent_retrieval_family(intent) == "gsea"
        and intent.get("analysis_method") == "unknown"
        and not intent.get("geometry_subtypes")
    ):
        return {
            "needed": True,
            "reason": "Enrichment visualization depends on the analysis field contract.",
            "question": "Is this ORA output or a ranked-list GSEA result?",
            "options": [
                {"analysis_method": "ora", "required_fields": ["GeneRatio/Count", "p.adjust/FDR"]},
                {"analysis_method": "gsea", "required_fields": ["NES", "FDR", "ranked list"]},
            ],
        }
    return None


def positive_decorative_intent(query: str) -> bool:
    """Return True only when decorative Christmas content is requested positively.

    This discriminator is shared by the scientific atlas gate and its strict
    regression.  Negative wording such as “不要圣诞树” must remain available
    to a normal scientific/palette query instead of suppressing all results.
    """
    normalized = normalize_text(query)
    if not re.search(r"圣诞树|christmas\s*tree", normalized, re.I):
        return False
    negated = re.search(
        r"(?:不要|排除|避免|不是|非|without|exclude|not)\s*.{0,12}(?:圣诞树|christmas\s*tree)",
        normalized,
        re.I,
    )
    return not bool(negated)


def search_scheme_records(
    schemes: list[dict[str, Any]],
    query: str,
    backend: str | None = None,
    family: str | None = None,
    domain: str | None = None,
    top_k: int = 3,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    intent = query_intent(query, backend=backend, family=family, domain=domain)
    if positive_decorative_intent(query) and not intent.get("source_lookup"):
        intent["retrieval_gate"] = "decorative_content_excluded_from_default_scientific_search"
        return intent, [], [], [], None
    block_dispositions = load_disposition_map(BLOCK_DISPOSITIONS_PATH, "block") if BLOCK_DISPOSITIONS_PATH.exists() else {}
    exact_identifiers = code_identifier_terms(query)
    if exact_identifiers:
        intent["lookup_mode"] = "exact_code_identifier"
        intent["exact_code_identifiers"] = exact_identifiers
    candidate_ids = index_candidate_ids(query)
    # The catalog is intentionally small (hundreds, not millions).  Use the
    # precomputed index as a warm-cache signal, never as a recall gate: an
    # incomplete posting list must not suppress a Scheme whose controlled
    # alias or visual fingerprint is the best match.
    pool = schemes

    ranked: list[tuple[float, dict[str, Any], dict[str, float], list[str], list[str]]] = []
    rejected: list[tuple[float, dict[str, Any]]] = []
    for record in pool:
        allowed, gate_reasons, gate_missing = scheme_hard_gate(record, intent, block_dispositions)
        appearance_score, appearance_breakdown, _ = scheme_appearance_score(record, query)
        if not allowed:
            if appearance_score > 0 or canonical_family(record.get("broad_family")) == intent_retrieval_family(intent):
                rejected_plan = scheme_execution_plan(record, intent)
                rejected.append((appearance_score, {
                    "id": record.get("scheme_id"),
                    "scheme_id": record.get("scheme_id"),
                    "title": record.get("title"),
                    "eligibility": scheme_eligibility(record),
                    "geometry_subtype": record.get("geometry_subtype"),
                    "analysis_method": scheme_analysis_method(record),
                    "gate": "hard_compatibility",
                    "reason": "; ".join(gate_reasons),
                    "availability": rejected_plan.get("availability"),
                    "executable_plan": rejected_plan,
                }))
            continue
        if exact_identifiers:
            lineage_text = flatten_text(record.get("code_lineage") or {})
            source_text = " ".join((lineage_text, str(record.get("search_text") or "")))
            matched_identifiers = [
                identifier
                for identifier in exact_identifiers
                if re.search(
                    r"(?<![A-Za-z0-9_])" + re.escape(identifier) + r"(?![A-Za-z0-9_])",
                    source_text,
                    re.I,
                )
            ]
            if not matched_identifiers:
                continue
            score_missing: list[str] = []
            breakdown = {
                "question_evidence": 30.0,
                "data_compatibility": 10.0,
                "visual_encoding": 10.0,
                "visual_intent": 5.0,
                "executability": 8.0 if scheme_validation_tier(record) == "parse_verified" else 4.0,
                "readability": 5.0,
                "source_diversity": 5.0,
            }
            score = min(100.0, sum(breakdown.values()) + 5.0 * len(matched_identifiers))
            ranked.append(
                (
                    score,
                    record,
                    breakdown,
                    [*gate_reasons, "exact code identifier=" + ",".join(matched_identifiers)],
                    [*gate_missing, *score_missing],
                )
            )
            continue
        score, breakdown, reasons, score_missing = scheme_scientific_score(record, intent)
        record_family = canonical_family(record.get("broad_family"))
        intent_family = intent_retrieval_family(intent)
        family_match = record_family == intent_family or (
            intent_family == "sample_level_composition" and record_family == "composition"
        )
        subtype_match = bool(
            set(intent.get("geometry_subtypes") or [])
            & {str(record.get("geometry_subtype") or "unknown")}
        )
        method_match = (
            intent.get("analysis_method") in {"ora", "gsea"}
            and scheme_analysis_method(record) == intent.get("analysis_method")
        )
        explicit_secondary = {
            canonical_family(item) for item in intent.get("families", [])[1:]
        }
        policy_companion = (
            intent_family == "sample_level_composition"
            and record_family in {"composition", "boxplot", "embedding"}
        )
        exact_appearance = appearance_breakdown.get("exact_subtype_alias", 0.0) >= 40.0
        scientifically_relevant = (
            family_match
            or record_family in explicit_secondary
            or policy_companion
            or subtype_match
            or method_match
            or exact_appearance
        )
        if score <= 0 or not scientifically_relevant:
            continue
        ranked.append((score, record, breakdown, [*gate_reasons, *reasons], [*gate_missing, *score_missing]))

    requested_subtypes_ordered = [str(item) for item in intent.get("geometry_subtypes") or []]
    requested_subtypes = set(requested_subtypes_ordered)
    requested_subtype_rank = {
        subtype: index for index, subtype in enumerate(requested_subtypes_ordered)
    }
    ranked.sort(
        key=lambda item: (
            requested_subtype_rank.get(
                str(item[1].get("geometry_subtype") or "unknown"),
                len(requested_subtype_rank) + 1,
            ),
            -item[0],
            normalize_text(item[1].get("title")),
            str(item[1].get("scheme_id")),
        )
    )
    selected: list[tuple[float, dict[str, Any], dict[str, float], list[str], list[str]]] = []
    signatures: set[tuple[str, str, str]] = set()
    if intent_retrieval_family(intent) == "sample_level_composition":
        for desired_family in ("composition", "boxplot", "embedding"):
            candidate = next(
                (
                    item
                    for item in ranked
                    if canonical_family(item[1].get("broad_family")) == desired_family
                    and item[1].get("scheme_id") not in {chosen[1].get("scheme_id") for chosen in selected}
                ),
                None,
            )
            if candidate:
                selected.append(candidate)
            if len(selected) >= max(1, top_k):
                break
        signatures.update(
            (
                canonical_family(item[1].get("broad_family")),
                str(item[1].get("geometry_subtype") or "unknown"),
                scheme_analysis_method(item[1]),
            )
            for item in selected
        )
    selection_limit = max(
        1,
        top_k,
        len(requested_subtypes_ordered)
        if intent_retrieval_family(intent) == "cellchat_chord"
        else 0,
    )
    for item in ranked:
        if len(selected) >= selection_limit:
            break
        if item[1].get("scheme_id") in {chosen[1].get("scheme_id") for chosen in selected}:
            continue
        signature = (
            canonical_family(item[1].get("broad_family")),
            str(item[1].get("geometry_subtype") or "unknown"),
            scheme_analysis_method(item[1]),
        )
        if selected and signature in signatures:
            continue
        selected.append(item)
        signatures.add(signature)
        if len(selected) >= selection_limit:
            break
    if not selected and ranked:
        selected = ranked[:selection_limit]

    appearance_pool = schemes
    if intent.get("requires_executable"):
        appearance_pool = [
            record
            for record in schemes
            if scheme_hard_gate(record, intent, block_dispositions)[0]
        ]
    appearance = rank_scheme_appearance(appearance_pool, query, top_k=max(3, top_k))
    scheme_by_id = {str(record.get("scheme_id")): record for record in schemes}
    for appearance_row in appearance:
        appearance_record = scheme_by_id.get(str(appearance_row.get("scheme_id")), {})
        appearance_plan = scheme_execution_plan(appearance_record, intent)
        appearance_row["availability"] = appearance_plan.get("availability")
        appearance_row["executable_plan"] = appearance_plan
    available_scientific_subtypes = {
        str(record.get("geometry_subtype") or "unknown")
        for record in schemes
        if scheme_eligibility(record) in SCIENTIFIC_SCHEME_ELIGIBILITY
        or scheme_eligibility(record) == "visual_reference"
    }
    subtype_equivalents = {
        "enrichment_rose": {"radial_bar_lollipop"},
        "radial_bar_lollipop": {"enrichment_rose"},
    }
    unresolved_subtypes = sorted(
        requested
        for requested in requested_subtypes
        if requested not in available_scientific_subtypes
        and not (subtype_equivalents.get(requested, set()) & available_scientific_subtypes)
    )
    if unresolved_subtypes and not exact_identifiers and not intent.get("source_lookup"):
        # Do not silently substitute a rank-track, score-dot or GO circle for a
        # requested GSEA running-score curve.  Nearby options remain explicit
        # non-equivalent choices, and the appearance channel is kept empty so a
        # visually unrelated reviewed image cannot masquerade as the target.
        explicit_nearby = {
            "gsea_running_score": {"gsea_rank_track", "gsea_rank_score_dot"},
        }
        allowed_nearby = set().union(
            *(explicit_nearby.get(item, set()) for item in unresolved_subtypes)
        )
        nearby_options = []
        for score, record, _breakdown, _reasons, _missing in ranked:
            option_subtype = str(record.get("geometry_subtype") or "unknown")
            if option_subtype in unresolved_subtypes:
                continue
            if allowed_nearby and option_subtype not in allowed_nearby:
                continue
            nearby_options.append(
                {
                    "scheme_id": record.get("scheme_id"),
                    "title": record.get("title"),
                    "geometry_subtype": option_subtype,
                    "equivalent": False,
                }
            )
            if len(nearby_options) >= 3:
                break
        clarification = {
            "needed": True,
            "reason": "The requested exact visualization subtype is not represented by a verified Scheme in this offline source library.",
            "question": "Should I use one of the explicitly non-equivalent nearby designs, or wait for an exact source-backed Scheme?",
            "requested_subtypes": unresolved_subtypes,
            "options": nearby_options,
        }
        appearance = []
    else:
        clarification = clarification_for_query(intent, appearance)
    if clarification and clarification.get("needed"):
        decisions: list[dict[str, Any]] = []
    else:
        decisions = [
            scheme_result_row(
                record,
                score,
                breakdown,
                reasons,
                missing,
                index,
                intent=intent,
            )
            for index, (score, record, breakdown, reasons, missing) in enumerate(selected, 1)
        ]
    rejected.sort(key=lambda item: (-item[0], str(item[1].get("id"))))
    rejected_rows = [item[1] for item in rejected[: max(10, top_k * 5)]]
    intent["retrieval_index_used"] = candidate_ids is not None
    return intent, decisions, appearance, rejected_rows, clarification


def search_records(records: list[dict[str, Any]], query: str, backend: str | None = None, family: str | None = None, domain: str | None = None, top_k: int = 3) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    intent = query_intent(query, backend=backend, family=family, domain=domain)
    exact_identifiers = code_identifier_terms(query)
    if exact_identifiers:
        intent["lookup_mode"] = "exact_code_identifier"
        intent["exact_code_identifiers"] = exact_identifiers
    ranked = []
    for record in records:
        score, reasons, breakdown, missing_inputs = score_record(record, intent)
        if score < 0:
            continue
        ranked.append((score, record, reasons, breakdown, missing_inputs))
    type_priority = {"recipe": 4, "strategy": 3, "source_block": 2, "image": 1, "article": 0}
    ranked.sort(key=lambda item: (item[0], type_priority.get(item[1].get("record_type"), 0)), reverse=True)

    primary_family = intent_retrieval_family(intent)
    detected_secondary = [item for item in intent.get("families", [])[1:] if item != primary_family]
    alternatives = list(ALTERNATIVE_FAMILIES.get(primary_family, ()))
    if primary_family == "layout" and detected_secondary:
        alternatives = ["visual_review", detected_secondary[0]]
    desired_families = [primary_family, *alternatives]
    selected: list[tuple[float, dict[str, Any], list[str], dict[str, float], list[str]]] = []
    seen_ids: set[str] = set()
    if exact_identifiers:
        exact_ranked = []
        for item in ranked:
            record = item[1]
            if record.get("record_type") not in {"recipe", "source_block"}:
                continue
            code_text = str(record.get("code") or "")
            all_text = " ".join((code_text, str(record.get("title") or ""), str(record.get("search_text") or "")))
            matches = [
                identifier
                for identifier in exact_identifiers
                if re.search(r"(?<![A-Za-z0-9_])" + re.escape(identifier) + r"(?![A-Za-z0-9_])", all_text, re.I)
            ]
            if not matches:
                continue
            code_hits = sum(
                len(re.findall(r"(?<![A-Za-z0-9_])" + re.escape(identifier) + r"(?![A-Za-z0-9_])", code_text, re.I))
                for identifier in matches
            )
            exact_ranked.append((bool(code_hits), record.get("role") == "plot", -len(record.get("safety_flags") or []), code_hits, item))
        exact_ranked.sort(key=lambda entry: (entry[0], entry[1], entry[2], entry[3], entry[4][0]), reverse=True)
        for _, _, _, _, item in exact_ranked[: max(1, top_k)]:
            selected.append(item)
            seen_ids.add(item[1].get("id"))
    for desired in desired_families[: min(3, max(1, top_k))]:
        if len(selected) >= max(1, top_k):
            break
        family_items = [item for item in ranked if item[1].get("id") not in seen_ids and canonical_family(item[1].get("family")) == desired]
        if desired == "layout" and intent.get("component_target"):
            targeted = [item for item in family_items if str(item[1].get("id", "")).startswith(intent["component_target"])]
            family_items = targeted or family_items
        if desired != "layout":
            decision_ready = [
                item for item in family_items
                if item[1].get("record_type") in {"recipe", "strategy"}
                and (item[1].get("record_type") == "strategy" or item[1].get("kind") in {"base_recipe", "adapter"})
            ]
            top_level = [item for item in family_items if item[1].get("record_type") != "recipe" or item[1].get("kind") in {"base_recipe", "adapter"}]
            family_items = decision_ready or top_level or family_items
        candidate = family_items[0] if family_items else None
        if candidate:
            selected.append(candidate)
            seen_ids.add(candidate[1].get("id"))
    if len(selected) < max(1, top_k):
        for item in ranked:
            if item[1].get("id") in seen_ids:
                continue
            selected.append(item)
            seen_ids.add(item[1].get("id"))
            if len(selected) >= max(1, top_k):
                break

    result_rows: list[dict[str, Any]] = []
    role_names = ["primary", "conservative", "information_dense"]
    for index, (score, record, reasons, breakdown, missing_inputs) in enumerate(selected):
        family_name = canonical_family(record.get("family"))
        semantic = record.get("semantic_card") or {}
        boundary = CLAIM_BOUNDARIES.get(family_name, {})
        role = role_names[index] if index < 3 else "additional"
        tradeoff = recommendation_tradeoff(primary_family, family_name, role)
        preferred_companions = semantic.get("preferred_companions") or []
        availability = "direct_recipe" if record.get("record_type") == "recipe" else "decision_strategy" if record.get("record_type") == "strategy" else "source_candidate"
        compatible_ids = (record.get("compatible_with") or {}).get("ids", []) if isinstance(record.get("compatible_with"), dict) else []
        compatible_modifiers = compatible_ids if record.get("kind") in {"base_recipe", "adapter"} else []
        compatible_bases = compatible_ids if record.get("kind") in COMPONENT_ORDER else []
        selected_modifiers: list[str] = []
        selected_adapter: str | None = None
        selected_base: str | None = None
        if record.get("kind") == "base_recipe":
            query_terms = text_tokens(intent.get("query", ""))
            requested_objects = set(intent.get("input_objects") or [])
            for _, adapter, _, _, _ in ranked:
                if adapter.get("record_type") != "recipe" or adapter.get("kind") != "adapter":
                    continue
                adapter_inputs = set((adapter.get("requires") or {}).get("object_types") or [])
                adapter_targets = set((adapter.get("compatible_with") or {}).get("ids") or [])
                if record.get("id") in adapter_targets and requested_objects and requested_objects & adapter_inputs:
                    selected_adapter = adapter.get("id")
                    break
            component_candidates = []
            for _, component, _, _, _ in ranked:
                if component.get("record_type") != "recipe" or component.get("kind") not in {"semantic_modifier", "aesthetic_modifier"}:
                    continue
                if component.get("id") not in compatible_modifiers:
                    continue
                component_overlap = query_terms & text_tokens(component.get("search_text", ""))
                target_bonus = 100 if intent.get("component_target") and str(component.get("id", "")).startswith(intent["component_target"]) else 0
                if component_overlap or target_bonus:
                    component_candidates.append((target_bonus + len(component_overlap), component.get("id")))
            component_candidates.sort(reverse=True)
            if component_candidates:
                selected_modifiers = [component_candidates[0][1]]
        elif record.get("kind") in COMPONENT_ORDER and compatible_bases:
            secondary_families = set(intent.get("families", [])[1:])
            base_candidates = [
                item for item in ranked
                if item[1].get("id") in compatible_bases and item[1].get("kind") == "base_recipe"
                and (not secondary_families or canonical_family(item[1].get("family")) in secondary_families)
            ]
            if base_candidates:
                selected_base = base_candidates[0][1].get("id")
        composition_plan = (
            [selected_base, record.get("id")] if selected_base
            else [*([selected_adapter] if selected_adapter else []), record.get("id"), *selected_modifiers]
        )
        supports_claims = semantic.get("supports_claims") or record.get("supports_claims") or ([boundary.get("supports")] if boundary.get("supports") else [])
        does_not_support = semantic.get("does_not_support") or semantic.get("does_not_support_claims") or record.get("does_not_support") or ([boundary.get("does_not_support")] if boundary.get("does_not_support") else [])
        visual_channels = semantic.get("visual_channels") or {}
        if not supports_claims:
            supports_claims = ["Reference-only candidate: supports implementation or visual-style inspection after its encoding is explicitly audited."]
        if not does_not_support:
            does_not_support = ["Does not support a scientific or statistical conclusion until its input, encoding, and analysis contracts are validated."]
        if not visual_channels:
            visual_channels = {"unverified": "inspect the legend, code mapping, and scale before interpretation"}
        if record.get("record_type") in {"source_block", "image", "article"}:
            missing_inputs = [*missing_inputs, "distill and validate a SemanticCard before scientific use"]
        questions_answered = semantic.get("questions_answered") or []
        semantic_reason = (
            "可回答: " + ", ".join(str(item) for item in questions_answered[:3]) + "; "
            if questions_answered else ""
        )
        why_match = semantic_reason + ("; ".join(reasons[:6]) or "catalog match")
        priority_rationale = (
            "主方案优先回答核心科学问题；其他图形只承担稳健性核对或补充信息。"
            if role == "primary" else "未列为主方案：" + tradeoff
        )
        result_rows.append(
            {
                "rank": index + 1,
                "recommendation_role": role,
                "id": record.get("id"),
                "record_type": record.get("record_type"),
                "title": record.get("title") or record.get("name"),
                "score": score,
                "score_breakdown": breakdown,
                "why_match": why_match,
                "tradeoff": tradeoff,
                "priority_rationale": priority_rationale,
                "family": family_name,
                "backend": record.get("backend"),
                "validation_tier": get_validation_tier(record),
                "safety_flags": record.get("safety_flags") or [],
                "input_contract": record.get("input_contract") or record.get("requires") or {},
                "visual_channels": visual_channels,
                "supports_claims": supports_claims,
                "does_not_support": does_not_support,
                "required_statistics": semantic.get("required_statistics") or [],
                "missing_inputs": missing_inputs,
                "companion_evidence": preferred_companions,
                "compatible_modifiers": compatible_modifiers,
                "compatible_bases": compatible_bases,
                "selected_adapter": selected_adapter,
                "selected_base": selected_base,
                "selected_modifiers": selected_modifiers,
                "composition_plan": composition_plan,
                "preview_path": record.get("preview_path") or (record.get("files") or {}).get("preview"),
                "source_role": record.get("role"),
                "availability": availability,
                "requires_backend_choice_before_adapt_or_render": record.get("backend") is None or intent.get("backend") is None,
                "code_path": record.get("code_path"),
                "code": record.get("code"),
            }
        )
    return intent, result_rows


def markdown_results(intent: dict[str, Any], results: list[dict[str, Any]], include_code: bool = False) -> str:
    lines = ["# Plot recommendations", "", f"Intent: `{json.dumps({k: v for k, v in intent.items() if k != 'tokens'}, ensure_ascii=False)}`", ""]
    for result in results:
        lines.extend(
            [
                f"## {result['rank']}. {result['title']} ({result['recommendation_role']})",
                "",
                f"- Score: {result['score']}",
                f"- Family/backend: `{result['family']}` / `{result.get('backend') or 'unspecified'}`",
                f"- Why: {result['why_match']}",
                f"- Supports: {'; '.join(result.get('supports_claims') or ['not yet curated'])}",
                f"- Does not support: {'; '.join(result.get('does_not_support') or ['requires semantic review'])}",
                "",
            ]
        )
        if include_code and result.get("code"):
            language = result.get("backend") or "text"
            lines.extend([f"```{language}", result["code"], "```", ""])
    return "\n".join(lines)


def command_build(args: argparse.Namespace) -> int:
    records, coverage = build_catalog(Path(args.source).resolve() if args.source else SOURCE_ROOT, write=True)
    print(json.dumps({"catalog": rel_posix(CATALOG_PATH), "coverage": coverage, "total_records": len(records)}, ensure_ascii=False, indent=2))
    return 0 if all(coverage["expectations_pass"].values()) else 2


def command_search_v2(args: argparse.Namespace) -> int:
    """Search the generated Scheme catalog without walking the source archive."""
    if args.top_k < 1:
        raise ValueError("--top-k must be at least 1")
    schemes = load_scheme_records()
    records = load_catalog_fast()
    if schemes:
        intent, results, appearance_matches, rejected_candidates, clarification = search_scheme_records(
            schemes,
            args.query,
            backend=args.backend,
            family=args.family,
            domain=args.domain,
            top_k=args.top_k,
        )
        if (
            intent.get("source_lookup")
            and not intent.get("requires_executable")
            and not results
            and records
        ):
            legacy_intent, legacy_results = search_records(
                records,
                args.query,
                backend=args.backend,
                family=args.family,
                domain=args.domain,
                top_k=max(args.top_k, 10),
            )
            safe_source_roles = {"plot", "semantic_modifier", "aesthetic_modifier", "layout", "export"}
            exact_identifiers = code_identifier_terms(args.query)
            results = [
                item
                for item in legacy_results
                if (
                    item.get("record_type") == "recipe"
                    or (
                        item.get("record_type") == "source_block"
                        and item.get("source_role") in safe_source_roles
                    )
                )
                and all(
                    re.search(
                        r"(?<![A-Za-z0-9_])" + re.escape(identifier) + r"(?![A-Za-z0-9_])",
                        " ".join(
                            (
                                str(item.get("code") or ""),
                                str(item.get("title") or ""),
                                str(item.get("id") or ""),
                            )
                        ),
                        re.I,
                    )
                    for identifier in exact_identifiers
                )
            ][: args.top_k]
            if results:
                intent.update(
                    {
                        "lookup_mode": legacy_intent.get("lookup_mode"),
                        "exact_code_identifiers": legacy_intent.get("exact_code_identifiers"),
                        "source_lookup_fallback": "legacy_catalog_plot_blocks_only",
                    }
                )
        if appearance_matches:
            strongest_appearance = max(float(item.get("score") or 0.0) for item in appearance_matches)
            if strongest_appearance >= 20.0:
                appearance_floor = max(15.0, strongest_appearance * 0.25)
                appearance_matches = [
                    item
                    for item in appearance_matches
                    if float(item.get("score") or 0.0) >= appearance_floor
                ]
    else:
        intent, results = search_records(
            records,
            args.query,
            backend=args.backend,
            family=args.family,
            domain=args.domain,
            top_k=args.top_k,
        )
        appearance_matches = rank_style_matches(
            args.query, top_k=max(3, args.top_k), backend=args.backend
        )
        rejected_candidates = []
        clarification = None

    # Preserve v1 response fields while exposing the independent Scheme-v2
    # scientific and appearance channels on every query.
    style_matches = rank_style_matches(
        args.query, top_k=max(3, args.top_k), backend=args.backend
    )
    if schemes:
        scheme_by_id = {str(item.get("scheme_id")): item for item in schemes}
        filtered_style_matches = []
        for item in style_matches:
            if canonical_family(item.get("family")) == "decorative":
                continue
            targets = resolve_scheme_alias(str(item.get("style_id") or ""))
            if targets and all(
                scheme_eligibility(scheme_by_id.get(target, {}))
                in {"decorative", "decorative_result", "excluded", "nonplot", "prompt_non_code"}
                for target in targets
            ):
                continue
            filtered_style_matches.append(item)
        style_matches = filtered_style_matches
    if intent.get("requires_executable"):
        allowed_recipe_ids = {
            str(recipe_id)
            for result in results
            for recipe_id in ((result.get("executable_plan") or {}).get("recipe_ids") or [])
        }
        style_matches = [
            item
            for item in style_matches
            if allowed_recipe_ids & set(map(str, item.get("recipe_ids") or []))
        ]
    scientific_family = intent_retrieval_family(intent)
    atlas_family = (
        "composition"
        if scientific_family == "sample_level_composition"
        else canonical_family(scientific_family)
    )
    appearance = next(
        (
            item
            for item in appearance_matches
            if canonical_family(item.get("broad_family") or item.get("family")) == atlas_family
        ),
        None,
    )
    if appearance is None and appearance_matches:
        appearance = {
            **appearance_matches[0],
            "compatibility_note": "appearance match requires separate scientific compatibility review",
        }
    decision_bundle = {
        "scientific_primary": results[0].get("id") if results else None,
        "conservative_alternative": results[1].get("id") if len(results) > 1 else None,
        "appearance_alternative": (
            (appearance.get("scheme_id") or appearance.get("style_id")) if appearance else None
        ),
        "appearance_coverage_status": (
            (appearance.get("validation_tier") or appearance.get("coverage_status")) if appearance else None
        ),
        "merge_rule": "scientific fitness controls the primary; appearance is independently scored and cannot bypass hard gates",
    }
    if not args.include_code:
        for result in results:
            result.pop("code", None)

    if args.format == "markdown":
        rendered = markdown_results(intent, results, include_code=args.include_code)
        if clarification and clarification.get("needed"):
            rendered += "\n\n## Clarification required\n\n" + str(clarification.get("question") or clarification.get("reason"))
        if appearance:
            appearance_id = appearance.get("scheme_id") or appearance.get("style_id")
            rendered += (
                "\n\n## Visual appearance anchor\n\n"
                f"- `{appearance_id}` - {appearance.get('title') or appearance_id}\n"
                "- Scientific fitness still controls the primary recommendation."
            )
        print(rendered)
    else:
        serializable_intent = {
            key: sorted(value) if isinstance(value, set) else value
            for key, value in intent.items()
        }
        print(
            json.dumps(
                {
                    "intent": serializable_intent,
                    "results": results,
                    "scientific_decisions": results,
                    "appearance_matches": appearance_matches,
                    "rejected_candidates": rejected_candidates,
                    "clarification": clarification,
                    "style_matches": style_matches,
                    "decision_bundle": decision_bundle,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0 if results or appearance_matches or (clarification and clarification.get("needed")) else 3


def command_search(args: argparse.Namespace) -> int:
    records = ensure_catalog()
    intent, results = search_records(records, args.query, backend=args.backend, family=args.family, domain=args.domain, top_k=args.top_k)
    style_requested = bool(intent.get("visual_intents")) or bool(
        re.search(r"同款|样式|style|外观|喜欢|参考|素材库|图册|atlas|好看|高颜值|期刊", args.query, re.I)
    )
    style_matches = rank_style_matches(args.query, top_k=max(3, args.top_k), backend=args.backend) if style_requested else []
    scientific_family = intent_retrieval_family(intent)
    atlas_family = "composition" if scientific_family == "sample_level_composition" else canonical_family(scientific_family)
    appearance = next((item for item in style_matches if item.get("family") == atlas_family), None)
    if appearance is None and style_matches:
        appearance = {**style_matches[0], "compatibility_note": "appearance match requires separate scientific compatibility review"}
    decision_bundle = None
    if style_matches:
        decision_bundle = {
            "scientific_primary": results[0].get("id") if results else None,
            "conservative_alternative": results[1].get("id") if len(results) > 1 else None,
            "appearance_alternative": appearance.get("style_id") if appearance else None,
            "appearance_coverage_status": appearance.get("coverage_status") if appearance else None,
            "merge_rule": "scientific fitness controls the primary; the atlas card is an appearance/provenance anchor and keeps its coverage status",
        }
    if not args.include_code:
        for result in results:
            result.pop("code", None)
    if args.format == "markdown":
        rendered = markdown_results(intent, results, include_code=args.include_code)
        if appearance:
            rendered += (
                "\n\n## Visual atlas anchor\n\n"
                f"- `{appearance['style_id']}` — {appearance.get('title') or appearance['style_id']} "
                f"(`{appearance.get('coverage_status') or 'unrated'}`)\n"
                "- Scientific fitness still controls the primary recommendation; this card anchors appearance and provenance."
            )
        print(rendered)
    else:
        serializable_intent = {key: sorted(value) if isinstance(value, set) else value for key, value in intent.items()}
        print(json.dumps({
            "intent": serializable_intent,
            "results": results,
            "style_matches": style_matches,
            "decision_bundle": decision_bundle,
        }, ensure_ascii=False, indent=2))
    return 0 if results else 3


def resolve_scheme_alias(record_id: str) -> list[str]:
    if not SCHEME_ALIASES_PATH.exists():
        return []
    payload = load_json_object(SCHEME_ALIASES_PATH, {})
    mapping = payload.get("aliases") or payload.get("old_to_new") or payload.get("mappings") or payload
    if not isinstance(mapping, dict) or record_id not in mapping:
        return []
    value = mapping[record_id]
    if isinstance(value, dict):
        value = value.get("scheme_ids") or value.get("targets") or value.get("scheme_id") or []
    return [str(item) for item in as_list(value) if item]


def command_inspect_v2(args: argparse.Namespace) -> int:
    schemes = load_scheme_records()
    by_scheme = {str(item.get("scheme_id")): item for item in schemes}
    requested_id = str(args.id)
    aliases = resolve_scheme_alias(requested_id)
    if requested_id not in by_scheme and len(aliases) > 1:
        print(
            json.dumps(
                {
                    "record_type": "scheme_alias_migration",
                    "requested_id": requested_id,
                    "scheme_ids": aliases,
                    "note": "one-to-many aliases are not resolved arbitrarily; inspect a scheme_id explicitly",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    resolved_id = requested_id if requested_id in by_scheme else aliases[0] if len(aliases) == 1 else requested_id
    scheme = by_scheme.get(resolved_id)
    records = load_catalog_fast()
    if scheme:
        output = dict(scheme)
        output["requested_id"] = requested_id if requested_id != resolved_id else None
        if not args.include_lineage:
            output.pop("code_lineage", None)
        if not args.include_visual:
            output.pop("image_evidence", None)
            output.pop("visual_fingerprint", None)
        if args.include_code:
            source_ids = lineage_block_ids(scheme)
            output["source_blocks"] = [
                dict(item)
                for item in records
                if item.get("record_type") == "source_block" and str(item.get("id")) in source_ids
            ]
            candidate_modules: dict[str, Any] = {}
            for backend, relative in (scheme.get("candidate_code_path") or {}).items():
                path = (SKILL_ROOT / str(relative)).resolve()
                if SCHEME_CANDIDATE_ROOT.resolve() in path.parents and path.is_file():
                    candidate_modules[str(backend)] = {
                        "relative_path": str(relative).replace("\\", "/"),
                        "code": read_text(path),
                    }
            output["candidate_modules"] = candidate_modules
            metadata_path = SCHEME_CANDIDATE_ROOT / resolved_id / "metadata.json"
            if metadata_path.is_file():
                output["candidate_metadata"] = load_json_object(metadata_path, {})
        else:
            output.pop("code", None)
            output.pop("candidate_code", None)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    record = next((item for item in records if item.get("id") == requested_id), None)
    if not record and STYLE_ATLAS_PATH.exists():
        card = next(
            (item for item in load_jsonl(STYLE_ATLAS_PATH) if item.get("style_id") == requested_id),
            None,
        )
        if card:
            output = {"record_type": "style_card", **card}
            if args.include_code:
                source_ids = set(card.get("source_block_ids") or [])
                output["source_blocks"] = [
                    dict(item)
                    for item in records
                    if item.get("record_type") == "source_block" and item.get("id") in source_ids
                ]
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0
    if not record:
        print(json.dumps({"error": "record not found", "id": requested_id}, ensure_ascii=False), file=sys.stderr)
        return 4
    output = dict(record)
    if not args.include_code:
        output.pop("code", None)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    records = ensure_catalog()
    record = next((item for item in records if item.get("id") == args.id), None)
    if not record and STYLE_ATLAS_PATH.exists():
        card = next((item for item in load_jsonl(STYLE_ATLAS_PATH) if item.get("style_id") == args.id), None)
        if card:
            output = {"record_type": "style_card", **card}
            if args.include_code:
                source_ids = set(card.get("source_block_ids") or [])
                output["source_blocks"] = [
                    dict(item) for item in records
                    if item.get("record_type") == "source_block" and item.get("id") in source_ids
                ]
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0
    if not record:
        print(json.dumps({"error": "record not found", "id": args.id}, ensure_ascii=False), file=sys.stderr)
        return 4
    output = dict(record)
    if not args.include_code:
        output.pop("code", None)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def atlas_backend_values(card: dict[str, Any]) -> set[str]:
    """Normalize the optional backend/backends field of a style card."""
    raw = card.get("backends", card.get("backend", []))
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return set()
    aliases = {
        "py": "python",
        "python3": "python",
        "backend-neutral": "neutral",
        "backend_neutral": "neutral",
        "agnostic": "neutral",
        "both": "neutral",
        "any": "neutral",
    }
    values = set()
    for item in raw:
        value = normalize_text(item).replace(" ", "_")
        if value:
            values.add(aliases.get(value, value))
    return values


def atlas_field_match(query: str, query_tokens: set[str], value: Any) -> tuple[float, list[str]]:
    """Return a deterministic 0..1 match and the matched normalized terms."""
    if isinstance(value, (list, tuple, set)):
        text = " ".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = " ".join(f"{key} {item}" for key, item in value.items())
    else:
        text = str(value or "")
    normalized = normalize_text(text)
    if not normalized:
        return 0.0, []
    field_tokens = text_tokens(normalized)
    overlap = query_tokens & field_tokens
    token_score = len(overlap) / max(1, len(query_tokens)) if query_tokens else 0.0
    phrase_score = 1.0 if query and query in normalized else 0.0
    prefix_score = 0.9 if query and normalized.startswith(query) else 0.0
    return max(token_score, phrase_score, prefix_score), sorted(overlap, key=lambda item: (-len(item), item))


def score_atlas_card(card: dict[str, Any], query: str) -> tuple[float, list[str], set[str]]:
    """Score one style card using the same deterministic logic as the atlas CLI."""
    query = normalize_text(query)
    query_tokens = text_tokens(query)
    coverage_status = normalize_text(card.get("coverage_status")).replace(" ", "_")
    weights = {"title": 4.0, "keywords": 3.0, "analysis_use": 2.0, "description": 1.0}
    if not query:
        return ({
            "formal_exact": 1.0,
            "formal_family": 0.8,
            "source_only": 0.5,
            "code_only": 0.3,
            "visual_only": 0.3,
            "resource_only": 0.1,
            "full": 1.0,
            "complete": 1.0,
            "partial": 0.5,
        }.get(coverage_status, 0.0), [], set())

    score = 0.0
    matched_fields: list[str] = []
    matched_terms: set[str] = set()
    for field, weight in weights.items():
        field_score, terms = atlas_field_match(query, query_tokens, card.get(field))
        if field_score:
            score += weight * field_score
            matched_fields.append(field)
            matched_terms.update(terms)
    family_score, family_terms = atlas_field_match(query, query_tokens, card.get("family"))
    if family_score:
        score += 1.5 * family_score
        matched_fields.append("family")
        matched_terms.update(family_terms)
    detected_families = [canonical_family(item) for item in detect_terms(query, FAMILY_TERMS)]
    inferred_family = infer_primary_family(query, detected_families, detect_terms(query, VISUAL_TERMS))
    atlas_intent_family = "composition" if inferred_family == "sample_level_composition" else inferred_family
    if canonical_family(card.get("family")) == atlas_intent_family:
        score += 0.9
        matched_fields.append("intent_family")
    if score <= 0:
        return 0.0, matched_fields, matched_terms
    score += {
        "formal_exact": 1.25,
        "formal_family": 0.45,
        "source_only": 0.1,
    }.get(coverage_status, 0.0)
    return score, matched_fields, matched_terms


def rank_style_matches(query: str, top_k: int = 5, backend: str | None = None) -> list[dict[str, Any]]:
    """Return compact atlas matches for integration with scientific search."""
    if not STYLE_ATLAS_PATH.exists() or top_k < 1:
        return []
    requested_backend = normalize_text(backend).replace(" ", "_") if backend else None
    ranked: list[tuple[float, str, dict[str, Any], list[str], set[str]]] = []
    for card in load_jsonl(STYLE_ATLAS_PATH):
        backends = atlas_backend_values(card)
        if requested_backend and (not backends or (requested_backend not in backends and "neutral" not in backends)):
            continue
        score, fields, terms = score_atlas_card(card, query)
        if score <= 0:
            continue
        ranked.append((score, str(card.get("style_id")), card, fields, terms))
    ranked.sort(key=lambda item: (-item[0], normalize_text(item[2].get("title")), item[1]))
    summaries: list[dict[str, Any]] = []
    for score, style_id, card, fields, terms in ranked[:top_k]:
        summaries.append({
            "style_id": style_id,
            "family": canonical_family(card.get("family")),
            "title": card.get("title"),
            "analysis_use": card.get("analysis_use"),
            "sample_image": card.get("sample_image"),
            "source_article_id": card.get("source_article_id"),
            "source_block_ids": card.get("source_block_ids") or [],
            "recipe_ids": card.get("recipe_ids") or [],
            "coverage_status": card.get("coverage_status"),
            "why_match": (
                "matched " + ", ".join(dict.fromkeys(fields))
                + ("; terms=" + ", ".join(sorted(terms, key=lambda item: (-len(item), item))[:8]) if terms else "")
                + f"; score={score:.3f}"
            ),
        })
    return summaries


def command_atlas_v2(args: argparse.Namespace) -> int:
    """Browse Scheme-v2 cards, falling back to the v1 style atlas."""
    schemes = load_scheme_records()
    if not schemes:
        return command_atlas(args)
    if args.top_k < 1:
        raise ValueError("--top-k must be at least 1")

    requested_family = canonical_family(args.family) if args.family else None
    requested_subtype = normalize_text(args.subtype).replace(" ", "_") if args.subtype else None
    requested_method = normalize_analysis_method(args.method) if args.method else None
    requested_review = normalize_text(args.review_status).replace(" ", "_") if args.review_status else None
    requested_coverage = normalize_text(args.coverage).replace(" ", "_") if args.coverage else None
    requested_backend = normalize_text(args.backend).replace(" ", "_") if args.backend else None
    query = args.query or ""
    suppress_decorative_scientific_query = (
        args.scope == "scientific" and positive_decorative_intent(query)
    )
    ranked: list[tuple[float, str, dict[str, Any], dict[str, float], list[str]]] = []

    for record in schemes:
        if suppress_decorative_scientific_query:
            continue
        if not scheme_scope_matches(record, args.scope):
            continue
        family = canonical_family(record.get("broad_family"))
        subtype = str(record.get("geometry_subtype") or "unknown")
        method = scheme_analysis_method(record)
        review = scheme_review_status(record)
        tier = scheme_validation_tier(record)
        if requested_family and family != requested_family:
            continue
        if requested_subtype and subtype != requested_subtype:
            continue
        if requested_method and method != requested_method:
            continue
        if requested_review and review != requested_review:
            continue
        if requested_coverage and tier != requested_coverage:
            continue
        backends = {
            normalize_text(item).replace(" ", "_")
            for item in as_list(record.get("backends", record.get("backend")))
            if item
        }
        if requested_backend and backends and requested_backend not in backends and "neutral" not in backends:
            continue
        score, breakdown, reasons = scheme_appearance_score(record, query)
        if query and score <= 0:
            continue
        ranked.append((score, str(record.get("scheme_id")), record, breakdown, reasons))

    ranked.sort(key=lambda item: (-item[0], normalize_text(item[2].get("title")), item[1]))
    results: list[dict[str, Any]] = []
    for score, scheme_id, record, breakdown, reasons in ranked[: args.top_k]:
        results.append(
            {
                "scheme_id": scheme_id,
                "id": scheme_id,
                "title": record.get("title"),
                "eligibility": scheme_eligibility(record),
                "broad_family": record.get("broad_family"),
                "geometry_subtype": record.get("geometry_subtype"),
                "analysis_method": scheme_analysis_method(record),
                "review_status": scheme_review_status(record),
                "validation_tier": scheme_validation_tier(record),
                "backend": record.get("backend"),
                "backends": record.get("backends") or as_list(record.get("backend")),
                "image_evidence": record.get("image_evidence"),
                "score": score,
                "score_breakdown": breakdown,
                "why_match": "; ".join(reasons) or "Scheme atlas browse order",
            }
        )

    filters = {
        "scope": args.scope,
        "family": args.family,
        "subtype": args.subtype,
        "method": args.method,
        "review_status": args.review_status,
        "coverage": args.coverage,
        "backend": args.backend,
    }
    if args.format == "json":
        print(
            json.dumps(
                {"query": args.query, "filters": filters, "count": len(results), "results": results},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        if not results:
            print("No matching visualization schemes.")
        for position, result in enumerate(results, 1):
            print(
                f"{position}. {result['title'] or result['scheme_id']} "
                f"[{result['broad_family']}/{result['geometry_subtype']}] "
                f"({result['eligibility']}; {result['review_status']})"
            )
            print(f"   scheme_id: {result['scheme_id']}")
            print(f"   analysis_method: {result['analysis_method']}")
            print(f"   why_match: {result['why_match']}")
    return 0


def command_atlas(args: argparse.Namespace) -> int:
    """Browse and rank the optional style atlas without embeddings or network I/O."""
    override = os.environ.get("PLOT_CODE_RETRIEVER_STYLE_ATLAS")
    atlas_path = Path(override).expanduser().resolve() if override else STYLE_ATLAS_PATH
    if not atlas_path.exists():
        raise FileNotFoundError(
            f"Style atlas is missing: {atlas_path}. "
            "Create references/style-atlas.jsonl or set PLOT_CODE_RETRIEVER_STYLE_ATLAS."
        )
    if not atlas_path.is_file():
        raise ValueError(f"Style atlas path is not a file: {atlas_path}")
    if args.top_k < 1:
        raise ValueError("--top-k must be at least 1")

    cards = load_jsonl(atlas_path)
    query = normalize_text(args.query or "")
    requested_family = canonical_family(args.family) if args.family else None
    requested_coverage = normalize_text(args.coverage).replace(" ", "_") if args.coverage else None
    requested_backend = normalize_text(args.backend).replace(" ", "_") if args.backend else None
    ranked: list[tuple[float, str, dict[str, Any]]] = []

    for index, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            raise ValueError(f"Style atlas record {index} must be a JSON object")
        style_id = str(card.get("style_id") or card.get("id") or "").strip()
        if not style_id:
            raise ValueError(f"Style atlas record {index} is missing style_id")
        family = canonical_family(card.get("family"))
        coverage_status = normalize_text(card.get("coverage_status")).replace(" ", "_")
        backends = atlas_backend_values(card)
        if requested_family and family != requested_family:
            continue
        if requested_coverage and coverage_status != requested_coverage:
            continue
        if requested_backend and (not backends or (requested_backend not in backends and "neutral" not in backends)):
            continue

        score, matched_fields, matched_terms = score_atlas_card(card, query)
        if query and score <= 0:
            continue

        reasons = []
        if matched_fields:
            reasons.append("matched " + ", ".join(dict.fromkeys(matched_fields)))
        if matched_terms:
            reasons.append("terms=" + ", ".join(sorted(matched_terms, key=lambda item: (-len(item), item))[:8]))
        if requested_family:
            reasons.append(f"family={family}")
        if requested_coverage:
            reasons.append(f"coverage={coverage_status}")
        if requested_backend:
            reasons.append(f"backend={requested_backend}")
        if not reasons:
            reasons.append("atlas browse order")

        source_block_ids = card.get("source_block_ids") or []
        recipe_ids = card.get("recipe_ids") or []
        if isinstance(source_block_ids, str):
            source_block_ids = [source_block_ids]
        if isinstance(recipe_ids, str):
            recipe_ids = [recipe_ids]
        output = {
            "style_id": style_id,
            "family": family,
            "title": card.get("title"),
            "analysis_use": card.get("analysis_use"),
            "sample_image": card.get("sample_image"),
            "source_article_id": card.get("source_article_id"),
            "source_block_ids": source_block_ids,
            "recipe_ids": recipe_ids,
            "coverage_status": card.get("coverage_status"),
            "why_match": "; ".join(reasons) + f"; score={score:.3f}",
        }
        ranked.append((score, style_id, output))

    ranked.sort(key=lambda item: (-item[0], normalize_text(item[2].get("title")), item[1]))
    results = [item[2] for item in ranked[: args.top_k]]
    if args.format == "json":
        print(json.dumps({
            "query": args.query,
            "filters": {"family": args.family, "coverage": args.coverage, "backend": args.backend},
            "count": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No matching style cards.")
        for position, result in enumerate(results, 1):
            print(f"{position}. {result['title'] or result['style_id']} [{result['family']}] ({result['coverage_status'] or 'unrated'})")
            print(f"   style_id: {result['style_id']}")
            print(f"   analysis_use: {result['analysis_use'] or 'not declared'}")
            print(f"   sample_image: {result['sample_image'] or 'not available'}")
            print(f"   source_article_id: {result['source_article_id'] or 'not declared'}")
            print(f"   source_block_ids: {', '.join(map(str, result['source_block_ids'])) or 'none'}")
            print(f"   recipe_ids: {', '.join(map(str, result['recipe_ids'])) or 'none'}")
            print(f"   why_match: {result['why_match']}")
    return 0


COMPONENT_ORDER = {"semantic_modifier": 2, "aesthetic_modifier": 3, "layout": 4, "export": 5}


def normalized_contract_values(values: Iterable[Any]) -> set[str]:
    return {normalize_text(value).replace(" ", "") for value in values if value is not None}


def compatible(
    base: dict[str, Any],
    component: dict[str, Any],
    pipeline_objects: set[str],
    pipeline_capabilities: set[str],
    selected: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if base.get("backend") != component.get("backend"):
        reasons.append("backend mismatch")
    if component.get("kind") not in COMPONENT_ORDER:
        reasons.append(f"invalid component kind: {component.get('kind')}")

    base_compat = base.get("compatible_with") or {}
    if isinstance(base_compat, dict):
        base_allowed_ids = set(base_compat.get("ids") or [])
        base_allowed_kinds = set(base_compat.get("kinds") or [])
        if base_allowed_ids and component.get("id") not in base_allowed_ids:
            reasons.append("component id not allowed by base")
        if base_allowed_kinds and component.get("kind") not in base_allowed_kinds:
            reasons.append("component kind not allowed by base")

    component_compat = component.get("compatible_with") or {}
    if isinstance(component_compat, dict):
        allowed_ids = set(component_compat.get("ids") or [])
        allowed_kinds = set(component_compat.get("kinds") or [])
        if allowed_ids and base.get("id") not in allowed_ids:
            reasons.append("base id not allowed by component")
        if allowed_kinds and base.get("kind") not in allowed_kinds:
            reasons.append("base kind not allowed by component")

    participants = [base, *selected]
    participant_ids = {item.get("id") for item in participants}
    component_conflicts = set(component.get("conflicts") or [])
    if participant_ids & component_conflicts:
        reasons.append("component declares an explicit conflict")
    for item in participants:
        if component.get("id") in set(item.get("conflicts") or []):
            reasons.append(f"explicit conflict declared by {item.get('id')}")

    required_objects = normalized_contract_values((component.get("requires") or {}).get("object_types") or [])
    if required_objects and pipeline_objects and not required_objects & pipeline_objects:
        reasons.append(
            "object contract mismatch: pipeline provides "
            + ", ".join(sorted(pipeline_objects))
            + "; component requires "
            + ", ".join(sorted(required_objects))
        )
    required_capabilities = set((component.get("requires") or {}).get("capabilities") or [])
    if component.get("kind") == "semantic_modifier" and not required_capabilities.issubset(pipeline_capabilities):
        missing = sorted(required_capabilities - pipeline_capabilities)
        reasons.append("missing semantic capabilities: " + ", ".join(missing))
    return not reasons, reasons


def command_compose(args: argparse.Namespace) -> int:
    recipes = {item.get("id"): item for item in ensure_catalog() if item.get("record_type") == "recipe"}
    base = recipes.get(args.base_id)
    if not base:
        print(json.dumps({"error": "base recipe not found", "id": args.base_id}, ensure_ascii=False), file=sys.stderr)
        return 4
    if base.get("kind") != "base_recipe":
        print(json.dumps({"error": "--base-id must identify a base_recipe", "id": args.base_id, "kind": base.get("kind")}, ensure_ascii=False), file=sys.stderr)
        return 5
    if base.get("backend") != args.backend:
        print(json.dumps({"error": "selected backend differs from base recipe"}, ensure_ascii=False), file=sys.stderr)
        return 5
    adapter = None
    if args.adapter_id:
        adapter = recipes.get(args.adapter_id)
        if not adapter:
            print(json.dumps({"error": "adapter recipe not found", "id": args.adapter_id}, ensure_ascii=False), file=sys.stderr)
            return 4
        adapter_errors: list[str] = []
        if adapter.get("kind") != "adapter":
            adapter_errors.append("--adapter-id must identify an adapter")
        if adapter.get("backend") != args.backend:
            adapter_errors.append("adapter backend mismatch")
        adapter_compat = adapter.get("compatible_with") or {}
        allowed_ids = set(adapter_compat.get("ids") or []) if isinstance(adapter_compat, dict) else set()
        allowed_kinds = set(adapter_compat.get("kinds") or []) if isinstance(adapter_compat, dict) else set()
        if allowed_ids and base.get("id") not in allowed_ids:
            adapter_errors.append("base id not allowed by adapter")
        if allowed_kinds and base.get("kind") not in allowed_kinds:
            adapter_errors.append("base kind not allowed by adapter")
        adapter_objects = normalized_contract_values((adapter.get("provides") or {}).get("object_types") or [])
        base_objects = normalized_contract_values((base.get("requires") or {}).get("object_types") or [])
        if base_objects and not adapter_objects & base_objects:
            adapter_errors.append("adapter output object does not satisfy base input")
        adapter_capabilities = set((adapter.get("provides") or {}).get("capabilities") or [])
        base_capabilities = set((base.get("requires") or {}).get("capabilities") or [])
        if not base_capabilities.issubset(adapter_capabilities):
            adapter_errors.append("adapter is missing base capabilities: " + ", ".join(sorted(base_capabilities - adapter_capabilities)))
        if adapter_errors:
            print(json.dumps({"error": "incompatible adapter", "details": adapter_errors}, ensure_ascii=False, indent=2), file=sys.stderr)
            return 6
    components: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    pipeline_objects = normalized_contract_values((base.get("provides") or {}).get("object_types") or [])
    pipeline_capabilities = set((base.get("provides") or {}).get("capabilities") or [])
    last_order = 1
    for component_id in args.modifier or []:
        component = recipes.get(component_id)
        if not component:
            errors.append({"id": component_id, "reason": "not found"})
            continue
        component_order = COMPONENT_ORDER.get(component.get("kind"), -1)
        if component_order < last_order:
            errors.append({"id": component_id, "reason": "component order must be semantic_modifier -> aesthetic_modifier -> layout -> export"})
            continue
        ok, reasons = compatible(base, component, pipeline_objects, pipeline_capabilities, components)
        if not ok:
            errors.append({"id": component_id, "reason": "; ".join(reasons)})
        else:
            components.append(component)
            last_order = component_order
            provided_objects = normalized_contract_values((component.get("provides") or {}).get("object_types") or [])
            if provided_objects:
                pipeline_objects = provided_objects
            pipeline_capabilities.update((component.get("provides") or {}).get("capabilities") or [])
    if errors:
        print(json.dumps({"error": "incompatible composition", "details": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 6
    chain = [*([adapter] if adapter else []), base, *components]
    source_fingerprints = sorted({
        fingerprint
        for item in chain
        for fingerprint in ((item.get("lineage") or {}).get("source_fingerprints") or [])
    })
    unbound_parameters = [
        {
            "component_id": item.get("id"),
            "name": parameter.get("name"),
            "type": parameter.get("type"),
            "required": parameter.get("required"),
            "default": parameter.get("default"),
            "allowed": parameter.get("allowed"),
        }
        for item in chain
        for parameter in (item.get("parameters") or [])
    ]
    candidate = {
        "schema_version": "1.0",
        "id": "candidate-" + hashlib.sha256("|".join(item["id"] for item in chain).encode()).hexdigest()[:12],
        "kind": "candidate",
        "backend": base.get("backend"),
        "family": base.get("family"),
        "lineage": {
            "parent_id": base.get("id"),
            "components": [{"id": item.get("id")} for item in [*([adapter] if adapter else []), *components]],
            "source_fingerprints": source_fingerprints,
        },
        "composition_order": [item.get("id") for item in chain],
        "parameter_bindings": {},
        "unbound_parameters": unbound_parameters,
        "component_interfaces": [
            {"id": item.get("id"), "kind": item.get("kind"), "requires": item.get("requires"), "provides": item.get("provides")}
            for item in chain
        ],
        "requires": {
            "variables": sorted({value for item in chain for value in ((item.get("requires") or {}).get("variables") or [])}),
            "packages": sorted({value for item in chain for value in ((item.get("requires") or {}).get("packages") or [])}),
        },
        "provides": {"object_types": sorted(pipeline_objects), "capabilities": sorted(pipeline_capabilities)},
        "validation": {"tier": "reference-only", "checks": {"schema": "pass", "syntax": "pending", "safety": "pending", "fixture": "pending", "render": "pending", "visual": "pending", "semantic": "pending", "provenance": "pending"}},
        "component_code": [{"id": item.get("id"), "kind": item.get("kind"), "code": item.get("code")} for item in chain],
        "note": "Materialization pending.",
    }
    try:
        from recipe_runtime import build_chain as build_runtime_chain
        from recipe_runtime import materialize_chain

        runtime_chain = build_runtime_chain(
            base_id=str(args.base_id),
            backend=str(args.backend),
            adapter_id=str(args.adapter_id) if args.adapter_id else None,
            modifier_ids=[str(value) for value in (args.modifier or [])],
        )
        materialized = materialize_chain(runtime_chain)
    except (FileNotFoundError, ImportError, SyntaxError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": "composition materialization failed",
                    "details": f"{type(exc).__name__}: {exc}",
                    "composition_order": [item.get("id") for item in chain],
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 7
    preflight_ok = bool((materialized.get("preflight") or {}).get("ok"))
    candidate.update(
        {
            "schema_version": "2.0",
            "entrypoint": "build_plot",
            "code": materialized.get("code"),
            "component_entrypoints": materialized.get("component_entrypoints") or {},
            "preflight": materialized.get("preflight") or {},
            "status": "materialized_candidate" if preflight_ok else "materialized_preflight_blocked",
            "promotable": False,
            "validation": {
                "tier": "parse-verified" if preflight_ok else "blocked-preflight",
                "checks": {
                    "schema": "pass",
                    "syntax": "pass",
                    "safety": "pass",
                    "fixture": "pending",
                    "render": "pending",
                    "visual": "pending_native_review",
                    "semantic": "pending",
                    "provenance": "pass",
                },
            },
            "note": (
                "Callable backend-pure build_plot materialized through declared component interfaces; "
                "execution still requires input/dependency preflight and native visual review."
            ),
        }
    )
    if args.save_candidate:
        candidate_dir = CANDIDATES_ROOT / candidate["id"]
        if candidate_dir.exists():
            print(json.dumps({"error": "candidate plan already exists", "id": candidate["id"]}, ensure_ascii=False), file=sys.stderr)
            return 11
        candidate_dir.mkdir(parents=True)
        code_path = candidate_dir / ("candidate.py" if args.backend == "python" else "candidate.R")
        code_path.write_text(str(candidate["code"]), encoding="utf-8", newline="\n")
        candidate["code_path"] = rel_posix(code_path)
        candidate["code_sha256"] = hashlib.sha256(code_path.read_bytes()).hexdigest()
        write_json(candidate_dir / "composition.json", candidate)
        candidate["saved_to"] = rel_posix(candidate_dir / "composition.json")
        candidate["next_gate"] = "Add stable recipe.json, fixture execution, exact render, visual-review-state.json, semantic QA, and user-approved promotion."
    print(json.dumps(candidate, ensure_ascii=False, indent=2))
    return 0


def parse_runtime_json(value: str | None) -> dict[str, Any]:
    """Read an inline JSON object or a JSON file for deterministic runtime parameters."""
    if not value:
        return {}
    path = Path(value).expanduser()
    parsed = load_json_object(path, {}) if path.is_file() else json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("runtime parameters must be a JSON object")
    return parsed


def command_preflight(args: argparse.Namespace) -> int:
    """Check a formal Recipe or declared composition before any execution."""
    from recipe_runtime import build_chain as build_runtime_chain
    from recipe_runtime import load_recipe as load_runtime_recipe
    from recipe_runtime import preflight_chain

    if args.recipe_id:
        recipe = load_runtime_recipe(str(args.recipe_id))
        if args.backend and recipe.get("backend") != args.backend:
            raise ValueError(
                f"selected backend {args.backend} differs from Recipe backend {recipe.get('backend')}"
            )
        chain = [recipe]
    else:
        if not args.backend:
            raise ValueError("--backend is required with --base-id")
        chain = build_runtime_chain(
            base_id=str(args.base_id),
            backend=str(args.backend),
            adapter_id=str(args.adapter_id) if args.adapter_id else None,
            modifier_ids=[str(value) for value in (args.modifier or [])],
        )
    result = preflight_chain(chain)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 8


def run_render_safely(operation, backend: str | None) -> dict[str, Any]:
    """Convert expected Recipe/runtime failures to the structured blocked contract."""
    try:
        return operation()
    except Exception as exc:
        # Recipe/user-runtime failures should remain machine-readable blockers.
        # KeyboardInterrupt and SystemExit inherit BaseException and therefore
        # still propagate instead of being silently swallowed.
        return {
            "ok": False,
            "status": "blocked",
            "stage": "runtime",
            "backend": backend,
            "error_type": type(exc).__name__,
            "reason": str(exc),
            "partial_artifacts": [],
        }


def command_render(args: argparse.Namespace) -> int:
    """Run the selected backend and optionally initialize the native-review state."""
    from recipe_runtime import build_chain as build_runtime_chain
    from recipe_runtime import load_recipe as load_runtime_recipe
    from recipe_runtime import render_python_chain, render_python_recipe
    from recipe_runtime import render_r_chain, render_r_recipe

    parameters = parse_runtime_json(args.params_json)
    requested_backend = str(args.backend) if args.backend else None
    if args.recipe_id:
        recipe = load_runtime_recipe(str(args.recipe_id))
        backend = str(recipe.get("backend"))
        if requested_backend and requested_backend != backend:
            raise ValueError(
                f"selected backend {requested_backend} differs from Recipe backend {backend}"
            )
        if backend == "python":
            result = run_render_safely(
                lambda: render_python_recipe(
                    str(args.recipe_id), args.input, args.output_dir, parameters,
                    args.width_mm, args.height_mm, args.dpi,
                ),
                backend,
            )
        elif backend == "r":
            result = run_render_safely(
                lambda: render_r_recipe(
                    str(args.recipe_id), args.input, args.output_dir, parameters,
                    args.width_mm, args.height_mm, args.dpi, args.timeout_seconds,
                ),
                backend,
            )
        else:
            raise ValueError(f"unsupported Recipe backend: {backend}")
    else:
        if not requested_backend:
            raise ValueError("--backend is required with --base-id")
        backend = requested_backend
        chain = build_runtime_chain(
            base_id=str(args.base_id),
            backend=backend,
            adapter_id=str(args.adapter_id) if args.adapter_id else None,
            modifier_ids=[str(value) for value in (args.modifier or [])],
        )
        if backend == "python":
            result = run_render_safely(
                lambda: render_python_chain(
                    chain, args.input, args.output_dir, parameters,
                    args.width_mm, args.height_mm, args.dpi,
                ),
                backend,
            )
        else:
            result = run_render_safely(
                lambda: render_r_chain(
                    chain, args.input, args.output_dir, parameters,
                    args.width_mm, args.height_mm, args.dpi, args.timeout_seconds,
                ),
                backend,
            )

    rendered = bool(result.get("ok", True)) and result.get("status") == "rendered_pending_native_review"
    if rendered and args.review_state:
        from visual_review_controller import (
            initialize_state,
            native_review_template,
            register_render,
            write_state,
        )

        state_path = Path(args.review_state).expanduser().resolve()
        if state_path.exists():
            raise ValueError(f"review state already exists; refusing to overwrite: {state_path}")
        code_source = result.get("code_path") or ("sha256:" + str(result.get("code_sha256") or ""))
        runtime_parameters_path = result.get("parameters_path")
        params_path = Path(str(runtime_parameters_path)).expanduser() if runtime_parameters_path else None
        if params_path and params_path.is_file():
            input_source = str(params_path.resolve())
        else:
            parameter_digest = hashlib.sha256(
                json.dumps(parameters, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            input_source = "sha256:" + parameter_digest
        identity = str(result.get("recipe_id") or result.get("candidate_id") or "plot")
        review_id = args.review_id or f"review-{identity}-{str(result.get('input_sha256') or '')[:12]}"
        state = initialize_state(
            review_id=review_id,
            backend=backend,
            data_source=args.input,
            code_source=code_source,
            input_source=input_source,
            scheme_id=args.scheme_id,
            intent={"parameters": parameters, "composition_order": result.get("composition_order") or []},
        )
        state = register_render(
            state,
            round_number=1,
            original_path=str((result.get("original") or {}).get("path")),
            final_path=str((result.get("final") or {}).get("path")),
            parameter_diff=[],
        )
        write_state(state_path, state)
        template_path = state_path.with_name(state_path.stem + "-native-review-template.json")
        write_state(template_path, native_review_template(state))
        result["visual_review"] = {
            "state": str(state_path),
            "native_review_template": str(template_path),
            "status": "awaiting_native_review",
            "controller_capability": "state_and_policy_only_no_visual_model",
            "next_step": "Open original and final PNG with native image viewing, fill the template from visible pixels, then ingest it with visual_review_controller.py.",
        }
    elif rendered:
        result["visual_review"] = {
            "status": "not_initialized",
            "controller_capability": "state_and_policy_only_no_visual_model",
            "next_step": "Re-run with --review-state, then open both PNG artifacts with native image viewing.",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if rendered else 8


def find_image_record(record_id: str) -> dict[str, Any] | None:
    return next((item for item in ensure_catalog() if item.get("id") == record_id and item.get("record_type") == "image"), None)


def command_image_meta(args: argparse.Namespace) -> int:
    if args.id:
        record = find_image_record(args.id)
        if not record:
            print(json.dumps({"error": "image record not found", "id": args.id}, ensure_ascii=False), file=sys.stderr)
            return 4
        path = SKILL_ROOT / record["path"]
        output = {"id": args.id, "role": record.get("role"), "reviewed": record.get("reviewed"), "path": record.get("path"), "metadata": image_metadata(path)}
    else:
        path = Path(args.path).resolve()
        output = {"path": str(path), "metadata": image_metadata(path)}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["metadata"].get("readable") else 7


def locate_rscript() -> str | None:
    found = shutil.which("Rscript")
    if found:
        return found
    candidates = [
        Path(r"C:\Program Files\R\R-4.5.3\bin\Rscript.exe"),
        Path(r"C:\Program Files\R\R-4.5.3\bin\x64\Rscript.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    base = Path(r"C:\Program Files\R")
    if base.exists():
        matches = sorted(base.glob("R-*\\bin\\Rscript.exe"), reverse=True)
        if matches:
            return str(matches[0])
    return None


def validate_recipe(
    metadata_path: Path,
    run_r_parse: bool = True,
    catalog_by_id: dict[str, dict[str, Any]] | None = None,
    recipe_ids: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        recipe = json.loads(read_text(metadata_path))
    except Exception as exc:
        return [f"{metadata_path}: invalid JSON: {exc}"], warnings
    required = {
        "schema_version", "id", "name", "description", "kind", "family", "backend", "tags",
        "requires", "provides", "compatible_with", "conflicts", "parameters", "lineage",
        "semantic_card", "visual_fingerprint", "source", "validation", "files",
    }
    missing = sorted(required - set(recipe))
    if missing:
        errors.append(f"{recipe.get('id', metadata_path.parent.name)}: missing fields {missing}")
    if recipe.get("backend") not in {"r", "python"}:
        errors.append(f"{recipe.get('id')}: invalid backend")
    if recipe.get("schema_version") != "1.0":
        errors.append(f"{recipe.get('id')}: unsupported schema_version")
    allowed_kinds = {"adapter", "base_recipe", "semantic_modifier", "aesthetic_modifier", "layout", "export"}
    if recipe.get("kind") not in allowed_kinds:
        errors.append(f"{recipe.get('id')}: invalid kind {recipe.get('kind')}")
    if not re.fullmatch(r"[a-z0-9-]+", str(recipe.get("id", ""))):
        errors.append(f"{recipe.get('id')}: invalid id")
    for contract_name in ("requires", "provides", "compatible_with"):
        if not isinstance(recipe.get(contract_name), dict):
            errors.append(f"{recipe.get('id')}: {contract_name} must be an object")
    if not isinstance(recipe.get("conflicts"), list) or not isinstance(recipe.get("parameters"), list):
        errors.append(f"{recipe.get('id')}: conflicts and parameters must be arrays")
    parameter_names: list[str] = []
    for parameter in recipe.get("parameters") or []:
        if not isinstance(parameter, dict) or not {"name", "type", "required", "default", "allowed", "description"}.issubset(parameter):
            errors.append(f"{recipe.get('id')}: invalid parameter declaration")
            continue
        parameter_names.append(str(parameter.get("name") or ""))
    duplicate_parameters = sorted(
        {name for name in parameter_names if name and parameter_names.count(name) > 1}
    )
    if duplicate_parameters:
        errors.append(f"{recipe.get('id')}: duplicate parameters {duplicate_parameters}")
    input_parameter = recipe.get("input_parameter")
    if input_parameter is not None and str(input_parameter) not in parameter_names:
        errors.append(
            f"{recipe.get('id')}: input_parameter must name a declared parameter"
        )
    visual_revision = recipe.get("visual_revision")
    if visual_revision is not None:
        if not isinstance(visual_revision, dict):
            errors.append(f"{recipe.get('id')}: visual_revision must be an object")
        else:
            if visual_revision.get("parameter_policy") != "declared-only":
                errors.append(
                    f"{recipe.get('id')}: visual_revision.parameter_policy must be declared-only"
                )
            if visual_revision.get("max_rounds") != 3:
                errors.append(f"{recipe.get('id')}: visual_revision.max_rounds must be 3")
            issue_map = visual_revision.get("issue_parameter_map")
            if not isinstance(issue_map, dict):
                errors.append(
                    f"{recipe.get('id')}: visual_revision.issue_parameter_map must be an object"
                )
            else:
                issue_registry = load_json_object(
                    SKILL_ROOT / "references" / "visual-issue-actions.json", {}
                ).get("issues") or {}
                for issue_id, names in issue_map.items():
                    if issue_id not in issue_registry:
                        errors.append(
                            f"{recipe.get('id')}: unknown visual issue code {issue_id}"
                        )
                    if not isinstance(names, list) or not names:
                        errors.append(
                            f"{recipe.get('id')}: visual issue {issue_id} must map to a non-empty parameter list"
                        )
                        continue
                    undeclared = sorted(
                        str(name) for name in names if str(name) not in parameter_names
                    )
                    if undeclared:
                        errors.append(
                            f"{recipe.get('id')}: visual issue {issue_id} maps to undeclared parameters {undeclared}"
                        )

    semantic_required = {
        "questions_answered", "evidence_roles", "units", "data_topologies", "required_variables",
        "transformations", "visual_channels", "supports_claims", "does_not_support",
        "required_statistics", "misread_risks", "preferred_companions", "safer_alternatives",
    }
    semantic = recipe.get("semantic_card") or {}
    semantic_missing = sorted(semantic_required - set(semantic))
    if semantic_missing:
        errors.append(f"{recipe.get('id')}: incomplete SemanticCard {semantic_missing}")
    fingerprint_required = {
        "family", "panels", "panel_structure", "channels", "legend_mode", "information_density",
        "strengths", "risks", "final_size_behavior", "evidence_level", "reviewed",
    }
    visual_fingerprint = recipe.get("visual_fingerprint") or {}
    fingerprint_missing = sorted(fingerprint_required - set(visual_fingerprint))
    if fingerprint_missing:
        errors.append(f"{recipe.get('id')}: incomplete VisualFingerprint {fingerprint_missing}")

    files = recipe.get("files") or {}
    for required_file in ("code", "example"):
        if not files.get(required_file):
            errors.append(f"{recipe.get('id')}: missing files.{required_file}")
    resolved_files: dict[str, Path] = {}
    for label, relative in files.items():
        if relative in {None, ""}:
            continue
        relative_path = Path(str(relative))
        if relative_path.is_absolute():
            errors.append(f"{recipe.get('id')}: absolute files.{label} path is forbidden")
            continue
        resolved = (metadata_path.parent / relative_path).resolve()
        try:
            resolved.relative_to(SKILL_ROOT.resolve())
        except ValueError:
            errors.append(f"{recipe.get('id')}: files.{label} escapes the skill root")
            continue
        resolved_files[label] = resolved
        if not resolved.exists():
            errors.append(f"{recipe.get('id')}: missing {label} file {relative}")

    for label in ("code", "example"):
        code_path = resolved_files.get(label)
        if not code_path or not code_path.exists():
            continue
        code = read_text(code_path)
        for name, pattern in SAFETY_PATTERNS.items():
            if pattern.search(code):
                errors.append(f"{recipe.get('id')}: unsafe pattern {name} in {label}")
        if recipe.get("backend") == "python":
            if code_path.suffix.lower() != ".py":
                errors.append(f"{recipe.get('id')}: Python {label} must use .py")
            try:
                ast.parse(code, filename=str(code_path))
            except SyntaxError as exc:
                errors.append(f"{recipe.get('id')}: Python syntax in {label}: {exc}")
        elif recipe.get("backend") == "r" and run_r_parse:
            if code_path.suffix.lower() != ".r":
                errors.append(f"{recipe.get('id')}: R {label} must use .R")
            rscript = locate_rscript()
            if rscript:
                process = subprocess.run(
                    [rscript, "-e", "parse(file=commandArgs(trailingOnly=TRUE)[1])", str(code_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if process.returncode:
                    errors.append(f"{recipe.get('id')}: R syntax failed in {label}: {process.stderr.strip()[-400:]}")
            else:
                warnings.append(f"{recipe.get('id')}: Rscript unavailable; {label} syntax not checked")

    preview = resolved_files.get("preview")
    if preview and preview.exists() and not image_metadata(preview).get("readable"):
        errors.append(f"{recipe.get('id')}: preview is unreadable")

    lineage = recipe.get("lineage") or {}
    if not isinstance(lineage, dict) or "parent_id" not in lineage or "components" not in lineage or "source_fingerprints" not in lineage:
        errors.append(f"{recipe.get('id')}: incomplete lineage")
    if recipe_ids:
        parent_id = lineage.get("parent_id")
        if parent_id and parent_id not in recipe_ids:
            errors.append(f"{recipe.get('id')}: unresolved lineage parent {parent_id}")
        for compatible_id in (recipe.get("compatible_with") or {}).get("ids", []):
            if compatible_id not in recipe_ids:
                errors.append(f"{recipe.get('id')}: unresolved compatible id {compatible_id}")

    source = recipe.get("source") or {}
    if source.get("status") not in {"original", "internal_distillation", "derived", "unknown"}:
        errors.append(f"{recipe.get('id')}: invalid source status")
    source_fingerprints = set(lineage.get("source_fingerprints") or [])
    if source.get("status") == "internal_distillation" and not source_fingerprints:
        errors.append(f"{recipe.get('id')}: internal distillation requires source fingerprints")
    if catalog_by_id is not None:
        for article in source.get("articles") or []:
            for source_id in [article.get("source_id"), *(article.get("block_ids") or []), *(article.get("image_ids") or [])]:
                if not source_id:
                    continue
                source_record = catalog_by_id.get(source_id)
                if not source_record:
                    errors.append(f"{recipe.get('id')}: unresolved source record {source_id}")
                elif source_record.get("fingerprint") and source_record["fingerprint"] not in source_fingerprints:
                    errors.append(f"{recipe.get('id')}: lineage omits fingerprint for {source_id}")

    validation = recipe.get("validation") or {}
    if validation.get("tier") not in {"verified", "parse-verified", "reference-only", "visual-only"}:
        errors.append(f"{recipe.get('id')}: invalid validation tier")
    required_checks = {"schema", "syntax", "safety", "fixture", "render", "visual", "semantic", "provenance"}
    checks = validation.get("checks") or {}
    if not required_checks.issubset(checks.keys()):
        errors.append(f"{recipe.get('id')}: validation checks are incomplete")
    if checks.get("visual") == "pass":
        if not visual_fingerprint.get("reviewed"):
            errors.append(f"{recipe.get('id')}: visual=pass requires reviewed VisualFingerprint")
        if visual_fingerprint.get("evidence_level") not in {"image_code", "image_code_data"}:
            errors.append(f"{recipe.get('id')}: visual=pass requires image_code or image_code_data evidence")
        if not visual_fingerprint.get("review_note"):
            errors.append(f"{recipe.get('id')}: visual=pass requires a native review note")
        preview_relative = str(files.get("preview") or "")
        if "previews-rendered" not in preview_relative.replace("\\", "/"):
            errors.append(f"{recipe.get('id')}: visual=pass requires an exact generalized render, not a source preview")
        elif preview and preview.exists():
            final_preview = preview.with_name(preview.stem + "-final" + preview.suffix)
            if not final_preview.exists() or not image_metadata(final_preview).get("readable"):
                errors.append(f"{recipe.get('id')}: visual=pass requires a readable final-submission-size companion render")
    if get_validation_tier(recipe) == "verified":
        failed = [name for name in ("schema", "syntax", "safety", "visual", "semantic", "provenance") if checks.get(name) != "pass"]
        if failed:
            errors.append(f"{recipe.get('id')}: verified tier has non-pass checks {failed}")
        if not visual_fingerprint.get("reviewed"):
            errors.append(f"{recipe.get('id')}: verified tier requires reviewed visual fingerprint")
        if not preview and recipe.get("kind") not in {"adapter", "export"}:
            errors.append(f"{recipe.get('id')}: verified tier requires an exact rendered preview")
    return errors, warnings


def validate_manifest_paths() -> list[str]:
    errors = []
    manifest_path = SKILL_ROOT / "manifest.yaml"
    if not manifest_path.exists():
        return ["manifest.yaml missing"]
    text = read_text(manifest_path)
    # Validate every local resource class declared by the manifest, including
    # generated JSON/JSONL indexes, scripts, assets and extensionless folders.
    candidates = re.findall(
        r"(?:^|\s)((?:static|references|scripts|assets)/[A-Za-z0-9_./-]+)",
        text,
        re.M,
    )
    for rel in sorted(set(candidates)):
        if not (SKILL_ROOT / rel).exists():
            errors.append(f"manifest path missing: {rel}")
    return errors


def benchmark_search(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not BENCHMARK_PATH.exists():
        return {"available": False, "total": 0, "hits": 0, "top3_rate": None}
    cases = load_jsonl(BENCHMARK_PATH)
    hits = 0
    failures = []
    primary_hits = 0
    backend_cases = 0
    backend_passes = 0
    role_contract_passes = 0
    semantic_contract_passes = 0
    diversity_passes = 0
    expected_top3_coverage: list[float] = []
    forbidden_support_violations: list[dict[str, str]] = []
    for case in cases:
        query = case.get("query") or case.get("prompt") or ""
        expected = case.get("expected_family") or case.get("family")
        expected_values = {canonical_family(item) for item in expected} if isinstance(expected, list) else {canonical_family(expected)}
        expected_backend = case.get("backend") or case.get("expected_backend")
        _, results = search_records(records, query, backend=expected_backend, top_k=3)
        actual_ordered = [canonical_family(item.get("family")) for item in results[:3]]
        actual = set(actual_ordered)
        if expected_values & actual:
            hits += 1
        else:
            failures.append({"query": query, "expected": sorted(expected_values), "actual": sorted(actual)})
        if results and canonical_family(results[0].get("family")) in expected_values:
            primary_hits += 1
        if expected_backend:
            backend_cases += 1
            if results and results[0].get("backend") == expected_backend and all(item.get("backend") in {None, expected_backend} for item in results):
                backend_passes += 1
        expected_top3 = {canonical_family(item) for item in case.get("expected_top3_families") or []}
        if expected_top3:
            expected_top3_coverage.append(len(expected_top3 & actual) / len(expected_top3))
        expected_roles = ["primary", "conservative", "information_dense"][: len(results[:3])]
        role_rows = results[:3]
        role_tradeoffs = [item.get("tradeoff") for item in role_rows]
        role_semantics_ok = (
            [item.get("recommendation_role") for item in role_rows] == expected_roles
            and all(role_tradeoffs)
            and len(set(role_tradeoffs)) == len(role_tradeoffs)
            and all(item.get("priority_rationale") for item in role_rows)
            and all(
                item.get("priority_rationale", "").startswith("未列为主方案")
                for item in role_rows[1:]
            )
        )
        if role_semantics_ok:
            role_contract_passes += 1
        if results and all(
            item.get("why_match") and item.get("tradeoff") and item.get("visual_channels")
            and item.get("supports_claims") and item.get("does_not_support")
            and "required_statistics" in item and "missing_inputs" in item
            for item in results[:3]
        ):
            semantic_contract_passes += 1
        if len(actual_ordered) == len(set(actual_ordered)):
            diversity_passes += 1
        supported_text = normalize_text(" ".join(claim for item in results[:3] for claim in item.get("supports_claims") or []))
        for forbidden in case.get("forbidden_claims") or []:
            normalized_forbidden = normalize_text(forbidden)
            if normalized_forbidden and normalized_forbidden in supported_text:
                forbidden_support_violations.append({"id": case.get("id"), "claim": forbidden})
    rate = hits / len(cases) if cases else 0.0
    total = len(cases)
    backend_rate = backend_passes / backend_cases if backend_cases else 1.0
    role_rate = role_contract_passes / total if total else 0.0
    semantic_rate = semantic_contract_passes / total if total else 0.0
    diversity_rate = diversity_passes / total if total else 0.0
    benchmark_pass = (
        total >= 40 and rate >= 0.9 and backend_rate == 1.0 and role_rate == 1.0
        and semantic_rate == 1.0 and diversity_rate >= 0.9 and not forbidden_support_violations
    )
    return {
        "available": True,
        "total": total,
        "hits": hits,
        "top3_rate": round(rate, 4),
        "primary_family_rate": round(primary_hits / total, 4) if total else 0.0,
        "backend_contract": {"cases": backend_cases, "passes": backend_passes, "rate": round(backend_rate, 4)},
        "role_contract_rate": round(role_rate, 4),
        "semantic_contract_rate": round(semantic_rate, 4),
        "diversity_rate": round(diversity_rate, 4),
        "expected_top3_mean_coverage": round(sum(expected_top3_coverage) / len(expected_top3_coverage), 4) if expected_top3_coverage else None,
        "forbidden_support_violations": forbidden_support_violations[:10],
        "pass": benchmark_pass,
        "failure_examples": failures[:10],
    }


def validate_visual_benchmark(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not VISUAL_BENCHMARK_PATH.exists():
        return {"available": False, "pass": False, "errors": ["visual benchmark missing"]}
    cases = load_jsonl(VISUAL_BENCHMARK_PATH)
    errors: list[str] = []
    expected_defects = {
        "legend_clipped", "continuous_scale_legend_missing", "label_overlap",
        "text_unreadable_at_final_size", "cross_panel_category_color_inconsistent",
        "red_green_only_critical_encoding", "heatmap_midpoint_semantically_wrong",
    }
    found_defects = {case.get("expected_issue") for case in cases if case.get("scope") == "rendered_result"}
    missing_defects = sorted(expected_defects - found_defects)
    if missing_defects:
        errors.append("missing visual defect cases: " + ", ".join(missing_defects))
    required_fields = {"id", "evidence_level", "expected_issue", "allowed_auto_fix", "requires_confirmation", "pass_criteria"}
    ids: set[str] = set()
    for case in cases:
        missing = required_fields - set(case)
        if missing:
            errors.append(f"{case.get('id')}: missing fields {sorted(missing)}")
        if case.get("id") in ids:
            errors.append(f"duplicate visual benchmark id: {case.get('id')}")
        ids.add(case.get("id"))
        if case.get("expected_issue") == "heatmap_midpoint_semantically_wrong":
            if case.get("allowed_auto_fix") is not False or case.get("requires_confirmation") is not True:
                errors.append("heatmap midpoint case must require confirmation and forbid automatic semantic change")
        if case.get("scope") == "source_curation":
            asset = SKILL_ROOT / case.get("asset", "")
            if not asset.exists():
                errors.append(f"{case.get('id')}: source asset missing")
                continue
            actual_hash = hashlib.sha256(asset.read_bytes()).hexdigest().upper()
            if actual_hash != str(case.get("sha256", "")).upper():
                errors.append(f"{case.get('id')}: source asset checksum mismatch")
            archive_rel = asset.relative_to(SOURCE_ROOT).as_posix()
            catalog_image = next((record for record in records if record.get("record_type") == "image" and record.get("archive_path") == archive_rel), None)
            if not catalog_image or catalog_image.get("role") != "promotion_or_qr" or catalog_image.get("reviewed") is not True:
                errors.append(f"{case.get('id')}: QR asset is not a reviewed promotion_or_qr catalog record")
            curated_hashes = {hashlib.sha256(path.read_bytes()).hexdigest().upper() for path in (SKILL_ROOT / "assets" / "previews-curated").glob("*") if path.is_file()}
            if actual_hash in curated_hashes:
                errors.append(f"{case.get('id')}: QR asset leaked into curated previews")
    return {"available": True, "total": len(cases), "defect_cases": len(found_defects), "pass": not errors, "errors": errors}


def validate_visual_review_results() -> dict[str, Any]:
    """Validate persisted native-image review evidence for injected defects.

    This intentionally validates review records, not computer-vision inference by
    the Python CLI.  The `native_image_viewed` flag records that the skill opened
    each fixture with Codex's local image capability.
    """
    if not VISUAL_RESULTS_PATH.exists():
        return {"available": False, "pass": False, "errors": ["visual review results missing"]}
    specs = {
        case.get("id"): case
        for case in load_jsonl(VISUAL_BENCHMARK_PATH)
        if case.get("scope") == "rendered_result"
    }
    results = load_jsonl(VISUAL_RESULTS_PATH)
    errors: list[str] = []
    seen: set[str] = set()
    for result in results:
        result_id = result.get("benchmark_id")
        if result_id in seen:
            errors.append(f"duplicate visual review result: {result_id}")
            continue
        seen.add(result_id)
        spec = specs.get(result_id)
        if not spec:
            errors.append(f"visual review result has no benchmark spec: {result_id}")
            continue
        asset = SKILL_ROOT / str(result.get("asset") or "")
        if not asset.exists() or not image_metadata(asset).get("readable"):
            errors.append(f"{result_id}: reviewed asset is missing or unreadable")
        if result.get("native_image_viewed") is not True:
            errors.append(f"{result_id}: native image view was not recorded")
        if result.get("expected_issue_match") is not True:
            errors.append(f"{result_id}: injected issue was not matched")
        if result.get("evidence_level") != spec.get("evidence_level"):
            errors.append(f"{result_id}: evidence level differs from protocol")
        if result.get("allowed_auto_fix") != spec.get("allowed_auto_fix"):
            errors.append(f"{result_id}: auto-fix boundary differs from protocol")
        if result.get("requires_confirmation") != spec.get("requires_confirmation"):
            errors.append(f"{result_id}: confirmation boundary differs from protocol")
        if not result.get("observed_issue") or not result.get("fix") or not result.get("claim_limit"):
            errors.append(f"{result_id}: review lacks observation, executable fix, or claim limit")
    missing = sorted(set(specs) - seen)
    if missing:
        errors.append("missing executed visual review results: " + ", ".join(missing))
    return {
        "available": True,
        "protocol_cases": len(specs),
        "executed_cases": len(results),
        "matched_cases": sum(1 for item in results if item.get("expected_issue_match") is True),
        "pass": not errors and len(results) == len(specs),
        "errors": errors,
        "boundary": "Evidence records were produced by native image review; this Python validator does not perform semantic vision.",
    }


def validate_exact_render_reviews(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not EXACT_RENDER_REVIEW_PATH.exists():
        return {"available": False, "pass": False, "errors": ["exact render review evidence missing"]}
    reviews = load_jsonl(EXACT_RENDER_REVIEW_PATH)
    recipes = {
        record.get("id"): record
        for record in records
        if record.get("record_type") == "recipe" and record.get("kind") == "base_recipe"
    }
    blocked_recipes = {
        recipe_id: {
            name: ((recipe.get("validation") or {}).get("checks") or {}).get(name)
            for name in ("fixture", "render")
            if normalize_text(((recipe.get("validation") or {}).get("checks") or {}).get(name)).replace(" ", "_").startswith("blocked")
        }
        for recipe_id, recipe in recipes.items()
    }
    blocked_recipes = {recipe_id: reasons for recipe_id, reasons in blocked_recipes.items() if reasons}
    reviewable_recipes = {recipe_id: recipe for recipe_id, recipe in recipes.items() if recipe_id not in blocked_recipes}
    errors: list[str] = []
    seen: set[str] = set()
    decisions: Counter[str] = Counter()
    for review in reviews:
        recipe_id = review.get("recipe_id")
        if recipe_id in seen:
            errors.append(f"duplicate exact render review: {recipe_id}")
            continue
        seen.add(recipe_id)
        recipe = recipes.get(recipe_id)
        if not recipe:
            errors.append(f"exact render review has no base Recipe: {recipe_id}")
            continue
        if review.get("backend") != recipe.get("backend"):
            errors.append(f"{recipe_id}: render backend differs from Recipe backend")
        if recipe_id in blocked_recipes:
            errors.append(f"{recipe_id}: exact-render record exists despite an explicit blocked runtime; clear the blocker before claiming a render review")
        if set(review.get("native_views_opened") or []) != {"original", "final"}:
            errors.append(f"{recipe_id}: original and final native views are both required")
        if review.get("semantic_match") is not True:
            errors.append(f"{recipe_id}: exact render does not match Recipe semantics")
        decision = review.get("decision")
        decisions[decision] += 1
        if decision not in {"keep", "revise", "reselect"}:
            errors.append(f"{recipe_id}: invalid exact render decision {decision}")
        for label in ("original_asset", "final_asset"):
            asset = SKILL_ROOT / str(review.get(label) or "")
            if not asset.exists() or not image_metadata(asset).get("readable"):
                errors.append(f"{recipe_id}: {label} missing or unreadable")
        checks = (recipe.get("validation") or {}).get("checks") or {}
        if decision == "keep":
            if checks.get("visual") != "pass":
                errors.append(f"{recipe_id}: keep decision is not reflected as visual=pass")
            preview = str((recipe.get("files") or {}).get("preview") or "").replace("\\", "/")
            if "previews-rendered" not in preview:
                errors.append(f"{recipe_id}: kept exact render is not the active preview")
        elif checks.get("visual") == "pass":
            errors.append(f"{recipe_id}: non-keep render must not be marked visual=pass")
    missing = sorted(set(reviewable_recipes) - seen)
    if missing:
        errors.append("base Recipes without exact render review: " + ", ".join(missing))
    return {
        "available": True,
        "base_recipes": len(recipes),
        "reviewable_base_recipes": len(reviewable_recipes),
        "blocked_base_recipes": blocked_recipes,
        "reviewed": len(reviews),
        "decisions": dict(decisions),
        "pass": not errors and len(reviews) == len(reviewable_recipes),
        "errors": errors,
    }


def snapshot_policy_exclusions(root: Path) -> set[str]:
    snapshot = root / "SNAPSHOT.json"
    if not snapshot.exists():
        return set()
    try:
        payload = json.loads(read_text(snapshot))
    except (OSError, json.JSONDecodeError):
        return set()
    excluded: set[str] = set()
    for item in payload.get("excluded") or []:
        path = item.get("path") if isinstance(item, dict) else item
        if path:
            excluded.add(str(path).replace("\\", "/").rstrip("/"))
    return excluded


def path_is_policy_excluded(relative: str, exclusions: set[str]) -> bool:
    normalized = relative.replace("\\", "/").lstrip("./")
    return any(normalized == item or normalized.startswith(item + "/") for item in exclusions)


def validate_source_checksums(root: Path = SOURCE_ROOT) -> dict[str, Any]:
    checksum_path = root / SOURCE_CHECKSUMS_NAME
    if not checksum_path.exists():
        return {"available": False, "pass": False, "errors": [f"{SOURCE_CHECKSUMS_NAME} missing"]}
    errors: list[str] = []
    verified = 0
    excluded_by_policy: list[str] = []
    listed: set[str] = set()
    exclusions = snapshot_policy_exclusions(root)
    try:
        with checksum_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        return {"available": True, "pass": False, "errors": [f"checksum index unreadable: {exc}"]}
    for row_no, row in enumerate(rows, 2):
        relative = str(row.get("path") or "").replace("\\", "/")
        if not relative or relative in listed:
            errors.append(f"invalid or duplicate checksum row {row_no}: {relative!r}")
            continue
        listed.add(relative)
        target = root / Path(relative)
        if not target.exists():
            if path_is_policy_excluded(relative, exclusions):
                excluded_by_policy.append(relative)
            else:
                errors.append(f"checksum target missing: {relative}")
            continue
        if not target.is_file():
            errors.append(f"checksum target is not a file: {relative}")
            continue
        try:
            expected_bytes = int(row.get("bytes") or -1)
        except (TypeError, ValueError):
            expected_bytes = -1
        actual_bytes = target.stat().st_size
        actual_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual_bytes != expected_bytes:
            errors.append(f"checksum size mismatch: {relative}")
        elif actual_hash.lower() != str(row.get("sha256") or "").lower():
            errors.append(f"checksum digest mismatch: {relative}")
        else:
            verified += 1
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.name not in {SOURCE_CHECKSUMS_NAME, "SNAPSHOT.json"}
        and snapshot_file_allowed(path, root)
    }
    unlisted = sorted(actual - listed)
    if unlisted:
        errors.append("files absent from checksum index: " + ", ".join(unlisted[:10]))
    return {
        "available": True,
        "rows": len(rows),
        "verified": verified,
        "excluded_by_policy": excluded_by_policy,
        "unlisted": unlisted,
        "pass": not errors,
        "errors": errors,
    }


def write_source_checksums(root: Path) -> dict[str, Any]:
    checksum_path = root / SOURCE_CHECKSUMS_NAME
    paths = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.name not in {SOURCE_CHECKSUMS_NAME, "SNAPSHOT.json"}
        and snapshot_file_allowed(path, root)
    ]
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=root) as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        for path in paths:
            writer.writerow({
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        temporary = Path(handle.name)
    temporary.replace(checksum_path)
    return {"rows": len(paths), "verified": len(paths), "excluded_by_policy": [], "failures": 0}


def validate_style_atlas(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate atlas linkage, preview safety, coverage semantics, and completeness."""
    errors: list[str] = []
    warnings: list[str] = []
    if not STYLE_ATLAS_PATH.exists():
        return {"available": False, "pass": False, "cards": 0, "errors": ["style-atlas.jsonl missing"], "warnings": []}
    try:
        cards = load_jsonl(STYLE_ATLAS_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"available": True, "pass": False, "cards": 0, "errors": [f"invalid style atlas: {exc}"], "warnings": []}

    by_id = {str(record.get("id")): record for record in records if record.get("id")}
    article_ids = {record_id for record_id, record in by_id.items() if record.get("record_type") == "article"}
    recipe_ids = {record_id for record_id, record in by_id.items() if record.get("record_type") == "recipe"}
    seen: set[str] = set()
    covered_articles: set[str] = set()
    allowed_status = {"formal_exact", "formal_family", "source_only", "code_only", "visual_only", "resource_only"}
    allowed_backends = {"r", "python", "neutral"}
    forbidden_roles = {"promotion_or_qr", "cover_or_web_screenshot", "code_screenshot"}
    evidence_roles = {"scientific_result", "published_reference"}
    heuristic_sample_count = 0

    for index, card in enumerate(cards, 1):
        style_id = str(card.get("style_id") or "").strip()
        prefix = style_id or f"record-{index}"
        if not style_id:
            errors.append(f"record {index}: missing style_id")
            continue
        if style_id in seen:
            errors.append(f"{prefix}: duplicate style_id")
        seen.add(style_id)
        for field in ("title", "family", "description", "analysis_use", "keywords", "source_article_id", "sample_image_id", "sample_image", "coverage_status"):
            if card.get(field) in (None, "", []):
                errors.append(f"{prefix}: missing {field}")

        article_id = str(card.get("source_article_id") or "")
        article = by_id.get(article_id)
        if not article or article.get("record_type") != "article":
            errors.append(f"{prefix}: unresolved source article {article_id}")
        else:
            covered_articles.add(article_id)

        for block_id in card.get("source_block_ids") or []:
            block = by_id.get(str(block_id))
            if not block or block.get("record_type") != "source_block":
                errors.append(f"{prefix}: unresolved source block {block_id}")
            elif str(block.get("article_id")) != article_id:
                errors.append(f"{prefix}: source block belongs to another article: {block_id}")

        sample_id = str(card.get("sample_image_id") or "")
        sample = by_id.get(sample_id)
        if not sample or sample.get("record_type") != "image":
            errors.append(f"{prefix}: unresolved sample image {sample_id}")
        else:
            if str(sample.get("article_id")) != article_id:
                errors.append(f"{prefix}: sample image belongs to another article: {sample_id}")
            if card.get("sample_image") != sample.get("path"):
                errors.append(f"{prefix}: sample_image path does not match catalog image {sample_id}")
            role = str(sample.get("role") or "")
            if role in forbidden_roles or bool((sample.get("metadata") or {}).get("qr_like")):
                errors.append(f"{prefix}: disallowed sample image role/QR: {sample_id} ({role})")
            if card.get("coverage_status") != "resource_only" and role not in evidence_roles:
                errors.append(f"{prefix}: evidence style requires scientific_result/published_reference sample, got {role}")
            sample_path = SKILL_ROOT / str(sample.get("path") or "")
            if not sample_path.exists() or not sample_path.is_file():
                errors.append(f"{prefix}: sample image file missing: {sample.get('path')}")

        backends = atlas_backend_values(card)
        unknown_backends = backends - allowed_backends
        if unknown_backends:
            errors.append(f"{prefix}: unsupported backends: {sorted(unknown_backends)}")
        status = normalize_text(card.get("coverage_status")).replace(" ", "_")
        if status not in allowed_status:
            errors.append(f"{prefix}: unsupported coverage_status {status}")

        declared_recipes = {str(item) for item in card.get("recipe_ids") or []}
        unresolved_recipes = declared_recipes - recipe_ids
        if unresolved_recipes:
            errors.append(f"{prefix}: unresolved recipe_ids {sorted(unresolved_recipes)}")
        exact_ids = {str(item) for item in card.get("exact_recipe_ids") or []}
        family_ids = {str(item) for item in card.get("family_recipe_ids") or []}
        if status == "formal_exact" and not exact_ids:
            errors.append(f"{prefix}: formal_exact without exact_recipe_ids")
        if status == "formal_family" and not family_ids:
            errors.append(f"{prefix}: formal_family without family_recipe_ids")
        if status in {"source_only", "code_only", "visual_only"} and (exact_ids or family_ids):
            errors.append(f"{prefix}: {status} cannot declare formal Recipe coverage")
        for recipe_id in exact_ids:
            recipe = by_id.get(recipe_id) or {}
            source_articles = {
                str(item.get("source_id"))
                for item in ((recipe.get("source") or {}).get("articles") or [])
                if isinstance(item, dict) and item.get("source_id")
            }
            if article_id not in source_articles:
                errors.append(f"{prefix}: exact Recipe {recipe_id} does not cite source article")

        validation = card.get("validation") or {}
        if validation.get("sample_selection") == "heuristic_intermediate_candidate" and status != "resource_only":
            errors.append(f"{prefix}: non-resource card has an unreviewed intermediate sample")
        if validation.get("sample_selection") == "heuristic_scientific_result":
            heuristic_sample_count += 1

    atlas_benchmark_specs = [
        {
            "query": "颜色表示平均表达、点大小表示表达比例，并给 marker 分组加框",
            "expected_top1": "style-4329102050694250504-010-dotplot-v1",
        },
        {
            "query": "NC 杂志同款连线堆积柱状图",
            "expected_top1": "style-3792985494804332545-054-composition-v1",
        },
        {
            "query": "单细胞拟时序轨迹",
            "expected_top1": "style-4329102050694250504-013-trajectory-v1",
        },
    ]
    atlas_benchmark_results: list[dict[str, Any]] = []
    for spec in atlas_benchmark_specs:
        ranked_cards = sorted(
            (
                (score_atlas_card(card, spec["query"])[0], str(card.get("style_id")), card)
                for card in cards
            ),
            key=lambda item: (-item[0], normalize_text(item[2].get("title")), item[1]),
        )
        top_ids = [item[1] for item in ranked_cards if item[0] > 0][:3]
        passed = bool(top_ids and top_ids[0] == spec["expected_top1"])
        atlas_benchmark_results.append({**spec, "top3": top_ids, "pass": passed})
        if not passed:
            errors.append(
                "atlas retrieval regression: " + spec["query"]
                + f" expected top1={spec['expected_top1']} got={top_ids[:1]}"
            )

    missing_articles = sorted(article_ids - covered_articles)
    unexpected_articles = sorted(covered_articles - article_ids)
    if missing_articles:
        errors.append("atlas missing source articles: " + ", ".join(missing_articles))
    if unexpected_articles:
        errors.append("atlas contains unknown source articles: " + ", ".join(unexpected_articles))
    if heuristic_sample_count:
        warnings.append(
            f"{heuristic_sample_count} samples passed deterministic scientific-result checks "
            "but were not individually native-reviewed"
        )
    return {
        "available": True,
        "pass": not errors,
        "cards": len(cards),
        "articles_covered": len(covered_articles),
        "sample_roles": dict(Counter(str((by_id.get(str(card.get('sample_image_id'))) or {}).get('role') or 'missing') for card in cards)),
        "coverage_status": dict(Counter(str(card.get("coverage_status")) for card in cards)),
        "retrieval_benchmark": {
            "total": len(atlas_benchmark_results),
            "passed": sum(1 for item in atlas_benchmark_results if item["pass"]),
            "results": atlas_benchmark_results,
        },
        "errors": errors,
        "warnings": warnings,
    }


def validate_scheme_benchmark(schemes: list[dict[str, Any]]) -> dict[str, Any]:
    if not SCHEME_BENCHMARK_PATH.exists():
        return {"available": False, "pass": True, "total": 0, "passed": 0, "results": []}
    specs = load_jsonl(SCHEME_BENCHMARK_PATH)
    results: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    if specs:
        # Prime JSON/index/feature caches so the contract measures warm search.
        search_scheme_records(schemes, str(specs[0].get("query") or ""), top_k=3)
    for index, spec in enumerate(specs, 1):
        case_id = str(spec.get("case_id") or spec.get("id") or f"case-{index:03d}")
        query = str(spec.get("query") or "")
        if not query:
            results.append({"case_id": case_id, "pass": False, "errors": ["missing query"]})
            continue
        started = time.perf_counter()
        intent, decisions, appearance, rejected, clarification = search_scheme_records(
            schemes,
            query,
            backend=spec.get("backend"),
            family=spec.get("family"),
            domain=spec.get("domain"),
            top_k=max(3, int(spec.get("top_k") or 3)),
        )
        latencies_ms.append((time.perf_counter() - started) * 1000.0)
        ids = [str(item.get("scheme_id") or item.get("id")) for item in decisions]
        subtypes = [str(item.get("geometry_subtype")) for item in decisions]
        families = [canonical_family(item.get("broad_family") or item.get("family")) for item in decisions]
        methods = [normalize_analysis_method(item.get("analysis_method")) for item in decisions]
        appearance_ids = [str(item.get("scheme_id") or item.get("id")) for item in appearance]
        appearance_subtypes = [str(item.get("geometry_subtype")) for item in appearance]
        errors: list[str] = []

        expected_top1 = (
            spec.get("expected_top1")
            or spec.get("expected_scheme_id")
            or spec.get("expected_top1_scheme_id")
        )
        if expected_top1 and (not ids or ids[0] != str(expected_top1)):
            errors.append(f"expected top1={expected_top1}, got={ids[:1]}")
        expected_subtype = spec.get("expected_top1_subtype") or spec.get("expected_subtype")
        if expected_subtype and (not subtypes or subtypes[0] != str(expected_subtype)):
            errors.append(f"expected top1 subtype={expected_subtype}, got={subtypes[:1]}")
        expected_family = spec.get("expected_family") or spec.get("expected_top1_family")
        if expected_family and (not families or families[0] != canonical_family(expected_family)):
            errors.append(f"expected top1 family={expected_family}, got={families[:1]}")
        expected_method = spec.get("expected_analysis_method")
        if expected_method and (not methods or methods[0] != normalize_analysis_method(expected_method)):
            errors.append(f"expected top1 analysis_method={expected_method}, got={methods[:1]}")
        expected_availability = spec.get("expected_availability")
        actual_availability = str(decisions[0].get("availability")) if decisions else ""
        if expected_availability and actual_availability != str(expected_availability):
            errors.append(
                f"expected availability={expected_availability}, got={actual_availability or 'none'}"
            )
        expected_execution_availability = spec.get("expected_execution_availability")
        actual_execution_availability = (
            str(decisions[0].get("execution_availability")) if decisions else ""
        )
        if (
            expected_execution_availability
            and actual_execution_availability != str(expected_execution_availability)
        ):
            errors.append(
                "expected execution_availability="
                f"{expected_execution_availability}, got={actual_execution_availability or 'none'}"
            )
        expected_action = spec.get("expected_action_intent")
        if expected_action and intent.get("action_intent") != expected_action:
            errors.append(
                f"expected action_intent={expected_action}, got={intent.get('action_intent')}"
            )
        expected_actions = set(map(str, as_list(spec.get("expected_action_intents_contains"))))
        missing_actions = sorted(expected_actions - set(map(str, intent.get("action_intents") or [])))
        if missing_actions:
            errors.append("expected action_intents absent: " + ", ".join(missing_actions))
        if spec.get("expected_review_requested") is not None and bool(intent.get("review_requested")) != bool(spec.get("expected_review_requested")):
            errors.append(
                "expected review_requested="
                f"{bool(spec.get('expected_review_requested'))}, got={bool(intent.get('review_requested'))}"
            )
        if spec.get("expected_review_after_execution") is not None and bool(intent.get("review_after_execution")) != bool(spec.get("expected_review_after_execution")):
            errors.append(
                "expected review_after_execution="
                f"{bool(spec.get('expected_review_after_execution'))}, got={bool(intent.get('review_after_execution'))}"
            )
        expected_intent_backend = spec.get("expected_intent_backend")
        if expected_intent_backend and intent.get("backend") != expected_intent_backend:
            errors.append(
                f"expected intent backend={expected_intent_backend}, got={intent.get('backend')}"
            )
        expected_core_question = spec.get("expected_core_question")
        if expected_core_question and intent.get("core_question") != expected_core_question:
            errors.append(
                f"expected core_question={expected_core_question}, got={intent.get('core_question')}"
            )
        expected_retrieval_family = spec.get("expected_retrieval_family")
        if expected_retrieval_family and intent_retrieval_family(intent) != canonical_family(expected_retrieval_family):
            errors.append(
                "expected retrieval_family="
                f"{canonical_family(expected_retrieval_family)}, got={intent_retrieval_family(intent)}"
            )
        if spec.get("expected_source_lookup") is not None and bool(intent.get("source_lookup")) != bool(spec.get("expected_source_lookup")):
            errors.append(
                f"expected source_lookup={bool(spec.get('expected_source_lookup'))}, got={bool(intent.get('source_lookup'))}"
            )
        if spec.get("expected_requires_executable") is not None and bool(intent.get("requires_executable")) != bool(spec.get("expected_requires_executable")):
            errors.append(
                "expected requires_executable="
                f"{bool(spec.get('expected_requires_executable'))}, got={bool(intent.get('requires_executable'))}"
            )
        top_plan = decisions[0].get("executable_plan") if decisions else {}
        top_plan = top_plan if isinstance(top_plan, dict) else {}
        expected_plan_status = spec.get("expected_plan_status")
        if expected_plan_status and top_plan.get("status") != expected_plan_status:
            errors.append(
                f"expected plan status={expected_plan_status}, got={top_plan.get('status') or 'none'}"
            )
        expected_base_recipe = spec.get("expected_base_recipe_id")
        if expected_base_recipe and top_plan.get("base_recipe_id") != expected_base_recipe:
            errors.append(
                f"expected base Recipe={expected_base_recipe}, got={top_plan.get('base_recipe_id') or 'none'}"
            )
        expected_adapter = spec.get("expected_adapter_id")
        if expected_adapter and top_plan.get("adapter_id") != expected_adapter:
            errors.append(
                f"expected adapter={expected_adapter}, got={top_plan.get('adapter_id') or 'none'}"
            )
        if spec.get("expected_direct_execution") is not None and bool(top_plan.get("direct_execution")) != bool(spec.get("expected_direct_execution")):
            errors.append(
                "expected direct_execution="
                f"{bool(spec.get('expected_direct_execution'))}, got={bool(top_plan.get('direct_execution'))}"
            )
        expected_modifiers = set(map(str, as_list(spec.get("expected_modifier_ids"))))
        missing_modifiers = sorted(expected_modifiers - set(map(str, top_plan.get("modifier_ids") or [])))
        if missing_modifiers:
            errors.append("expected modifiers absent from plan: " + ", ".join(missing_modifiers))
        forbidden_tiers = set(map(str, as_list(spec.get("forbidden_validation_tiers"))))
        tier_hits = sorted(
            forbidden_tiers & {str(item.get("validation_tier")) for item in decisions}
        )
        if tier_hits:
            errors.append("forbidden validation tiers returned: " + ", ".join(tier_hits))
        appearance_tier_hits = sorted(
            forbidden_tiers & {str(item.get("validation_tier")) for item in appearance}
        )
        if appearance_tier_hits:
            errors.append(
                "forbidden appearance validation tiers returned: "
                + ", ".join(appearance_tier_hits)
            )
        expected_top3_bases = set(map(str, as_list(spec.get("expected_top3_base_recipe_ids"))))
        actual_top3_bases = {
            str((item.get("executable_plan") or {}).get("base_recipe_id"))
            for item in decisions[:3]
            if (item.get("executable_plan") or {}).get("base_recipe_id")
        }
        missing_top3_bases = sorted(expected_top3_bases - actual_top3_bases)
        if missing_top3_bases:
            errors.append("expected base Recipes absent from top3: " + ", ".join(missing_top3_bases))
        expected_top3_families = {
            canonical_family(value)
            for value in as_list(spec.get("expected_top3_families_contains"))
        }
        missing_top3_families = sorted(expected_top3_families - set(families[:3]))
        if missing_top3_families:
            errors.append("expected families absent from top3: " + ", ".join(missing_top3_families))
        expected_appearance_subtype = spec.get("expected_appearance_top1_subtype")
        if expected_appearance_subtype and (
            not appearance_subtypes or appearance_subtypes[0] != str(expected_appearance_subtype)
        ):
            errors.append(
                f"expected appearance top1 subtype={expected_appearance_subtype}, "
                f"got={appearance_subtypes[:1]}"
            )
        if spec.get("expect_appearance_none") and appearance:
            errors.append("expected no appearance substitute, got: " + ", ".join(appearance_ids[:3]))

        expected_top3 = (
            spec.get("expected_top3_contains")
            or spec.get("expected_top3")
            or spec.get("expected_ids")
            or []
        )
        missing_expected = sorted(set(map(str, as_list(expected_top3))) - set(ids[:3]))
        if missing_expected:
            errors.append("expected IDs absent from top3: " + ", ".join(missing_expected))
        forbidden = set(
            map(
                str,
                as_list(spec.get("forbidden_ids") or spec.get("must_not_match") or spec.get("negative_ids")),
            )
        )
        forbidden_hits = sorted(forbidden & set(ids))
        if forbidden_hits:
            errors.append("forbidden IDs returned: " + ", ".join(forbidden_hits))
        expect_none = bool(spec.get("expect_no_match") or spec.get("expected_none"))
        positive_expectations = any(
            (
                expected_top1,
                expected_top3,
                expected_subtype,
                expected_family,
                expected_method,
            )
        )
        if normalize_text(spec.get("case_type")) == "negative" and not forbidden and not positive_expectations:
            expect_none = True
        if expect_none and ids:
            errors.append("expected no scientific decision, got: " + ", ".join(ids))
        expected_clarification = spec.get("expect_clarification")
        if expected_clarification is not None:
            actual = bool(clarification and clarification.get("needed"))
            if actual != bool(expected_clarification):
                errors.append(f"expected clarification={bool(expected_clarification)}, got={actual}")
        expected_unavailable = spec.get("expected_unavailable_subtype")
        if expected_unavailable:
            unavailable = set(map(str, as_list((clarification or {}).get("requested_subtypes"))))
            if str(expected_unavailable) not in unavailable:
                errors.append(
                    f"expected unavailable subtype={expected_unavailable}, got={sorted(unavailable)}"
                )

        results.append(
            {
                "case_id": case_id,
                "case_type": spec.get("case_type"),
                "query": query,
                "top3": ids[:3],
                "top3_subtypes": subtypes[:3],
                "top3_methods": methods[:3],
                "top3_availability": [item.get("availability") for item in decisions[:3]],
                "top3_base_recipes": [
                    (item.get("executable_plan") or {}).get("base_recipe_id")
                    for item in decisions[:3]
                ],
                "appearance_top3": appearance_ids[:3],
                "appearance_top3_subtypes": appearance_subtypes[:3],
                "rejected_count": len(rejected),
                "clarification": clarification,
                "pass": not errors,
                "errors": errors,
            }
        )
    ordered_latency = sorted(latencies_ms)
    p95_index = max(0, min(len(ordered_latency) - 1, (95 * len(ordered_latency) + 99) // 100 - 1)) if ordered_latency else 0
    performance = {
        "queries": len(latencies_ms),
        "warm_median_ms": round(ordered_latency[len(ordered_latency) // 2], 3) if ordered_latency else None,
        "warm_p95_ms": round(ordered_latency[p95_index], 3) if ordered_latency else None,
        "target_p95_ms": 750.0,
        "pass": bool(len(latencies_ms) >= 50 and ordered_latency and ordered_latency[p95_index] <= 750.0),
    }
    return {
        "available": True,
        "pass": all(item.get("pass") for item in results) and performance["pass"],
        "total": len(results),
        "passed": sum(1 for item in results if item.get("pass")),
        "case_types": dict(Counter(str(spec.get("case_type") or "unspecified") for spec in specs)),
        "performance": performance,
        "results": results,
    }


def validate_scheme_v2_strict(records: list[dict[str, Any]]) -> dict[str, Any]:
    schemes = load_scheme_records()
    errors: list[str] = []
    warnings: list[str] = []
    if not schemes:
        return {
            "available": False,
            "pass": False,
            "errors": ["scheme-catalog.jsonl missing or empty"],
            "warnings": [],
            "benchmark": {"available": False},
        }

    ids = [str(item.get("scheme_id") or "") for item in schemes]
    duplicate_ids = sorted(identifier for identifier, count in Counter(ids).items() if identifier and count > 1)
    if duplicate_ids:
        errors.append("duplicate scheme_id values: " + ", ".join(duplicate_ids[:20]))

    block_audit = disposition_audit(BLOCK_DISPOSITIONS_PATH, "block", EXPECTED["source_blocks"])
    image_audit = disposition_audit(IMAGE_DISPOSITIONS_PATH, "image", EXPECTED["images"])
    if not block_audit.get("available") or not block_audit.get("pass"):
        errors.append("621 source blocks must each have exactly one valid BlockDisposition")
    if not image_audit.get("available") or not image_audit.get("pass"):
        errors.append("709 images must each have exactly one valid image disposition")

    catalog_block_ids = {
        str(item.get("id")) for item in records if item.get("record_type") == "source_block" and item.get("id")
    }
    catalog_image_ids = {
        str(item.get("id")) for item in records if item.get("record_type") == "image" and item.get("id")
    }
    if block_audit.get("available") and catalog_block_ids:
        disposition_ids = {
            disposition_record_id(row, "block") for row in load_jsonl(BLOCK_DISPOSITIONS_PATH)
        }
        missing = sorted(catalog_block_ids - disposition_ids)
        extra = sorted(disposition_ids - catalog_block_ids)
        if missing or extra:
            errors.append(
                f"block disposition/catalog ID mismatch: missing={len(missing)} extra={len(extra)}"
            )
    if image_audit.get("available") and catalog_image_ids:
        disposition_ids = {
            disposition_record_id(row, "image") for row in load_jsonl(IMAGE_DISPOSITIONS_PATH)
        }
        missing = sorted(catalog_image_ids - disposition_ids)
        extra = sorted(disposition_ids - catalog_image_ids)
        if missing or extra:
            errors.append(
                f"image disposition/catalog ID mismatch: missing={len(missing)} extra={len(extra)}"
            )

    image_rows = load_jsonl(IMAGE_DISPOSITIONS_PATH) if IMAGE_DISPOSITIONS_PATH.exists() else []
    high_risk_roles = {"scientific_result", "published_reference", "uncertain"}
    unreviewed_high_risk = [
        str(row.get("image_id"))
        for row in image_rows
        if str(row.get("role")) in high_risk_roles and row.get("reviewed") is not True
    ]
    if unreviewed_high_risk:
        errors.append(
            "final/reference/uncertain images require native review: "
            + ", ".join(unreviewed_high_risk[:20])
        )
    incomplete_shared_reviews: list[str] = []
    for row in image_rows:
        linked = [str(item) for item in as_list(row.get("native_scheme_ids") or row.get("scheme_ids")) if item]
        if row.get("reviewed") is not True or not linked:
            continue
        fingerprint = row.get("visual_fingerprint")
        consistency = normalize_text(row.get("code_image_consistency")).replace("-", "_").replace(" ", "_")
        if not isinstance(fingerprint, dict) or not fingerprint or consistency in {"", "pending", "unknown"}:
            incomplete_shared_reviews.append(str(row.get("image_id")))
    if incomplete_shared_reviews:
        errors.append(
            "native Scheme-linked image reviews require fingerprint and code-image consistency: "
            + ", ".join(incomplete_shared_reviews[:20])
        )

    heuristic_scientific_previews: list[str] = []
    unreviewed_scientific: list[str] = []
    missing_scientific_evidence: list[str] = []
    withheld_scientific: list[str] = []
    unsafe_native_links: list[str] = []
    image_by_id = {str(row.get("image_id")): row for row in image_rows if row.get("image_id")}
    for record in schemes:
        if scheme_eligibility(record) not in SCIENTIFIC_SCHEME_ELIGIBILITY:
            continue
        scheme_id = str(record.get("scheme_id"))
        evidence_text = normalize_text(flatten_text(record.get("image_evidence")))
        review = scheme_review_status(record)
        image_evidence = record.get("image_evidence") if isinstance(record.get("image_evidence"), dict) else {}
        selection_method = normalize_text(
            image_evidence.get("selection_method")
            or image_evidence.get("preview_selection")
            or ""
        )
        if "heuristic" in review or "deterministic" in review or "heuristic" in selection_method:
            heuristic_scientific_previews.append(scheme_id)
        if not evidence_text:
            missing_scientific_evidence.append(scheme_id)
        if review in {
            "unreviewed",
            "unknown",
            "heuristic",
            "heuristic_scientific_result",
            "deterministic_only",
            "deterministic_scientific_result",
        }:
            unreviewed_scientific.append(scheme_id)
            withheld_scientific.append(scheme_id)
        if review in {"no_confirmed_native_image", "native_reviewed_nonfinal"}:
            withheld_scientific.append(scheme_id)
        primary_id = str((record.get("image_evidence") or {}).get("primary_image_id") or "")
        if review == "native_reviewed":
            primary = image_by_id.get(primary_id, {})
            if (
                str(primary.get("role")) not in {"scientific_result", "published_reference"}
                or not bool((record.get("image_evidence") or {}).get("scheme_link_confirmed"))
                or normalize_text((record.get("image_evidence") or {}).get("code_image_consistency"))
                in {"mismatch", "fail", "failed", "pending", "unknown", ""}
            ):
                unsafe_native_links.append(scheme_id)
    if heuristic_scientific_previews:
        warnings.append(
            "scientific Schemes with heuristic/deterministic evidence are withheld from the atlas: "
            + ", ".join(heuristic_scientific_previews[:20])
        )
    if missing_scientific_evidence:
        errors.append(
            "scientific schemes missing image evidence: "
            + ", ".join(missing_scientific_evidence[:20])
        )
    if unreviewed_scientific:
        warnings.append(
            f"{len(unreviewed_scientific)} scientific Schemes remain searchable but are withheld from the atlas pending native review"
        )
    if unsafe_native_links:
        errors.append(
            "native scientific previews require a safe role, confirmed Scheme link, and reviewed consistency: "
            + ", ".join(unsafe_native_links[:20])
        )
    if withheld_scientific:
        warnings.append(
            f"{len(set(withheld_scientific))} scientific Schemes have no confirmed final/reference preview and are withheld from the atlas"
        )

    candidate_errors: list[str] = []
    python_candidate_count = 0
    r_candidate_count = 0
    for record in schemes:
        if scheme_eligibility(record) not in SCIENTIFIC_SCHEME_ELIGIBILITY:
            continue
        scheme_id = str(record.get("scheme_id"))
        paths = record.get("candidate_code_path") if isinstance(record.get("candidate_code_path"), dict) else {}
        metadata_path = SKILL_ROOT / "assets" / "scheme-candidates" / scheme_id / "metadata.json"
        metadata = load_json_object(metadata_path, {}) if metadata_path.is_file() else {}
        metadata_callable = bool(metadata.get("callable", True))
        if not paths:
            claimed_status = normalize_text(record.get("code_status")).replace("-", "_")
            if claimed_status in {"candidate", "callable_candidate", "parse_verified", "verified"}:
                candidate_errors.append(
                    f"{scheme_id}: code_status={claimed_status} requires a candidate module"
                )
            continue
        for backend, relative in paths.items():
            path = (SKILL_ROOT / str(relative)).resolve()
            if SCHEME_CANDIDATE_ROOT.resolve() not in path.parents or not path.is_file():
                candidate_errors.append(f"{scheme_id}: missing/out-of-root candidate {relative}")
                continue
            text = read_text(path)
            source_match = re.search(
                r"(?m)^CANDIDATE_SOURCE\s*(?:=|<-)\s*(.+)$",
                text,
            )
            embedded_source = ""
            if not source_match:
                candidate_errors.append(f"{scheme_id}: candidate lacks embedded source contract")
            else:
                try:
                    embedded_source = json.loads(source_match.group(1))
                except json.JSONDecodeError:
                    candidate_errors.append(f"{scheme_id}: candidate embedded source is not a JSON string")
            if embedded_source:
                unsafe = [name for name, pattern in CANDIDATE_SAFETY_PATTERNS.items() if pattern.search(embedded_source)]
                if unsafe:
                    candidate_errors.append(
                        f"{scheme_id}: unsafe embedded candidate source ({', '.join(sorted(unsafe))})"
                    )
            if backend == "python":
                python_candidate_count += 1
                try:
                    ast.parse(text, filename=str(path))
                except SyntaxError as exc:
                    candidate_errors.append(f"{scheme_id}: Python candidate syntax error: {exc.msg}")
                if embedded_source:
                    try:
                        ast.parse(embedded_source, filename=f"{path}:CANDIDATE_SOURCE")
                    except SyntaxError as exc:
                        candidate_errors.append(f"{scheme_id}: embedded Python source syntax error: {exc.msg}")
                has_entrypoint = "def build_candidate_plot(" in text
                if metadata_callable and not has_entrypoint:
                    candidate_errors.append(f"{scheme_id}: callable Python candidate lacks build_candidate_plot")
                if not metadata_callable and has_entrypoint:
                    candidate_errors.append(f"{scheme_id}: non-callable Python candidate exposes build_candidate_plot")
            elif backend == "r":
                r_candidate_count += 1
                has_entrypoint = "build_candidate_plot <- function(" in text
                if "CANDIDATE_SOURCE <-" not in text:
                    candidate_errors.append(f"{scheme_id}: R candidate lacks source contract")
                if metadata_callable and not has_entrypoint:
                    candidate_errors.append(f"{scheme_id}: callable R candidate lacks build_candidate_plot")
                if not metadata_callable and has_entrypoint:
                    candidate_errors.append(f"{scheme_id}: non-callable R candidate exposes build_candidate_plot")
            else:
                candidate_errors.append(f"{scheme_id}: unsupported candidate backend {backend}")
        if not metadata_path.is_file():
            candidate_errors.append(f"{scheme_id}: candidate metadata missing")
        else:
            if not metadata.get("input_contract") or not metadata.get("return_contract"):
                candidate_errors.append(f"{scheme_id}: candidate input/return contract missing")
    if candidate_errors:
        errors.append("candidate module QA failed: " + "; ".join(candidate_errors[:20]))

    no_code_articles = {
        "article-4329102050694250504-013",
        "article-4329102050694250504-019",
        "article-4329102050694250504-020",
        "article-3792985494804332545-029",
    }
    for record in schemes:
        provenance_text = flatten_text(
            {
                "source_article_id": record.get("source_article_id"),
                "source": record.get("source"),
                "lineage": record.get("code_lineage"),
            }
        )
        matched_articles = {article for article in no_code_articles if article in provenance_text}
        if matched_articles and lineage_block_ids(record) and not scheme_is_visual_only(record):
            errors.append(
                f"{record.get('scheme_id')}: no-code source article cannot claim target plotting code "
                + ", ".join(sorted(matched_articles))
            )

    built_in_specs = [
        {
            "case_id": "strict-rose-exact",
            "query": "富集玫瑰图",
            "expected_subtypes": ["enrichment_rose", "radial_bar_lollipop"],
        },
        {
            "case_id": "strict-rose-fuzzy",
            "query": "通路围成一圈，柱高和点表示不同指标",
            "expected_subtypes": ["enrichment_rose", "radial_bar_lollipop"],
        },
    ]
    built_in_results: list[dict[str, Any]] = []
    for spec in built_in_specs:
        _, decisions, _, _, clarification = search_scheme_records(schemes, spec["query"], top_k=3)
        subtypes = [str(item.get("geometry_subtype")) for item in decisions]
        passed = bool(subtypes and subtypes[0] in spec["expected_subtypes"] and not clarification)
        built_in_results.append({**spec, "top3_subtypes": subtypes, "pass": passed})
        if not passed:
            errors.append(f"Scheme retrieval regression failed: {spec['case_id']} got={subtypes[:3]}")

    for method, query in (
        ("ora", "ORA GeneRatio Count p.adjust 富集结果"),
        ("gsea", "GSEA NES FDR ranked list running score"),
    ):
        _, decisions, _, _, clarification = search_scheme_records(schemes, query, top_k=3)
        methods = [normalize_analysis_method(item.get("analysis_method")) for item in decisions]
        opposite = "gsea" if method == "ora" else "ora"
        passed = bool(methods and methods[0] == method and opposite not in methods and not clarification)
        built_in_results.append({"case_id": f"strict-{method}-gate", "methods": methods, "pass": passed})
        if not passed:
            errors.append(f"{method.upper()} hard-gate regression failed: got={methods}")

    _, christmas_decisions, christmas_appearance, _, _ = search_scheme_records(
        schemes, "圣诞树 Christmas tree", top_k=3
    )
    christmas_pass = not christmas_decisions and not any(
        "christmas" in normalize_text(item.get("title")) or "圣诞" in normalize_text(item.get("title"))
        for item in christmas_appearance
    )
    built_in_results.append(
        {
            "case_id": "strict-decorative-negative",
            "scientific_ids": [item.get("scheme_id") for item in christmas_decisions],
            "appearance_ids": [item.get("scheme_id") for item in christmas_appearance],
            "pass": christmas_pass,
        }
    )
    if not christmas_pass:
        errors.append("decorative Christmas-tree content leaked into scientific retrieval")

    atlas_christmas_pass = positive_decorative_intent("圣诞树 Christmas tree") and not positive_decorative_intent(
        "动漫配色科研图，不要圣诞树"
    )
    built_in_results.append(
        {
            "case_id": "strict-scientific-atlas-decorative-gate",
            "positive_decorative_intent_blocked": positive_decorative_intent("圣诞树 Christmas tree"),
            "negated_decorative_intent_allowed": not positive_decorative_intent("动漫配色科研图，不要圣诞树"),
            "pass": atlas_christmas_pass,
        }
    )
    if not atlas_christmas_pass:
        errors.append("scientific atlas decorative-intent gate regression failed")

    benchmark = validate_scheme_benchmark(schemes)
    if benchmark.get("available") and not benchmark.get("pass"):
        failed_ids = [item.get("case_id") for item in benchmark.get("results", []) if not item.get("pass")]
        errors.append("Scheme benchmark failed: " + ", ".join(map(str, failed_ids[:20])))

    return {
        "available": True,
        "pass": not errors,
        "schemes": len(schemes),
        "eligibility": dict(Counter(scheme_eligibility(item) for item in schemes)),
        "block_dispositions": block_audit,
        "image_dispositions": image_audit,
        "native_image_review": {
            "high_risk_unreviewed": len(unreviewed_high_risk),
            "incomplete_linked_reviews": len(incomplete_shared_reviews),
        },
        "candidate_modules": {
            "python": python_candidate_count,
            "r": r_candidate_count,
            "errors": candidate_errors,
            "r_external_parser": "unavailable" if shutil.which("Rscript") is None else "available",
        },
        "heuristic_scientific_previews": len(heuristic_scientific_previews),
        "withheld_scientific_schemes": len(withheld_scientific),
        "built_in_regressions": built_in_results,
        "benchmark": benchmark,
        "errors": errors,
        "warnings": warnings,
    }


def validate_scheme_target(scheme_id: str, catalog_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Run scoped Scheme/code/image/Recipe checks without auditing all 310 Schemes."""
    errors: list[str] = []
    warnings: list[str] = []
    matches = [row for row in load_scheme_records() if str(row.get("scheme_id")) == str(scheme_id)]
    if len(matches) != 1:
        return {
            "available": False,
            "scheme_id": scheme_id,
            "pass": False,
            "errors": [f"expected exactly one Scheme record, found {len(matches)}"],
            "warnings": [],
        }
    record = matches[0]
    catalog_ids = {str(row.get("id")) for row in catalog_records if row.get("id")}
    missing_blocks = sorted(set(lineage_block_ids(record)) - catalog_ids)
    if missing_blocks:
        errors.append("lineage references missing source blocks: " + ", ".join(missing_blocks))

    image_rows = {
        str(row.get("image_id")): row
        for row in load_jsonl(IMAGE_DISPOSITIONS_PATH)
        if row.get("image_id")
    } if IMAGE_DISPOSITIONS_PATH.exists() else {}
    evidence = record.get("image_evidence") if isinstance(record.get("image_evidence"), dict) else {}
    primary_image_id = str(evidence.get("primary_image_id") or "")
    if primary_image_id:
        image_row = image_rows.get(primary_image_id)
        if not image_row:
            errors.append(f"primary image disposition is missing: {primary_image_id}")
        elif scheme_review_status(record) == "native_reviewed":
            if image_row.get("reviewed") is not True:
                errors.append("native-reviewed Scheme points to an image without native review")
            if str(image_row.get("role")) not in {"scientific_result", "published_reference"}:
                errors.append(f"native scientific preview has unsafe role={image_row.get('role')}")
    elif scheme_eligibility(record) in SCIENTIFIC_SCHEME_ELIGIBILITY:
        warnings.append("scientific Scheme has no primary image and remains withheld from the atlas")

    candidate_paths = record.get("candidate_code_path") if isinstance(record.get("candidate_code_path"), dict) else {}
    candidate_checks: dict[str, Any] = {}
    metadata_path = SCHEME_CANDIDATE_ROOT / str(scheme_id) / "metadata.json"
    metadata = load_json_object(metadata_path, {}) if metadata_path.is_file() else {}
    for backend, relative in candidate_paths.items():
        path = (SKILL_ROOT / str(relative)).resolve()
        in_root = SCHEME_CANDIDATE_ROOT.resolve() in path.parents
        exists = path.is_file()
        parse_ok = False
        callable_entrypoint = False
        if in_root and exists:
            text = read_text(path)
            callable_entrypoint = (
                "def build_candidate_plot(" in text
                if backend == "python"
                else "build_candidate_plot <- function(" in text
            )
            try:
                if backend == "python":
                    ast.parse(text, filename=str(path))
                parse_ok = True
            except SyntaxError as exc:
                errors.append(f"{backend} candidate syntax error: {exc.msg}")
        if not in_root or not exists:
            errors.append(f"missing/out-of-root {backend} candidate: {relative}")
        if metadata and bool(metadata.get("callable")) != callable_entrypoint:
            errors.append(
                f"{backend} candidate callable metadata/entrypoint mismatch: "
                f"metadata={bool(metadata.get('callable'))} entrypoint={callable_entrypoint}"
            )
        candidate_checks[str(backend)] = {
            "path_exists": exists,
            "in_candidate_root": in_root,
            "parse": parse_ok,
            "callable_entrypoint": callable_entrypoint,
        }
    if candidate_paths and not metadata:
        errors.append("candidate metadata is missing")

    installed = formal_recipe_index()
    declared_recipe_ids = [
        str(value)
        for value in as_list(
            record.get("recipe_ids")
            or (record.get("validation") or {}).get("recipe_ids")
        )
        if value
    ]
    missing_recipes = sorted(recipe_id for recipe_id in declared_recipe_ids if recipe_id not in installed)
    if missing_recipes:
        errors.append("declared formal Recipes are not installed: " + ", ".join(missing_recipes))
    target_application = record.get("target_application") if isinstance(record.get("target_application"), dict) else {}
    target_methods = [normalize_analysis_method(value) for value in as_list(target_application.get("compatible_analysis_methods"))]
    target_method = next((value for value in target_methods if value in {"ora", "gsea"}), scheme_analysis_method(record))
    target_core_question = (
        "sample_level_composition"
        if str(record.get("geometry_subtype")) == "stacked_composition_bar"
        and canonical_family(record.get("broad_family")) == "composition"
        else canonical_family(record.get("broad_family"))
    )
    execution_plans = {
        backend: scheme_execution_plan(
            record,
            {
                "backend": backend,
                "action_intent": "adapt",
                "core_question": target_core_question,
                "analysis_method": target_method,
                "input_objects": set(),
                "component_targets": [],
            },
        )
        for backend in ("python", "r")
    }
    return {
        "available": True,
        "scheme_id": scheme_id,
        "pass": not errors,
        "eligibility": scheme_eligibility(record),
        "geometry_subtype": record.get("geometry_subtype"),
        "review_status": scheme_review_status(record),
        "candidate_checks": candidate_checks,
        "execution_plans": execution_plans,
        "errors": errors,
        "warnings": warnings,
    }


def command_validate(args: argparse.Namespace) -> int:
    errors = validate_manifest_paths()
    warnings: list[str] = []
    freshness = catalog_freshness()
    records = load_jsonl(CATALOG_PATH) if CATALOG_PATH.exists() else []
    if not freshness.get("fresh"):
        errors.append("catalog is stale or missing; run build before validation")
    catalog_by_id = {record.get("id"): record for record in records if record.get("id")}
    recipe_paths = sorted(RECIPES_ROOT.rglob("recipe.json"))
    recipe_ids = {json.loads(read_text(path)).get("id") for path in recipe_paths}
    if args.id:
        recipe_paths = [path for path in recipe_paths if path.parent.name == args.id or json.loads(read_text(path)).get("id") == args.id]
        if not recipe_paths:
            errors.append(f"recipe not found: {args.id}")
    elif args.scheme_id:
        recipe_paths = []
    for path in recipe_paths:
        recipe_errors, recipe_warnings = validate_recipe(path, catalog_by_id=catalog_by_id, recipe_ids=recipe_ids)
        errors.extend(recipe_errors)
        warnings.extend(recipe_warnings)

    coverage = json.loads(read_text(COVERAGE_PATH)) if COVERAGE_PATH.exists() else None
    if args.all:
        if not coverage:
            errors.append("coverage.json missing; run build")
        else:
            for name, passed in coverage.get("expectations_pass", {}).items():
                if not passed:
                    errors.append(f"source inventory mismatch: {name}")
    benchmark = benchmark_search(records) if args.all and records else {"available": False}
    if benchmark.get("available") and not benchmark.get("pass"):
        errors.append(f"benchmark failed: top3_rate={benchmark.get('top3_rate')} total={benchmark.get('total')}")
    visual_protocol = validate_visual_benchmark(records) if args.all and records else {"available": False}
    if visual_protocol.get("available") and not visual_protocol.get("pass"):
        errors.extend("visual benchmark protocol: " + item for item in visual_protocol.get("errors", []))
    visual_execution = validate_visual_review_results() if args.all else {"available": False}
    if visual_execution.get("available") and not visual_execution.get("pass"):
        errors.extend("executed visual benchmark: " + item for item in visual_execution.get("errors", []))
    exact_render_review = validate_exact_render_reviews(records) if args.all and records else {"available": False}
    if exact_render_review.get("available") and not exact_render_review.get("pass"):
        errors.extend("exact render review: " + item for item in exact_render_review.get("errors", []))
    source_checksums = validate_source_checksums() if args.all else {"available": False}
    if source_checksums.get("available") and not source_checksums.get("pass"):
        errors.extend("source checksums: " + item for item in source_checksums.get("errors", []))
    style_atlas = validate_style_atlas(records) if args.all and records else {"available": False}
    if style_atlas.get("available") and not style_atlas.get("pass"):
        errors.extend("style atlas: " + item for item in style_atlas.get("errors", []))
    warnings.extend("style atlas: " + item for item in style_atlas.get("warnings", []))
    scheme_target = validate_scheme_target(args.scheme_id, records) if args.scheme_id else {"available": False}
    if scheme_target.get("available") and not scheme_target.get("pass"):
        errors.extend("target Scheme: " + item for item in scheme_target.get("errors", []))
    elif args.scheme_id and not scheme_target.get("available"):
        errors.extend("target Scheme: " + item for item in scheme_target.get("errors", ["unavailable"]))
    warnings.extend("target Scheme: " + item for item in scheme_target.get("warnings", []))
    strict = bool(getattr(args, "strict", False))
    if strict and not args.all:
        errors.append("--strict requires --all")
    scheme_v2 = validate_scheme_v2_strict(records) if strict and args.all else {"available": False}
    if scheme_v2.get("available") and not scheme_v2.get("pass"):
        errors.extend("scheme v2: " + item for item in scheme_v2.get("errors", []))
    elif strict and args.all and not scheme_v2.get("available"):
        errors.extend("scheme v2: " + item for item in scheme_v2.get("errors", ["strict artifacts unavailable"]))
    warnings.extend("scheme v2: " + item for item in scheme_v2.get("warnings", []))
    result = {
        "ok": not errors,
        "recipes_checked": len(recipe_paths),
        "errors": errors,
        "warnings": warnings,
        "catalog_freshness": freshness,
        "coverage": coverage,
        "source_checksums": source_checksums,
        "benchmark": benchmark,
        "visual_benchmark_protocol": visual_protocol,
        "visual_benchmark_execution": visual_execution,
        "exact_render_review": exact_render_review,
        "style_atlas": style_atlas,
        "scheme_v2": scheme_v2,
        "scheme_target": scheme_target,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 8


MANAGED_SNAPSHOT_FILES = {"SNAPSHOT.json"}


def snapshot_file_allowed(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    return path.is_file() and ".state" not in rel.parts and "_tools" not in rel.parts and rel.as_posix() not in MANAGED_SNAPSHOT_FILES


def snapshot_content_manifest(root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    manifest: dict[str, dict[str, Any]] = {}
    excluded: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if not snapshot_file_allowed(path, root):
            excluded.append(rel)
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest[rel] = {"sha256": digest, "bytes": path.stat().st_size}
    return manifest, excluded


def inventory_signature(root: Path) -> dict[str, Any]:
    manifest, excluded = snapshot_content_manifest(root)
    digest = hashlib.sha256()
    for rel, metadata in manifest.items():
        digest.update(rel.encode("utf-8"))
        digest.update(metadata["sha256"].encode("ascii"))
    return {"files": len(manifest), "signature": digest.hexdigest(), "excluded": excluded}


def snapshot_diff(installed: dict[str, dict[str, Any]], incoming: dict[str, dict[str, Any]]) -> dict[str, Any]:
    installed_paths = set(installed)
    incoming_paths = set(incoming)
    added = sorted(incoming_paths - installed_paths)
    missing_upstream = sorted(installed_paths - incoming_paths)
    changed = sorted(path for path in installed_paths & incoming_paths if installed[path]["sha256"] != incoming[path]["sha256"])
    unchanged = len(installed_paths & incoming_paths) - len(changed)
    return {
        "added": added,
        "changed": changed,
        "missing_upstream_preserved": missing_upstream,
        "unchanged": unchanged,
        "would_change": bool(added or changed),
    }


def copy_snapshot_incremental(source: Path, destination: Path) -> dict[str, int]:
    copied = 0
    unchanged = 0
    for path in source.rglob("*"):
        if not path.is_file() or not snapshot_file_allowed(path, source):
            continue
        rel = path.relative_to(source)
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size == path.stat().st_size and hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(path.read_bytes()).digest():
            unchanged += 1
            continue
        shutil.copy2(path, target)
        copied += 1
    return {"copied": copied, "unchanged": unchanged}


def scan_snapshot_secrets(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    readable_suffixes = {".md", ".txt", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".py", ".r"}
    for path in root.rglob("*"):
        if not path.is_file() or not snapshot_file_allowed(path, root) or path.suffix.lower() not in readable_suffixes:
            continue
        try:
            text = read_text(path)
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in {
            "wechat_session_secret": re.compile(r"pass_ticket|exportkey|wx_header=|sessionid=undefined|\bkey=[0-9a-f]{32,}", re.I),
            "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        }.items():
            if pattern.search(text):
                findings.append({"path": path.relative_to(root).as_posix(), "rule": label})
    return findings


def disposition_audit(path: Path, kind: str, expected_count: int) -> dict[str, Any]:
    if not path.exists():
        return {
            "available": False,
            "pass": False,
            "records": 0,
            "unique_ids": 0,
            "duplicates": [],
            "invalid_dispositions": [],
        }
    rows = load_jsonl(path)
    identifiers = [disposition_record_id(row, kind) for row in rows]
    counts = Counter(identifier for identifier in identifiers if identifier)
    duplicates = sorted(identifier for identifier, count in counts.items() if count != 1)
    allowed = BLOCK_DISPOSITIONS if kind == "block" else IMAGE_DISPOSITIONS
    invalid = sorted(
        {
            disposition_value(row, kind)
            for row in rows
            if disposition_value(row, kind) not in allowed
        }
    )
    missing_id_rows = sum(1 for identifier in identifiers if not identifier)
    return {
        "available": True,
        "pass": len(rows) == expected_count
        and len(counts) == expected_count
        and not duplicates
        and not invalid
        and not missing_id_rows,
        "records": len(rows),
        "unique_ids": len(counts),
        "expected": expected_count,
        "duplicates": duplicates,
        "missing_id_rows": missing_id_rows,
        "invalid_dispositions": invalid,
        "dispositions": dict(Counter(disposition_value(row, kind) for row in rows)),
    }


def source_inventory_read_only(source: Path) -> dict[str, Any]:
    markdown_files = [
        path
        for path in sorted(source.rglob("*.md"))
        if path.name.lower() != "readme.md" and ".state" not in path.parts and "_tools" not in path.parts
    ]
    fence_count = 0
    raw_languages: Counter[str] = Counter()
    image_targets: set[str] = set()
    missing_images: list[str] = []
    for path in markdown_files:
        try:
            lines = read_text(path).splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        in_fence = False
        for line in lines:
            match = FENCE_RE.match(line)
            if match and match.group(1) and not in_fence:
                in_fence = True
                fence_count += 1
                raw_languages[match.group(1).lower()] += 1
                continue
            if in_fence and re.match(r"^\s*```\s*$", line):
                in_fence = False
            for image_match in IMAGE_RE.finditer(line):
                target = image_match.group(1).strip().strip("<>")
                if re.match(r"https?://", target, re.I):
                    continue
                target = re.sub(r'\s+["\'].*["\']\s*$', "", target)
                resolved = (path.parent / unquote(target)).resolve()
                identity = str(resolved).lower()
                image_targets.add(identity)
                if not resolved.exists() and len(missing_images) < 20:
                    missing_images.append(path.relative_to(source).as_posix() + " -> " + target)
    image_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff"}
    image_files = [
        path
        for path in source.rglob("*")
        if path.is_file() and path.suffix.lower() in image_suffixes and ".state" not in path.parts and "_tools" not in path.parts
    ]
    return {
        "articles": len(markdown_files),
        "source_blocks": fence_count,
        "referenced_images": len(image_targets),
        "image_files": len(image_files),
        "raw_languages": dict(raw_languages),
        "missing_image_references": missing_images,
        "expectations_pass": {
            "articles": len(markdown_files) == EXPECTED["articles"],
            "source_blocks": fence_count == EXPECTED["source_blocks"],
            "images": len(image_targets) == EXPECTED["images"],
        },
    }


def command_audit_source(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"source directory does not exist: {source}")
    inventory = source_inventory_read_only(source)
    block_audit = disposition_audit(BLOCK_DISPOSITIONS_PATH, "block", EXPECTED["source_blocks"])
    image_audit = disposition_audit(IMAGE_DISPOSITIONS_PATH, "image", EXPECTED["images"])
    schemes = load_scheme_records()
    coverage = load_json_object(SCHEME_COVERAGE_PATH, {}) if SCHEME_COVERAGE_PATH.exists() else {}
    errors: list[str] = []
    warnings: list[str] = []
    for name, passed in inventory["expectations_pass"].items():
        if not passed:
            errors.append(f"source inventory mismatch: {name}")
    for name, audit in (("block", block_audit), ("image", image_audit)):
        if audit.get("available") and not audit.get("pass"):
            errors.append(f"{name} dispositions are incomplete or non-unique")
        elif not audit.get("available"):
            warnings.append(f"{name} disposition artifact is not available")
    if inventory.get("missing_image_references"):
        errors.append("source contains missing local image references")
    result = {
        "ok": not errors,
        "mode": "read_only",
        "source": str(source),
        "inventory": inventory,
        "block_dispositions": block_audit,
        "image_dispositions": image_audit,
        "schemes": {
            "available": bool(schemes),
            "count": len(schemes),
            "eligibility": dict(Counter(scheme_eligibility(item) for item in schemes)),
            "subtypes": dict(Counter(str(item.get("geometry_subtype")) for item in schemes)),
        },
        "scheme_coverage": coverage,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 8


def load_scheme_builder_module() -> Any:
    """Load the sibling Scheme builder without depending on the caller's cwd."""
    module_name = "_plot_code_retriever_scheme_builder"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = SKILL_ROOT / "scripts" / "build_scheme_catalog.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Scheme builder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def prepare_scheme_build(
    records: list[dict[str, Any]],
    source: Path,
) -> tuple[Any, dict[str, str], dict[str, Any]]:
    builder = load_scheme_builder_module()
    curation = builder.load_json(builder.CURATION_PATH, {"overrides": {}})
    reviews, review_files = builder.load_native_reviews(builder.DEFAULT_NATIVE_REVIEWS)
    files, coverage = builder.build_all(records, curation, source, reviews, review_files)
    return builder, files, coverage


def command_update(args: argparse.Namespace) -> int:
    source = Path(args.source).resolve()
    if not source.exists():
        print(json.dumps({"error": "source does not exist", "source": str(source)}, ensure_ascii=False), file=sys.stderr)
        return 4
    installed_manifest, installed_excluded = snapshot_content_manifest(SOURCE_ROOT)
    incoming_manifest, incoming_excluded = snapshot_content_manifest(source)
    before = inventory_signature(SOURCE_ROOT)
    incoming = inventory_signature(source)
    diff = snapshot_diff(installed_manifest, incoming_manifest)
    secret_findings = scan_snapshot_secrets(source)
    if args.dry_run:
        print(json.dumps({
            "mode": "dry-run",
            "installed": before,
            "incoming": incoming,
            "diff": diff,
            "excluded": {"installed": installed_excluded, "incoming": incoming_excluded},
            "secret_scan": {"ok": not secret_findings, "findings": secret_findings},
            "would_change": diff["would_change"],
            "scheme_rebuild_required": diff["would_change"],
            "note": "curated recipes, stable IDs, and existing lineage are never overwritten; upstream-missing files are preserved",
        }, ensure_ascii=False, indent=2))
        return 0 if not secret_findings else 12
    if not args.apply:
        print(json.dumps({"error": "use --dry-run or --apply"}, ensure_ascii=False), file=sys.stderr)
        return 9
    if secret_findings:
        print(json.dumps({"error": "incoming snapshot failed secret scan", "findings": secret_findings}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 12
    if not diff["would_change"]:
        print(json.dumps({
            "mode": "apply",
            "changed": False,
            "diff": diff,
            "scheme_catalog_rebuilt": False,
            "curated_recipes_preserved": True,
        }, ensure_ascii=False, indent=2))
        return 0

    assets_root = SOURCE_ROOT.parent.resolve()
    stage = assets_root / (".source-archive-stage-" + hashlib.sha256(now_iso().encode()).hexdigest()[:10])
    backup = assets_root / (".source-archive-backup-" + hashlib.sha256((now_iso() + "backup").encode()).hexdigest()[:10])
    if stage.exists() or backup.exists():
        print(json.dumps({"error": "update staging path collision"}, ensure_ascii=False), file=sys.stderr)
        return 13
    builder = None
    staged_scheme_files: dict[str, str] = {}
    staged_scheme_coverage: dict[str, Any] = {}
    scheme_changed_files: list[str] = []
    try:
        stage.mkdir(parents=True)
        preserved = copy_snapshot_incremental(SOURCE_ROOT, stage)
        applied = copy_snapshot_incremental(source, stage)
        staged_records, staged_coverage = build_catalog(stage, write=False)
        baseline_ok = (
            staged_coverage.get("records", {}).get("article", 0) >= EXPECTED["articles"]
            and staged_coverage.get("records", {}).get("source_block", 0) >= EXPECTED["source_blocks"]
            and staged_coverage.get("records", {}).get("image", 0) >= EXPECTED["images"]
        )
        if not baseline_ok:
            raise ValueError("staged snapshot failed baseline inventory validation")
        staged_by_id = {record.get("id"): record for record in staged_records if record.get("id")}
        staged_recipe_ids = {
            record.get("id") for record in staged_records if record.get("record_type") == "recipe"
        }
        staged_recipe_errors: list[str] = []
        for recipe_path in sorted(RECIPES_ROOT.rglob("recipe.json")):
            recipe_errors, _ = validate_recipe(
                recipe_path,
                catalog_by_id=staged_by_id,
                recipe_ids=staged_recipe_ids,
            )
            staged_recipe_errors.extend(recipe_errors)
        if staged_recipe_errors:
            raise ValueError(
                "staged snapshot breaks curated Recipe provenance or lineage: "
                + "; ".join(staged_recipe_errors[:8])
            )
        builder, staged_scheme_files, staged_scheme_coverage = prepare_scheme_build(staged_records, stage)
        checksum_summary = write_source_checksums(stage)
        existing_snapshot = {}
        if (stage / "SNAPSHOT.json").exists():
            existing_snapshot = json.loads(read_text(stage / "SNAPSHOT.json"))
        existing_snapshot.update({
            "schema_version": 1,
            "updated_at": now_iso(),
            "files": len(snapshot_content_manifest(stage)[0]),
            "source_kind": "incremental_local_archive_update",
            "diff": diff,
            "checksum_verification": {
                "verified_entries": checksum_summary["verified"],
                "intentional_missing_entries": 0,
                "failures": checksum_summary["failures"],
            },
        })
        write_json(stage / "SNAPSHOT.json", existing_snapshot)
        staged_checksum_validation = validate_source_checksums(stage)
        if not staged_checksum_validation.get("pass"):
            raise ValueError("staged snapshot checksum validation failed: " + "; ".join(staged_checksum_validation.get("errors", [])[:8]))
        SOURCE_ROOT.replace(backup)
        try:
            stage.replace(SOURCE_ROOT)
        except Exception:
            backup.replace(SOURCE_ROOT)
            raise
        _, coverage = build_catalog(SOURCE_ROOT, write=True)
        _, scheme_changed_files = builder.write_or_check(staged_scheme_files, check=False)
        scheme_ok, scheme_residual = builder.write_or_check(staged_scheme_files, check=True)
        if not scheme_ok:
            raise ValueError(
                "Scheme v2 artifacts did not converge after rebuild: "
                + ", ".join(scheme_residual[:8])
            )
        shutil.rmtree(backup)
    except Exception as exc:
        if stage.exists() and stage.resolve().parent == assets_root:
            shutil.rmtree(stage)
        rollback_error = None
        if backup.exists() and backup.resolve().parent == assets_root:
            try:
                if SOURCE_ROOT.exists():
                    shutil.rmtree(SOURCE_ROOT)
                backup.replace(SOURCE_ROOT)
                restored_records, _ = build_catalog(SOURCE_ROOT, write=True)
                restored_builder, restored_files, _ = prepare_scheme_build(restored_records, SOURCE_ROOT)
                restored_builder.write_or_check(restored_files, check=False)
            except Exception as rollback_exc:
                rollback_error = f"{type(rollback_exc).__name__}: {rollback_exc}"
        payload = {"error": f"update failed safely: {type(exc).__name__}: {exc}"}
        if rollback_error:
            payload["rollback_error"] = rollback_error
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 13
    print(json.dumps({
        "mode": "apply",
        "changed": True,
        "preserved": preserved,
        "incoming_copy": applied,
        "diff": diff,
        "coverage": coverage,
        "scheme_catalog_rebuilt": True,
        "scheme_changed_files": {
            "count": len(scheme_changed_files),
            "examples": scheme_changed_files[:20],
        },
        "scheme_coverage": staged_scheme_coverage,
        "source_checksums": staged_checksum_validation,
        "curated_recipes_preserved": True,
        "stable_ids_preserved": True,
        "recipe_lineage_validated_before_swap": True,
        "atlas_export_required": "python scripts/export_style_atlas.py --output-dir <dir> --scope all",
    }, ensure_ascii=False, indent=2))
    return 0 if baseline_ok else 13


def command_promote(args: argparse.Namespace) -> int:
    candidate_dir = CANDIDATES_ROOT / args.candidate
    metadata = candidate_dir / "recipe.json"
    if not metadata.exists():
        composition = candidate_dir / "composition.json"
        detail = "composition plan exists but has not been adapted into recipe.json" if composition.exists() else "candidate recipe not found"
        print(json.dumps({"error": detail, "candidate": args.candidate}, ensure_ascii=False), file=sys.stderr)
        return 4
    catalog_records = ensure_catalog()
    catalog_by_id = {record.get("id"): record for record in catalog_records if record.get("id")}
    installed_recipe_ids = {record.get("id") for record in catalog_records if record.get("record_type") == "recipe"}
    recipe = json.loads(read_text(metadata))
    errors, warnings = validate_recipe(metadata, catalog_by_id=catalog_by_id, recipe_ids=installed_recipe_ids | {recipe.get("id")})
    checks = (recipe.get("validation") or {}).get("checks") or {}
    required_checks = {"schema", "syntax", "safety", "fixture", "render", "visual", "semantic", "provenance"}
    incomplete = sorted(name for name in required_checks if checks.get(name) != "pass")
    if recipe.get("validation", {}).get("tier") != "verified" or incomplete:
        errors.append(f"candidate is not fully verified; incomplete checks: {incomplete}")
    if str(recipe.get("id", "")).startswith("candidate-"):
        errors.append("candidate must receive a stable descriptive recipe id before promotion")

    visual_review_path = candidate_dir / "visual-review.json"
    if not visual_review_path.exists():
        errors.append("native visual-review.json is required; deterministic Python checks cannot substitute for visual understanding")
    else:
        try:
            visual_review = json.loads(read_text(visual_review_path))
            if visual_review.get("reviewed") is not True or visual_review.get("decision") != "keep":
                errors.append("visual review must be reviewed=true with decision=keep")
            if visual_review.get("evidence_level") not in {"image_code", "image_code_data"}:
                errors.append("promotion visual review requires image_code or image_code_data evidence")
            if visual_review.get("original_size_reviewed") is not True or visual_review.get("final_size_reviewed") is not True:
                errors.append("visual review must inspect original and final submission sizes")
            serious = [
                issue
                for issue in visual_review.get("issues", [])
                if isinstance(issue, dict)
                and issue.get("severity") in {"blocker", "major"}
                and issue.get("status") != "resolved"
            ]
            if serious:
                errors.append("visual review contains unresolved blocker/major findings")
            render_rel = visual_review.get("render_path")
            if not render_rel:
                errors.append("visual review must reference the exact candidate render")
            else:
                render_path = (candidate_dir / render_rel).resolve()
                try:
                    render_path.relative_to(candidate_dir.resolve())
                except ValueError:
                    errors.append("visual review render_path escapes candidate directory")
                else:
                    if not render_path.exists() or not image_metadata(render_path).get("readable"):
                        errors.append("visual review render is missing or unreadable")
                    elif visual_review.get("render_sha256") and visual_review["render_sha256"] != hashlib.sha256(render_path.read_bytes()).hexdigest():
                        errors.append("visual review render checksum mismatch")
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid visual-review.json: {exc}")

    controller_state_path = candidate_dir / "visual-review-state.json"
    if not controller_state_path.exists():
        errors.append(
            "visual-review-state.json is required; promotion needs the hash-bound, "
            "maximum-three-round native-review controller record"
        )
    else:
        try:
            from visual_review_controller import read_state, validate_state

            controller_state = read_state(controller_state_path)
            controller_result = validate_state(
                controller_state,
                verify_files=True,
                require_terminal=True,
            )
            if not controller_result.get("ready_for_delivery"):
                errors.append(
                    "visual review controller is not delivery-ready: "
                    + json.dumps(controller_result.get("errors") or [], ensure_ascii=False)
                )
            code_rel = (recipe.get("files") or {}).get("code")
            if code_rel:
                candidate_code_path = (candidate_dir / str(code_rel)).resolve()
                baseline_code_sha = str((controller_state.get("baseline") or {}).get("code_sha256") or "")
                baseline_code_sha = baseline_code_sha.removeprefix("sha256:")
                if candidate_code_path.is_file():
                    candidate_code_sha = hashlib.sha256(candidate_code_path.read_bytes()).hexdigest()
                    if baseline_code_sha != candidate_code_sha:
                        errors.append("visual review controller code hash does not match the candidate Recipe code")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid visual-review-state.json: {exc}")

    files = recipe.get("files") or {}
    example_rel = files.get("example")
    if not errors and example_rel:
        example_path = (candidate_dir / example_rel).resolve()
        environment = os.environ.copy()
        environment["MPLBACKEND"] = "Agg"
        try:
            if recipe.get("backend") == "python":
                process = subprocess.run(
                    [sys.executable, str(example_path)],
                    cwd=candidate_dir,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                )
            else:
                rscript = locate_rscript()
                if not rscript:
                    errors.append("Rscript unavailable; candidate execution gate cannot run")
                    process = None
                else:
                    expression = "pdf(tempfile(fileext='.pdf')); source(commandArgs(trailingOnly=TRUE)[1], chdir=TRUE); while(dev.cur()>1) dev.off()"
                    process = subprocess.run(
                        [rscript, "-e", expression, str(example_path)],
                        cwd=candidate_dir,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=120,
                    )
        except subprocess.TimeoutExpired:
            process = None
            errors.append("candidate example execution timed out after 120 seconds")
        if process is not None and process.returncode:
            errors.append(f"candidate example execution failed: {(process.stderr or process.stdout).strip()[-600:]}")
    if errors:
        print(json.dumps({"error": "promotion gate failed", "details": errors, "warnings": warnings}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 10
    if not args.apply:
        print(json.dumps({"candidate": args.candidate, "eligible": True, "would_promote_to": f"assets/recipes/{recipe['id']}", "apply": False}, ensure_ascii=False, indent=2))
        return 0
    target = RECIPES_ROOT / recipe["id"]
    if target.exists():
        print(json.dumps({"error": "target recipe already exists", "id": recipe["id"]}, ensure_ascii=False), file=sys.stderr)
        return 11
    staging = RECIPES_ROOT / (".promote-" + recipe["id"])
    if staging.exists():
        print(json.dumps({"error": "promotion staging path already exists"}, ensure_ascii=False), file=sys.stderr)
        return 11
    try:
        shutil.copytree(candidate_dir, staging, ignore=shutil.ignore_patterns("composition.json"))
        staging.replace(target)
        build_catalog(SOURCE_ROOT, write=True)
    except Exception as exc:
        if staging.exists() and staging.resolve().parent == RECIPES_ROOT.resolve():
            shutil.rmtree(staging)
        if target.exists() and target.resolve().parent == RECIPES_ROOT.resolve():
            shutil.rmtree(target)
            build_catalog(SOURCE_ROOT, write=True)
        print(json.dumps({"error": f"promotion failed atomically: {type(exc).__name__}: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 11
    print(json.dumps({"promoted": recipe["id"], "target": rel_posix(target)}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline scientific plot catalog and recipe manager")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build catalog from bundled source and curated recipes")
    build.add_argument("--source", help="Optional alternate read-only archive root")
    build.set_defaults(func=command_build)

    search = sub.add_parser("search", help="Search recipes and source snippets")
    search.add_argument("--query", required=True)
    search.add_argument("--backend", choices=["r", "python"])
    search.add_argument("--family")
    search.add_argument("--domain")
    search.add_argument("--top-k", type=int, default=3)
    search.add_argument("--format", choices=["json", "markdown"], default="json")
    search.add_argument("--include-code", action="store_true")
    search.set_defaults(func=command_search_v2)

    atlas = sub.add_parser("atlas", help="Search the optional offline visual style atlas")
    atlas.add_argument("--query", help="Natural-language style or analysis-use query")
    atlas.add_argument(
        "--scope",
        choices=["scientific", "modifier", "resource", "excluded", "all"],
        default="scientific",
        help="Scheme-v2 eligibility scope (default: scientific)",
    )
    atlas.add_argument("--family", help="Exact normalized plot-family filter")
    atlas.add_argument("--subtype", help="Exact Scheme-v2 geometry_subtype filter")
    atlas.add_argument("--method", help="Exact Scheme-v2 analysis_method filter (for example ORA or GSEA)")
    atlas.add_argument("--review-status", help="Exact Scheme-v2 visual review-status filter")
    atlas.add_argument("--coverage", help="Exact coverage_status filter")
    atlas.add_argument("--backend", choices=["r", "python"], help="Backend compatibility filter")
    atlas.add_argument("--top-k", type=int, default=10)
    atlas.add_argument("--format", choices=["json", "text"], default="json")
    atlas.set_defaults(func=command_atlas_v2)

    inspect = sub.add_parser("inspect", help="Inspect a catalog record")
    inspect.add_argument("--id", required=True)
    inspect.add_argument("--include-code", action="store_true")
    inspect.add_argument("--include-lineage", action="store_true", help="Include Scheme-v2 code lineage")
    inspect.add_argument("--include-visual", action="store_true", help="Include image evidence and visual fingerprint")
    inspect.set_defaults(func=command_inspect_v2)

    compose = sub.add_parser("compose", help="Materialize a callable backend-pure component composition")
    compose.add_argument("--base-id", required=True)
    compose.add_argument("--adapter-id")
    compose.add_argument("--modifier", action="append", default=[])
    compose.add_argument("--backend", choices=["r", "python"], required=True)
    compose.add_argument("--save-candidate", action="store_true")
    compose.set_defaults(func=command_compose)

    preflight = sub.add_parser("preflight", help="Check runtime, dependencies, syntax, and entrypoints before execution")
    preflight_target = preflight.add_mutually_exclusive_group(required=True)
    preflight_target.add_argument("--recipe-id")
    preflight_target.add_argument("--base-id")
    preflight.add_argument("--adapter-id")
    preflight.add_argument("--modifier", action="append", default=[])
    preflight.add_argument("--backend", choices=["r", "python"])
    preflight.set_defaults(func=command_preflight)

    render = sub.add_parser("render", help="Execute one formal Recipe or composition and render original/final PNGs")
    render_target = render.add_mutually_exclusive_group(required=True)
    render_target.add_argument("--recipe-id")
    render_target.add_argument("--base-id")
    render.add_argument("--adapter-id")
    render.add_argument("--modifier", action="append", default=[])
    render.add_argument("--backend", choices=["r", "python"])
    render.add_argument("--input", required=True, type=Path)
    render.add_argument("--output-dir", required=True, type=Path)
    render.add_argument("--params-json", help="Inline JSON object or path; for compositions, keyed by Recipe ID")
    render.add_argument("--width-mm", type=float, default=85.0)
    render.add_argument("--height-mm", type=float, default=70.0)
    render.add_argument("--dpi", type=int, default=300)
    render.add_argument("--timeout-seconds", type=float, default=120.0)
    render.add_argument("--review-state", help="Initialize hash-bound native-review state after a successful render")
    render.add_argument("--review-id")
    render.add_argument("--scheme-id")
    render.set_defaults(func=command_render)

    image_meta = sub.add_parser("image-meta", help="Inspect deterministic image metadata")
    group = image_meta.add_mutually_exclusive_group(required=True)
    group.add_argument("--id")
    group.add_argument("--path")
    image_meta.set_defaults(func=command_image_meta)

    validate = sub.add_parser("validate", help="Validate recipes, inventory, and retrieval benchmark")
    validate_group = validate.add_mutually_exclusive_group(required=True)
    validate_group.add_argument("--all", action="store_true")
    validate_group.add_argument("--id", help="Validate one formal Recipe ID")
    validate_group.add_argument("--scheme-id", help="Validate one Scheme and its code/image/Recipe links")
    validate.add_argument("--strict", action="store_true", help="Apply Scheme-v2 release gates")
    validate.set_defaults(func=command_validate)

    audit_source = sub.add_parser("audit-source", help="Read-only source inventory and disposition audit")
    audit_source.add_argument("--source", required=True)
    audit_source.set_defaults(func=command_audit_source)

    update = sub.add_parser("update", help="Incrementally refresh the bundled source snapshot")
    update.add_argument("--source", required=True)
    update_mode = update.add_mutually_exclusive_group(required=True)
    update_mode.add_argument("--dry-run", action="store_true")
    update_mode.add_argument("--apply", action="store_true")
    update.set_defaults(func=command_update)

    promote = sub.add_parser("promote", help="Promote a fully verified candidate recipe")
    promote.add_argument("--candidate", required=True)
    promote.add_argument("--apply", action="store_true")
    promote.set_defaults(func=command_promote)
    return parser


def main() -> int:
    # Windows may expose a legacy GBK console even though catalog text is UTF-8.
    # Emit a stable UTF-8 CLI contract for both interactive use and pipelines.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            except (OSError, ValueError):
                pass
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
