# ruff: noqa: E402
"""Unit tests for JEV follow-up scoring (followup_scoring.py).

HTTP layer is mocked; the deterministic `derive_difficulty_hint` mapping is
tested directly without any network call.
"""

import pytest


class _FakeResp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload


@pytest.fixture
def jev_key(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")


def _followup_payload(mastery, ask_type, on_topic, quality):
    return {
        "model": "jev-1.13.0",
        "answers": {
            "mastery": {"type": "score", "score": mastery, "confidence": 0.5},
            "ask_type": {"type": "choice", "choice": ask_type, "confidence": 0.78},
            "answer_on_topic": {"type": "noul", "noul": on_topic},
            "answer_quality": {"type": "score", "score": quality},
        },
    }


# ---- derive_difficulty_hint: pure, no network ----

@pytest.mark.parametrize(
    "mastery,ask_type,expected",
    [
        (1.33, "confusion", "easier"),
        (1.0, "clarify", "easier"),
        (3.9, "deepen", "harder"),
        (3.6, "clarify", "harder"),
        (2.75, "deepen", "keep"),
        (2.0, "clarify", "keep"),
        (None, "off_topic", "keep"),
    ],
)
def test_derive_difficulty_hint(mastery, ask_type, expected):
    from flaskr.service.learn.followup_scoring import derive_difficulty_hint

    assert derive_difficulty_hint(mastery, ask_type, 0.9) == expected


def test_confusion_overrides_high_mastery():
    from flaskr.service.learn.followup_scoring import derive_difficulty_hint

    assert derive_difficulty_hint(3.9, "confusion", 0.9) == "easier"


# ---- score_followup: HTTP mocked ----

def test_score_followup_confusion(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import followup_scoring

    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: _FakeResp(200, _followup_payload(1.33, "confusion", 0.97, 2.36)),
    )
    r = followup_scoring.score_followup(
        question="为什么 FSC 反映大小？", answer="细胞越大遮挡前向光越多。", chapter_title="流式"
    )
    assert r["mastery"] == pytest.approx(1.33)
    assert r["ask_type"] == "confusion"
    assert r["answer_on_topic"] == pytest.approx(0.97)
    assert r["difficulty_hint"] == "easier"
    assert r["model"] == "jev-1.13.0"


def test_score_followup_deepen(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import followup_scoring

    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: _FakeResp(200, _followup_payload(2.75, "deepen", 0.94, 2.52)),
    )
    r = followup_scoring.score_followup(question="q", answer="a")
    assert r["ask_type"] == "deepen"
    assert r["difficulty_hint"] == "keep"


def test_score_followup_high_mastery_deepen_harder(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import followup_scoring

    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **k: _FakeResp(200, _followup_payload(3.8, "deepen", 0.95, 4.0)),
    )
    r = followup_scoring.score_followup(question="q", answer="a")
    assert r["difficulty_hint"] == "harder"


def test_score_followup_missing_key_returns_none(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    from flaskr.service.learn import followup_scoring

    assert followup_scoring.score_followup(question="q", answer="a") is None


def test_score_followup_empty_input_returns_none(monkeypatch, jev_key):
    from flaskr.service.learn import followup_scoring

    assert followup_scoring.score_followup(question="  ", answer="  ") is None
