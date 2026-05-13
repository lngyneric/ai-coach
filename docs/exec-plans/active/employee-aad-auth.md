# Employee AAD Authentication

This ExecPlan is a living document and must stay aligned with `PLANS.md`.

## Purpose / Big Picture

Add an `employee` authentication provider that validates users against the
internal enterprise AAD (Active Directory) server at
`http://10.40.20.195:8082/getAccessTokenByEmployeeNo` using employee number and
password, then maps the validated identity to a local ai-shifu user.

## Progress

- [x] 2026-05-12 CST: Created ExecPlan skeleton and initial design.
- [x] 2026-05-12 CST: Implemented EmployeeAuthProvider, route, and config; all
  harness and architecture checks pass.

## Surprises & Discoveries

_None yet._

## Decision Log

- Decision: implement employee auth as a new `AuthProvider` (not a modification
  to the existing `password` provider) so the AAD server integration remains
  isolated and the local password-hash flow stays unchanged.
  Date/Author: 2026-05-12 / deepseek-tui

- Decision: base64-encode the password before sending it to the AAD server as a
  query parameter, matching the server's expected contract.
  Date/Author: 2026-05-12 / deepseek-tui

- Decision: map employee identity to local user via
  `ensure_user_for_identifier` with `provider="employee"` and `subject_id`
  set to the employee number. First-time AAD-authenticated users are
  automatically created with the "learner" role.
  Date/Author: 2026-05-12 / deepseek-tui

- Decision: on first login, the user's nickname defaults to the employee number
  (can be changed later). No profile fields are synced from AAD in this phase
  because the response format is not yet documented.
  Date/Author: 2026-05-12 / deepseek-tui

## Outcomes & Retrospective

_To be filled after implementation._

## Context and Orientation

The ai-shifu authentication layer already supports pluggable `AuthProvider`
implementations registered via a factory pattern. The existing providers are
`phone` (SMS code), `email` (email code), `google` (OAuth), and `password`
(local hash). Each provider implements `verify()` and optionally
`send_challenge()` or OAuth methods.

The target AAD server exposes a single endpoint:

```
GET http://10.40.20.195:8082/getAccessTokenByEmployeeNo
  ?employeeNo=<employee_number>
  &password=<base64_encoded_password>
```

A successful response (HTTP 200) indicates valid credentials. The response
body format is not yet documented; the provider should accept any 200 response
as proof of identity. Additional fields (name, department) can be consumed in
a follow-up once the response schema is known.

## Plan of Work

1. Create `EmployeeAuthProvider` class implementing `verify()` with AAD HTTP
   call, user lookup/creation, and token generation.
2. Register the provider in the factory and builtin-provider loader.
3. Add `/api/user/login_employee` route in the user route module.
4. Add `AAD_AUTH_URL` and `AAD_AUTH_TIMEOUT` configuration entries.
5. Run repository harness and architecture checks; end-to-end manual
   verification with the AAD server.

## Concrete Steps

- Add `src/api/flaskr/service/user/auth/providers/employee.py`.
- Update `src/api/flaskr/service/user/auth/providers/__init__.py` to export
  `EmployeeAuthProvider`.
- Update `src/api/flaskr/service/user/auth/__init__.py` to include `employee`
  in `register_builtin_providers()`.
- Add `login_employee` route to `src/api/flaskr/route/user.py`.
- Add `AAD_AUTH_URL` and `AAD_AUTH_TIMEOUT` to `src/api/flaskr/common/config.py`.
- (Optional) Add `employee` to the `LOGIN_METHODS_ENABLED` default values
  once the frontend login UI supports it.

## Validation and Acceptance

- `python scripts/check_repo_harness.py` passes.
- `python scripts/check_architecture_boundaries.py --run-fixture-tests` passes.
- Manual curl test against the AAD server:
  ```
  curl -X POST http://localhost:5000/api/user/login_employee \
    -H "Content-Type: application/json" \
    -d '{"employeeNo":"sch0000","password":"123"}'
  ```
  Expected: 200 with `{"token": "...", "userInfo": {...}}`.

## Idempotence and Recovery

- Provider registration is idempotent (guarded by `has_provider()` check).
- `ensure_user_for_identifier` is idempotent — repeated calls for the same
  employee number return the existing user.
- If the AAD server is unreachable, the provider returns a generic
  `invalidCredentials` error to avoid leaking internal infrastructure details.
- Config defaults to empty `AAD_AUTH_URL`; the provider fails gracefully with
  a configuration error when the URL is not set.

## Interfaces and Dependencies

- `src/api/flaskr/service/user/auth/providers/employee.py` — new provider module.
- `src/api/flaskr/service/user/auth/providers/__init__.py` — export added.
- `src/api/flaskr/service/user/auth/__init__.py` — builtin registration updated.
- `src/api/flaskr/route/user.py` — new route added.
- `src/api/flaskr/common/config.py` — two new `EnvVar` entries.
- External dependency: `requests` library (already a project dependency).
- External dependency: AAD server at `10.40.20.195:8082` must be reachable
  from the backend container/process.
