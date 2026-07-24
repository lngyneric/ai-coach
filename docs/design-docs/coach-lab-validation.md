---
title: Coaching Interaction Redesign Validation (Coach Lab)
status: implemented
owner_surface: frontend
last_reviewed: 2026-07-22
canonical: true
---

# Coaching Interaction Redesign Validation (Coach Lab)

## Summary

The coaching and analysis-report interactions were re-designed and validated
in an isolated Next.js project at `/home/sysmex/coach-lab/` (outside this
repository, zero risk to the shipping surfaces).

v2 (2026-07-22) realigned the lab with the **real dev database structure**
(MySQL behind `:8082`), the phase-closure model from
`docs/onboarding-training-design.md`, and the 1v1 three-ring session model
from `docs/coach-system-v2-design.md`. All 36 Playwright end-to-end
assertions pass in mock mode; the adapter layer also smokes against the real
backend through Next.js rewrites.

Full report: `/home/sysmex/coach-lab/VALIDATION-REPORT.md`.
Dev DB findings: `/home/sysmex/coach-lab/docs/dev-db-structure.md`.

## Validated Interaction Changes (v2)

Evidence: `e2e/walkthrough.mjs` (36/36 passing), screenshots in `e2e/shots/`.

1. Scoring panel submits `record_bid` and shows the real checklist item name
   + learner submission (legacy `coach.html` drops `record_bid`, scores blind).
2. Phase-closure timeline mirrors the real dev phases — ph-001
   血球/尿液/凝血, ph-002 免疫/生化/糖化/Alifax, ph-003 生命科学/招标/压货
   (60 days each) — with duration, passing score, and four score dimensions
   (theory / practice / review / mentor).
3. Acceptance-criteria card groups the real 38 checklist items by category
   (exam / review / practice) with scored counts.
4. Compliance control points visualized: coach sign-off, record sync to
   training archive, and a mandatory improvement plan when a phase score is
   below the passing line (summary form blocks save until filled).
5. 1v1 three-ring session flow (entirely absent in production): pre-session
   (goal + recommended courseware) → session (notes + action items) →
   post-session (AI summary placeholder + next action + coach rating), with
   a step indicator and closure badge.
6. Analysis report page (production only exposes JSON): overview cards,
   echarts score trend with passing markline, dimension breakdown, phase
   summaries, session timeline; dual coach/learner perspective.
7. Design tokens from cook-web (`--primary: #0f63ee`, `.dark` palette);
   working light/dark/system theme; no overflow at 375px.

## Bugs & Schema Gaps Found (v2 verified against dev DB)

| Severity | Location | Issue |
|---|---|---|
| High | `docker/coach.html` | Score request body omits `record_bid`; scoring broken. |
| High | `src/api/flaskr/service/learning_portal/routes.py` | `register_learning_portal_routes` never called → whole `/api/portal/*` family 404; only `/api/shifu/*` is live. |
| High | dev DB | `coach_sessions` and `coach_feedback` tables do **not exist** — the 1v1 flow has nowhere to persist. |
| Medium | dev DB | Legacy table names `mentorship_*` vs models.py `coaching_*`; field names `mentor_*` vs `coach_*` mismatch. |
| Medium | dev DB `learner_mentorship` | Missing `coach_summary` / `learner_feedback` / `improvement_plan` columns that routes write dynamically. |
| Medium | API gap | No `/coach/phases` (phase metadata) and no per-learner checklist-detail endpoint. |
| Low | `myenroll/coach_sync.py` | WeCom sync placeholder. |
| Low | report pass rule | Hardcoded `score >= 3` vs percent-based `passing_score`. |

## API Unification Recommendations

1. Keep `/api/shifu/*` as the single live family; if the portal family is
   ever enabled, register its routes and unify naming (prefer `coach_*` per
   models.py, with a migration).
2. Standardize scoring as `POST /api/shifu/coach/items/<record_bid>/score`.
3. Add `GET /api/shifu/coach/phases` and
   `GET /api/shifu/coach/checklist/<learner_bid>`.
4. Create `coach_sessions` / `coach_feedback` tables plus the three-ring
   endpoints, or add the three summary columns to `learner_mentorship`.
5. Include `improvement_plan` / `learner_feedback` in the report endpoint;
   back AI advice with a real LLM.

## Migration Notes (lab → this repo)

- The lab shares the cook-web stack (Next.js, Tailwind v4 tokens, echarts);
  components port into `src/cook-web/src/features/coaching/`.
- Before production: real auth, i18n keys for all copy (hard rule), dev DB
  table/column additions, and seeding business data.
- Session UI degrades cleanly when the `coach_sessions` table is missing
  (http adapter raises a clear error).

## References

- Validation report: `/home/sysmex/coach-lab/VALIDATION-REPORT.md`
- Dev DB structure: `/home/sysmex/coach-lab/docs/dev-db-structure.md`
- Specs: `docs/onboarding-training-design.md`,
  `docs/coach-system-v2-design.md`, `docs/mentorship-system-design.md`,
  `docs/wecom-coach-integration.md`
