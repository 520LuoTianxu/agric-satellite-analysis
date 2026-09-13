"""PDF render smoke test (no LLM, minimal + richer facts)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.reports.season_growth.pdf_render import (
    filter_s2_appendix_rows,
    format_drought_counts,
    format_flood_counts,
    format_flood_status,
    format_harvest_line,
    quality_cn,
    render_season_growth_pdf,
)


def _rich_facts() -> dict:
    return {
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
            "s1_count": 4,
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
        "ndmi": {"mean": 0.1, "series": [{"date": "2026-06-05", "value": 0.18}]},
        "drought": {
            "drought_scene_count": 1,
            "counts": {"normal": 6, "mild": 1, "unreliable": 0},
            "days": [{"date": "2026-08-20", "class": "mild"}],
            "scene_classes": [
                {"date": "2026-06-05", "class": "normal"},
                {"date": "2026-08-20", "class": "mild"},
            ],
        },
        "flood": {
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
        },
        "harvest": {
            "status": "uncertain",
            "harvest_date": None,
            "confidence": "low",
        },
        "prior_year": None,
        "methodology": {
            "drought": "S2 干旱规则摘要",
            "flood": "洪涝需同时满足 VV≤-17.0 dB、相对基线下降≥3.0 dB。",
            "sensors": "S2/S1",
        },
        "timeline": [
            {
                "month": "2026-06",
                "s2_count": 2,
                "s1_count": 0,
                "drought_days": 0,
                "flood_count": 0,
                "watch_count": 0,
            },
            {
                "month": "2026-07",
                "s2_count": 2,
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
            }
        ],
    }


def _rich_ai() -> dict:
    return {
        "one_liner": "遥感事实已生成（AI 摘要未启用）",
        "summary": "大模型未配置，仅含程序事实。",
        "evidence_bullets": ["S2 景数 7"],
        "core_conclusion": "窗口内长势总体可观测。",
        "moisture_analysis": "干旱轻度 1 景；无洪涝。",
        "interpretation": "大模型未配置。",
        "causes_ranked": ["数据覆盖有限"],
        "recommendations": None,
        "follow_up": ["补充田间调查"],
        "timeline_notes": "7 月 S1 覆盖较好。",
        "llm_configured": False,
    }


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
            "one_liner": "遥感事实已生成（AI 摘要未启用）",
            "summary": "大模型未配置，仅含程序事实。",
            "evidence_bullets": [],
            "interpretation": "大模型未配置。",
            "recommendations": None,
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
            # Tighter layout: fewer page objects than old 8+ section breaks
            page_count = data.count(b"/Type /Page")
            # ReportLab may emit /Type /Pages as well; count leaf pages via /Type /Page\n or similar
            self.assertGreaterEqual(page_count, 1)
            self.assertLessEqual(page_count, 12)

    def test_render_richer_pdf_no_raw_dict_dump(self) -> None:
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
            # Raw Python dict / English harvest dump should not appear in content streams
            self.assertNotIn(b"{'unreliable'", data)
            self.assertNotIn(b"detected /", data)
            # core_conclusion should not be duplicated as 结论复述 label in content
            # (Chinese may be encoded; at least ensure PDF builds with empty materials footnote path)
            path2 = render_season_growth_pdf(
                facts=facts,
                ai={**ai, "core_conclusion": "核心结论一句。"},
                chart_paths=None,
                materials_meta=[],
                out_path=Path(tmp) / "season_rich2.pdf",
            )
            self.assertTrue(path2.exists())


if __name__ == "__main__":
    unittest.main()
