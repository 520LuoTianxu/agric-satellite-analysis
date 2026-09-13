# -*- coding: utf-8 -*-
"""NDVI / NDMI / S1 VV season charts for season-growth PDF."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from app.core.agri_classify import FLOOD_VV_MAX, WATCH_VV_MAX
from app.reports.land_assessment.paths import FONT_PATH

_DROUGHT_MARKER_COLORS = {
    "normal": "#2e7d32",
    "mild": "#f9a825",
    "moderate": "#ef6c00",
    "severe": "#c62828",
    "unreliable": "#9e9e9e",
    "out_of_season": "#9e9e9e",
}

_FLOOD_MARKER_COLORS = {
    "dry": "#2e7d32",
    "watch": "#f9a825",
    "flood_moderate": "#ef6c00",
    "flood_severe": "#c62828",
}

_PHENO_BAND_COLORS = (
    "#e8f5e9",
    "#fff8e1",
    "#e3f2fd",
    "#fce4ec",
    "#f3e5f5",
    "#efebe9",
)


def _setup_font() -> None:
    if FONT_PATH.exists():
        font_manager.fontManager.addfont(str(FONT_PATH))
        plt.rcParams["font.family"] = "WenQuanYi Zen Hei"
    plt.rcParams["axes.unicode_minus"] = False


def _drought_class_by_date(facts: dict[str, Any]) -> dict[str, str]:
    drought = facts.get("drought") or {}
    out: dict[str, str] = {}
    source = (
        drought.get("usable_scene_classes")
        or drought.get("scene_classes")
        or drought.get("classified")
        or []
    )
    # Prefer higher-priority class if duplicates sneak in
    prio = {
        "severe": 60,
        "moderate": 50,
        "mild": 40,
        "normal": 30,
        "out_of_season": 20,
        "unreliable": 10,
    }
    for sc in source:
        d = sc.get("date")
        if not d:
            continue
        key = str(d)[:10]
        cls = str(sc.get("class") or "")
        prev = out.get(key)
        if prev is None or prio.get(cls, 0) > prio.get(prev, 0):
            out[key] = cls
    return out


def _to_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def point_is_reliable(point: dict[str, Any], class_by_date: dict[str, str] | None = None) -> bool:
    """Official/usable points participate in the trend line; others are hollow."""
    if point.get("official") is False:
        return False
    if point.get("official") is True:
        return True
    q = str(point.get("quality") or point.get("decloud_quality") or "").lower()
    if q in ("bad", "raw", "fair", "poor"):
        return False
    return True


def _split_series(
    series: list[dict[str, Any]], class_by_date: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reliable: list[dict[str, Any]] = []
    unreliable: list[dict[str, Any]] = []
    for p in series:
        if p.get("value") is None or not p.get("date"):
            continue
        if point_is_reliable(p, class_by_date):
            reliable.append(p)
        else:
            unreliable.append(p)
    return reliable, unreliable


def _draw_phenology_bands(ax, facts: dict[str, Any]) -> None:
    bands = list(facts.get("phenology_estimate") or [])
    if not bands:
        return
    ymin, ymax = ax.get_ylim()
    for i, band in enumerate(bands):
        a = _to_dt(band.get("start"))
        b = _to_dt(band.get("end"))
        if not a or not b:
            continue
        color = _PHENO_BAND_COLORS[i % len(_PHENO_BAND_COLORS)]
        ax.axvspan(a, b + timedelta(days=1), color=color, alpha=0.35, zorder=0)
        mid = a + (b - a) / 2
        label = str(band.get("label") or "")
        if label:
            ax.text(
                mid,
                ymax - (ymax - ymin) * 0.04,
                label,
                ha="center",
                va="top",
                fontsize=6.5,
                color="#5d6d5e",
                zorder=4,
            )


def _dry_spells(class_by_date: dict[str, str]) -> list[tuple[datetime, datetime]]:
    drought_dates = sorted(
        _to_dt(d)
        for d, c in class_by_date.items()
        if c in ("mild", "moderate", "severe") and _to_dt(d)
    )
    drought_dates = [d for d in drought_dates if d is not None]
    if len(drought_dates) < 2:
        return []
    spells: list[tuple[datetime, datetime]] = []
    run_start = drought_dates[0]
    prev = drought_dates[0]
    for d in drought_dates[1:]:
        if (d - prev).days <= 8:
            prev = d
            continue
        if prev != run_start:
            spells.append((run_start, prev))
        run_start = d
        prev = d
    if prev != run_start:
        spells.append((run_start, prev))
    return spells


def render_ndvi_ndmi_chart(
    facts: dict[str, Any],
    out_path: Path | str,
    *,
    scene_classes: list[dict[str, Any]] | None = None,
) -> Path | None:
    """NDVI/NDMI: solid line through reliable points only; unreliable = hollow gray."""
    ndvi = list((facts.get("ndvi") or {}).get("series") or [])
    ndmi = list((facts.get("ndmi") or {}).get("series") or [])
    if not ndvi and not ndmi:
        return None

    class_by_date: dict[str, str] = {}
    if scene_classes is not None:
        for sc in scene_classes:
            d = sc.get("date")
            if d and d not in class_by_date:
                class_by_date[str(d)[:10]] = str(sc.get("class") or "")
    else:
        class_by_date = _drought_class_by_date(facts)

    _setup_font()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7.4, 3.55), dpi=140)

    rel_ndvi, unrel_ndvi = _split_series(ndvi, class_by_date)
    rel_ndmi, unrel_ndmi = _split_series(ndmi, class_by_date)

    if rel_ndvi:
        xs = [datetime.fromisoformat(p["date"][:10]) for p in rel_ndvi]
        ys = [float(p["value"]) for p in rel_ndvi]
        ax.plot(xs, ys, color="#1b4332", linewidth=2.4, label="NDVI（可靠）", zorder=3)
        ax.scatter(
            xs, ys, c="#2e7d32", s=22, zorder=4, edgecolors="white", linewidths=0.4
        )
    if unrel_ndvi:
        xu = [datetime.fromisoformat(p["date"][:10]) for p in unrel_ndvi]
        yu = [float(p["value"]) for p in unrel_ndvi]
        ax.scatter(
            xu,
            yu,
            facecolors="none",
            edgecolors="#cfd8dc",
            s=20,
            linewidths=0.6,
            alpha=0.45,
            zorder=2,
            label="不可靠（不连线）",
        )
    if rel_ndmi:
        xs2 = [datetime.fromisoformat(p["date"][:10]) for p in rel_ndmi]
        ys2 = [float(p["value"]) for p in rel_ndmi]
        ax.plot(
            xs2,
            ys2,
            color="#1565c0",
            linewidth=1.1,
            linestyle="--",
            label="NDMI（可靠）",
            alpha=0.9,
            zorder=3,
        )
    if unrel_ndmi:
        xu2 = [datetime.fromisoformat(p["date"][:10]) for p in unrel_ndmi]
        yu2 = [float(p["value"]) for p in unrel_ndmi]
        ax.scatter(
            xu2,
            yu2,
            facecolors="none",
            edgecolors="#90a4ae",
            s=14,
            marker="s",
            linewidths=0.5,
            alpha=0.35,
            zorder=2,
        )

    # Annotate peak / latest official
    peak = (facts.get("ndvi") or {}).get("peak") or {}
    if peak.get("date") and peak.get("value") is not None:
        pdt = _to_dt(peak["date"])
        if pdt is not None:
            ax.annotate(
                f"峰值 {float(peak['value']):.3f}",
                xy=(pdt, float(peak["value"])),
                xytext=(8, 10),
                textcoords="offset points",
                fontsize=7.5,
                color="#1b4332",
                arrowprops={"arrowstyle": "->", "color": "#1b4332", "lw": 0.7},
            )
    latest = (facts.get("ndvi") or {}).get("latest") or {}
    if latest.get("date") and latest.get("value") is not None:
        ldt = _to_dt(latest["date"])
        peak_date = str(peak.get("date") or "")
        if ldt is not None and str(latest.get("date")) != peak_date:
            ax.annotate(
                f"最新 {float(latest['value']):.3f}",
                xy=(ldt, float(latest["value"])),
                xytext=(-28, -14),
                textcoords="offset points",
                fontsize=7.5,
                color="#37474f",
            )

    # Annotate September dry if present
    sep_dry = [
        (d, c)
        for d, c in class_by_date.items()
        if d[5:7] == "09" and c in ("mild", "moderate", "severe")
    ]
    if sep_dry:
        sdt = _to_dt(sep_dry[0][0])
        if sdt is not None:
            ax.annotate(
                "九月偏干",
                xy=(sdt, ax.get_ylim()[0] + 0.02),
                xytext=(0, 18),
                textcoords="offset points",
                fontsize=7,
                color="#c62828",
                ha="center",
            )

    win = facts.get("window") or {}
    title = "生育期 NDVI / NDMI（可靠点连线）"
    label = win.get("label")
    if label:
        title = f"{title}（{label}）"
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("指数值")
    ax.set_xlabel("日期")
    ax.grid(True, alpha=0.22, zorder=0)
    _draw_phenology_bands(ax, facts)

    # Bottom drought event strip (not rainbow point colors)
    ymin, ymax = ax.get_ylim()
    strip_y = ymin - (ymax - ymin) * 0.08
    ax.set_ylim(strip_y - (ymax - ymin) * 0.02, ymax)
    for d, c in class_by_date.items():
        if c not in ("mild", "moderate", "severe"):
            continue
        dt = _to_dt(d)
        if dt is None:
            continue
        ax.plot(
            [dt, dt],
            [strip_y, strip_y + (ymax - ymin) * 0.05],
            color=_DROUGHT_MARKER_COLORS.get(c, "#c62828"),
            linewidth=2.2,
            solid_capstyle="round",
            zorder=5,
        )
    ax.axhline(strip_y, color="#eceff1", linewidth=6, zorder=1, alpha=0.9)

    handles, labels = ax.get_legend_handles_labels()
    extra = [
        Line2D([0], [0], color=_DROUGHT_MARKER_COLORS["mild"], lw=2, label="干旱事件·轻"),
        Line2D([0], [0], color=_DROUGHT_MARKER_COLORS["moderate"], lw=2, label="干旱事件·中"),
        Line2D([0], [0], color=_DROUGHT_MARKER_COLORS["severe"], lw=2, label="干旱事件·重"),
        Line2D(
            [0], [0], marker="o", color="w", markerfacecolor="none",
            markeredgecolor="#cfd8dc", markersize=6, label="不可靠（不连线）",
        ),
        Patch(facecolor="#e8f5e9", edgecolor="none", label="物候带（估计）"),
    ]
    ax.legend(
        handles + extra,
        labels + [h.get_label() for h in extra],
        loc="lower left",
        fontsize=6.0,
        ncol=3,
        framealpha=0.9,
    )
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out if out.exists() else None


def render_s1_vv_chart(
    facts: dict[str, Any],
    out_path: Path | str,
) -> Path | None:
    """Plot S1 VV; hlines at flood/watch thresholds -17.0 / -15.0."""
    flood = facts.get("flood") or {}
    scenes = list(flood.get("scenes") or [])
    points = [s for s in scenes if s.get("vv") is not None and s.get("date")]
    if not points:
        return None

    _setup_font()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    xs = [datetime.fromisoformat(str(s["date"])[:10]) for s in points]
    ys = [float(s["vv"]) for s in points]
    colors = [
        _FLOOD_MARKER_COLORS.get(str(s.get("class") or "dry"), "#757575")
        for s in points
    ]

    fig, ax = plt.subplots(figsize=(7.4, 2.85), dpi=140)
    ax.plot(xs, ys, color="#90a4ae", linewidth=1.2, zorder=1)
    ax.scatter(xs, ys, c=colors, s=32, zorder=3, edgecolors="white", linewidths=0.4)
    ax.axhline(
        FLOOD_VV_MAX,
        color="#c62828",
        linestyle="--",
        linewidth=1.1,
        label=f"洪涝阈值 {FLOOD_VV_MAX:.1f} dB",
    )
    ax.axhline(
        WATCH_VV_MAX,
        color="#f9a825",
        linestyle="--",
        linewidth=1.1,
        label=f"关注阈值 {WATCH_VV_MAX:.1f} dB",
    )
    win = facts.get("window") or {}
    title = "Sentinel-1 VV 洪涝监测"
    label = win.get("label")
    if label:
        title = f"{title}（{label}）"
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("VV (dB)")
    ax.set_xlabel("日期")
    ax.grid(True, alpha=0.25)
    handles, labels = ax.get_legend_handles_labels()
    extra = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=c,
            markersize=7,
            label=lab,
        )
        for lab, c in (
            ("正常", _FLOOD_MARKER_COLORS["dry"]),
            ("关注", _FLOOD_MARKER_COLORS["watch"]),
            ("洪涝", _FLOOD_MARKER_COLORS["flood_moderate"]),
            ("洪涝(重)", _FLOOD_MARKER_COLORS["flood_severe"]),
        )
    ]
    ax.legend(
        handles + extra,
        labels + [h.get_label() for h in extra],
        loc="best",
        fontsize=6.5,
    )
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out if out.exists() else None


def render_season_charts(
    facts: dict[str, Any],
    out_dir: Path | str,
) -> dict[str, Path]:
    """Render available charts; keys like ndvi_ndmi, s1_vv (omit missing)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    ndvi_path = render_ndvi_ndmi_chart(facts, out_dir / "ndvi_ndmi.png")
    if ndvi_path is not None:
        paths["ndvi_ndmi"] = ndvi_path
    s1_path = render_s1_vv_chart(facts, out_dir / "s1_vv.png")
    if s1_path is not None:
        paths["s1_vv"] = s1_path
    return paths
