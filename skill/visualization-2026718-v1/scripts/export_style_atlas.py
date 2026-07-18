#!/usr/bin/env python3
"""Export the Scheme v2 scientific visual atlas as HTML, Markdown, and CSV.

The exporter is deliberately presentation-only.  It never promotes a Scheme or
changes source/catalog records.  ``scheme-catalog.jsonl`` is preferred; the
legacy style atlas is accepted only as a migration fallback.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
REFS = SKILL_ROOT / "references"
SCHEME_PATH = REFS / "scheme-catalog.jsonl"
SCHEME_COVERAGE_PATH = REFS / "scheme-coverage.json"
IMAGE_DISPOSITIONS_PATH = REFS / "image-dispositions.jsonl"
LEGACY_ATLAS_PATH = REFS / "style-atlas.jsonl"
CATALOG_PATH = REFS / "catalog.jsonl"
CATALOG_COVERAGE_PATH = REFS / "coverage.json"


CATEGORY_LABELS = {
    "scientific": "科研方案",
    "semantic_modifier": "语义组件",
    "aesthetic_modifier": "美学 / 配色",
    "layout_resource": "布局资源",
    "visual_reference": "视觉参考",
    "excluded": "排除审计",
}

ELIGIBILITY_TO_CATEGORY = {
    "scientific_scheme": "scientific",
    "semantic_modifier": "semantic_modifier",
    "aesthetic_modifier": "aesthetic_modifier",
    "layout_resource": "layout_resource",
    "visual_reference": "visual_reference",
    "excluded": "excluded",
}

IMAGE_ROLE_LABELS = {
    "scientific_result": "科研结果图",
    "published_reference": "论文参考图",
    "intermediate_step": "中间绘图步骤",
    "data_or_console_output": "数据或控制台输出",
    "cover_or_web_screenshot": "封面或网页截图",
    "code_screenshot": "代码截图",
    "promotion_or_qr": "宣传图或二维码",
    "decorative_result": "装饰性结果",
    "uncertain": "待确认",
}

NATIVE_REVIEW_VALUES = {
    "native_reviewed",
    "native-reviewed",
    "native_visual_reviewed",
    "visual_confirmed",
    "visually_confirmed",
}

SAFE_SCIENTIFIC_IMAGE_ROLES = {"scientific_result", "published_reference"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Expected JSON object at {path}:{line_number}")
            records.append(value)
    return records


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def join_values(value: Any, separator: str = "；") -> str:
    if isinstance(value, dict):
        return separator.join(f"{key}: {item}" for key, item in value.items())
    if isinstance(value, list):
        return separator.join(str(item) for item in value)
    return str(value or "未声明")


def review_value(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("status", "tier", "review_status", "image_role_review"):
            if value.get(key):
                return str(value[key]).strip().lower()
        return "unreviewed"
    if value is True:
        return "native_reviewed"
    return str(value or "unreviewed").strip().lower()


def is_native_reviewed(value: Any) -> bool:
    return review_value(value) in NATIVE_REVIEW_VALUES


def index_catalog() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    images: dict[str, dict[str, Any]] = {}
    articles: dict[str, dict[str, Any]] = {}
    for record in load_jsonl(CATALOG_PATH):
        kind = record.get("record_type") or record.get("type")
        record_id = str(record.get("id") or "")
        if kind == "image" and record_id:
            images[record_id] = record
        elif kind == "article" and record_id:
            articles[record_id] = record
    return images, articles


def index_image_dispositions() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in load_jsonl(IMAGE_DISPOSITIONS_PATH):
        image_id = str(record.get("image_id") or record.get("id") or "")
        if image_id:
            result[image_id] = record
    return result


def image_ids_from_evidence(evidence: dict[str, Any]) -> list[str]:
    ordered: list[str] = []
    for key in ("primary_image_id", "final_image_ids", "reference_image_ids", "intermediate_image_ids"):
        for value in as_list(evidence.get(key)):
            value = str(value)
            if value and value not in ordered:
                ordered.append(value)
    return ordered


def resolve_skill_image(relative: str) -> Path | None:
    if not relative:
        return None
    candidate = (SKILL_ROOT / relative).resolve()
    try:
        candidate.relative_to(SKILL_ROOT.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def normalise_scheme(
    record: dict[str, Any],
    images: dict[str, dict[str, Any]],
    dispositions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    scheme_id = str(record.get("scheme_id") or record.get("id") or "")
    eligibility = str(record.get("eligibility") or "excluded")
    category = ELIGIBILITY_TO_CATEGORY.get(eligibility, "excluded")
    evidence = record.get("image_evidence") or {}
    evidence_ids = image_ids_from_evidence(evidence)
    primary_id = str(evidence.get("primary_image_id") or (evidence_ids[0] if evidence_ids else ""))
    image_record = images.get(primary_id, {})
    primary_path_raw = str(image_record.get("path") or "")
    primary_path = primary_path_raw if resolve_skill_image(primary_path_raw) else ""
    image_disposition = dispositions.get(primary_id, {})
    image_role = str(
        image_disposition.get("role")
        or image_disposition.get("disposition")
        or image_record.get("role")
        or "uncertain"
    )
    review_status = review_value(evidence.get("review_status") or record.get("review_status"))
    native_reviewed = is_native_reviewed(review_status)
    consistency = str(evidence.get("code_image_consistency") or "unknown")
    atlas_category = category
    section_notes = {
        "semantic_modifier": "进入语义组件分区；必须与兼容父 Scheme 组合",
        "aesthetic_modifier": "进入美学 / 配色分区；不改变数据含义",
        "layout_resource": "进入布局资源分区；不作为独立科学证据",
        "visual_reference": "进入视觉参考分区；不代表存在可执行复现代码",
        "excluded": "来源记录已标记为 excluded；仅保留审计，不进入科研检索或科研图册",
    }
    atlas_exclusion_reason = section_notes.get(category, "")
    if category == "scientific" and image_role not in SAFE_SCIENTIFIC_IMAGE_ROLES:
        atlas_category = "excluded"
        atlas_exclusion_reason = f"科研图册禁用图片角色：{image_role}"
    elif category == "scientific" and not native_reviewed:
        atlas_category = "excluded"
        atlas_exclusion_reason = "尚未完成原生视觉复核，不能进入科研默认图册"
    elif category == "scientific" and consistency.lower() in {"mismatch", "fail", "failed"}:
        atlas_category = "excluded"
        atlas_exclusion_reason = "代码—图片一致性未通过，不能进入科研默认图册"
    elif category == "scientific" and not primary_path:
        atlas_category = "excluded"
        atlas_exclusion_reason = "原生复核图片缺失或路径越界，不能进入科研默认图册"

    source = record.get("source") or {}
    source_semantics = record.get("source_semantics") or {}
    target = record.get("target_application") or {}
    validation = record.get("validation") or {}
    lineage = record.get("code_lineage") or {}
    code_ids = [str(item) for item in as_list(lineage.get("block_ids"))]
    if not code_ids:
        for key in ("base_block_ids", "modifier_block_ids", "layout_block_ids", "export_block_ids"):
            for value in as_list(lineage.get(key)):
                value = str(value)
                if value not in code_ids:
                    code_ids.append(value)
    aliases = [str(item) for item in as_list(record.get("aliases_zh")) + as_list(record.get("aliases_en"))]
    fuzzy = [str(item) for item in as_list(record.get("fuzzy_descriptions"))]
    feature_terms = [str(item) for item in as_list(record.get("visual_feature_terms"))]
    why_match_parts = []
    if aliases:
        why_match_parts.append("名称/别名：" + "、".join(aliases[:5]))
    if feature_terms:
        why_match_parts.append("视觉特征：" + "、".join(feature_terms[:6]))
    if fuzzy:
        why_match_parts.append("可识别描述：" + fuzzy[0])

    code_status = str(record.get("code_status") or validation.get("code") or "unknown")
    if validation.get("promotion_status") or validation.get("recipe_status") or validation.get("status"):
        recipe_status = str(
            validation.get("promotion_status") or validation.get("recipe_status") or validation.get("status")
        )
    elif validation.get("promotable") is True:
        recipe_status = "candidate"
    else:
        recipe_status = "not_promotable"
    return {
        "scheme_id": scheme_id,
        "title": str(record.get("title") or scheme_id),
        "eligibility": eligibility,
        "category": atlas_category,
        "original_category": category,
        "atlas_exclusion_reason": atlas_exclusion_reason,
        "broad_family": str(record.get("broad_family") or "unknown"),
        "geometry_subtype": str(record.get("geometry_subtype") or "unknown"),
        "appearance_subtype": str(record.get("appearance_subtype") or ""),
        "analysis_method": str(record.get("analysis_method") or "unknown"),
        "scientific_position": str(target.get("question") or source_semantics.get("question") or "未声明"),
        "source_semantics": source_semantics,
        "target_application": target,
        "visual_channels": record.get("visual_channels") or {},
        "required_inputs": record.get("required_inputs") or [],
        "optional_inputs": record.get("optional_inputs") or [],
        "transformations": record.get("transformations") or [],
        "supported_claims": record.get("supported_claims") or [],
        "claim_limits": record.get("claim_limits") or [],
        "misread_risks": record.get("misread_risks") or [],
        "recommended_companion": record.get("recommended_companion") or "无",
        "backends": [str(item) for item in as_list(record.get("backends"))],
        "code_status": code_status,
        "recipe_status": recipe_status,
        "code_block_ids": code_ids,
        "object_chain": lineage.get("object_chain") or [],
        "image_ids": evidence_ids,
        "primary_image_id": primary_id,
        "primary_image_path": primary_path,
        "image_role": image_role,
        "review_status": review_status,
        "native_reviewed": native_reviewed,
        "code_image_consistency": consistency,
        "evidence_level": str(evidence.get("evidence_level") or "none"),
        "panel_locator": str(evidence.get("panel_locator") or ""),
        "why_match": "；".join(why_match_parts) or "按科学定位、数据契约与视觉通道匹配",
        "confusable_with": record.get("confusable_with") or [],
        "negative_terms": record.get("negative_terms") or [],
        "aliases": aliases,
        "fuzzy_descriptions": fuzzy,
        "visual_feature_terms": feature_terms,
        "source_article_id": str(source.get("article_id") or ""),
        "legacy_style_ids": [str(item) for item in as_list(record.get("legacy_style_ids"))],
    }


def normalise_legacy(
    record: dict[str, Any],
    images: dict[str, dict[str, Any]],
    dispositions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    validation = record.get("validation") or {}
    review_status = review_value(validation.get("sample_selection"))
    native_reviewed = is_native_reviewed(review_status)
    image_id = str(record.get("sample_image_id") or "")
    image_record = images.get(image_id, {})
    image_disposition = dispositions.get(image_id, {})
    primary_path_raw = str(record.get("sample_image") or "")
    primary_path = primary_path_raw if resolve_skill_image(primary_path_raw) else ""
    role = str(
        image_disposition.get("role")
        or image_disposition.get("disposition")
        or validation.get("sample_role")
        or image_record.get("role")
        or "uncertain"
    )
    scientific = str(record.get("coverage_status")) != "resource_only"
    safe = scientific and native_reviewed and role in SAFE_SCIENTIFIC_IMAGE_ROLES and bool(primary_path)
    return {
        "scheme_id": str(record.get("style_id") or ""),
        "title": str(record.get("title") or ""),
        "eligibility": "scientific_scheme" if scientific else "layout_resource",
        "category": "scientific" if safe else ("layout_resource" if not scientific else "excluded"),
        "original_category": "scientific" if scientific else "layout_resource",
        "atlas_exclusion_reason": "" if safe else "旧版卡片未满足 Scheme v2 原生视觉复核门控",
        "broad_family": str(record.get("family") or "unknown"),
        "geometry_subtype": str(record.get("family") or "unknown"),
        "appearance_subtype": "",
        "analysis_method": "legacy",
        "scientific_position": str(record.get("analysis_use") or "未声明"),
        "source_semantics": {},
        "target_application": {},
        "visual_channels": record.get("visual_channels") or {},
        "required_inputs": record.get("required_inputs") or [],
        "optional_inputs": [],
        "transformations": [],
        "supported_claims": record.get("supported_claims") or [],
        "claim_limits": record.get("claim_limits") or [],
        "misread_risks": [],
        "recommended_companion": record.get("recommended_companion") or "无",
        "backends": record.get("backends") or [],
        "code_status": str(record.get("coverage_status") or "unknown"),
        "recipe_status": str(record.get("coverage_status") or "unknown"),
        "code_block_ids": record.get("source_block_ids") or [],
        "object_chain": [],
        "image_ids": [image_id],
        "primary_image_id": image_id,
        "primary_image_path": primary_path,
        "image_role": role,
        "review_status": review_status,
        "native_reviewed": native_reviewed,
        "code_image_consistency": "unknown",
        "evidence_level": "none",
        "panel_locator": "",
        "why_match": str(record.get("prompt_example") or "旧版样式关键词匹配"),
        "confusable_with": [],
        "negative_terms": [],
        "aliases": record.get("keywords") or [],
        "fuzzy_descriptions": [str(record.get("prompt_example") or "")],
        "visual_feature_terms": [],
        "source_article_id": str(record.get("source_article_id") or ""),
        "legacy_style_ids": [str(record.get("style_id") or "")],
    }


def load_cards() -> tuple[list[dict[str, Any]], str]:
    images, _ = index_catalog()
    dispositions = index_image_dispositions()
    schemes = load_jsonl(SCHEME_PATH)
    if schemes:
        return [normalise_scheme(item, images, dispositions) for item in schemes], "scheme-v2"
    legacy = load_jsonl(LEGACY_ATLAS_PATH)
    return [normalise_legacy(item, images, dispositions) for item in legacy], "legacy-fallback"


def copy_images(cards: Iterable[dict[str, Any]], output_dir: Path) -> dict[str, str]:
    assets = output_dir / "visualization-2026718-v1-style-atlas-assets"
    assets.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    expected: set[str] = set()
    for card in cards:
        image_id = str(card.get("primary_image_id") or "")
        rel_path = str(card.get("primary_image_path") or "")
        if not image_id or not rel_path or image_id in mapping:
            continue
        source = resolve_skill_image(rel_path)
        if source is None:
            continue
        suffix = source.suffix.lower() or ".png"
        filename = f"{image_id}{suffix}"
        destination = assets / filename
        shutil.copy2(source, destination)
        expected.add(filename)
        mapping[image_id] = f"visualization-2026718-v1-style-atlas-assets/{filename}"
    for existing in assets.iterdir():
        if existing.is_file() and existing.name not in expected:
            existing.unlink()
    return mapping


def visible_cards(cards: list[dict[str, Any]], scope: str, subtype: str | None) -> list[dict[str, Any]]:
    if scope == "all":
        selected = cards
    elif scope == "resource":
        selected = [card for card in cards if card["category"] in {"aesthetic_modifier", "layout_resource", "visual_reference"}]
    elif scope == "modifier":
        selected = [card for card in cards if card["category"] in {"semantic_modifier", "aesthetic_modifier"}]
    else:
        selected = [card for card in cards if card["category"] == scope]
    if subtype:
        selected = [card for card in selected if card["geometry_subtype"] == subtype]
    return selected


def card_markdown(card: dict[str, Any], image_link: str | None) -> list[str]:
    image_line = f"![{card['title']}]({image_link})" if image_link else "> 本卡未展示图片：没有通过当前图册门控的可用预览。"
    return [
        f"### `{card['scheme_id']}` — {card['title']}",
        "",
        image_line,
        "",
        f"- **Subtype**：`{card['geometry_subtype']}`；**原生外观 subtype**：`{card['appearance_subtype'] or '未单独细分'}`；**family**：`{card['broad_family']}`；**method**：`{card['analysis_method']}`",
        f"- **科学定位**：{card['scientific_position']}",
        f"- **视觉通道**：{join_values(card['visual_channels'])}",
        f"- **代码状态**：`{card['code_status']}`；**Recipe**：`{card['recipe_status']}`",
        f"- **图片角色 / 复核**：`{card['image_role']}` / `{card['review_status']}`；证据等级：`{card['evidence_level']}`；代码—图片一致性：`{card['code_image_consistency']}`；panel：`{card['panel_locator'] or 'whole image / 未声明'}`",
        f"- **为什么可匹配**：{card['why_match']}",
        f"- **可支持**：{join_values(card['supported_claims'])}",
        f"- **不能支持**：{join_values(card['claim_limits'])}",
        f"- **误读风险**：{join_values(card['misread_risks'])}",
        f"- **建议伴随证据**：{card['recommended_companion']}",
        f"- **图册状态**：{card['atlas_exclusion_reason'] or '通过当前分区门控'}",
        "",
    ]


def render_markdown(cards: list[dict[str, Any]], images: dict[str, str], mode: str) -> str:
    category_counts = Counter(card["category"] for card in cards)
    original_counts = Counter(card["original_category"] for card in cards)
    review_withheld = original_counts.get("scientific", 0) - category_counts.get("scientific", 0)
    lines = [
        "# visualization-2026718-v1 Scheme v2 可视化图册",
        "",
        f"> 数据模式：`{mode}`。科研方案只展示具有 `scientific_result` / `published_reference` 且完成原生视觉复核的 Scheme。",
        "",
        "## 图册概览",
        "",
        f"- Scheme 总数：{len(cards)}",
        f"- 科研资格记录：{original_counts.get('scientific', 0)}；进入科研默认图册：{category_counts.get('scientific', 0)}；待原生复核/门控排除：{review_withheld}",
        f"- 语义组件：{category_counts.get('semantic_modifier', 0)}",
        f"- 美学 / 配色：{category_counts.get('aesthetic_modifier', 0)}",
        f"- 布局资源：{category_counts.get('layout_resource', 0)}",
        f"- 视觉参考：{category_counts.get('visual_reference', 0)}",
        f"- 排除审计：{category_counts.get('excluded', 0)}",
        "",
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        grouped[card["category"]].append(card)
    for category in CATEGORY_LABELS:
        members = sorted(grouped.get(category, []), key=lambda item: (item["broad_family"], item["geometry_subtype"], item["scheme_id"]))
        if not members:
            continue
        lines.extend([f"## {CATEGORY_LABELS[category]}", ""])
        for card in members:
            lines.extend(card_markdown(card, images.get(card["primary_image_id"])))
    lines.extend([
        "## 使用边界",
        "",
        "- 外观匹配不替代科学问题、分析单位、统计前提和数据契约判断。",
        "- `pixels_only` 不得推出 p 值、样本量、标准化方法、显著性或因果结论。",
        "- 候选代码只有通过明确的代码、执行、语义、视觉、来源和导出 QA 后，才能显式晋升为正式 Recipe。",
        "- 适配、组合或渲染前必须明确选择 Python 或 R，并在同一后端完成成图和 QA。",
        "",
    ])
    return "\n".join(lines)


def card_html(card: dict[str, Any], image_link: str | None) -> str:
    searchable = " ".join(
        [
            card["scheme_id"], card["title"], card["broad_family"], card["geometry_subtype"], card["appearance_subtype"],
            card["analysis_method"], card["scientific_position"], card["why_match"],
            *card["aliases"], *card["fuzzy_descriptions"], *card["visual_feature_terms"],
        ]
    ).lower()
    if image_link:
        image = f'<img loading="lazy" src="{html.escape(image_link)}" alt="{html.escape(card["title"])}">'
    else:
        image = '<div class="no-image">无通过当前图册门控的预览</div>'
    category_label = CATEGORY_LABELS[card["category"]]
    return f"""
<article class="scheme-card" data-category="{html.escape(card['category'])}" data-family="{html.escape(card['broad_family'])}" data-subtype="{html.escape(card['geometry_subtype'])}" data-backends="{html.escape(' '.join(card['backends']))}" data-code="{html.escape(card['code_status'])}" data-search="{html.escape(searchable)}">
  <div class="card-head"><span class="category {html.escape(card['category'])}">{html.escape(category_label)}</span><span class="review">{html.escape(card['review_status'])}</span></div>
  <h3>{html.escape(card['title'])}</h3>
  <code class="scheme-id">{html.escape(card['scheme_id'])}</code>
  {image}
  <div class="tags"><span>{html.escape(card['geometry_subtype'])}</span>{f'<span>{html.escape(card["appearance_subtype"])}</span>' if card['appearance_subtype'] else ''}<span>{html.escape(card['broad_family'])}</span><span>{html.escape(card['analysis_method'])}</span></div>
  <p><strong>科学定位：</strong>{html.escape(card['scientific_position'])}</p>
  <p><strong>为什么匹配：</strong>{html.escape(card['why_match'])}</p>
  <details open><summary>视觉通道与结论边界</summary>
    <p><strong>视觉通道：</strong>{html.escape(join_values(card['visual_channels']))}</p>
    <p><strong>可支持：</strong>{html.escape(join_values(card['supported_claims']))}</p>
    <p><strong>不能支持：</strong>{html.escape(join_values(card['claim_limits']))}</p>
    <p><strong>误读风险：</strong>{html.escape(join_values(card['misread_risks']))}</p>
    <p><strong>建议伴随证据：</strong>{html.escape(str(card['recommended_companion']))}</p>
  </details>
  <details><summary>代码、图片与 Recipe 状态</summary>
    <p><strong>代码：</strong><code>{html.escape(card['code_status'])}</code>；<strong>Recipe：</strong><code>{html.escape(card['recipe_status'])}</code></p>
    <p><strong>图片角色：</strong>{html.escape(IMAGE_ROLE_LABELS.get(card['image_role'], card['image_role']))}；<strong>复核：</strong><code>{html.escape(card['review_status'])}</code></p>
    <p><strong>证据等级：</strong><code>{html.escape(card['evidence_level'])}</code>；<strong>panel：</strong>{html.escape(card['panel_locator'] or 'whole image / 未声明')}</p>
    <p><strong>代码—图片一致性：</strong><code>{html.escape(str(card['code_image_consistency']))}</code></p>
    <p><strong>图册门控：</strong>{html.escape(card['atlas_exclusion_reason'] or '通过')}</p>
  </details>
</article>"""


def render_html(cards: list[dict[str, Any]], images: dict[str, str], mode: str, coverage: dict[str, Any]) -> str:
    counts = Counter(card["category"] for card in cards)
    original_counts = Counter(card["original_category"] for card in cards)
    review_withheld = original_counts.get("scientific", 0) - counts.get("scientific", 0)
    families = sorted({card["broad_family"] for card in cards})
    subtypes = sorted({card["geometry_subtype"] for card in cards})
    code_states = sorted({card["code_status"] for card in cards})
    metric_items = [
        (len(cards), "全部 Scheme"),
        (original_counts.get("scientific", 0), "科研资格记录"),
        (counts.get("scientific", 0), "科研默认图册"),
        (review_withheld, "待原生复核 / 门控排除"),
        (counts.get("semantic_modifier", 0), "语义组件"),
        (counts.get("aesthetic_modifier", 0), "美学 / 配色"),
        (counts.get("layout_resource", 0), "布局资源"),
        (counts.get("visual_reference", 0), "视觉参考"),
        (original_counts.get("excluded", 0), "源记录明确排除"),
    ]
    metric_html = "".join(
        f'<div class="metric"><b>{value}</b>{html.escape(label)}</div>' for value, label in metric_items
    )
    tabs = "".join(
        f'<button type="button" data-scope="{html.escape(key)}" class="scope{(" active" if key == "scientific" else "")}">{html.escape(label)} <span>{counts.get(key, 0)}</span></button>'
        for key, label in CATEGORY_LABELS.items()
    )
    family_options = "".join(f'<option value="{html.escape(item)}">{html.escape(item)}</option>' for item in families)
    subtype_options = "".join(f'<option value="{html.escape(item)}">{html.escape(item)}</option>' for item in subtypes)
    code_options = "".join(f'<option value="{html.escape(item)}">{html.escape(item)}</option>' for item in code_states)
    cards_html = "\n".join(card_html(card, images.get(card["primary_image_id"])) for card in cards)
    coverage_note = html.escape(str(coverage.get("generated_at") or coverage.get("schema_version") or "未声明"))
    page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>visualization-2026718-v1 Scheme v2 可视化图册</title>
<style>
:root{--ink:#17202a;--muted:#667085;--line:#d8e1e8;--paper:#f4f7fa;--accent:#126286;--scientific:#0f766e;--semantic:#7c3aed;--aesthetic:#b45309;--layout:#2563eb;--reference:#64748b;--excluded:#9f1239}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}.wrap{max-width:1560px;margin:auto;padding:28px}h1,h2,h3{line-height:1.25}.lead{max-width:1080px;color:var(--muted)}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:20px 0}.metric{background:white;border:1px solid var(--line);border-radius:12px;padding:13px}.metric b{display:block;font-size:24px;color:var(--accent)}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}.scope{border:1px solid #b9c8d3;background:white;border-radius:999px;padding:8px 12px;cursor:pointer}.scope.active{background:#133f57;color:white;border-color:#133f57}.scope span{opacity:.75}
.controls{position:sticky;top:0;z-index:4;display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:9px;background:rgba(244,247,250,.96);padding:11px 0}.controls input,.controls select{width:100%;padding:9px;border:1px solid #b9c8d3;border-radius:8px;background:white}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(370px,1fr));gap:16px}.scheme-card{background:white;border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 2px 8px rgba(20,40,60,.05)}.scheme-card img{width:100%;height:300px;object-fit:contain;background:#fff;border:1px solid #edf0f4;border-radius:8px;margin:12px 0}.no-image{height:140px;display:grid;place-items:center;color:var(--muted);border:1px dashed #b8c4ce;border-radius:8px;margin:12px 0;background:#fafbfd}
.card-head{display:flex;justify-content:space-between;gap:8px}.category,.review{border-radius:999px;padding:2px 9px;font-size:12px;color:white}.category.scientific{background:var(--scientific)}.category.semantic_modifier{background:var(--semantic)}.category.aesthetic_modifier{background:var(--aesthetic)}.category.layout_resource{background:var(--layout)}.category.visual_reference{background:var(--reference)}.category.excluded{background:var(--excluded)}.review{background:#475569}
.scheme-id{display:block;overflow-wrap:anywhere;color:#475467}.tags{display:flex;gap:6px;flex-wrap:wrap}.tags span{background:#edf3f6;color:#23475a;border-radius:999px;padding:2px 8px;font-size:12px}details{border-top:1px solid #edf0f4;padding-top:8px;margin-top:8px}summary{cursor:pointer;font-weight:650}code{background:#f1f4f7;border-radius:5px;padding:2px 5px;overflow-wrap:anywhere}.hidden{display:none!important}.result-count{color:var(--muted);margin:8px 0 14px}.audit-note{background:#fff7ed;border-left:4px solid #c2410c;padding:12px 16px;margin:14px 0}
@media(max-width:920px){.wrap{padding:15px}.controls{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.scheme-card img{height:240px}}
</style></head><body><main class="wrap">
<h1>visualization-2026718-v1 Scheme v2 可视化图册</h1>
<p class="lead">先用科学问题、分析单位、数据拓扑和统计前提选择证据方案，再用外观通道锚定素材库样板。科研默认页只展示完成原生视觉复核、且预览角色为科研结果图或论文参考图的 Scheme；外观相似不能替代科学适配。</p>
<p class="lead">数据模式：<code>@@MODE@@</code>；覆盖版本：<code>@@COVERAGE@@</code></p>
<section class="metrics">@@METRICS@@</section>
<div class="audit-note"><strong>严格门控：</strong>圣诞树、宣传图、二维码、封面、代码截图和未完成原生视觉复核的预览不会出现在“科研方案”。它们只在“排除审计”中保留可追溯原因。</div>
<nav class="tabs" aria-label="图册分区">@@TABS@@</nav>
<section class="controls"><input id="q" placeholder="搜索科学问题、模糊描述、subtype、视觉通道或 Scheme ID"><select id="family"><option value="">全部 family</option>@@FAMILIES@@</select><select id="subtype"><option value="">全部 subtype</option>@@SUBTYPES@@</select><select id="backend"><option value="">全部后端</option><option value="r">R</option><option value="python">Python</option></select><select id="code"><option value="">全部代码状态</option>@@CODE@@</select></section>
<div class="result-count" id="count"></div><section class="grid" id="cards">@@CARDS@@</section>
<h2>阅读边界</h2><ul><li>“为什么匹配”说明该 Scheme 的受控别名、视觉结构与可识别描述，不代表它已适合当前数据。</li><li><code>pixels_only</code> 不得推出 p 值、样本量、标准化方法、显著性或因果结论。</li><li>只有完成代码、执行、语义、视觉、来源和导出 QA，并显式执行 promotion 的 Candidate 才是正式 Recipe。</li><li>适配、组合或渲染前必须明确选择 Python 或 R，并在同一后端完成成图和 QA。</li></ul>
</main><script>
const cards=[...document.querySelectorAll('.scheme-card')],buttons=[...document.querySelectorAll('.scope')],q=document.querySelector('#q'),family=document.querySelector('#family'),subtype=document.querySelector('#subtype'),backend=document.querySelector('#backend'),code=document.querySelector('#code'),count=document.querySelector('#count');let scope='scientific';
function filter(){const text=q.value.trim().toLowerCase();let n=0;for(const card of cards){const show=card.dataset.category===scope&&(!text||card.dataset.search.includes(text))&&(!family.value||card.dataset.family===family.value)&&(!subtype.value||card.dataset.subtype===subtype.value)&&(!backend.value||card.dataset.backends.split(' ').includes(backend.value))&&(!code.value||card.dataset.code===code.value);card.classList.toggle('hidden',!show);if(show)n++}count.textContent=`显示 ${n} 个 Scheme（当前分区：${document.querySelector('.scope.active').textContent.trim()}）`;}
buttons.forEach(button=>button.addEventListener('click',()=>{buttons.forEach(item=>item.classList.remove('active'));button.classList.add('active');scope=button.dataset.scope;filter()}));[q,family,subtype,backend,code].forEach(el=>el.addEventListener(el===q?'input':'change',filter));filter();
</script></body></html>"""
    return (
        page.replace("@@MODE@@", html.escape(mode))
        .replace("@@COVERAGE@@", coverage_note)
        .replace("@@METRICS@@", metric_html)
        .replace("@@TABS@@", tabs)
        .replace("@@FAMILIES@@", family_options)
        .replace("@@SUBTYPES@@", subtype_options)
        .replace("@@CODE@@", code_options)
        .replace("@@CARDS@@", cards_html)
    )


def write_csv(cards: list[dict[str, Any]], images: dict[str, str], path: Path) -> None:
    fields = [
        "scheme_id", "category", "eligibility", "broad_family", "geometry_subtype", "appearance_subtype", "analysis_method",
        "title", "scientific_position", "visual_channels", "code_status", "recipe_status", "image_role",
        "review_status", "evidence_level", "panel_locator", "code_image_consistency", "why_match", "supported_claims", "claim_limits",
        "misread_risks", "recommended_companion", "backends", "primary_image", "atlas_exclusion_reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for card in cards:
            writer.writerow({
                "scheme_id": card["scheme_id"], "category": card["category"], "eligibility": card["eligibility"],
                "broad_family": card["broad_family"], "geometry_subtype": card["geometry_subtype"],
                "appearance_subtype": card["appearance_subtype"],
                "analysis_method": card["analysis_method"], "title": card["title"],
                "scientific_position": card["scientific_position"], "visual_channels": join_values(card["visual_channels"]),
                "code_status": card["code_status"], "recipe_status": card["recipe_status"], "image_role": card["image_role"],
                "review_status": card["review_status"], "evidence_level": card["evidence_level"],
                "panel_locator": card["panel_locator"], "code_image_consistency": card["code_image_consistency"],
                "why_match": card["why_match"], "supported_claims": join_values(card["supported_claims"]),
                "claim_limits": join_values(card["claim_limits"]), "misread_risks": join_values(card["misread_risks"]),
                "recommended_companion": card["recommended_companion"], "backends": "|".join(card["backends"]),
                "primary_image": images.get(card["primary_image_id"], ""),
                "atlas_exclusion_reason": card["atlas_exclusion_reason"],
            })


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            except (OSError, ValueError):
                pass
    parser = argparse.ArgumentParser(description="Export the Scheme v2 visual atlas")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--scope", choices=["scientific", "modifier", "resource", "excluded", "all"], default="all",
        help="Limit exported records; HTML still defaults to the scientific tab.",
    )
    parser.add_argument("--subtype", help="Export only one geometry subtype")
    args = parser.parse_args()

    cards, mode = load_cards()
    cards = visible_cards(cards, args.scope, args.subtype)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    images = copy_images(cards, output_dir)
    coverage = load_json(SCHEME_COVERAGE_PATH) or load_json(CATALOG_COVERAGE_PATH)

    markdown_path = output_dir / "visualization-2026718-v1-visual-atlas.md"
    html_path = output_dir / "visualization-2026718-v1-visual-atlas.html"
    csv_path = output_dir / "visualization-2026718-v1-style-index.csv"
    markdown_path.write_text(render_markdown(cards, images, mode), encoding="utf-8", newline="\n")
    html_path.write_text(render_html(cards, images, mode, coverage), encoding="utf-8", newline="\n")
    write_csv(cards, images, csv_path)

    counts = Counter(card["category"] for card in cards)
    print(json.dumps({
        "schema": "scheme-v2-atlas-export/2.0",
        "mode": mode,
        "cards": len(cards),
        "categories": dict(sorted(counts.items())),
        "copied_images": len(images),
        "scientific_heuristic_previews": sum(
            1 for card in cards if card["category"] == "scientific" and not card["native_reviewed"]
        ),
        "markdown": str(markdown_path), "html": str(html_path), "csv": str(csv_path),
        "assets": str(output_dir / "visualization-2026718-v1-style-atlas-assets"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
