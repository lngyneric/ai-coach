# JEV Content-Quality Judgment & Scoring

This ExecPlan is a living document and must stay aligned with `PLANS.md`.

## Purpose / Big Picture

Integrate **TypeSafe System One (JEV)** — a typed-judgment model returning
`noul` / `choice` / `score` answers — as the content-quality layer of ai-shifu
lessons. JEV is used at four call sites:

1. **In-lesson quiz generation gate** — validate an LLM-generated question
   (unambiguous stem, unique correct answer, plausible distractors) before it is
   shown; regenerate when invalid.
2. **Open-answer grading** — lenient semantic grading of fill-in / short-answer
   responses instead of brittle exact string matching.
3. **Follow-up (追问) scoring** — score a learner question and the tutor answer,
   derive an `easier / keep / harder` difficulty hint for lesson adaptation.
4. **TTS semantic boundary** — when a long clause must be split, ask JEV which
   candidate break-point is the most natural.

Every JEV call **fails open**: on missing key, timeout, or non-200 it returns
`None` and the caller degrades gracefully (accept the quiz, fall back to string
matching, skip scoring, deterministic split). JEV must never block or break a
learner's session.

Outcome: lessons get a quality gate on generated content and semantic grading,
without introducing a hard dependency on an external service.

## Progress

- [x] 2026-09-28 CST: Feature implemented (uncommitted "shadow code" in the dev
      worktree: 5 new modules + 2 migrations + 6 file edits).
- [x] 2026-10-09 CST: JEV change review (via JEV itself) rated it a **major
      change** (is_major_change 0.94, release_risk 3.44, external dep not ready).
- [x] 2026-10-09 CST: Manually probed all 4 call sites end-to-end against the
      live API (8/8 cases), after discovering the region block (see Surprises).
- [x] 2026-10-09 CST: Committed as independent PR #3 on branch
      `feat/jev-content-quality` (base `dev`), worktree `ai-shifu-jev`.
- [x] 2026-10-09 CST: Added unit tests (28 passing, HTTP mocked, no external
      call) for all 4 call sites + degradation paths.
- [ ] Wire into a planned release: confirm egress network + `TYPESAFE_API_KEY`
      in the target environment before enabling.

## Surprises & Discoveries

- Discovery: **TypeSafe is region-blocked from this network.** The dev api
  container has no proxy env and egresses directly; `api.typesafe.ai` returns
  **HTTP 451 "Typesafe is not available in your region."** Routing through the
  host clash proxy (`http://172.17.0.1:7897`) yields a normal response.
  Evidence: direct call → 451; via proxy → 200/403 (auth), and a 2026-09-28
  follow-up score row exists with `provider_model=jev-1.13.0`.

- Discovery: because JEV degrades silently, the 451 block makes the quality
  gate **fail open invisibly** — quizzes pass unvalidated, open answers fall
  back to substring match. This is easy to misread as "the feature isn't
  working / has no data".

- Discovery: `gh pr create` (GraphQL) reports `Head/Base sha can't be blank /
  No commits between` even when the branches are healthy; the REST
  `gh api -X POST .../pulls` path works. (Generic tooling issue, recorded
  separately.)

## Decision Log

- Decision: keep `QUIZ_ENABLED` default **False**. The quiz/side-effect surface
  ships dark and is enabled per-environment.
  Date/Author: 2026-09-28 / sysmex

- Decision: **fail-open everywhere.** Every JEV helper returns `None` on any
  failure so learners are never blocked. Trade-off: silent quality-gate loss
  (see Surprises) is accepted in exchange for availability.
  Date/Author: 2026-09-28 / sysmex

- Decision: `validity >= 2.5 AND (unique_answer >= 0.5)` is the accept rule for
  a generated question; open answers use `noul(correct) >= 0.5` for
  `is_correct`.
  Date/Author: 2026-09-28 / sysmex

- Decision: score answers are probability-weighted positions on an ordered
  0..4 level scale (the `criteria` list), not raw model output.
  Date/Author: 2026-09-28 / sysmex

- Decision: deliver as an independent PR (base `dev`) rather than folding into
  the dev→main merge, so the review is scoped to JEV only.
  Date/Author: 2026-10-09 / sysmex

## Context and Orientation

New modules (all under `src/api/flaskr/`):

- `service/learn/quiz_judging.py` — `judge_question_validity`, `judge_open_answer`
- `service/learn/quiz_generation.py` — LLM question generation
- `service/learn/quiz_analytics.py` — attempt grading + chapter aggregation
- `service/learn/followup_scoring.py` — `score_followup`, `derive_difficulty_hint`
- `service/tts/semantic_split.py` — `choose_split_point_via_jev`

Edited:
- `common/config.py` — `QUIZ_ENABLED`, `QUIZ_EVERY_N_BLOCKS`,
  `QUIZ_GENERATION_MODEL`, `QUIZ_MAX_VALIDITY_RETRIES`, `QUIZ_GRADE_ASYNC`,
  `TYPESAFE_API_KEY`
- `service/learn/context_v2.py` — quiz emit integration
- `service/learn/handle_input_ask.py` — follow-up scoring hook (async)
- `service/learn/models.py` — 3 quiz tables + `learn_followup_scores`
- `service/tts/pipeline.py` — clause splitting + JEV break-point
- `service/learning_portal/routes.py` — `/api/portal/quiz/analysis`

Migrations: `..._add_learn_followup_scores.py`, `..._add_learn_quiz_tables.py`
(pure additive; no existing table rewritten).

Transport is uniform across modules: `POST https://api.typesafe.ai/v1/systemone`,
`model=jev-latest`, `Authorization: Bearer $TYPESAFE_API_KEY`, 8s timeout, 3
retries with 0.5/1/2s backoff on 429/529.

## Plan of Work

1. (Done) Implement the four call sites + config + tables + migrations.
2. (Done) Manual end-to-end probe of all four call sites against the live API.
3. (Done) Unit tests with the HTTP layer mocked (no external call):
   accept/reject thresholds, open-answer grading, follow-up hint derivation,
   split-point selection, and the no-key / non-200 degradation paths.
4. (Todo) Environment readiness before enable: confirm the deployment can reach
   `api.typesafe.ai` (egress/proxy) and that `TYPESAFE_API_KEY` is set; otherwise
   the gate silently no-ops.
5. (Todo) Enable behind `QUIZ_ENABLED` in a non-production environment first.

## Concrete Steps

- Run unit tests (no network):
  `cd src/api && python -m pytest tests/service/learn/test_quiz_judging.py tests/service/learn/test_followup_scoring.py tests/service/tts/test_semantic_split.py -q`
- Live probe (requires proxy egress):
  `docker exec -e HTTPS_PROXY=http://172.17.0.1:7897 -e HTTP_PROXY=http://172.17.0.1:7897 <api-container> python /app/<probe>.py`
- Enable quizzes: set `QUIZ_ENABLED=true` and ensure `TYPESAFE_API_KEY` set.

## Validation and Acceptance

Observable acceptance:

- With `TYPESAFE_API_KEY` set and reachable: a well-formed generated question is
  `accepted=True`; a malformed one is `accepted=False` and regenerated.
- An open answer semantically matching the reference → `is_correct=1`; a wrong
  answer → `is_correct=0` with a `misconception` label.
- A confused follow-up on a low-mastery learner → `difficulty_hint=easier`; a
  deepening question at high mastery → `harder`.
- With `TYPESAFE_API_KEY` absent or region-blocked (451): all four call sites
  return `None` and the lesson proceeds without error.
- Unit tests: 28 passing, no external call.

## Idempotence and Recovery

- All calls are read-only judgments; re-running is safe.
- Quiz emission is idempotent per (progress_record, outline_item, position) via
  a `%{sys_quiz_N}%` marker check; an existing block is reused.
- Follow-up scoring is idempotent per `answer_block_bid` (one row).
- Migrations are pure additive; `downgrade` drops only the new tables.
- If JEV is unavailable, no data loss and no learner-visible failure — the gate
  is simply skipped.

## Interfaces and Dependencies

- External: `api.typesafe.ai` (`/v1/systemone`, model `jev-latest`), env
  `TYPESAFE_API_KEY` (secret). **Region-restricted** — verify egress.
- DB: `learn_followup_scores`, `learn_quiz_questions`, `learn_quiz_attempts`,
  `learn_quiz_chapter_aggregates` (all new).
- Config: `QUIZ_*` flags gate the quiz path; TTS split path always available but
  falls back deterministically when JEV returns `None`.
- HTTP: `requests` (already a dependency).
