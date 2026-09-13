# -*- coding: utf-8 -*-
"""ReportLab Chinese PDF for 生育期长势分析报告."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reports.land_assessment.paths import FONT_PATH
from app.reports.season_growth.facts import drought_class_cn, flood_class_cn

CST = timezone(timedelta(hours=8))
_APPENDIX_MAX_ROWS = 80

_QUALITY_CN = {
    "official": "官方",
    "good": "良好",
    "fair": "一般",
    "bad": "较差",
    "raw": "原始",
    "classic": "经典",
}

_QUALITY_RANK = {
    "official": 5,
    "good": 4,
    "fair": 3,
    "raw": 2,
    "classic": 2,
    "bad": 1,
}

_DROUGHT_COUNT_ORDER = (
    ("severe", "重度"),
    ("moderate", "中度"),
    ("mild", "轻度"),
    ("normal", "正常"),
    ("unreliable", "不可靠"),
    ("out_of_season", "季外"),
)

_FLOOD_COUNT_ORDER = (
    ("flood_severe", "洪涝(重)"),
    ("flood_moderate", "洪涝"),
    ("watch", "关注"),
    ("dry", "正常"),
    ("unknown", "未定"),
)

_FLOOD_STATUS_CN = {
    "ok": "正常监测",
    "no_s1_data": "无S1数据",
    "not_applicable": "不适用",
}

_HARVEST_STATUS_CN = {
    "detected": "已检测",
    "uncertain": "不确定",
    "not_detected": "未检测",
    "no_data": "无数据",
}

_HARVEST_CONF_CN = {
    "high": "高",
    "medium": "中",
    "low": "低",
}


def _register_fonts() -> None:
    if "CN" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("CN", str(FONT_PATH)))
        pdfmetrics.registerFont(TTFont("CNB", str(FONT_PATH)))


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "cover_title": ParagraphStyle(
            "sg_cover_title",
            fontName="CNB",
            fontSize=20,
            leading=28,
            alignment=TA_CENTER,
            textColor=HexColor("#143d2b"),
        ),
        "cover_subtitle": ParagraphStyle(
            "sg_cover_subtitle",
            fontName="CN",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            textColor=HexColor("#3d5a4a"),
        ),
        "cover_field": ParagraphStyle(
            "sg_cover_field",
            fontName="CNB",
            fontSize=14,
            leading=20,
            alignment=TA_CENTER,
            textColor=HexColor("#1b4332"),
        ),
        "cover_sub": ParagraphStyle(
            "sg_cover_sub",
            fontName="CN",
            fontSize=11,
            leading=16,
            alignment=TA_CENTER,
            textColor=HexColor("#5a6a60"),
        ),
        "h1": ParagraphStyle(
            "sg_h1",
            fontName="CNB",
            fontSize=13,
            leading=18,
            textColor=HexColor("#143d2b"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "sg_h2",
            fontName="CNB",
            fontSize=11,
            leading=15,
            textColor=HexColor("#1b4332"),
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "sg_body",
            fontName="CN",
            fontSize=10,
            leading=15,
            alignment=TA_JUSTIFY,
            textColor=HexColor("#222"),
        ),
        "small": ParagraphStyle(
            "sg_small",
            fontName="CN",
            fontSize=8.5,
            leading=12,
            textColor=HexColor("#666"),
        ),
        "caption": ParagraphStyle(
            "sg_caption",
            fontName="CN",
            fontSize=8.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=HexColor("#555"),
            spaceBefore=2,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "sg_bullet",
            fontName="CN",
            fontSize=9.5,
            leading=14,
            leftIndent=8,
            textColor=HexColor("#222"),
        ),
        "left": ParagraphStyle(
            "sg_left",
            fontName="CN",
            fontSize=10,
            leading=15,
            alignment=TA_LEFT,
            textColor=HexColor("#222"),
        ),
        "meta_label": ParagraphStyle(
            "sg_meta_label",
            fontName="CN",
            fontSize=9,
            leading=13,
            textColor=HexColor("#555"),
        ),
        "meta_value": ParagraphStyle(
            "sg_meta_value",
            fontName="CN",
            fontSize=9,
            leading=13,
            textColor=HexColor("#222"),
        ),
    }


def _esc(s: Any) -> str:
    t = "" if s is None else str(s)
    return (
        t.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _fmt(v: Any, digits: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def format_drought_counts(counts: dict[str, Any] | None) -> str:
    """Chinese drought counts, omit zeros: 重度8 / 中度1 / …"""
    if not counts:
        return "—"
    parts: list[str] = []
    for key, label in _DROUGHT_COUNT_ORDER:
        n = int(counts.get(key) or 0)
        if n > 0:
            parts.append(f"{label}{n}")
    # Any unexpected keys
    known = {k for k, _ in _DROUGHT_COUNT_ORDER}
    for key, n in counts.items():
        if key in known:
            continue
        try:
            iv = int(n or 0)
        except (TypeError, ValueError):
            continue
        if iv > 0:
            parts.append(f"{drought_class_cn(str(key))}{iv}")
    return " / ".join(parts) if parts else "—"


def format_flood_counts(counts: dict[str, Any] | None) -> str:
    """Chinese flood counts, omit zeros."""
    if not counts:
        return "—"
    parts: list[str] = []
    for key, label in _FLOOD_COUNT_ORDER:
        n = int(counts.get(key) or 0)
        if n > 0:
            parts.append(f"{label}{n}")
    known = {k for k, _ in _FLOOD_COUNT_ORDER}
    for key, n in counts.items():
        if key in known:
            continue
        try:
            iv = int(n or 0)
        except (TypeError, ValueError):
            continue
        if iv > 0:
            parts.append(f"{flood_class_cn(str(key))}{iv}")
    return " / ".join(parts) if parts else "—"


def format_flood_status(status: Any) -> str:
    if status is None or status == "":
        return "—"
    s = str(status)
    return _FLOOD_STATUS_CN.get(s, s)


def format_harvest_line(harvest: dict[str, Any] | None) -> str:
    h = harvest or {}
    status = h.get("status")
    status_cn = _HARVEST_STATUS_CN.get(str(status), str(status) if status else "—")
    date_s = h.get("harvest_date") or "—"
    conf = h.get("confidence")
    conf_cn = _HARVEST_CONF_CN.get(str(conf), str(conf) if conf else "—")
    if status in (None, "", "not_detected", "no_data") and not h.get("harvest_date"):
        return f"{status_cn}（置信度{conf_cn}）" if conf else status_cn
    return f"{status_cn} / {date_s}（{conf_cn}）"


def quality_cn(quality: Any) -> str:
    if quality is None or quality == "":
        return "—"
    q = str(quality).strip().lower()
    return _QUALITY_CN.get(q, str(quality))


def _quality_rank(quality: Any) -> int:
    q = str(quality or "").strip().lower()
    return _QUALITY_RANK.get(q, 0)


def _ndvi_usable(ndvi: Any) -> bool:
    if ndvi is None:
        return False
    try:
        v = float(ndvi)
    except (TypeError, ValueError):
        return False
    return abs(v) > 1e-9


def filter_s2_appendix_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer usable S2 scenes: best quality per date; drop bad/raw NDVI~0 noise."""
    if not rows:
        return []
    by_date: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        d = str(r.get("date") or "")
        by_date.setdefault(d, []).append(r)

    out: list[dict[str, Any]] = []
    for d in sorted(by_date.keys()):
        group = by_date[d]
        usable = [r for r in group if _ndvi_usable(r.get("ndvi"))]
        candidates = usable if usable else group

        def sort_key(r: dict[str, Any]) -> tuple:
            q = str(r.get("quality") or "").lower()
            # Prefer official/good over bad/raw
            rank = _quality_rank(q)
            if q == "official" or r.get("official"):
                rank = max(rank, 5)
            ndvi_ok = 1 if _ndvi_usable(r.get("ndvi")) else 0
            # Prefer non-bad
            not_bad = 0 if q == "bad" else 1
            return (ndvi_ok, not_bad, rank)

        best = max(candidates, key=sort_key)
        # Skip pure noise: NDVI none/0 and quality bad when anything better existed
        q = str(best.get("quality") or "").lower()
        if not _ndvi_usable(best.get("ndvi")) and q == "bad" and len(group) > 1:
            better = [
                r
                for r in group
                if _ndvi_usable(r.get("ndvi")) or str(r.get("quality") or "").lower() != "bad"
            ]
            if better:
                best = max(better, key=sort_key)
            else:
                continue
        if not _ndvi_usable(best.get("ndvi")) and q in ("bad", "raw") and not usable:
            # Keep one marker row only if it's the sole date entry with no NDVI
            # Prefer dropping pure noise rows
            continue
        out.append(best)
    return out


def _table(rows: list[list[str]], col_widths: list[float] | None = None) -> Table:
    data = [[Paragraph(_esc(c), _styles()["small"]) for c in row] for row in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e8f0ea")),
                ("FONTNAME", (0, 0), (-1, -1), "CN"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#c5d5c8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def _meta_table(rows: list[tuple[str, str]]) -> Table:
    styles = _styles()
    data = []
    for label, value in rows:
        data.append(
            [
                Paragraph(_esc(label), styles["meta_label"]),
                Paragraph(_esc(value), styles["meta_value"]),
            ]
        )
    # Two columns of label/value pairs → flatten into 4-col grid when even
    grid: list[list[Any]] = []
    i = 0
    while i < len(data):
        if i + 1 < len(data):
            grid.append(data[i] + data[i + 1])
            i += 2
        else:
            grid.append(data[i] + ["", ""])
            i += 1
    t = Table(grid, colWidths=[28 * mm, 52 * mm, 28 * mm, 52 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), HexColor("#f3f7f4")),
                ("BACKGROUND", (2, 0), (2, -1), HexColor("#f3f7f4")),
                ("FONTNAME", (0, 0), (-1, -1), "CN"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#c5d5c8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#d7e3da")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def _resolve_chart_paths(
    chart_paths: dict[str, Path | str] | None,
    chart_path: Path | str | None,
) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if chart_paths:
        for k, v in chart_paths.items():
            if v and Path(v).exists():
                out[str(k)] = Path(v)
    if chart_path and Path(chart_path).exists() and "ndvi_ndmi" not in out:
        out["ndvi_ndmi"] = Path(chart_path)
    return out


def _bullets(story: list[Any], items: list[Any] | None, styles: dict) -> None:
    for b in items or []:
        story.append(Paragraph(f"• {_esc(b)}", styles["bullet"]))


def _text_or_dash(story: list[Any], text: Any, styles: dict, empty: str = "—") -> None:
    story.append(Paragraph(_esc(text or empty), styles["body"]))


def _chart_block(
    story: list[Any],
    *,
    path: Path | None,
    width_mm: float,
    height_mm: float,
    caption: str,
    missing: str,
    styles: dict,
) -> None:
    if path and path.exists():
        block = [
            Image(str(path), width=width_mm * mm, height=height_mm * mm),
            Paragraph(_esc(caption), styles["caption"]),
        ]
        story.append(KeepTogether(block))
    else:
        story.append(Paragraph(_esc(missing), styles["body"]))


def render_season_growth_pdf(
    *,
    facts: dict[str, Any],
    ai: dict[str, Any] | None,
    chart_path: Path | str | None = None,
    chart_paths: dict[str, Path | str] | None = None,
    materials_meta: list[dict[str, Any]] | None,
    out_path: Path | str,
) -> Path:
    _register_fonts()
    styles = _styles()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    field = facts.get("field") or {}
    window = facts.get("window") or {}
    scenes = facts.get("scenes") or {}
    ndvi = facts.get("ndvi") or {}
    drought = facts.get("drought") or {}
    flood = facts.get("flood") or {}
    harvest = facts.get("harvest") or {}
    methodology = facts.get("methodology") or {}
    timeline = facts.get("timeline") or []
    s2_appendix = filter_s2_appendix_rows(list(facts.get("s2_appendix") or []))
    s1_appendix = list(facts.get("s1_appendix") or [])
    ai = ai or {}
    charts = _resolve_chart_paths(chart_paths, chart_path)
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="生育期长势分析报告",
    )
    story: list[Any] = []

    # ── 1. Cover（短封面）──
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("生育期长势分析报告", styles["cover_title"]))
    story.append(Paragraph("遥感长势与水分证据", styles["cover_subtitle"]))
    story.append(Spacer(1, 4 * mm))
    field_name = field.get("field_name") or "地块"
    story.append(Paragraph(_esc(field_name), styles["cover_field"]))
    story.append(Spacer(1, 4 * mm))

    season_label = window.get("label") or f"{window.get('start_date')} ~ {window.get('end_date')}"
    crops = window.get("crops") or []
    crops_s = "、".join(str(c) for c in crops) if crops else "—"
    meta_rows = [
        ("地块编号", str(field.get("land_id") or "—")),
        ("生育期窗口", str(season_label)),
        ("观测日期", f"{window.get('start_date') or '—'} ~ {window.get('end_date') or '—'}"),
        ("作物", crops_s),
        ("Sentinel-2", f"{scenes.get('s2_count', '—')} 景"),
        ("Sentinel-1", f"{scenes.get('s1_count', '—')} 景"),
        ("报告生成", now),
        ("数据来源", str(facts.get("data_source") or "遥感产品")),
    ]
    story.append(_meta_table(meta_rows))
    story.append(PageBreak())

    # ── 2. 摘要 → 方法 → 水分证据 → 时间线（连续流排）──
    story.append(Paragraph("一、摘要", styles["h1"]))
    one = ai.get("one_liner") or "（无 AI 一句话摘要）"
    story.append(Paragraph(_esc(one), styles["body"]))
    story.append(Spacer(1, 1.5 * mm))
    if ai.get("core_conclusion"):
        story.append(Paragraph("核心结论", styles["h2"]))
        _text_or_dash(story, ai.get("core_conclusion"), styles)
    if ai.get("summary"):
        story.append(Paragraph("摘要", styles["h2"]))
        _text_or_dash(story, ai.get("summary"), styles)
    if ai.get("evidence_bullets"):
        story.append(Paragraph("证据要点", styles["h2"]))
        _bullets(story, ai.get("evidence_bullets"), styles)

    # ── 方法 ──
    story.append(Paragraph("二、判定方法说明", styles["h1"]))
    method_rows = [
        ["类别", "说明"],
        ["光学干旱（S2）", methodology.get("drought") or "基于 agri_classify 干旱分类器。"],
        ["SAR 洪涝（S1）", methodology.get("flood") or "基于 agri_classify 洪涝分类器。"],
        ["传感器", methodology.get("sensors") or "Sentinel-2 / Sentinel-1"],
    ]
    story.append(_table(method_rows, col_widths=[40 * mm, 130 * mm]))

    mats = materials_meta or []
    if mats:
        story.append(Paragraph("材料说明", styles["h2"]))
        for m in mats:
            line = f"• {_esc(m.get('filename'))}"
            if m.get("note"):
                line += f"（{_esc(m.get('note'))}）"
            elif m.get("ok"):
                line += "（已提取/已登记）"
            story.append(Paragraph(line, styles["bullet"]))
    else:
        story.append(
            Paragraph("注：本次未上传附加材料。", styles["small"])
        )

    # ── 水分证据 ──
    story.append(Paragraph("三、生育期水分证据", styles["h1"]))

    story.append(Paragraph("3.1 遥感事实摘要", styles["h2"]))
    fact_rows = [
        ["项目", "数值"],
        ["S2 景数", str(scenes.get("s2_count", "—"))],
        ["S2 官方/可用景数", str(scenes.get("s2_official_count", "—"))],
        ["S2 晴空景数", str(scenes.get("s2_clear_count", "—"))],
        ["S1 景数", str(scenes.get("s1_count", "—"))],
        ["NDVI 均值", _fmt(ndvi.get("mean"), 4)],
        [
            "NDVI 峰值",
            f"{_fmt((ndvi.get('peak') or {}).get('value'), 4)} @ "
            f"{(ndvi.get('peak') or {}).get('date') or '—'}",
        ],
        [
            "最新 NDVI",
            f"{_fmt((ndvi.get('latest') or {}).get('value'), 4)} @ "
            f"{(ndvi.get('latest') or {}).get('date') or '—'}",
        ],
        ["NDMI 均值", _fmt((facts.get("ndmi") or {}).get("mean"), 4)],
        ["干旱景数(轻/中/重合计)", str(drought.get("drought_scene_count", "—"))],
        ["干旱分级计数", format_drought_counts(drought.get("counts"))],
        ["洪涝状态", format_flood_status(flood.get("status"))],
        [
            "洪涝景数",
            str(
                flood.get(
                    "flood_scene_count",
                    (flood.get("counts") or {}).get("flood_severe", "—"),
                )
            ),
        ],
        ["洪涝分级计数", format_flood_counts(flood.get("counts"))],
        ["S1 VV 中位数", _fmt(flood.get("vv_median"), 3)],
        ["收获检测", format_harvest_line(harvest)],
    ]
    prior = facts.get("prior_year")
    if prior:
        fact_rows.append(
            [
                "上年同期 NDVI 均值",
                f"{_fmt(prior.get('ndvi_mean'), 4)}（{prior.get('start_date')}~"
                f"{prior.get('end_date')}，n={prior.get('point_count')}）",
            ]
        )
    story.append(_table(fact_rows, col_widths=[55 * mm, 115 * mm]))
    if flood.get("note"):
        story.append(Paragraph(_esc(flood["note"]), styles["small"]))

    story.append(Paragraph("3.2 NDVI / NDMI 曲线（干旱分级着色）", styles["h2"]))
    _chart_block(
        story,
        path=charts.get("ndvi_ndmi"),
        width_mm=160,
        height_mm=78,
        caption="图1  生育期 NDVI / NDMI 曲线（点色表示干旱等级）",
        missing="窗口内无足够 NDVI/NDMI 点，未生成曲线图。",
        styles=styles,
    )

    story.append(Paragraph("3.3 Sentinel-1 VV 曲线", styles["h2"]))
    _chart_block(
        story,
        path=charts.get("s1_vv"),
        width_mm=160,
        height_mm=74,
        caption="图2  Sentinel-1 VV 洪涝监测曲线",
        missing="窗口内无 S1 VV 数据，未生成洪涝曲线图。",
        styles=styles,
    )

    story.append(Paragraph("3.4 水分证据解读", styles["h2"]))
    _text_or_dash(
        story,
        ai.get("moisture_analysis"),
        styles,
        empty="（无 AI 水分分析）",
    )

    # ── 时间线（继续流排）──
    story.append(Paragraph("四、时间线", styles["h1"]))
    if timeline:
        tl_rows = [["月份", "S2景数", "S1景数", "干旱日", "洪涝", "关注"]]
        for row in timeline:
            tl_rows.append(
                [
                    str(row.get("month") or "—"),
                    str(row.get("s2_count", 0)),
                    str(row.get("s1_count", 0)),
                    str(row.get("drought_days", 0)),
                    str(row.get("flood_count", 0)),
                    str(row.get("watch_count", 0)),
                ]
            )
        story.append(
            _table(
                tl_rows,
                col_widths=[30 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm],
            )
        )
    else:
        story.append(Paragraph("无按月时间线事实。", styles["body"]))
    if ai.get("timeline_notes"):
        story.append(Paragraph("时间线说明", styles["h2"]))
        _text_or_dash(story, ai.get("timeline_notes"), styles)

    # ── 综合分析（可新页，避免与前面图表挤在一起）──
    story.append(PageBreak())
    story.append(Paragraph("五、综合分析与结论", styles["h1"]))
    _text_or_dash(story, ai.get("interpretation"), styles, empty="（无 AI 解读）")
    if ai.get("causes_ranked"):
        story.append(Paragraph("可能原因（排序）", styles["h2"]))
        _bullets(story, ai.get("causes_ranked"), styles)
    # Do NOT repeat core_conclusion here

    story.append(Paragraph("六、管理建议与补充取证", styles["h1"]))
    story.append(Paragraph("管理建议", styles["h2"]))
    _text_or_dash(story, ai.get("recommendations"), styles)
    story.append(Paragraph("建议补充取证", styles["h2"]))
    if ai.get("follow_up"):
        _bullets(story, ai.get("follow_up"), styles)
    else:
        story.append(Paragraph("（无补充取证建议）", styles["body"]))
    if ai.get("llm_configured") is False:
        story.append(
            Paragraph(
                "说明：未配置 BAILIAN_API_KEY，AI 章节为占位提示，数值均来自程序计算。",
                styles["small"],
            )
        )

    # ── 附录 ──
    story.append(PageBreak())
    story.append(Paragraph("七、附录", styles["h1"]))

    story.append(Paragraph("附录 A：Sentinel-2 逐景表", styles["h2"]))
    if not s2_appendix:
        story.append(Paragraph("无 S2 逐景记录。", styles["body"]))
    else:
        truncated = len(s2_appendix) > _APPENDIX_MAX_ROWS
        rows_a = s2_appendix[:_APPENDIX_MAX_ROWS]
        s2_rows = [
            ["日期", "云量%", "质量", "干旱等级", "NDVI", "NDMI", "EVI", "MNDWI"]
        ]
        for r in rows_a:
            cls = r.get("drought_class_cn") or drought_class_cn(r.get("drought_class"))
            q_label = r.get("quality_cn") or quality_cn(r.get("quality"))
            s2_rows.append(
                [
                    str(r.get("date") or "—"),
                    _fmt(r.get("cloud_pct"), 1),
                    str(q_label),
                    str(cls),
                    _fmt(r.get("ndvi"), 3),
                    _fmt(r.get("ndmi"), 3),
                    _fmt(r.get("evi"), 3),
                    _fmt(r.get("mndwi"), 3),
                ]
            )
        story.append(
            _table(
                s2_rows,
                col_widths=[
                    22 * mm,
                    16 * mm,
                    18 * mm,
                    20 * mm,
                    18 * mm,
                    18 * mm,
                    18 * mm,
                    20 * mm,
                ],
            )
        )
        if truncated:
            story.append(
                Paragraph(
                    f"注：筛选后共 {len(s2_appendix)} 行，附录仅展示前 {_APPENDIX_MAX_ROWS} 行。",
                    styles["small"],
                )
            )
        else:
            story.append(
                Paragraph(
                    "注：同日多景已按质量优选；已过滤 NDVI 缺失/为零的较差噪声行。",
                    styles["small"],
                )
            )

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("附录 B：Sentinel-1 逐景表", styles["h2"]))
    if not s1_appendix:
        story.append(Paragraph("无 S1 逐景记录。", styles["body"]))
    else:
        truncated_b = len(s1_appendix) > _APPENDIX_MAX_ROWS
        rows_b = s1_appendix[:_APPENDIX_MAX_ROWS]
        s1_rows = [["日期", "轨道", "VV (dB)", "VH (dB)", "洪涝等级"]]
        for r in rows_b:
            cls = r.get("flood_class_cn") or flood_class_cn(r.get("flood_class"))
            s1_rows.append(
                [
                    str(r.get("date") or "—"),
                    str(r.get("relative_orbit") if r.get("relative_orbit") is not None else "—"),
                    _fmt(r.get("vv"), 2),
                    _fmt(r.get("vh"), 2),
                    str(cls),
                ]
            )
        story.append(
            _table(
                s1_rows,
                col_widths=[30 * mm, 25 * mm, 30 * mm, 30 * mm, 40 * mm],
            )
        )
        if truncated_b:
            story.append(
                Paragraph(
                    f"注：共 {len(s1_appendix)} 行，附录仅展示前 {_APPENDIX_MAX_ROWS} 行。",
                    styles["small"],
                )
            )

    story.append(Spacer(1, 5 * mm))
    story.append(
        Paragraph(
            f"数据来源：{_esc(facts.get('data_source') or '遥感产品')}；"
            "程序计算事实；AI 仅作解读不编造数值。Sentinel-2 / Sentinel-1。",
            styles["small"],
        )
    )

    doc.build(story)
    return out
