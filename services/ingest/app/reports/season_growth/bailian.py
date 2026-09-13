# -*- coding: utf-8 -*-
"""Alibaba Bailian (DashScope compatible-mode) chat client for season reports."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

DEFAULT_BASE_URL = (
    "https://llm-7cudikcfvgf9l1hy.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)
DEFAULT_MODEL = "qwen3.7-flash"

SYSTEM_PROMPT = """你是资深农学与遥感分析助手，撰写面向农户与农技人员的中文「生育期长势分析报告」解读。
只能基于用户提供的 JSON 事实撰写；不得编造数值、日期、景数、等级、百分比或田间事实。

硬性规则：
1. 程序拥有全部数字（NDVI/NDMI/EVI/MNDWI/VV/VH、日期、景数、等级、收获）。你只解读，不重算、不发明。
2. 不得编造天气、播种、品种、土壤、产量、墒情、成熟度；缺失则写「未提供，需进一步确认」。
3. 语气必须谨慎：使用 提示/可能/疑似/需进一步确认。禁止虚假因果。
4. 不能仅凭 NDVI 推断产量损失或写「生物量积累达标」「生物量达标」；应写冠层绿度。
5. 九月 NDVI 下降与干旱等级共现：只能写「成熟脱水与天气偏干可能同时存在」，缺少土壤/气象资料时不能定量。
6. 收获：若程序置信度为低，必须写「疑似进入成熟后期或收获准备阶段」并强调需田间确认；禁止「立即收割」。
7. 同比：只能写「峰值日期提前/推后 N 天」；禁止「生育进程提前一个月」或推断播种/积温。
8. 严禁散文出现英文字段名/JSON 键（如 flood_scene_count、status=ok、detected、low）。
9. 物候阶段为估计，不得写成实测播种日期。
10. 输出必须是合法 JSON，键恰好为：
    core_conclusion, synthesis, timeline_bullets, monthly_notes,
    conclusions, factors_strong, factors_mid, factors_weak,
    actions_now, actions_week, actions_next_season, evidence_gaps。
11. 字段分工（禁止互相复读同一段）：
    - core_conclusion：≤80字，一句核心判断（谨慎，引用程序事实）。
    - synthesis：150–250字，综合回答以下6问：①当前冠层绿度如何？②是否提示干旱？③是否提示洪涝？④是否疑似成熟后期/收获准备？⑤与上年相比峰值日期差多少（只谈峰值日期）？⑥还缺哪些证据才能下更强结论？
    - timeline_bullets：3–5条按月短句（6–9月），只解读程序时间线。
    - monthly_notes：字符串数组，与 facts.timeline 月份对齐，写入表格「AI判读」列，每条≤40字。
    - conclusions：3–4条综合结论（可呼应 program_conclusions，勿复述数字清单）。
    - factors_strong / factors_mid / factors_weak：可能影响因素，按证据强度分三档（字符串数组）。证据不足档写「资料不足，不能认定…」。
    - actions_now / actions_week / actions_next_season：现在 / 未来7天 / 下一季建议。收获相关必须用「疑似…需田间确认」，禁止立即收割。
    - evidence_gaps：需要补充的证据（字符串数组）。
12. 不要输出 one_liner / summary / evidence_bullets / 结论复述 等重复块。"""

_AI_LIST_KEYS = (
    "timeline_bullets",
    "monthly_notes",
    "conclusions",
    "factors_strong",
    "factors_mid",
    "factors_weak",
    "evidence_gaps",
)
_AI_STR_KEYS = (
    "core_conclusion",
    "synthesis",
    "actions_now",
    "actions_week",
    "actions_next_season",
)

# Legacy keys still accepted as fallbacks when the model returns the old schema.
_LEGACY_MAP = {
    "one_liner": "core_conclusion",
    "summary": "synthesis",
    "interpretation": "synthesis",
    "moisture_analysis": "synthesis",
    "recommendations": "actions_now",
    "follow_up": "evidence_gaps",
    "causes_ranked": "factors_mid",
    "timeline_notes": "timeline_bullets",
}


def bailian_configured() -> bool:
    return bool((os.environ.get("BAILIAN_API_KEY") or "").strip())


def bailian_settings() -> dict[str, str]:
    """Read Bailian config from process env only (secrets never hard-coded)."""
    return {
        "api_key": (os.environ.get("BAILIAN_API_KEY") or "").strip(),
        "base_url": (
            os.environ.get("BAILIAN_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/"),
        "model": (os.environ.get("BAILIAN_MODEL") or DEFAULT_MODEL).strip()
        or DEFAULT_MODEL,
    }


def _extract_json(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, dict):
        # month -> note
        out: list[str] = []
        for k in sorted(value.keys(), key=lambda x: str(x)):
            v = value.get(k)
            if v is None:
                continue
            s = str(v).strip()
            if s:
                out.append(s if str(k) in s else f"{k} {s}")
        return out
    return []


def _as_str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        joined = "\n".join(str(x) for x in value if str(x).strip())
        return joined.strip() or None
    s = str(value).strip()
    return s or None


def _clip(text: str | None, max_chars: int) -> str | None:
    if not text:
        return text
    t = text.strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1] + "…"


def _empty_ai_fields() -> dict[str, Any]:
    return {
        "core_conclusion": None,
        "synthesis": None,
        "timeline_bullets": [],
        "monthly_notes": [],
        "conclusions": [],
        "factors_strong": [],
        "factors_mid": [],
        "factors_weak": [],
        "actions_now": None,
        "actions_week": None,
        "actions_next_season": None,
        "evidence_gaps": [],
        # kept so older callers/tests do not KeyError
        "one_liner": None,
        "summary": None,
        "evidence_bullets": [],
        "moisture_analysis": None,
        "interpretation": None,
        "causes_ranked": [],
        "recommendations": None,
        "follow_up": [],
        "timeline_notes": None,
    }


def _merge_legacy(obj: dict[str, Any]) -> dict[str, Any]:
    merged = dict(obj)
    for old, new in _LEGACY_MAP.items():
        if merged.get(new) in (None, "", []):
            if obj.get(old) not in (None, "", []):
                merged[new] = obj.get(old)
    return merged


def _normalize_ai(obj: dict[str, Any] | None) -> dict[str, Any]:
    if not obj:
        out = _empty_ai_fields()
        out["llm_configured"] = False
        out["error"] = "empty_response"
        return out
    obj = _merge_legacy(obj)
    out = _empty_ai_fields()
    for k in _AI_STR_KEYS:
        out[k] = _as_str_or_none(obj.get(k))
    for k in _AI_LIST_KEYS:
        out[k] = _as_str_list(obj.get(k))
    out["core_conclusion"] = _clip(out.get("core_conclusion"), 80)
    # keep a little headroom over 250 for punctuation
    if out.get("synthesis") and len(out["synthesis"]) > 280:
        out["synthesis"] = _clip(out["synthesis"], 250)
    # legacy mirrors for any leftover callers
    out["one_liner"] = out.get("core_conclusion")
    out["summary"] = out.get("synthesis")
    out["interpretation"] = out.get("synthesis")
    out["recommendations"] = out.get("actions_now")
    out["follow_up"] = list(out.get("evidence_gaps") or [])
    out["causes_ranked"] = list(out.get("factors_mid") or [])
    out["timeline_notes"] = (
        "\n".join(out.get("timeline_bullets") or []) or None
    )
    out["llm_configured"] = True
    out["error"] = None
    return out


def missing_llm_sections() -> dict[str, Any]:
    note = "大模型未配置（缺少 BAILIAN_API_KEY），本报告仅含程序计算的遥感事实与图表。"
    out = _empty_ai_fields()
    out.update(
        {
            "core_conclusion": "遥感事实已生成（AI 解读未启用）",
            "synthesis": note,
            "actions_now": "请配置 BAILIAN_API_KEY 后重新生成以获得 AI 解读与建议。",
            "one_liner": "遥感事实已生成（AI 解读未启用）",
            "summary": note,
            "interpretation": note,
            "recommendations": "请配置 BAILIAN_API_KEY 后重新生成以获得 AI 解读与建议。",
            "llm_configured": False,
            "error": "missing_api_key",
        }
    )
    return out


def generate_season_narrative(
    facts: dict[str, Any],
    material_text: str = "",
    *,
    timeout: float = 120.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Call Bailian chat/completions; return normalized AI sections.

    Soft-fails to missing_llm_sections / error payload — never invents numbers.
    """
    cfg = bailian_settings()
    if not cfg["api_key"]:
        return missing_llm_sections()

    user_payload = {
        "facts": facts,
        "materials_excerpt": (material_text or "")[:6000],
    }
    body = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "请根据以下 JSON 事实撰写生育期长势解读，仅输出 JSON：\n"
                    + json.dumps(user_payload, ensure_ascii=False)
                ),
            },
        ],
        "temperature": 0.2,
    }
    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    own_client = client is None
    http = client or httpx.Client(timeout=timeout)
    try:
        resp = http.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        content = (
            ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
            or ""
        )
        parsed = _extract_json(content)
        out = _normalize_ai(parsed)
        if not out.get("core_conclusion") and not out.get("synthesis"):
            out["error"] = out.get("error") or "unparseable_response"
            out["raw_excerpt"] = str(content)[:500]
        return out
    except Exception as exc:
        detail = str(exc)[:500]
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            detail = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        elif isinstance(exc, httpx.TimeoutException):
            detail = f"timeout after {timeout}s: {type(exc).__name__}"
        note = f"大模型调用失败：{type(exc).__name__}。报告仍包含程序计算事实。"
        out = _empty_ai_fields()
        out.update(
            {
                "core_conclusion": "遥感事实已生成（AI 调用失败）",
                "synthesis": note,
                "one_liner": "遥感事实已生成（AI 调用失败）",
                "summary": note,
                "interpretation": note,
                "recommendations": None,
                "llm_configured": True,
                "error": detail,
            }
        )
        return out
    finally:
        if own_client:
            http.close()
