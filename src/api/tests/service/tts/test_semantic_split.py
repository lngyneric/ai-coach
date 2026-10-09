# ruff: noqa: E402
"""Unit tests for JEV TTS semantic split point selection (tts/semantic_split.py).

HTTP layer mocked; also verifies candidate sampling and the no-confidence /
no-key fallbacks.
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


def test_picks_best_confident_point(monkeypatch, jev_key):
    import requests

    from flaskr.service.tts import semantic_split

    clause = "第一步先圈定目标客户群体，第二步再设计差异化的价值主张，第三步据此打磨话术。"
    points = [clause.index("第二步"), clause.index("第三步")]
    # p0 (first candidate) low, p1 (second) high -> expect points[1]
    answers = {
        "model": "jev-1.13.0",
        "answers": {
            "p0": {"type": "noul", "noul": 0.2},
            "p1": {"type": "noul", "noul": 0.9},
        },
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResp(200, answers))
    got = semantic_split.choose_split_point_via_jev(clause, points)
    assert got == points[1]


def test_no_confident_point_returns_none(monkeypatch, jev_key):
    import requests

    from flaskr.service.tts import semantic_split

    answers = {
        "model": "jev-1.13.0",
        "answers": {"p0": {"type": "noul", "noul": 0.1}, "p1": {"type": "noul", "noul": 0.3}},
    }
    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResp(200, answers))
    assert semantic_split.choose_split_point_via_jev("某段很长的话没有标点的中文", [3, 6]) is None


def test_empty_candidates_returns_none(jev_key):
    from flaskr.service.tts import semantic_split

    assert semantic_split.choose_split_point_via_jev("文本", []) is None


def test_missing_key_returns_none(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    from flaskr.service.tts import semantic_split

    assert semantic_split.choose_split_point_via_jev("文本", [1, 2]) is None


def test_non_200_returns_none(monkeypatch, jev_key):
    import requests

    from flaskr.service.tts import semantic_split

    monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResp(451, text="blocked"))
    assert semantic_split.choose_split_point_via_jev("文本", [1, 2]) is None


def test_sample_candidates_keeps_endpoints():
    from flaskr.service.tts import semantic_split

    cands = list(range(100))
    sampled = semantic_split._sample_candidates(cands, 10)
    assert len(sampled) == 10
    assert sampled[0] == 0
    assert sampled[-1] == 99
