# ruff: noqa: E402
"""Unit tests for JEV-based quiz judgment (quiz_judging.py).

These tests mock the HTTP layer (`requests.post`) so no external TypeSafe call
is made. They cover: question validity accept/reject, open-answer grading, the
no-key degradation path, and non-200 failure handling.
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


def _validity_payload(validity, unique, difficulty=1.0, reliability=3.9):
    return {
        "model": "jev-1.13.0",
        "answers": {
            "validity": {"type": "score", "score": validity, "confidence": 0.6},
            "unique_answer": {"type": "noul", "noul": unique},
            "difficulty": {"type": "score", "score": difficulty},
            "reliability": {"type": "score", "score": reliability},
        },
    }


def test_valid_question_accepted(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import quiz_judging

    monkeypatch.setattr(
        requests, "post", lambda *a, **k: _FakeResp(200, _validity_payload(3.47, 0.97))
    )
    r = quiz_judging.judge_question_validity(
        stem="反映细胞大小的散射光信号是？",
        options=["FSC", "SSC", "荧光", "阻抗"],
        correct_answer="FSC",
        paragraph="前向散射光反映细胞大小。",
        question_type="single_choice",
    )
    assert r is not None
    assert r["accepted"] is True
    assert r["validity"] == pytest.approx(3.47)
    assert r["unique_answer"] == pytest.approx(0.97)
    assert r["model"] == "jev-1.13.0"


def test_low_validity_question_rejected(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import quiz_judging

    monkeypatch.setattr(
        requests, "post", lambda *a, **k: _FakeResp(200, _validity_payload(0.25, 0.44))
    )
    r = quiz_judging.judge_question_validity(
        stem="下列说法哪个对？",
        options=["都对", "都不对"],
        correct_answer="都对",
        paragraph="p",
        question_type="single_choice",
    )
    assert r is not None
    assert r["accepted"] is False


def test_validity_below_threshold_boundary(monkeypatch, jev_key):
    """validity exactly at the 2.5 threshold is accepted (>=)."""
    import requests

    from flaskr.service.learn import quiz_judging

    monkeypatch.setattr(
        requests, "post", lambda *a, **k: _FakeResp(200, _validity_payload(2.5, 0.9))
    )
    r = quiz_judging.judge_question_validity(
        stem="q?", options=["a", "b"], correct_answer="a"
    )
    assert r["accepted"] is True


def test_non_unique_answer_rejected(monkeypatch, jev_key):
    """High validity but non-unique answer must be rejected."""
    import requests

    from flaskr.service.learn import quiz_judging

    monkeypatch.setattr(
        requests, "post", lambda *a, **k: _FakeResp(200, _validity_payload(3.9, 0.2))
    )
    r = quiz_judging.judge_question_validity(
        stem="q?", options=["a", "b"], correct_answer="a"
    )
    assert r["accepted"] is False


def test_empty_stem_returns_none_no_call(monkeypatch, jev_key):
    from flaskr.service.learn import quiz_judging

    called = {"n": 0}

    def _should_not_call(*a, **k):
        called["n"] += 1
        return _FakeResp(200, {})

    import requests

    monkeypatch.setattr(requests, "post", _should_not_call)
    assert (
        quiz_judging.judge_question_validity(stem="   ", options=[], correct_answer="a")
        is None
    )
    assert called["n"] == 0


def test_non_200_returns_none(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import quiz_judging

    monkeypatch.setattr(
        requests, "post", lambda *a, **k: _FakeResp(451, text="region blocked")
    )
    assert (
        quiz_judging.judge_question_validity(stem="q?", options=[], correct_answer="a")
        is None
    )


def test_missing_key_returns_none(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    from flaskr.service.learn import quiz_judging

    assert (
        quiz_judging.judge_question_validity(stem="q?", options=[], correct_answer="a")
        is None
    )


def test_open_answer_correct(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import quiz_judging

    payload = {
        "model": "jev-1.13.0",
        "answers": {
            "correct": {"type": "noul", "noul": 0.98},
            "partial_score": {"type": "score", "score": 3.89},
            "misconception": {"type": "choice", "choice": "correct"},
        },
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResp(200, payload))
    r = quiz_judging.judge_open_answer(
        question="用什么信号反映细胞大小？",
        reference_answer="前向散射光(FSC)",
        learner_answer="用前向散射光判断",
        paragraph="前向散射光反映大小。",
    )
    assert r["is_correct"] == 1
    assert r["partial_score"] == pytest.approx(3.89)
    assert r["misconception"] == "correct"


def test_open_answer_wrong(monkeypatch, jev_key):
    import requests

    from flaskr.service.learn import quiz_judging

    payload = {
        "model": "jev-1.13.0",
        "answers": {
            "correct": {"type": "noul", "noul": 0.02},
            "partial_score": {"type": "score", "score": 0.09},
            "misconception": {"type": "choice", "choice": "misconception"},
        },
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResp(200, payload))
    r = quiz_judging.judge_open_answer(
        question="q", reference_answer="FSC", learner_answer="荧光越大细胞越大"
    )
    assert r["is_correct"] == 0
    assert r["misconception"] == "misconception"
