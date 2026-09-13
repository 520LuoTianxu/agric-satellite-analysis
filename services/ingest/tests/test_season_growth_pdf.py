"""PDF render smoke test (no LLM, v2 layout)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.reports.season_growth.facts import (
    FOOTER_DISCLAIMER,
    compute_confidence,
    compute_evidence_cards,
    compute_status_cards,
    compute_yoy,
    program_conclusions,
    program_core_conclusion,
)
from app.reports.season_growth.pdf_render import (
    _items_from_value,
    filter_s1_appendix_rows,
    filter_s2_appendix_rows,
    format_drought_counts,
    format_flood_counts,
    format_flood_status,
    format_harvest_line,
    quality_cn,
    render_season_growth_pdf,
)


def _rich_facts() -> dict:
    ndvi = {
        "mean": 0.55,
        "peak": {"date": "2026-08-05", "value": 0.7},
        "latest": {"date": "2026-09-05", "value": 0.4},
        "point_count": 2,
        "series": [
            {"date": "2026-06-05", "value": 0.32, "official": True},
            {"date": "2026-08-05", "value": 0.7, "official": True},
            {"date": "2026-09-05", "value": 0.4, "official": True},
        ],
    }
    drought = {
        "drought_scene_count": 1,
        "counts": {"normal": 6, "mild": 1, "unreliable": 2},
        "days": [{"date": "2026-08-20", "class": "mild"}, {"date": "2026-09-05", "class": "severe"}],
        "scene_classes": [
            {"date": "2026-06-05", "class": "normal"},
            {"date": "2026-08-20", "class": "mild"},
        ],
    }
    flood = {
        "status": "ok",
        "vv_median": -12.0,
        "flood_scene_count": 0,
        "counts": {"dry": 4, "watch": 0},
        "scenes": [
            {
                "date": "2026-07-01",
                "vv": -12.0,
                "vh": -18.0,
                "relative_orbit": 10,
                "class": "dry",
            }
        ],
        "note": None,
    }
    harvest = {
        "status": "detected",
        "harvest_date": "2026-09-05",
        "confidence": "low",
    }
    scenes = {
        "s2_count": 18,
        "s1_count": 8,
        "s2_official_count": 16,
        "s2_clear_count": 14,
    }
    confidence = compute_confidence(
        official_s2=16,
        peak_exists=True,
        drought_counts=drought["counts"],
        s1_count=8,
        flood_scene_count=0,
        harvest=harvest,
    )
    status_cards = compute_status_cards(
        ndvi=ndvi,
        drought=drought,
        flood=flood,
        harvest=harvest,
        scenes=scenes,
        confidence=confidence,
    )
    yoy = compute_yoy(
        ndvi,
        {
            "start_date": "2025-06-01",
            "end_date": "2025-09-30",
            "ndvi_mean": 0.24,
            "ndvi_peak": {"date": "2025-08-11", "value": 0.85},
            "point_count": 20,
            "official_count": 12,
        },
        scenes,
    )
    evidence_cards = compute_evidence_cards(
        ndvi=ndvi, drought=drought, flood=flood, harvest=harvest, scenes=scenes, yoy=yoy
    )
    return {
        "field": {
            "field_name": "测试地块",
            "land_id": "LAND001",
            "field_id": "00000000-0000-0000-0000-000000000001",
            "area_ha": 0.93,
            "crop_type": "corn",
        },
        "window": {
            "start_date": "2026-06-01",
            "end_date": "2026-09-30",
            "label": "2026夏玉米",
            "crops": ["玉米"],
        },
        "data_source": "test",
        "scenes": scenes,
        "ndvi": ndvi,
        "ndmi": {"mean": 0.1, "series": [{"date": "2026-06-05", "value": 0.18, "official": True}]},
        "drought": drought,
        "flood": flood,
        "harvest": harvest,
        "prior_year": {
            "start_date": "2025-06-01",
            "end_date": "2025-09-30",
            "ndvi_mean": 0.24,
            "ndvi_peak": {"date": "2025-08-11", "value": 0.85},
            "point_count": 20,
        },
        "methodology": {
            "drought": "S2 干旱规则摘要",
            "flood": "洪涝需同时满足 VV≤-17.0 dB、相对基线下降≥3.0 dB。",
            "sensors": "S2/S1",
        },
        "timeline": [
            {
                "month": "2026-06",
                "period_label": "6月",
                "crop_stage_estimate": "苗期–拔节（估计）",
                "s2_growth": "官方/可用2景，NDVI均0.32，最高0.32",
                "moisture": "正常6",
                "s1_flood": "未检出洪涝（0景）",
                "s2_count": 2,
                "s2_official_count": 2,
                "s1_count": 0,
                "drought_days": 0,
                "flood_count": 0,
                "watch_count": 0,
            },
            {
                "month": "2026-07",
                "period_label": "7月",
                "crop_stage_estimate": "拔节–抽雄/吐丝（估计）",
                "s2_growth": "官方/可用2景",
                "moisture": "正常",
                "s1_flood": "未检出洪涝（3景）",
                "s2_count": 2,
                "s2_official_count": 2,
                "s1_count": 3,
                "drought_days": 0,
                "flood_count": 0,
                "watch_count": 0,
            },
        ],
        "s2_appendix": [
            {
                "date": "2026-06-05",
                "cloud_pct": 5.0,
                "quality": "bad",
                "ndvi": 0.0,
                "ndmi": None,
                "evi": None,
                "mndwi": None,
                "drought_class": "normal",
                "drought_class_cn": "正常",
            },
            {
                "date": "2026-06-05",
                "cloud_pct": 5.0,
                "quality": "good",
                "quality_cn": "良好",
                "drought_class": "normal",
                "drought_class_cn": "正常",
                "ndvi": 0.32,
                "ndmi": 0.18,
                "evi": 0.28,
                "mndwi": -0.1,
            },
            {
                "date": "2026-08-20",
                "cloud_pct": 8.0,
                "quality": "good",
                "quality_cn": "良好",
                "drought_class": "mild",
                "drought_class_cn": "轻度",
                "ndvi": 0.55,
                "ndmi": -0.05,
                "evi": 0.45,
                "mndwi": -0.05,
            },
        ],
        "s1_appendix": [
            {
                "date": "2026-07-01",
                "relative_orbit": 10,
                "vv": -12.0,
                "vh": -18.0,
                "flood_class": "dry",
                "flood_class_cn": "正常",
            },
            {
                "date": "2026-07-01",
                "relative_orbit": 10,
                "vv": -11.0,
                "vh": -17.0,
                "flood_class": "dry",
                "flood_class_cn": "正常",
            },
        ],
        "confidence": confidence,
        "status_cards": status_cards,
        "evidence_cards": evidence_cards,
        "yoy": yoy,
        "phenology_estimate": [
            {
                "start": "2026-06-01",
                "end": "2026-06-30",
                "month": 6,
                "label": "苗期–拔节（估计）",
            }
        ],
        "program_core_conclusion": program_core_conclusion(
            status_cards=status_cards, yoy=yoy, harvest=harvest
        ),
        "program_conclusions": program_conclusions(
            scenes=scenes, ndvi=ndvi, drought=drought, flood=flood, harvest=harvest, yoy=yoy
        ),
        "disclaimer": FOOTER_DISCLAIMER,
    }


def _rich_ai() -> dict:
    return {
        "core_conclusion": "冠层绿度中期较高，九月回落，收获需田间确认。",
        "synthesis": "官方可用景较充足。峰值在8月。干旱有提示，洪涝未检出。收获信号低置信度，疑似进入成熟后期或收获准备阶段，需田间确认。峰值日期较上年提前。还缺土壤与气象资料。",
        "timeline_bullets": ["6月苗期绿度上升", "8月峰值", "9月绿度回落"],
        "monthly_notes": ["绿度上升（估计）", "抽雄阶段绿度高（估计）"],
        "conclusions": ["冠层绿度前高后落", "干旱提示存在", "洪涝未检出"],
        "factors_strong": ["九月绿度回落与干旱等级共现"],
        "factors_mid": ["峰值日期提前"],
        "factors_weak": ["品种与播种未提供"],
        "actions_now": "田间确认成熟与脱水。\n检查灌溉设施。",
        "actions_week": "关注墒情变化。\n跟踪官方晴空景。",
        "actions_next_season": "下一季在拔节–抽雄、灌浆阶段安排墒情检查与灌溉准备。\n记录播种日期与品种。",
        "evidence_gaps": ["实测播种日期", "土壤墒情", "气象降水记录"],
        "llm_configured": False,
    }


def _pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return path.read_bytes().decode("latin-1", errors="ignore")
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts)


class SeasonGrowthPdfTests(unittest.TestCase):
    def test_format_helpers_chinese(self) -> None:
        self.assertEqual(
            format_drought_counts(
                {"unreliable": 48, "severe": 8, "normal": 17, "moderate": 1, "mild": 1}
            ),
            "重度8 / 中度1 / 轻度1 / 正常17 / 不可靠48",
        )
        self.assertEqual(format_drought_counts({"normal": 0, "mild": 0}), "—")
        self.assertEqual(format_flood_counts({"watch": 3, "dry": 12}), "关注3 / 正常12")
        self.assertEqual(format_flood_status("ok"), "正常监测")
        self.assertEqual(format_flood_status("no_s1_data"), "无S1数据")
        self.assertEqual(
            format_harvest_line(
                {"status": "detected", "harvest_date": "2026-09-05", "confidence": "low"}
            ),
            "已检测 / 2026-09-05（低）",
        )
        self.assertEqual(quality_cn("official"), "官方")
        self.assertEqual(quality_cn("bad"), "较差")
        self.assertEqual(quality_cn("raw"), "原始")

    def test_filter_s2_appendix_prefers_good(self) -> None:
        rows = [
            {"date": "2026-06-02", "quality": "bad", "ndvi": 0.0},
            {"date": "2026-06-02", "quality": "official", "ndvi": 0.229},
            {"date": "2026-06-05", "quality": "bad", "ndvi": 0.0},
            {"date": "2026-06-05", "quality": "raw", "ndvi": 0.34},
            {"date": "2026-06-07", "quality": "official", "ndvi": 0.379},
        ]
        out = filter_s2_appendix_rows(rows)
        by_date = {r["date"]: r for r in out}
        self.assertEqual(by_date["2026-06-02"]["quality"], "official")
        self.assertEqual(by_date["2026-06-05"]["quality"], "raw")
        self.assertIn("2026-06-07", by_date)
        self.assertEqual(len(out), 3)

    def test_filter_s1_appendix_dedupes(self) -> None:
        rows = [
            {"date": "2026-07-01", "vv": -11.0},
            {"date": "2026-07-01", "vv": -14.0},
            {"date": "2026-07-13", "vv": -12.0},
        ]
        out = filter_s1_appendix_rows(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["vv"], -14.0)

    def test_render_minimal_pdf_bytes(self) -> None:
        facts = {
            "field": {
                "field_name": "测试地块",
                "land_id": "LAND001",
                "field_id": "00000000-0000-0000-0000-000000000001",
            },
            "window": {
                "start_date": "2026-06-01",
                "end_date": "2026-09-30",
                "label": "2026夏玉米",
                "crops": ["summer_corn"],
            },
            "data_source": "test",
            "scenes": {
                "s2_count": 7,
                "s1_count": 0,
                "s2_official_count": 7,
                "s2_clear_count": 7,
            },
            "ndvi": {
                "mean": 0.55,
                "peak": {"date": "2026-08-05", "value": 0.7},
                "latest": {"date": "2026-09-05", "value": 0.4},
                "series": [
                    {"date": "2026-06-05", "value": 0.32},
                    {"date": "2026-08-05", "value": 0.7},
                ],
            },
            "ndmi": {"mean": 0.1, "series": []},
            "drought": {"drought_scene_count": 0, "counts": {"normal": 7}},
            "flood": {"status": "no_s1_data", "vv_median": None, "note": "无 S1"},
            "harvest": {
                "status": "uncertain",
                "harvest_date": None,
                "confidence": "low",
            },
            "prior_year": None,
        }
        ai = {
            "core_conclusion": "遥感事实已生成（AI 解读未启用）",
            "synthesis": "大模型未配置，仅含程序事实。",
            "timeline_bullets": [],
            "llm_configured": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "season.pdf"
            path = render_season_growth_pdf(
                facts=facts,
                ai=ai,
                chart_path=None,
                materials_meta=[],
                out_path=out,
            )
            self.assertTrue(path.exists())
            data = path.read_bytes()
            self.assertGreater(len(data), 500)
            self.assertTrue(data.startswith(b"%PDF"))
            page_count = data.count(b"/Type /Page")
            self.assertGreaterEqual(page_count, 5)
            self.assertLessEqual(page_count, 14)

    def test_render_richer_pdf_no_raw_dict_or_banned(self) -> None:
        facts = _rich_facts()
        ai = _rich_ai()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "season_rich.pdf"
            path = render_season_growth_pdf(
                facts=facts,
                ai=ai,
                chart_paths=None,
                materials_meta=[],
                out_path=out,
            )
            self.assertTrue(path.exists())
            data = path.read_bytes()
            self.assertGreater(len(data), 3000)
            self.assertTrue(data.startswith(b"%PDF"))
            self.assertIn(b"/Type /Page", data)
            self.assertNotIn(b"{'unreliable'", data)
            self.assertNotIn(b"detected /", data)
            extracted = _pdf_text(path)
            banned = ["生物量积累达标", "生物量达标"]
            haystack = extracted + (facts.get("program_core_conclusion") or "")
            for phrase in banned:
                self.assertNotIn(phrase, haystack)
                self.assertNotIn(phrase.encode("utf-8"), data)
            # 禁止用语仅允许出现在否定/免责表述中
            self.assertNotIn("建议立即收割", haystack)
            self.assertNotIn("请立即收割", haystack)
            self.assertNotIn("立即收割。", haystack)
            self.assertNotIn("生育进程提前一个月。", haystack)
            self.assertNotIn("已生育进程提前一个月", haystack)
            # v2 layout: cover+研判+curves+timeline+actions (+ appendix)
            page_count = data.count(b"/Type /Page")
            self.assertGreaterEqual(page_count, 5)
            # Chinese extraction is font-dependent; only assert when glyphs round-trip.
            if "地块" in extracted or "长势" in extracted:
                self.assertIn("综合研判", extracted)
                self.assertIn("核心结论", extracted)
                self.assertIn("可信度", extracted)
                self.assertIn("年度对比", extracted)
                self.assertNotIn("证据要点", extracted)
                self.assertNotIn("结论复述", extracted)
            self.assertIn("疑似进入成熟后期或收获准备阶段", facts["status_cards"][3]["value"])
            self.assertIn("估计", facts["timeline"][0]["crop_stage_estimate"])

    def test_status_cards_harvest_wording(self) -> None:
        facts = _rich_facts()
        harvest_card = next(c for c in facts["status_cards"] if c["key"] == "harvest")
        self.assertIn("疑似进入成熟后期或收获准备阶段", harvest_card["value"])
        self.assertEqual(harvest_card["confidence"], "低")
        self.assertIn("估计", facts["timeline"][0]["crop_stage_estimate"])

    def test_items_from_value_splits_newlines(self) -> None:
        self.assertEqual(
            _items_from_value("田间确认。\n检查灌溉。"),
            ["田间确认。", "检查灌溉。"],
        )
        self.assertEqual(
            _items_from_value(["A", " B ", ""]),
            ["A", "B"],
        )

    def test_conclusion_page_card_labels(self) -> None:
        facts = _rich_facts()
        ai = _rich_ai()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "season_cards.pdf"
            path = render_season_growth_pdf(
                facts=facts,
                ai=ai,
                chart_paths=None,
                materials_meta=[],
                out_path=out,
            )
            data = path.read_bytes()
            self.assertTrue(data.startswith(b"%PDF"))
            self.assertGreater(len(data), 3000)
            # Card layout should keep harvest caution separate from action columns.
            extracted = _pdf_text(path)
            hay = extracted + "\n".join(
                [
                    str(ai.get("actions_now") or ""),
                    str(ai.get("actions_week") or ""),
                    str(ai.get("actions_next_season") or ""),
                ]
            )
            self.assertIn("疑似进入成熟后期或收获准备阶段", hay + (facts.get("program_core_conclusion") or ""))
            banned = ["生物量积累达标", "生物量达标"]
            for phrase in banned:
                self.assertNotIn(phrase, extracted)
            self.assertNotIn("建议立即收割", extracted)
            self.assertNotIn("请立即收割", extracted)
            # Helpers used by the redesigned conclusion page.
            self.assertEqual(len(_items_from_value(ai["actions_now"])), 2)
            self.assertGreaterEqual(len(_items_from_value(ai["evidence_gaps"])), 2)
            if "农事" in extracted or "长势" in extracted:
                self.assertIn("农事风险", extracted)
            for banned_rs in ("无人机", "多源卫星"):
                self.assertNotIn(banned_rs, str(ai.get("actions_next_season") or ""))


if __name__ == "__main__":
    unittest.main()
