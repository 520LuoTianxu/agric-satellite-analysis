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

SYSTEM_PROMPT = """你是资深农学与遥感分析助手，撰写面向农户与农技人员的中文「生育期长势分析报告」正文。
只能基于用户提供的 JSON 事实与材料文本撰写；不得编造数值、日期、景数、等级或百分比。

硬性规则：
1. 数值只能引用 facts 中已有的数字；缺失则写「数据不足」或「未提供」，不要猜测。
2. 正文必须是正常农学报告文风：完整中文句子，不要像字段说明或日志。
3. 严禁在散文中出现英文字段名 / JSON 键 / 程序变量，例如 flood_scene_count、drought_class、status=ok、detected、low 等。
   状态请用中文表述：如「洪涝监测正常」「已检测到收获信号（低置信度）」「重度干旱」等。
4. 不得在没有材料证据时发明灌溉、施肥、土壤质地或田间管理细节；可能原因必须能从 facts 直接支撑。
5. 输出必须是合法 JSON，键为：
   one_liner, summary, evidence_bullets, core_conclusion,
   moisture_analysis, interpretation, causes_ranked,
   recommendations, follow_up, timeline_notes。
6. 字段分工（避免互相复读同一段话）：
   - one_liner：一句话总括（≤40字），点出长势主结论。
   - summary：2–4句背景与关键事实摘要，不要整段复制 one_liner / core_conclusion。
   - evidence_bullets：字符串数组，每条引用具体事实（中文表述）。
   - core_conclusion：核心结论（1–3句），侧重判断与风险，勿与 summary 逐句重复。
   - moisture_analysis：干旱/洪涝水分证据解读。
   - interpretation：综合长势分析（物候、曲线形态、同比等），不要再贴一遍 core_conclusion。
   - causes_ranked：可能原因排序（字符串数组，仅基于事实）。
   - recommendations：可执行管理建议（数组或分段文字）。
   - follow_up：建议补充取证（字符串数组）。
   - timeline_notes：对程序时间线的补充说明（可空字符串）。
7. 程序已给出 counts / appendix / timeline 等事实；你只做分析，不重算、不发明数字。"""

_AI_LIST_KEYS = ("evidence_bullets", "causes_ranked", "follow_up")
_AI_STR_KEYS = (
    "one_liner",
    "summary",
    "core_conclusion",
    "moisture_analysis",
    "interpretation",
    "recommendations",
    "timeline_notes",
)


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
    return []


def _as_str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        joined = "\n".join(str(x) for x in value if str(x).strip())
        return joined.strip() or None
    s = str(value).strip()
    return s or None


def _empty_ai_fields() -> dict[str, Any]:
    return {
        "one_liner": None,
        "summary": None,
        "evidence_bullets": [],
        "core_conclusion": None,
        "moisture_analysis": None,
        "interpretation": None,
        "causes_ranked": [],
        "recommendations": None,
        "follow_up": [],
        "timeline_notes": None,
    }


def _normalize_ai(obj: dict[str, Any] | None) -> dict[str, Any]:
    if not obj:
        out = _empty_ai_fields()
        out["llm_configured"] = False
        out["error"] = "empty_response"
        return out
    out = _empty_ai_fields()
    for k in _AI_STR_KEYS:
        out[k] = _as_str_or_none(obj.get(k))
    for k in _AI_LIST_KEYS:
        out[k] = _as_str_list(obj.get(k))
    out["llm_configured"] = True
    out["error"] = None
    return out


def missing_llm_sections() -> dict[str, Any]:
    note = "大模型未配置（缺少 BAILIAN_API_KEY），本报告仅含程序计算的遥感事实与图表。"
    out = _empty_ai_fields()
    out.update(
        {
            "one_liner": "遥感事实已生成（AI 摘要未启用）",
            "summary": note,
            "core_conclusion": note,
            "moisture_analysis": note,
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
        if not out.get("summary") and not out.get("one_liner"):
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
                "one_liner": "遥感事实已生成（AI 调用失败）",
                "summary": note,
                "core_conclusion": note,
                "moisture_analysis": note,
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
