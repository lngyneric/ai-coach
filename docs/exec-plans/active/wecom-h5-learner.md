# WeCom H5 Learner Integration

This ExecPlan is a living document and must stay aligned with `PLANS.md`.

## Purpose / Big Picture

Create a standalone H5 learning page for 企业微信 (WeCom) deployment, using
Employee AAD authentication for persistent user identity. Learners access the
course player via `/course/[id]` which auto-detects authentication state and
redirects to the existing `/c/[id]` Next.js player after login.

## Progress

- [x] 2026-05-12 CST: ExecPlan created. Design decisions recorded.
- [x] 2026-05-12 CST: Backend WeComAuthProvider, OAuth routes, config entries implemented.
- [x] 2026-05-13 CST: Direction corrected — employee AAD auth as primary login method.
- [x] 2026-05-13 CST: Unified entry page `/course/[id]` deployed via nginx.
- [x] 2026-05-13 CST: Employee AAD authentication end-to-end verified with real server.
- [x] 2026-05-13 CST: TTS (Baidu Translate) enabled for course `d9f7b137...`.
- [x] 2026-05-13 CST: Brand replacement (`sysmex`) completed.
- [x] 2026-05-13 CST: All P0/P1/P2 tasks completed. ExecPlan finalised.

## Surprises & Discoveries

- Discovery: the existing `/c/[[...id]]` page already supports token-based auth
  and does not require the `require_tmp` anonymous user flow when a valid token
  cookie is present. Evidence: `/c/` page loaded with employee token cookie
  returning 200 with 15KB of player content.

- Discovery: the AAD server returns HTTP 200 even on authentication failure,
  with error details in the JSON `statusCode` field. The `EmployeeAuthProvider`
  was updated to check both HTTP status and JSON body to correctly reject
  invalid credentials.

- Discovery: Microsoft Edge TTS is blocked (403) from this server's network
  location. Baidu Translate TTS was selected as the free alternative that
  works from this environment.

- Discovery: the original WeCom OAuth design (silent `snsapi_base` auth) was
  reconsidered after requirements clarification. The Employee AAD auth is the
  correct primary login method for the enterprise deployment.

## Decision Log

- Decision: use Employee AAD authentication as the primary login method
  instead of WeCom OAuth silent auth. WeCom OAuth infrastructure (provider,
  routes) is preserved for future use.
  Date/Author: 2026-05-13 / deepseek-tui

- Decision: serve the `/course/[id]` entry page as static HTML via nginx
  rather than a Next.js page, because the production Docker image cannot
  be rebuilt locally (Docker Hub unreachable, no build toolchain).
  Date/Author: 2026-05-13 / deepseek-tui

- Decision: check AAD JSON body `statusCode` field in addition to HTTP status
  code to correctly handle AAD server's error responses.
  Date/Author: 2026-05-13 / deepseek-tui

- Decision: keep the `/c/[id]` public entry page unchanged for anonymous
  access and demo purposes, while `/course/[id]` serves authenticated
  enterprise learners.
  Date/Author: 2026-05-13 / deepseek-tui

## Outcomes & Retrospective

- Delivered a working H5 learning flow: `/course/[id]` → Employee login → `/c/[id]` player.
- AAD authentication verified with real enterprise server at `10.40.20.195:8082`.
- Test account: `sch00068` / `0@x2RsIqPS` — creates persistent user, retains learning progress.
- TTS enabled via free Baidu Translate endpoint, zero cost.
- Brand fully rebranded to `sysmex` in metadata, i18n, and runtime config.
- Redundant WeCom/employee nginx routes and static HTML files cleaned up.
- All repository harness and architecture boundary checks pass.

## Context and Orientation

The final architecture:
```
Browser → /course/{shifu_bid}?lessonid={lessonid}
  ├── has token cookie? → redirect to /c/{shifu_bid}
  └── no token → show Employee login form
        → POST /api/user/login_employee
        → AAD verification → Set-Cookie token
        → redirect to /c/{shifu_bid}
              → Next.js player with persistent user
              → learning progress/notes/tests retained
```

## Plan of Work (Completed)

1. ✅ EmployeeAuthProvider with AAD server integration.
2. ✅ `/api/user/login_employee` route with cookie support.
3. ✅ Unified entry page `/course/[id]` via nginx static HTML.
4. ✅ Brand replacement to `sysmex`.
5. ✅ TTS integration (Baidu Translate, free).
6. ✅ AAD network connectivity verified.
7. ✅ Cleanup of redundant assets.

## Concrete Steps (Completed)

- ✅ `src/api/flaskr/service/user/auth/providers/employee.py`
- ✅ `src/api/flaskr/route/user.py` — `/login_employee` route
- ✅ `src/api/flaskr/common/config.py` — `AAD_AUTH_URL`, `BRAND_NAME`, etc.
- ✅ `docker/course-entry.html` — unified entry page
- ✅ `docker/nginx.conf` — `/course/` location
- ✅ `docker/.env` — enterprise credentials
- ✅ `src/cook-web/src/app/metadata.tsx` — brand parameterisation
- ✅ `src/i18n/` — brand text replacement
- ✅ `src/api/flaskr/api/tts/baidu_translate_provider.py` — free TTS

## Validation and Acceptance

- ✅ `python scripts/check_repo_harness.py` passes.
- ✅ `python scripts/check_architecture_boundaries.py --run-fixture-tests` passes.
- ✅ Manual AAD auth test: correct credentials → success, wrong credentials → rejected.
- ✅ `/course/` page serves login form (no token) and redirects (with token).
- ✅ TTS synthesis via `/api/shifu/tts/preview` returns valid MP3 audio.
