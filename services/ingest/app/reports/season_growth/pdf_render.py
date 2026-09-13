# -*- coding: utf-8 -*-
"""ReportLab Chinese PDF for 生育期长势分析报告 (v2 layout)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
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
from app.reports.season_growth.facts import (
    FOOTER_DISCLAIMER,
    drought_class_cn,
    flood_class_cn,
)

CST = timezone(timedelta(hours=8))
_APPENDIX_MAX_ROWS = 80
_CONTENT_W = 178 * mm

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
    "no_growth": "无明显旺长期",
}

_HARVEST_CONF_CN = {
    "high": "高",
    "medium": "中",
    "low": "低",
}

_CARD_ACCENT = {
    "growth": "#1b4332",
    "drought": "#c62828",
    "flood": "#1565c0",
    "harvest": "#ef6c00",
}

_CONF_BG = {
    "high": "#e8f5e9",
    "medium": "#fff8e1",
    "low": "#f5f5f5",
    "高": "#e8f5e9",
    "中": "#fff8e1",
    "低": "#f5f5f5",
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
            leading=26,
            alignment=TA_CENTER,
            textColor=HexColor("#143d2b"),
        ),
        "cover_subtitle": ParagraphStyle(
            "sg_cover_subtitle",
            fontName="CN",
            fontSize=11,
            leading=16,
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
        "h1": ParagraphStyle(
            "sg_h1",
            fontName="CNB",
            fontSize=13,
            leading=18,
            textColor=HexColor("#143d2b"),
            spaceBefore=6,
            spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "sg_h2",
            fontName="CNB",
            fontSize=10.5,
            leading=14,
            textColor=HexColor("#1b4332"),
            spaceBefore=5,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "sg_body",
            fontName="CN",
            fontSize=9.5,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=HexColor("#222"),
        ),
        "small": ParagraphStyle(
            "sg_small",
            fontName="CN",
            fontSize=8,
            leading=11,
            textColor=HexColor("#555"),
        ),
        "small_r": ParagraphStyle(
            "sg_small_r",
            fontName="CN",
            fontSize=8,
            leading=11,
            alignment=TA_RIGHT,
            textColor=HexColor("#222"),
        ),
        "small_c": ParagraphStyle(
            "sg_small_c",
            fontName="CN",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=HexColor("#222"),
        ),
        "th": ParagraphStyle(
            "sg_th",
            fontName="CNB",
            fontSize=8,
            leading=11,
            alignment=TA_LEFT,
            textColor=HexColor("#143d2b"),
        ),
        "caption": ParagraphStyle(
            "sg_caption",
            fontName="CN",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=HexColor("#555"),
            spaceBefore=1,
            spaceAfter=3,
        ),
        "bullet": ParagraphStyle(
            "sg_bullet",
            fontName="CN",
            fontSize=9,
            leading=13,
            leftIndent=8,
            textColor=HexColor("#222"),
        ),
        "left": ParagraphStyle(
            "sg_left",
            fontName="CN",
            fontSize=9.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=HexColor("#222"),
        ),
        "meta_label": ParagraphStyle(
            "sg_meta_label",
            fontName="CN",
            fontSize=8.5,
            leading=12,
            textColor=HexColor("#555"),
        ),
        "meta_value": ParagraphStyle(
            "sg_meta_value",
            fontName="CN",
            fontSize=8.5,
            leading=12,
            textColor=HexColor("#222"),
        ),
        "card_title": ParagraphStyle(
            "sg_card_title",
            fontName="CN",
            fontSize=8,
            leading=11,
            alignment=TA_CENTER,
            textColor=white,
        ),
        "card_value": ParagraphStyle(
            "sg_card_value",
            fontName="CNB",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=HexColor("#143d2b"),
        ),
        "card_detail": ParagraphStyle(
            "sg_card_detail",
            fontName="CN",
            fontSize=7.2,
            leading=10,
            alignment=TA_CENTER,
            textColor=HexColor("#555"),
        ),
        "card_conf": ParagraphStyle(
            "sg_card_conf",
            fontName="CNB",
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=HexColor("#1b4332"),
        ),
        "box": ParagraphStyle(
            "sg_box",
            fontName="CN",
            fontSize=9.5,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=HexColor("#1b4332"),
        ),
        "pill_num": ParagraphStyle(
            "sg_pill_num",
            fontName="CNB",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=white,
        ),
        "card_h": ParagraphStyle(
            "sg_card_h",
            fontName="CNB",
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
            textColor=HexColor("#143d2b"),
        ),
        "card_bullet": ParagraphStyle(
            "sg_card_bullet",
            fontName="CN",
            fontSize=8.2,
            leading=11.5,
            alignment=TA_LEFT,
            textColor=HexColor("#222"),
        ),
        "caution": ParagraphStyle(
            "sg_caution",
            fontName="CN",
            fontSize=8.5,
            leading=12,
            alignment=TA_LEFT,
            textColor=HexColor("#7a4a00"),
        ),
        "chip": ParagraphStyle(
            "sg_chip",
            fontName="CN",
            fontSize=7.8,
            leading=11,
            alignment=TA_LEFT,
            textColor=HexColor("#333"),
        ),
        "footer": ParagraphStyle(
            "sg_footer",
            fontName="CN",
            fontSize=7.5,
            leading=11,
            alignment=TA_JUSTIFY,
            textColor=HexColor("#666"),
        ),
    }


def _esc(s: Any) -> str:
    t = "" if s is None else str(s)
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    if status in (None, "", "not_detected", "no_data", "no_growth", "uncertain") and not h.get(
        "harvest_date"
    ):
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
            rank = _quality_rank(q)
            if q == "official" or r.get("official"):
                rank = max(rank, 5)
            ndvi_ok = 1 if _ndvi_usable(r.get("ndvi")) else 0
            not_bad = 0 if q == "bad" else 1
            return (ndvi_ok, not_bad, rank)

        best = max(candidates, key=sort_key)
        q = str(best.get("quality") or "").lower()
        if not _ndvi_usable(best.get("ndvi")) and q == "bad" and len(group) > 1:
            better = [
                r
                for r in group
                if _ndvi_usable(r.get("ndvi"))
                or str(r.get("quality") or "").lower() != "bad"
            ]
            if better:
                best = max(better, key=sort_key)
            else:
                continue
        if not _ndvi_usable(best.get("ndvi")) and q in ("bad", "raw") and not usable:
            continue
        out.append(best)
    return out


def filter_s1_appendix_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe S1 by date; keep the row with the lowest VV (more conservative)."""
    if not rows:
        return []
    by_date: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        d = str(r.get("date") or "")
        by_date.setdefault(d, []).append(r)
    out: list[dict[str, Any]] = []
    for d in sorted(by_date.keys()):
        group = by_date[d]

        def vv_key(r: dict[str, Any]) -> float:
            try:
                return float(r.get("vv"))
            except (TypeError, ValueError):
                return 999.0

        out.append(min(group, key=vv_key))
    return out


def _p(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_esc(text), style)


def _table(
    rows: list[list[Any]],
    col_widths: list[float] | None = None,
    *,
    numeric_cols: set[int] | None = None,
    zebra: bool = True,
) -> Table:
    """Body/appendix tables: all text and numbers LEFT-aligned.

    ``numeric_cols`` is retained for call-site compatibility but no longer
    switches to right alignment.
    """
    styles = _styles()
    _ = numeric_cols  # kept for API compatibility; alignment is always LEFT
    data: list[list[Any]] = []
    for i, row in enumerate(rows):
        cells = []
        for j, c in enumerate(row):
            if isinstance(c, Paragraph):
                cells.append(c)
            elif i == 0:
                cells.append(Paragraph(_esc(c), styles["th"]))
            else:
                cells.append(Paragraph(_esc(c), styles["small"]))
        data.append(cells)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    cmds: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dce8df")),
        ("FONTNAME", (0, 0), (-1, -1), "CN"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, HexColor("#c5d5c8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), HexColor("#f4f8f5")))
    t.setStyle(TableStyle(cmds))
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
    grid: list[list[Any]] = []
    i = 0
    while i < len(data):
        if i + 1 < len(data):
            grid.append(data[i] + data[i + 1])
            i += 2
        else:
            grid.append(data[i] + ["", ""])
            i += 1
    t = Table(grid, colWidths=[28 * mm, 61 * mm, 28 * mm, 61 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), HexColor("#f3f7f4")),
                ("BACKGROUND", (2, 0), (2, -1), HexColor("#f3f7f4")),
                ("FONTNAME", (0, 0), (-1, -1), "CN"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#c5d5c8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#d7e3da")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    return t


def _status_cards_table(cards: list[dict[str, Any]]) -> Table:
    styles = _styles()
    if len(cards) < 4:
        # pad so cover always shows four slots
        keys = ["growth", "drought", "flood", "harvest"]
        titles = ["当前长势", "干旱风险", "洪涝风险", "收获状态"]
        by_key = {c.get("key"): c for c in cards}
        cards = [
            by_key.get(
                k,
                {
                    "key": k,
                    "title": titles[i],
                    "value": "—",
                    "detail": "—",
                    "confidence": "低",
                    "confidence_level": "low",
                },
            )
            for i, k in enumerate(keys)
        ]
    col_w = 44.5 * mm
    inner_rows = []
    header = []
    values = []
    confs = []
    details = []
    for card in cards[:4]:
        header.append(Paragraph(_esc(card.get("title") or ""), styles["card_title"]))
        values.append(Paragraph(_esc(card.get("value") or "—"), styles["card_value"]))
        confs.append(
            Paragraph(f"置信度 {_esc(card.get('confidence') or '低')}", styles["card_conf"])
        )
        details.append(Paragraph(_esc(card.get("detail") or ""), styles["card_detail"]))
    inner_rows = [header, values, confs, details]
    t = Table(inner_rows, colWidths=[col_w] * 4)
    cmds: list[tuple] = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#c5d5c8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#d7e3da")),
        ("BACKGROUND", (0, 1), (-1, 3), HexColor("#fbfdfb")),
        ("TOPPADDING", (0, 1), (-1, 1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 5),
    ]
    for i, card in enumerate(cards[:4]):
        accent = _CARD_ACCENT.get(str(card.get("key") or ""), "#1b4332")
        cmds.append(("BACKGROUND", (i, 0), (i, 0), HexColor(accent)))
        bg = _CONF_BG.get(str(card.get("confidence_level") or card.get("confidence") or ""), "#f5f5f5")
        cmds.append(("BACKGROUND", (i, 2), (i, 2), HexColor(bg)))
    t.setStyle(TableStyle(cmds))
    return t


def _evidence_cards_table(cards: list[dict[str, Any]]) -> Table:
    styles = _styles()
    cells: list[Any] = []
    for card in cards[:4]:
        title = Paragraph(_esc(f"【{card.get('title') or ''}】"), styles["h2"])
        body = Paragraph(_esc(card.get("body") or "—"), styles["small"])
        inner = Table([[title], [body]], colWidths=[86 * mm])
        inner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e8f0ea")),
                    ("BACKGROUND", (0, 1), (-1, 1), HexColor("#fbfdfb")),
                    ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#c5d5c8")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        cells.append(inner)
    while len(cells) < 4:
        cells.append("")
    grid = [[cells[0], cells[1]], [cells[2], cells[3]]]
    t = Table(grid, colWidths=[89 * mm, 89 * mm])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )
    return t


def _highlight_box(title: str, body: str, styles: dict) -> Table:
    data = [
        [Paragraph(_esc(title), styles["h2"])],
        [Paragraph(_esc(body or "—"), styles["box"])],
    ]
    t = Table(data, colWidths=[_CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dce8df")),
                ("BACKGROUND", (0, 1), (-1, 1), HexColor("#f4f8f5")),
                ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#9db8a4")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t



def _items_from_value(value: Any, *, max_items: int = 6) -> list[str]:
    """Normalize str / list / None into short left-aligned bullet strings."""
    if value is None:
        return []
    raw: list[str] = []
    if isinstance(value, list):
        for x in value:
            s = str(x).strip()
            if s:
                raw.append(s)
    else:
        s = str(value).strip()
        if not s:
            return []
        # Prefer explicit newlines (LLM list joined by _as_str_or_none).
        if "\n" in s:
            raw = [p.strip() for p in s.splitlines() if p.strip()]
        else:
            # Split long Chinese sentences into short bullets when possible.
            parts = [p.strip() for p in s.replace("；", "。").split("。") if p.strip()]
            raw = parts if len(parts) > 1 else [s]
    cleaned: list[str] = []
    for item in raw:
        t = item.lstrip("•·-— ").strip()
        if t:
            cleaned.append(t)
    return cleaned[:max_items]


def _panel_card(
    title: str,
    bullets: list[str],
    *,
    header_bg: str,
    body_bg: str,
    border: str,
    width: float,
    styles: dict,
    title_color: str | None = None,
) -> Table:
    title_style = ParagraphStyle(
        f"sg_panel_title_{id(title)}_{int(width)}",
        parent=styles["card_h"],
        textColor=HexColor(title_color or "#143d2b"),
    )
    body_style = styles["card_bullet"]
    rows: list[list[Any]] = [[Paragraph(_esc(title), title_style)]]
    if bullets:
        for b in bullets:
            rows.append([Paragraph(f"• {_esc(b)}", body_style)])
    else:
        rows.append([Paragraph("—", body_style)])
    t = Table(rows, colWidths=[width])
    cmds: list[tuple] = [
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(header_bg)),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor(body_bg)),
        ("BOX", (0, 0), (-1, -1), 0.45, HexColor(border)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (0, 0), 3),
        ("BOTTOMPADDING", (0, 0), (0, 0), 3),
        ("TOPPADDING", (0, 1), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]
    t.setStyle(TableStyle(cmds))
    return t


def _conclusion_pills(items: list[str], styles: dict) -> KeepTogether:
    """3–4 short conclusion cards with numbered pills."""
    pills: list[Any] = []
    accent = HexColor("#1b4332")
    for i, item in enumerate(items[:4], start=1):
        num = Paragraph(str(i), styles["pill_num"])
        body = Paragraph(_esc(item), styles["card_bullet"])
        num_cell = Table([[num]], colWidths=[7 * mm])
        num_cell.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), accent),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 1),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        row = Table([[num_cell, body]], colWidths=[9 * mm, _CONTENT_W - 9 * mm])
        row.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f4f8f5")),
                    ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#9db8a4")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (0, 0), 3),
                    ("RIGHTPADDING", (0, 0), (0, 0), 2),
                    ("LEFTPADDING", (1, 0), (1, 0), 4),
                    ("RIGHTPADDING", (1, 0), (1, 0), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        pills.append(row)
        pills.append(Spacer(1, 1.8 * mm))
    return KeepTogether(pills)


def _factor_cards_row(
    strong: list[str], mid: list[str], weak: list[str], styles: dict
) -> Table:
    gap = 2.5 * mm
    col_w = (_CONTENT_W - 2 * gap) / 3
    cards = [
        _panel_card(
            "证据较强",
            strong or ["程序未列出更强因果；以下仅作提示。"],
            header_bg="#c8e6c9",
            body_bg="#e8f5e9",
            border="#81c784",
            width=col_w,
            styles=styles,
            title_color="#1b5e20",
        ),
        _panel_card(
            "证据中等",
            mid or ["—"],
            header_bg="#ffe082",
            body_bg="#fff8e1",
            border="#ffb300",
            width=col_w,
            styles=styles,
            title_color="#e65100",
        ),
        _panel_card(
            "证据不足",
            weak
            or [
                "天气、播种、品种、土壤、产量、墒情均未由本系统观测，不能认定。"
            ],
            header_bg="#e0e0e0",
            body_bg="#f5f5f5",
            border="#9e9e9e",
            width=col_w,
            styles=styles,
            title_color="#424242",
        ),
    ]
    spaced = Table(
        [[cards[0], "", cards[1], "", cards[2]]],
        colWidths=[col_w, gap, col_w, gap, col_w],
    )
    spaced.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return spaced


def _action_cards_row(
    now_items: list[str],
    week_items: list[str],
    next_items: list[str],
    styles: dict,
) -> Table:
    gap = 2.5 * mm
    col_w = (_CONTENT_W - 2 * gap) / 3
    cards = [
        _panel_card(
            "现在",
            now_items
            or ["结合田间确认当前冠层与墒情，不宜仅凭遥感安排作业。"],
            header_bg="#b2dfdb",
            body_bg="#e0f2f1",
            border="#4db6ac",
            width=col_w,
            styles=styles,
            title_color="#00695c",
        ),
        _panel_card(
            "未来7天",
            week_items or ["未来7天继续关注官方晴空景与田间脱水情况。"],
            header_bg="#bbdefb",
            body_bg="#e3f2fd",
            border="#64b5f6",
            width=col_w,
            styles=styles,
            title_color="#1565c0",
        ),
        _panel_card(
            "下一季",
            next_items or ["下一季请补充播种日期、品种与气象资料，以便校准物候估计。"],
            header_bg="#d1c4e9",
            body_bg="#ede7f6",
            border="#9575cd",
            width=col_w,
            styles=styles,
            title_color="#4527a0",
        ),
    ]
    spaced = Table(
        [[cards[0], "", cards[1], "", cards[2]]],
        colWidths=[col_w, gap, col_w, gap, col_w],
    )
    spaced.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return spaced


def _caution_banner(text: str, styles: dict) -> Table:
    data = [[Paragraph(f"⚠ {_esc(text)}", styles["caution"])]]
    t = Table(data, colWidths=[_CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#fff3e0")),
                ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#ef6c00")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def _gap_chips(items: list[str], styles: dict) -> Table:
    """Compact 2-column bullet list for evidence gaps."""
    if not items:
        items = ["—"]
    cells: list[Any] = []
    for it in items:
        chip = Table(
            [[Paragraph(f"• {_esc(it)}", styles["chip"])]],
            colWidths=[86 * mm],
        )
        chip.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#eceff1")),
                    ("BOX", (0, 0), (-1, -1), 0.3, HexColor("#b0bec5")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        cells.append(chip)
    if len(cells) % 2 == 1:
        cells.append("")
    grid: list[list[Any]] = []
    for i in range(0, len(cells), 2):
        grid.append([cells[i], cells[i + 1]])
    t = Table(grid, colWidths=[89 * mm, 89 * mm])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
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


def _fmt_area(area_ha: Any) -> str:
    if area_ha is None or area_ha == "":
        return "—"
    try:
        return f"{float(area_ha):.2f} ha"
    except (TypeError, ValueError):
        return str(area_ha)


def _crops_label(window: dict[str, Any], field: dict[str, Any]) -> str:
    crops = window.get("crops") or []
    if crops:
        return "、".join(str(c) for c in crops)
    return str(field.get("crop_type") or "—")


def _page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(HexColor("#6b7a70"))
    canvas.setFont("CN", 7.5)
    canvas.drawString(
        16 * mm,
        8 * mm,
        "程序计算事实 · AI 仅解读 · 需田间确认",
    )
    canvas.drawRightString(A4[0] - 16 * mm, 8 * mm, f"{doc.page}")
    canvas.restoreState()


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
    s1_appendix = filter_s1_appendix_rows(list(facts.get("s1_appendix") or []))
    confidence = facts.get("confidence") or {}
    status_cards = list(facts.get("status_cards") or [])
    evidence_cards = list(facts.get("evidence_cards") or [])
    yoy = facts.get("yoy") or {}
    program_core = facts.get("program_core_conclusion")
    program_conclusions = list(facts.get("program_conclusions") or [])
    disclaimer = facts.get("disclaimer") or FOOTER_DISCLAIMER
    ai = ai or {}
    charts = _resolve_chart_paths(chart_paths, chart_path)
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title="生育期长势分析报告",
    )
    story: list[Any] = []

    # ── P1 Cover + status ──
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("生育期长势分析报告", styles["cover_title"]))
    story.append(
        Paragraph("遥感长势 · 水分 · 灾害 · 收获监测", styles["cover_subtitle"])
    )
    story.append(Spacer(1, 3 * mm))
    field_name = field.get("field_name") or "地块"
    story.append(Paragraph(_esc(field_name), styles["cover_field"]))
    story.append(Spacer(1, 3 * mm))

    season_label = window.get("label") or (
        f"{window.get('start_date')} ~ {window.get('end_date')}"
    )
    window_s = (
        f"{window.get('start_date') or '—'} ~ {window.get('end_date') or '—'}"
        + (f"（{season_label}）" if window.get("label") else "")
    )
    meta_rows = [
        ("地块名称", str(field_name)),
        ("地块编号", str(field.get("land_id") or "—")),
        ("面积", _fmt_area(field.get("area_ha"))),
        ("作物", _crops_label(window, field)),
        ("监测窗口", window_s),
        ("报告时间", now),
    ]
    story.append(_meta_table(meta_rows))
    story.append(Spacer(1, 5 * mm))
    story.append(_status_cards_table(status_cards))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "置信度由程序规则给出（高/中/低），不是 AI 百分比。"
            f" 官方可用景 {scenes.get('s2_official_count', '—')} / 总 {scenes.get('s2_count', '—')}；"
            f"S1 {scenes.get('s1_count', '—')} 景。",
            styles["small"],
        )
    )
    story.append(PageBreak())

    # ── P2 综合研判 ──
    story.append(Paragraph("一、综合研判", styles["h1"]))
    core = ai.get("core_conclusion") or program_core or "（程序事实已生成）"
    story.append(_highlight_box("【核心结论】", str(core), styles))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("【关键证据】", styles["h2"]))
    if evidence_cards:
        story.append(_evidence_cards_table(evidence_cards))
    else:
        story.append(Paragraph("（无程序证据卡）", styles["small"]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("【可信度】", styles["h2"]))
    conf_items = list(confidence.get("items") or [])
    if not conf_items:
        for key in ("growth", "drought", "flood", "harvest"):
            block = confidence.get(key)
            if isinstance(block, dict):
                conf_items.append(block)
    if conf_items:
        conf_rows = [["主题", "置信度", "依据（程序规则）"]]
        for it in conf_items:
            conf_rows.append(
                [
                    str(it.get("label") or it.get("key") or "—"),
                    str(it.get("level_cn") or it.get("level") or "—"),
                    str(it.get("reason") or "—"),
                ]
            )
        story.append(
            _table(conf_rows, col_widths=[28 * mm, 22 * mm, 128 * mm], numeric_cols=set())
        )
    else:
        story.append(Paragraph("（可信度块未生成）", styles["small"]))
    story.append(Spacer(1, 3 * mm))
    synthesis = ai.get("synthesis") or ai.get("interpretation") or ""
    if not synthesis:
        synthesis = (
            program_core
            or "大模型未启用。以下仅列程序事实，不作天气/播种/产量推断。"
        )
    story.append(_highlight_box("【AI综合解读】", str(synthesis), styles))
    if ai.get("llm_configured") is False:
        story.append(
            Paragraph(
                "说明：未配置 BAILIAN_API_KEY，解读章节为占位提示，数值均来自程序计算。",
                styles["small"],
            )
        )
    story.append(PageBreak())

    # ── P3 curves ──
    story.append(Paragraph("二、长势与水分曲线", styles["h1"]))
    _chart_block(
        story,
        path=charts.get("ndvi_ndmi"),
        width_mm=176,
        height_mm=82,
        caption="图1  NDVI / NDMI：实线仅连接官方/可靠点；浅灰空心点为不可靠，不参与趋势。色带为物候估计。",
        missing="窗口内无足够 NDVI/NDMI 点，未生成曲线图。",
        styles=styles,
    )
    _chart_block(
        story,
        path=charts.get("s1_vv"),
        width_mm=176,
        height_mm=64,
        caption="图2  Sentinel-1 VV（阈值线 -17.0 / -15.0 dB）",
        missing="窗口内无 S1 VV 数据，未生成洪涝曲线图。",
        styles=styles,
    )
    story.append(Paragraph("【AI时序解读】", styles["h2"]))
    bullets = list(ai.get("timeline_bullets") or [])
    if not bullets and ai.get("timeline_notes"):
        bullets = [ai.get("timeline_notes")]
    if bullets:
        _bullets(story, bullets[:5], styles)
    else:
        story.append(
            Paragraph("（无 AI 时序解读；请以图1/图2 与程序时间线为准。）", styles["small"])
        )
    story.append(PageBreak())

    # ── P4 timeline + YoY ──
    story.append(Paragraph("三、生育期时间线", styles["h1"]))
    monthly_notes = list(ai.get("monthly_notes") or [])
    if timeline:
        tl_rows = [["时段", "作物阶段（估计）", "S2长势", "水分", "S1洪涝", "AI判读"]]
        for i, row in enumerate(timeline):
            note = monthly_notes[i] if i < len(monthly_notes) else "—"
            tl_rows.append(
                [
                    str(row.get("period_label") or row.get("month") or "—"),
                    str(row.get("crop_stage_estimate") or "生育阶段（估计）"),
                    str(row.get("s2_growth") or f"S2 {row.get('s2_count', 0)} 景"),
                    str(row.get("moisture") or "—"),
                    str(row.get("s1_flood") or "—"),
                    str(note),
                ]
            )
        story.append(
            _table(
                tl_rows,
                col_widths=[18 * mm, 32 * mm, 38 * mm, 32 * mm, 28 * mm, 30 * mm],
            )
        )
        story.append(
            Paragraph(
                "作物阶段为日历典型估计，不是实测播种或田间物候。",
                styles["small"],
            )
        )
    else:
        story.append(Paragraph("无按月时间线事实。", styles["body"]))

    story.append(Paragraph("【年度对比】", styles["h2"]))
    shift = yoy.get("peak_date_shift") or {}
    yoy_rows = [
        ["项目", "本年", "上年同期"],
        [
            "窗口",
            f"{window.get('start_date') or '—'} ~ {window.get('end_date') or '—'}",
            f"{yoy.get('prior_start') or '—'} ~ {yoy.get('prior_end') or '—'}",
        ],
        [
            "NDVI 峰值",
            f"{_fmt(yoy.get('this_peak_value'), 4)}（{yoy.get('this_peak_date') or '—'}）",
            f"{_fmt(yoy.get('prior_peak_value'), 4)}（{yoy.get('prior_peak_date') or '—'}）",
        ],
        [
            "峰值日期差",
            str(shift.get("label") or "—"),
            "仅比较峰值日期，不推断生育进程",
        ],
        [
            "NDVI 均值",
            _fmt(yoy.get("this_ndvi_mean"), 4),
            _fmt(yoy.get("prior_ndvi_mean"), 4),
        ],
        [
            "可用点数",
            str(yoy.get("this_point_count") if yoy.get("this_point_count") is not None else "—"),
            str(yoy.get("prior_point_count") if yoy.get("prior_point_count") is not None else "—"),
        ],
        [
            "官方可用景",
            str(yoy.get("this_official_count") if yoy.get("this_official_count") is not None else "—"),
            str(yoy.get("prior_official_count") if yoy.get("prior_official_count") is not None else "—"),
        ],
    ]
    story.append(
        _table(yoy_rows, col_widths=[36 * mm, 71 * mm, 71 * mm], numeric_cols={1, 2})
    )
    story.append(Spacer(1, 2 * mm))
    if shift.get("label"):
        yoy_ai = (
            f"程序计算：{shift.get('label')}。"
            "AI 仅描述峰值日期差异，不能据此写生育进程提前一个月或推断播种/积温。"
        )
    else:
        yoy_ai = "上年同期峰值日期不足，无法做峰值日期对比。"
    story.append(Paragraph(_esc(yoy_ai), styles["body"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("窗口覆盖摘要（程序）", styles["h2"]))
    cover_rows = [["月份", "S2景数", "官方/可用", "S1景数", "干旱日", "洪涝", "关注"]]
    for row in timeline:
        cover_rows.append(
            [
                str(row.get("month") or "—"),
                str(row.get("s2_count", 0)),
                str(row.get("s2_official_count", "—")),
                str(row.get("s1_count", 0)),
                str(row.get("drought_days", 0)),
                str(row.get("flood_count", 0)),
                str(row.get("watch_count", 0)),
            ]
        )
    if len(cover_rows) > 1:
        story.append(
            _table(
                cover_rows,
                col_widths=[28 * mm, 22 * mm, 26 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm],
                numeric_cols={1, 2, 3, 4, 5, 6},
            )
        )
    story.append(PageBreak())

    # ── P5 analysis + actions (card layout) ──
    story.append(Paragraph("四、综合结论与建议", styles["h1"]))
    story.append(Paragraph("【综合结论】", styles["h2"]))
    conclusions = list(ai.get("conclusions") or []) or program_conclusions
    conclusion_items = _items_from_value(conclusions, max_items=4)
    if conclusion_items:
        story.append(_conclusion_pills(conclusion_items, styles))
    else:
        story.append(Paragraph("（无综合结论）", styles["body"]))

    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("【可能影响因素】", styles["h2"]))
    strong = _items_from_value(ai.get("factors_strong"), max_items=4)
    mid = _items_from_value(
        ai.get("factors_mid") or ai.get("causes_ranked"), max_items=4
    )
    weak = _items_from_value(ai.get("factors_weak"), max_items=4)
    story.append(_factor_cards_row(strong, mid, weak, styles))

    story.append(Spacer(1, 2.5 * mm))
    story.append(Paragraph("【当前建议】", styles["h2"]))
    now_items = _items_from_value(
        ai.get("actions_now")
        or "结合田间确认当前冠层与墒情，不宜仅凭遥感安排作业。",
        max_items=5,
    )
    week_items = _items_from_value(
        ai.get("actions_week") or "未来7天继续关注官方晴空景与田间脱水情况。",
        max_items=5,
    )
    next_items = _items_from_value(
        ai.get("actions_next_season")
        or "下一季请补充播种日期、品种与气象资料，以便校准物候估计。",
        max_items=5,
    )
    story.append(_action_cards_row(now_items, week_items, next_items, styles))
    story.append(Spacer(1, 2 * mm))
    if harvest.get("status") == "detected" and str(harvest.get("confidence")) == "low":
        harvest_hint = (
            "收获注意：疑似进入成熟后期或收获准备阶段，需田间确认，不得作为立即收割依据。"
        )
    else:
        harvest_hint = "收获注意：收获安排须田间确认，不得作为立即收割依据。"
    story.append(_caution_banner(harvest_hint, styles))

    story.append(Spacer(1, 2.5 * mm))
    story.append(Paragraph("【需要补充的证据】", styles["h2"]))
    gaps = _items_from_value(
        ai.get("evidence_gaps") or ai.get("follow_up"), max_items=8
    )
    default_gaps = [
        "实测播种日期与品种",
        "土壤墒情或气象降水/蒸发",
        "田间收获进度核实",
        "产量与籽粒含水量（若需评估灾损）",
    ]
    story.append(_gap_chips(gaps or default_gaps, styles))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(_esc(disclaimer), styles["footer"]))
    story.append(PageBreak())

    # ── P6+ appendix ──
    story.append(Paragraph("五、附录", styles["h1"]))

    story.append(Paragraph("附录 A  Sentinel-2 逐景表", styles["h2"]))
    if not s2_appendix:
        story.append(Paragraph("无 S2 逐景记录。", styles["body"]))
    else:
        truncated = len(s2_appendix) > _APPENDIX_MAX_ROWS
        rows_a = s2_appendix[:_APPENDIX_MAX_ROWS]
        s2_rows = [["日期", "云量%", "质量", "干旱等级", "NDVI", "NDMI", "EVI", "MNDWI"]]
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
                    18 * mm,
                    18 * mm,
                    22 * mm,
                    20 * mm,
                    20 * mm,
                    20 * mm,
                    22 * mm,
                ],
                numeric_cols={1, 4, 5, 6, 7},
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

    story.append(Spacer(1, 2.5 * mm))
    story.append(Paragraph("附录 B  Sentinel-1 逐景表", styles["h2"]))
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
                col_widths=[32 * mm, 26 * mm, 32 * mm, 32 * mm, 40 * mm],
                numeric_cols={1, 2, 3},
            )
        )
        if truncated_b:
            story.append(
                Paragraph(
                    f"注：去重后共 {len(s1_appendix)} 行，附录仅展示前 {_APPENDIX_MAX_ROWS} 行。",
                    styles["small"],
                )
            )
        else:
            story.append(Paragraph("注：同日多景已按较低 VV 保留一条。", styles["small"]))

    story.append(Spacer(1, 2.5 * mm))
    story.append(Paragraph("附录 C  判定方法", styles["h2"]))
    method_rows = [
        ["类别", "说明"],
        ["光学干旱（S2）", methodology.get("drought") or "基于 agri_classify 干旱分类器。"],
        ["SAR 洪涝（S1）", methodology.get("flood") or "基于 agri_classify 洪涝分类器。"],
        ["传感器", methodology.get("sensors") or "Sentinel-2 / Sentinel-1"],
        [
            "曲线规则",
            "趋势线只连接官方/可靠点；不可靠点以浅灰空心标记，不进入连线。",
        ],
        [
            "物候",
            "作物阶段为日历典型估计，标注「估计」，不代表实测播种日期。",
        ],
        [
            "收获",
            "观察型检测；低置信度仅提示疑似成熟后期或收获准备，需田间确认。",
        ],
    ]
    story.append(_table(method_rows, col_widths=[32 * mm, 146 * mm], zebra=True))

    story.append(Spacer(1, 2.5 * mm))
    story.append(Paragraph("附录 D  质量说明", styles["h2"]))
    quality_notes = [
        f"数据来源：{facts.get('data_source') or '遥感产品'}；程序计算事实，AI 仅解读。",
        f"S2 总景 {scenes.get('s2_count', '—')}，官方/可用 {scenes.get('s2_official_count', '—')}，"
        f"晴空 {scenes.get('s2_clear_count', '—')}；S1 {scenes.get('s1_count', '—')} 景。",
        f"干旱分级计数：{format_drought_counts(drought.get('counts'))}。",
        f"洪涝状态：{format_flood_status(flood.get('status'))}；"
        f"{format_flood_counts(flood.get('counts'))}。",
        f"收获检测：{format_harvest_line(harvest)}。",
        "不可靠光学点不进入干旱官方判定，也不进入图1趋势线。",
    ]
    _bullets(story, quality_notes, styles)
    mats = materials_meta or []
    if mats:
        story.append(Paragraph("附加材料", styles["h2"]))
        for m in mats:
            line = f"• {_esc(m.get('filename'))}"
            if m.get("note"):
                line += f"（{_esc(m.get('note'))}）"
            elif m.get("ok"):
                line += "（已提取/已登记）"
            story.append(Paragraph(line, styles["bullet"]))
    else:
        story.append(Paragraph("注：本次未上传附加材料。", styles["small"]))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return out
