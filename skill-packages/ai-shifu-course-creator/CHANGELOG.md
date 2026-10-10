# Changelog

Record user-visible and maintainer-relevant changes in chronological release history.
Current behavior remains defined by `SKILL.md`, references, and scripts.

## Unreleased

- Add a JEV (TypeSafe System One) **segmentation-quality pre-check** (`scripts/segmentation-quality.py` + `references/segmentation-quality.md`), run after Segmentation and before Orchestration/Generation. JEV is a typed-judgment model (noul/score), so it is used as a quality classifier, not a segmenter: one batched request scores `coverage` (0..4) plus per-segment `granularity` (0..4), `boundary` (0..4), and `preserve_ok` (noul), returning per-segment `flag`, a `summary`, and `uncertainty`/`rerun_hints` aligned with `data-contracts.md#segment-schema`. Fail-open: without `TYPESAFE_API_KEY` or on call failure it returns `{"status":"skipped"}` and never blocks. `TYPESAFE_API_KEY` is resolved from the process environment first, then the skill's root `.env`. Route it from `SKILL.md` (Cross-File Concept Routing + Segmentation Validation).
- Verified the pre-check against `jev-1.13.0` on a 3-segment sample: it correctly flagged an over-packed segment (`granularity=1.64`) and a table with `preserve_block:false` (`preserve_ok=0.16`), and passed a well-formed segment.

### Evaluation — official CLI 1.2.10 vs ai-shifu dev backend (2026-10-10)

Assessed whether the official CLI 1.2.10 courseware-management commands work against the
dev backend, using existing courseware. Run via temporary configuration
(`SHIFU_BASE_URL=http://localhost:5800` + `SHIFU_TOKEN=<dev token>`, executed inside the
dev api container); no browser authorization required on dev (`AAD_BYPASS=1`).

Full command matrix:

| Command | Result | Notes |
|---|---|---|
| `verify` / `list` / `show` / `export` | ✅ | basic reads |
| `create` / `update-meta` / `add-chapter` | ✅ | create + metadata + chapter |
| `add-lesson` / `update-lesson` / `rename-lesson` / `delete-lesson` | ✅ | lesson CRUD; `update-lesson` advanced revision 801→802 |
| `set-access` (guest/trial/normal) | ✅ | lesson learning-access |
| `history` | ✅ | Teaching Prompt revisions |
| `archive` / `unarchive` | ✅ | |
| `upload-image` | ✅ | returns relative path `/api/storage/courses/<bid>` |
| **`pull` / `status`** | ✅ | **local↔cloud sync**: writes `course-config.json` / `course-prompt.md` / `structure.json` / `lessons/*.md` + `.shifu-sync.json`; `status` compares against the cloud revision |
| **`build` / `import --new`** | ✅ | **local course dir → platform**: `build` regenerates import JSON, `import --new` creates a full course (chapters + lessons + MarkdownFlow); round-trip verified |
| `find-title` | ⚠️ | silently returns "no match" on dev: its metadata lookup goes through the missing `creator-analytics` endpoint (Recipe 0b/0c), so even an existing title is not found |
| `set-avatar` | ❌ | dev `upfile` returns a relative path (`/api/storage/courses/<bid>`), which the CLI rejects as "not a valid resource URL" — CLI/backend response-format drift |
| `set-tts` | ❌ | CLI sends `tts_pitch=0` by default, but the dev backend requires pitch 1-5 for provider `baidu_translate` → `2001 参数错误` |
| `reorder` | ❌ | `PATCH /shifus/<bid>/outlines/reorder` → `code -1 "系统异常"` (dev endpoint errors regardless of order) |
| `analytics-query` / `credit-detail` | ❌ | target `/api/creator-analytics/*`, which does not exist in the dev backend (404) |

**Conclusion**: the CLI update materially helps courseware management — the standout gain is the
`pull`/`status`/`build`/`import` **bidirectional local-course-directory ↔ platform workflow**
(absent in the older CLI). All reads and lesson/chapter CRUD work on dev. Four commands are
blocked: `set-avatar` and `set-tts` by CLI/backend contract drift, `reorder` by a dev endpoint
error, and `analytics-query`/`credit-detail` (plus `find-title`'s metadata path) by missing
`creator-analytics` endpoints.

All temporary courses created during the evaluation were soft-deleted from dev.

### Blocked-command impact, adaptation, and JEV priority (2026-10-10)

Impact on the local skill is layered by whether the older local CLI already exposes the command:

- **Direct local impact** — `analytics-query` and `reorder` are already in the older local CLI (20 commands), and both fail on dev today: `analytics-query` against the missing `creator-analytics` endpoint, `reorder` against an erroring backend endpoint.
- **Upgrade-only impact** — `find-title`, `set-avatar`, `set-tts`, and `credit-detail` are official-only additions; the older local CLI has no such commands, so they can only block after upgrading.
- **Core path unaffected** — reads and chapter/lesson CRUD plus the `pull`/`status`/`build`/`import` sync flow all pass on dev, so the local courseware-management main flow remains fully usable; the blocked items sit in the structure-ordering / analytics / presentation-config layer and are degradable, not blocking.

Adaptation, per item (does it stay within the "dev-compatible, backend change not required" principle?):

| Command | Strategy | Concrete fix | Needs backend change |
|---|---|---|---|
| `reorder` | backend_fix | Fix `PATCH /shifus/<bid>/outlines/reorder` (currently `code -1 系统异常`) | yes |
| `find-title` | backend_fix / workaround | Root cause is the missing `creator-analytics` endpoint; locally fall back to `list` + client-side filter | yes (root cause) |
| `analytics-query` | backend_fix | Implement `/api/creator-analytics/query` | yes |
| `credit-detail` | backend_fix (low priority) | Implement `/api/creator-analytics/credit-detail` | yes |
| `set-tts` | **cli_patch** | Change the local CLI default `tts_pitch` from `0` to `1` (`scripts/shifu-cli.py`) | no — skill-side |
| `set-avatar` | **cli_patch** | Prefix `base_url` onto the relative upload path before validation | no — skill-side |

- `set-tts` and `set-avatar` are one-line, skill-side adaptations with zero backend change — consistent with the "dev-compatible, do not force backend implementation" principle.
- The remaining four require backend changes, which is outside that principle.
- **Single root cause worth noting**: `find-title`, `analytics-query`, and `credit-detail` all fail because `/api/creator-analytics/*` is missing — implementing that one endpoint family unlocks all three, so it should be treated as one backend task, not three.

JEV importance judgment (`jev-1.13.0`; importance/effort on a 0..4 scale):

| Command | Importance | Effort | JEV recommendation |
|---|---|---|---|
| `reorder` | 2.98 | 2.53 | backend_fix |
| `find-title` | 2.89 | 2.66 | backend_fix |
| `analytics-query` | 2.03 | 3.22 | backend_fix |
| `set-tts` | 1.87 | 1.47 | cli_patch |
| `set-avatar` | 1.62 | 1.55 | cli_patch |
| `credit-detail` | 0.84 | 3.19 | backend_fix |

- **Highest priority**: `reorder` and `find-title` (~2.9, "commonly used; absence clearly reduces efficiency"), but both need backend work.
- **Best value**: `set-tts` and `set-avatar` — lower importance but the lowest effort and doable skill-side, so they are the sensible first adaptations.
- **Lowest priority**: `credit-detail` (importance 0.84, effort 3.19 — worst return) — skip.
- Combined with the shared root cause: schedule the `creator-analytics` endpoint (unlocks `find-title` + `analytics-query` + `credit-detail`) and the `reorder` fix as medium-priority backend work, and the `set-tts`/`set-avatar` patches as immediate skill-side work.

### Local CLI adoption & cli_patch fixes (2026-10-10)

Applied the "best value" adaptations from the JEV judgment — the skill-side `cli_patch` items, with no backend change.

- Landed the official CLI 1.2.10 into the local skill: replaced `scripts/shifu-cli.py` and added its helpers (`scripts/profile_store.py`, `scripts/skill_update.py`, `scripts/image_utils.py`, `scripts/requirements.txt`) plus `.env.example` at the skill root. The local additions (`scripts/segmentation-quality.py` and the older `ivd-lookup.py` / `mdf-proxy.py` / `segmentation-eval.py`) are preserved.
- `set-tts` fix: changed the default `tts_pitch` from `0` to `1` (the dev backend requires pitch 1-5 for provider `baidu_translate`). Two occurrences in `scripts/shifu-cli.py`.
- `set-avatar` fix: accept a relative upload path (starting with `/`) as a valid resource URL, in addition to `https://`, because the dev `upfile` endpoint returns a relative path (`/api/storage/courses/<bid>`).
- Verified on dev (running the local skill's CLI inside the dev api container, temporary configuration): `list` and `pull`/`status` work; `set-tts --enabled true` now succeeds (`Listen Mode -> enabled`); `set-avatar` now succeeds (`Resource URL: /api/storage/courses/<bid>`); the JEV segmentation-quality pre-check still returns `status: ok` (`jev-1.13.0`). The temporary course used for testing was soft-deleted from dev.
- **Not done (per decision)**: the backend_fix items (`reorder`, `creator-analytics` endpoint family) remain blocked; they require backend changes and are out of the "dev-compatible, no forced backend change" scope.

## 1.0.0

- Local snapshot predating the official versioned releases; no version identity or CHANGELOG.
- Baseline capability: `list`, `show`, `export`, `history`, `permissions`, `build`, `publish`, `import`, and SMS/employee login via the skill `.env`.
