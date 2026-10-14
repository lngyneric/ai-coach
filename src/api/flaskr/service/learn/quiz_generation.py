"""
In-lesson flashcard quiz generation.

Given a course content paragraph, a text LLM generates a single question
(single-choice / multi-choice / fill-in / short-answer) and we render it into a
MarkdownFlow interaction line that the existing frontend renderer already
understands (``?[%{{var}} ...]``).

The emitted markdown is self-validated with ``markdown_flow.InteractionParser``
before being returned, so a malformed question is discarded rather than shown.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from flask import Flask

from flaskr.api.llm import chat_llm
from flaskr.service.metering import UsageContext
from flaskr.service.metering.consts import BILL_USAGE_SCENE_PROD


logger = logging.getLogger(__name__)

GENERATION_NAME = "quiz_question_generate"

# Question types (kept in sync with the markdown rendered by build_quiz_mdflow).
QT_SINGLE = "single_choice"
QT_MULTI = "multi_choice"
QT_FILL = "fill_blank"
QT_SHORT = "short_answer"
_ALL_TYPES = (QT_SINGLE, QT_MULTI, QT_FILL, QT_SHORT)

# Ordered 5-level difficulty rubric.
_DIFFICULTY_HINT = "请让题目难度与段落深度匹配，不要超纲。"

_SYSTEM_PROMPT = f"""你是一位课程出题专家。请根据给定的课程段落内容，出**一道**检测学员是否理解的题目。

要求：
- 题目必须能从给定段落中找到依据，不得引入段落之外的知识。
- 单选题：4 个选项，1 个正确，3 个合理干扰项。
- 多选题：4 个选项，2~3 个正确。
- 填空题：答案是段落中的一个关键术语或短语（简短）。
- 问答题：考查对某个原理/过程的解释，答案需 1~3 句话。
- 题干清晰、无歧义，正确答案唯一（多选除外）。{_DIFFICULTY_HINT}

只输出 JSON，不要任何解释或 markdown 代码围栏，格式：
{{"question_type": "single_choice|multi_choice|fill_blank|short_answer",
  "stem": "题干（不含选项文字）",
  "options": ["选项A", "选项B", "选项C", "选项D"],
  "correct_answer": "正确答案（单选填选项文本；多选用 | 分隔；填空/问答填参考答案）"}}
"""


def _strip_code_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_question_json(raw: str) -> dict[str, Any] | None:
    """Parse the LLM output into a normalized question dict, or None."""
    text = _strip_code_fence(raw)
    if not text:
        return None
    # Try direct, then first {...} block.
    candidates = [text]
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        candidates.append(match.group(0))
    data: dict[str, Any] | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                data = parsed
                break
        except (ValueError, TypeError):
            continue
    if not data:
        return None

    qtype = str(data.get("question_type", "")).strip().lower()
    if qtype not in _ALL_TYPES:
        return None
    stem = str(data.get("stem", "")).strip()
    correct = str(data.get("correct_answer", "")).strip()
    if not stem or not correct:
        return None

    options: list[str] = []
    raw_options = data.get("options")
    if isinstance(raw_options, list):
        options = [str(o).strip() for o in raw_options if str(o).strip()]
    if qtype in (QT_SINGLE, QT_MULTI) and len(options) < 2:
        return None

    return {
        "question_type": qtype,
        "stem": stem,
        "options": options,
        "correct_answer": correct,
    }


def _sanitize_for_interaction(text: str) -> str:
    """MarkdownFlow interaction lines must not contain |, ||, ], newlines."""
    cleaned = (text or "").replace("\n", " ").replace("\r", " ").strip()
    cleaned = cleaned.replace("]", "）").replace("|", "／")
    return cleaned


def build_quiz_mdflow(question: dict[str, Any], var_name: str) -> str | None:
    """
    Render a question dict into a MarkdownFlow interaction line.

    Returns None when the question cannot be rendered to a valid interaction.
    """
    if not isinstance(question, dict):
        return None
    qtype = question.get("question_type")
    stem = _sanitize_for_interaction(str(question.get("stem", "")))
    correct = str(question.get("correct_answer", "")).strip()
    options = [
        _sanitize_for_interaction(str(o)) for o in (question.get("options") or [])
    ]
    options = [o for o in options if o]
    var = var_name.strip() or "sys_quiz"
    if not stem:
        return None

    if qtype == QT_MULTI:
        if len(options) < 2:
            return None
        body = "||".join(options)
        return f"?[%{{{{{var}}}}} {body}||...{stem}]"
    if qtype == QT_SINGLE:
        if len(options) < 2:
            return None
        body = "|".join(options)
        return f"?[%{{{{{var}}}}} {body}|...{stem}]"
    if qtype in (QT_FILL, QT_SHORT):
        return f"?[%{{{{{var}}}}}...{stem}]"
    return None


def _validate_mdflow(md: str) -> bool:
    """Ensure the emitted line parses as a MarkdownFlow interaction."""
    try:
        from markdown_flow.parser.interaction import InteractionParser

        parsed = InteractionParser().parse(md)
        if not isinstance(parsed, dict):
            return False
        if parsed.get("error"):
            return False
        return bool(parsed.get("buttons") or parsed.get("type") or parsed.get("variable"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("quiz mdflow validation failed: %r", exc)
        return False


def generate_quiz_question(
    app: Flask,
    *,
    paragraph: str,
    chapter_title: str = "",
    model: str = "",
    var_name: str = "sys_quiz",
) -> tuple[str, dict[str, Any]] | None:
    """
    Generate one quiz question for ``paragraph`` and render it to markdown.

    Returns ``(mdflow, question_dict)`` or ``None`` on any failure. This never
    raises — callers treat ``None`` as "skip the quiz for this block".
    """
    paragraph = (paragraph or "").strip()
    if not paragraph:
        return None
    if not model:
        model = str(app.config.get("QUIZ_GENERATION_MODEL", "") or "").strip()
    if not model:
        model = str(app.config.get("DEFAULT_LLM_MODEL", "") or "").strip()
    if not model:
        logger.warning("quiz generation skipped: no model configured")
        return None

    chapter_line = f"章节：{chapter_title}\n" if chapter_title else ""
    user_prompt = f"{chapter_line}课程段落：\n{paragraph}\n\n请出题。"

    class _NoopSpan:
        def generation(self, **kwargs):
            return self

        def span(self, **kwargs):
            return self

        def event(self, **kwargs):
            return None

        def update(self, **kwargs):
            return None

        def end(self, **kwargs):
            return None

        def score(self, **kwargs):
            return None

    try:
        resp = chat_llm(
            app,
            "system",
            _NoopSpan(),
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            json=True,
            stream=False,
            generation_name=GENERATION_NAME,
            temperature=0.3,
            usage_context=UsageContext(
                user_bid="",
                usage_scene=BILL_USAGE_SCENE_PROD,
                billable=0,
            ),
            usage_scene=BILL_USAGE_SCENE_PROD,
            billable=0,
        )
        collected = "".join(chunk.result for chunk in resp if chunk.result)
    except Exception as exc:  # side channel must never raise
        logger.warning("quiz generation LLM call failed: %r", exc)
        return None

    question = _parse_question_json(collected)
    if not question:
        logger.warning("quiz generation produced unparseable output: %s", collected[:200])
        return None

    md = build_quiz_mdflow(question, var_name)
    if not md or not _validate_mdflow(md):
        logger.warning("quiz generation produced invalid mdflow: %r", md)
        return None
    return md, question
