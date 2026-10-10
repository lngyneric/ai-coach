#!/usr/bin/env python3
"""segmentation-quality.py — 分段(Segmentation)质量的 JEV 提前判断

在「抽取/分段」阶段之后、编排/生成之前，用 JEV（TypeSafe System One，
typed-judgment 模型：noul / choice / score）对分段结果**提前打分**，
把可疑段落（粒度/边界/保留标记）标出来，供人工确认或触发 re-segmentation。

jev 是判定模型、不生成文本，因此这里把它当作**分段质量分类器**：
一次请求批量提交多个问项（每段 3 问 + 1 个整体覆盖度问项）。

问项（对齐 references/data-contracts.md#segment-schema）：
  coverage   score 0..4  分段整体是否完整覆盖源材料核心要点（无遗漏/无冗余）
  gran_<i>   score 0..4  第 i 段是否只承载单一可教点、粒度是否合适
  bnd_<i>    score 0..4  第 i 段边界是否落在自然语义边界（不切断概念/步骤）
  pres_<i>   noul        第 i 段 preserve_block 标记是否正确
                         （含需逐字保留内容则为 true，否则 false 亦正确）

输出 JSON：
  {"status": "ok|skipped", "model": ..., "coverage": {...},
   "segments": [{"segment_id", "granularity", "boundary", "preserve_ok", "flag"}...],
   "summary": {"n", "mean", "min", "flagged"},
   "uncertainty": "low|medium|high", "rerun_hints": [...]}

fail-open：无 TYPESAFE_API_KEY / 请求失败 → 输出 {"status":"skipped"}，退出码 0，
绝不阻塞分段流程。

用法：
  python3 scripts/segmentation-quality.py --segments seg.json [--source raw.md] \
      [--out seg-quality.json] [--threshold 2.0]

  # 环境：TYPESAFE_API_KEY（出海网络；dev 见 docker compose 代理）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_TYPESAFE_URL = "https://api.typesafe.ai/v1/systemone"
_TYPESAFE_MODEL = "jev-latest"
_JEV_TIMEOUT = 30.0
_JEV_MAX_RETRIES = 3
_JEV_BACKOFF = (0.5, 1.0, 2.0)
_JEV_MAX_SEGMENTS = 40          # 单次请求最多评估的段数（防止 token 爆炸）
_MAX_SPAN_CHARS = 1200          # 单段 source_span/core_point 截断长度
_MAX_SOURCE_CHARS = 4000        # state（源材料）截断长度
_DEFAULT_THRESHOLD = 2.0        # score < 该值 → 标记该段可疑
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"   # skill 根 .env（TYPESAFE_API_KEY 回退）

# ── score 量表（0..4），顺序即分值 ───────────────────────────────
_COVERAGE_LEVELS = [
    "0 严重遗漏源材料核心要点",
    "1 遗漏若干核心要点",
    "2 基本覆盖核心要点，存在少量遗漏或冗余",
    "3 完整覆盖核心要点，冗余很少",
    "4 完整覆盖且无冗余，分段结构与源材料一致",
]
_GRANULARITY_LEVELS = [
    "0 段内混杂多个不相干可教点，或内容空洞无法教学",
    "1 段内混有 2 个以上可教点，粒度明显过粗",
    "2 段内基本单一可教点，但有少量旁枝内容",
    "3 段内单一可教点，粒度合适",
    "4 段内单一、聚焦且自洽的可教点，粒度理想",
]
_BOUNDARY_LEVELS = [
    "0 边界切断了句子/概念/步骤，前后都不可独立理解",
    "1 边界多处不自然，需大量改写才能教学",
    "2 边界基本可用，个别处不够自然",
    "3 边界落在自然语义边界，前后可独立理解",
    "4 边界完全自然，段与段衔接顺畅无冗余",
]


def _truncate(text: Any, limit: int) -> str:
    s = "" if text is None else str(text)
    return s if len(s) <= limit else s[:limit] + "…"


def _api_key() -> str:
    """TYPESAFE_API_KEY from the process environment, else the skill's .env."""
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key
    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            if name.strip() == "TYPESAFE_API_KEY":
                return value.strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def _jev_available() -> bool:
    return bool(_api_key())


def _extract_score(answer: Any) -> Optional[float]:
    if not isinstance(answer, dict):
        return None
    value = answer.get("score")
    if value is None:
        value = answer.get("value")
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _extract_noul(answer: Any) -> Optional[float]:
    if not isinstance(answer, dict):
        return None
    value = answer.get("noul")
    if value is None:
        value = answer.get("value")
    if value is None:
        value = answer.get("probability")
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _load_segments(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return [s for s in data if isinstance(s, dict)]
    if isinstance(data, dict):
        for key in ("segments", "items", "data"):
            if isinstance(data.get(key), list):
                return [s for s in data[key] if isinstance(s, dict)]
    raise ValueError(
        "segments JSON must be a list, or an object with a 'segments'/'items'/'data' array"
    )


def _segment_brief(seg: dict, idx: int, total: int) -> dict:
    prev_core = ""
    return {
        "index": idx + 1,
        "of": total,
        "segment_type": seg.get("segment_type", ""),
        "core_point": _truncate(seg.get("core_point", ""), _MAX_SPAN_CHARS),
        "preserve_block": bool(seg.get("preserve_block", False)),
        "source_span": _truncate(seg.get("source_span", ""), _MAX_SPAN_CHARS),
        "transfer_signals": seg.get("transfer_signals", {}),
        "_prev_core": prev_core,
    }


def _build_questions(segments: List[dict], source: str) -> Dict[str, Any]:
    questions: Dict[str, Any] = {}
    # 整体覆盖度
    questions["coverage"] = {
        "type": "score",
        "instructions": {
            "question": (
                "下面 state 是课程的源材料（raw material）。questions 之外另附"
                "该课程的分段结果（每段的 core_point）。分段是否完整覆盖了源材料的"
                "核心要点？有无关键要点遗漏、或段间大量重复冗余？"
            ),
            "segments_core_points": [
                _truncate(s.get("core_point", ""), 200) for s in segments
            ],
        },
        "criteria": list(_COVERAGE_LEVELS),
    }
    for idx, seg in enumerate(segments):
        brief = _segment_brief(seg, idx, len(segments))
        questions[f"gran_{idx}"] = {
            "type": "score",
            "instructions": {
                "question": (
                    "这是课程分段中的一段。它是否只承载【一个】可教点、粒度是否合适"
                    "（既不过粗——把多个点塞进一段，也不过细——把一句话拆成无意义碎片）？"
                ),
                "segment": brief,
            },
            "criteria": list(_GRANULARITY_LEVELS),
        }
        questions[f"bnd_{idx}"] = {
            "type": "score",
            "instructions": {
                "question": (
                    "该段的边界是否落在自然语义边界上？是否把一个概念/步骤/例子从中间"
                    "切断，导致本段或相邻段无法独立理解？"
                ),
                "segment": brief,
                "prev_core_point": _truncate(
                    segments[idx - 1].get("core_point", ""), 200
                ) if idx > 0 else "",
                "next_core_point": _truncate(
                    segments[idx + 1].get("core_point", ""), 200
                ) if idx + 1 < len(segments) else "",
            },
            "criteria": list(_BOUNDARY_LEVELS),
        }
        questions[f"pres_{idx}"] = {
            "type": "noul",
            "instructions": {
                "question": (
                    "该段的 preserve_block 标记是否正确？规则：若该段含必须逐字保留的"
                    "内容（代码/图片/表格/必须原样引用的文字），preserve_block 应为 true；"
                    "若不含此类内容，preserve_block 为 false 也算正确。标记正确即为 true。"
                ),
                "segment": brief,
            },
            "criteria": {
                "true": "preserve_block 标记与内容相符（该保留则 true，否则 false 亦正确）",
                "false": "preserve_block 标记与内容不符（该保留却 false，或反之）",
            },
        }
    return questions


def _call_systemone(state: str, questions: Dict[str, Any]) -> Optional[dict]:
    import requests

    if not _jev_available():
        return None
    payload = {"state": state, "model": _TYPESAFE_MODEL, "questions": questions}
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    for attempt in range(_JEV_MAX_RETRIES):
        try:
            resp = requests.post(
                _TYPESAFE_URL, json=payload, headers=headers, timeout=_JEV_TIMEOUT
            )
            if resp.status_code in (429, 529):
                raise requests.RequestException(f"transient status {resp.status_code}")
            if resp.status_code != 200:
                sys.stderr.write(
                    f"jev returned status {resp.status_code}: {resp.text[:300]}\n"
                )
                return None
            return resp.json() or {}
        except requests.RequestException as exc:
            wait = _JEV_BACKOFF[min(attempt, len(_JEV_BACKOFF) - 1)]
            sys.stderr.write(
                f"jev request failed (attempt {attempt + 1}/{_JEV_MAX_RETRIES}): "
                f"{exc}; retrying in {wait:.1f}s\n"
            )
            import time

            time.sleep(wait)
    return None


def _grade(min_score: Optional[float], threshold: float) -> str:
    if min_score is None:
        return "unknown"
    if min_score >= threshold + 1.0:
        return "good"
    if min_score >= threshold:
        return "fair"
    return "poor"


def evaluate(segments: List[dict], source: str, threshold: float) -> dict:
    if not _jev_available():
        return {
            "status": "skipped",
            "reason": "TYPESAFE_API_KEY not set",
        }

    total = len(segments)
    if total > _JEV_MAX_SEGMENTS:
        segments = segments[:_JEV_MAX_SEGMENTS]
    if not segments:
        return {"status": "skipped", "reason": "no segments"}

    questions = _build_questions(segments, source)
    data = _call_systemone(_truncate(source, _MAX_SOURCE_CHARS), questions)
    if data is None:
        return {"status": "skipped", "reason": "jev call failed"}

    answers = data.get("answers") or {}
    coverage = _extract_score(answers.get("coverage"))

    seg_results: List[dict] = []
    flagged = 0
    score_values: List[float] = []
    for idx, seg in enumerate(segments):
        gran = _extract_score(answers.get(f"gran_{idx}"))
        bnd = _extract_score(answers.get(f"bnd_{idx}"))
        pres = _extract_noul(answers.get(f"pres_{idx}"))
        # 段内最弱的 score 决定是否可疑
        candidates = [v for v in (gran, bnd) if v is not None]
        weakest = min(candidates) if candidates else None
        if weakest is not None:
            score_values.append(weakest)
        flag = (
            (weakest is not None and weakest < threshold)
            or (pres is not None and pres < 0.5)
        )
        if flag:
            flagged += 1
        seg_results.append(
            {
                "segment_id": seg.get("segment_id", f"seg-{idx}"),
                "granularity": gran,
                "boundary": bnd,
                "preserve_ok": pres,
                "weakest": weakest,
                "flag": flag,
            }
        )

    summary = {
        "n": len(seg_results),
        "mean": round(sum(score_values) / len(score_values), 2) if score_values else None,
        "min": min(score_values) if score_values else None,
        "flagged": flagged,
    }

    # uncertainty / rerun_hints（对齐 fallback 契约）
    uncertainty = "low"
    rerun_hints: List[str] = []
    if flagged:
        uncertainty = "medium" if flagged < max(1, len(seg_results) // 2) else "high"
        rerun_hints.append(
            f"{flagged}/{len(seg_results)} 段质量可疑，建议复核 core_point 粒度与边界"
        )
    if coverage is not None and coverage < threshold:
        uncertainty = "high"
        rerun_hints.append("整体覆盖度偏低，建议补充源材料要点或重新分段")

    return {
        "status": "ok",
        "model": str(data.get("model") or _TYPESAFE_MODEL),
        "threshold": threshold,
        "coverage": {"score": coverage, "grade": _grade(coverage, threshold)},
        "segments": seg_results,
        "summary": summary,
        "uncertainty": uncertainty,
        "rerun_hints": rerun_hints,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="JEV 分段质量提前判断（fail-open）")
    parser.add_argument("--segments", required=True, help="分段结果 JSON（segment-schema 列表）")
    parser.add_argument("--source", default="", help="源材料文本文件（用于覆盖度判断，可选）")
    parser.add_argument("--out", default="", help="输出 JSON 路径（可选；默认打印到 stdout）")
    parser.add_argument("--threshold", type=float, default=_DEFAULT_THRESHOLD,
                        help=f"可疑判定阈值（score< 该值即 flag，默认 {_DEFAULT_THRESHOLD}）")
    args = parser.parse_args(argv)

    try:
        segments = _load_segments(args.segments)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"cannot read segments: {exc}\n")
        return 2

    source = ""
    if args.source:
        try:
            with open(args.source, encoding="utf-8") as f:
                source = f.read()
        except OSError as exc:
            sys.stderr.write(f"cannot read source (ignored): {exc}\n")

    result = evaluate(segments, source, args.threshold)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
