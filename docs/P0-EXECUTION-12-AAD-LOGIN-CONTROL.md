# P0 · 执行记录 12：AAD 强登录控制（默认 learner 兜底 + 游客授权移除 + 登录收敛）

> 日期：2026-08-06
> 依据：`P0-REVIEW-PERMISSION-AAD.md` §五 执行顺序（1-6）+ `AAD-LOGIN-CONTROL-DESIGN.md`
> 落盘：docker rw 挂载写 worktree（`chown 1000:1000`）+ `docker cp` 运行容器 + gunicorn `--reload` 热加载
> 状态：✅ 已实现并复验通过

## 一、变更文件

| 文件 | 变更 |
|------|------|
| `src/api/flaskr/service/user/repository.py` | 新增 `assign_default_role`；`ensure_user_for_identifier` created=True 写 role-learner |
| `src/api/flaskr/service/user/phone_flow.py` | `init_first_course` 加 `ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO` 门控；`verify_phone_code` 加 `PHONE_LOGIN_ENABLED` 开关 |
| `src/api/flaskr/service/user/email_flow.py` | 新增 `_validate_email_domain`（`EMAIL_DOMAIN_ALLOWLIST`，兼容字符串化 list） |
| `src/api/flaskr/common/config.py` | 注册 `EMAIL_DOMAIN_ALLOWLIST`/`PHONE_LOGIN_ENABLED`/`AAD_BYPASS`；`ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO` 默认 False；`LOGIN_METHODS_ENABLED` 默认 employee |
| `src/api/tests/service/user/test_default_role_assignment.py` | 新增：默认角色/幂等/门控 |
| `src/api/tests/service/user/test_user_identify.py` | 更新：phone 开关、email 域白名单、bootstrap 新默认 |
| `src/api/tests/service/user/test_google_auth.py` | 更新：bootstrap 语义测试显式开 flag |
| `src/cook-web/src/api/api.ts` | 新增 `loginEmployee: POST /user/login_employee` |
| `src/cook-web/src/hooks/useAuth.ts` | 新增 `loginWithEmployee` |
| `src/cook-web/src/components/auth/EmployeeLogin.tsx` | 新增（employeeNo + password） |
| `src/cook-web/src/components/auth/EmployeeLogin.test.tsx` | 新增 3 用例 |
| `src/cook-web/src/app/login/page.tsx` | LoginMethod 增加 `employee` |
| `src/i18n/{en-US,zh-CN}/modules/auth.json` | 新增 employee 文案 |
| `docker/.env` / `.env.example` / `docker-compose.dev.yml` | flag False、白名单、前端 employee |
| `deploy-prod.sh` | 新增生产 flag 检查 |
| `docs/p0-patches/step12-aad/backfill_role_learner.sql` | 存量兜底迁移（已执行 dev 真库） |

## 二、数据迁移结果（dev 真库）

- 迁移前：`user_role_assignments` 6 行，4 个无角色用户。
- 迁移后：10 行（operator→role-admin、creator→role-coach、其余→role-learner），**孤儿用户=0**；重复执行幂等。
- 新用户 `sch08471` 登录 → role-learner×1，is_creator=0；`/api/portal/permissions` → `["learner:read","learner:write","view_own_report"]` + `data_scope=self`。

## 三、验证

| 验证 | 结果 |
|------|:----:|
| py_compile（6 文件） | ✅ |
| 单测（test_default_role_assignment / test_user_identify / test_google_auth） | ✅ 17 passed |
| user 服务全量 pytest | ✅ 118 passed / 1 known-baseline（login_sms 已移除） |
| 5 角色 login_employee | ✅ code=0 |
| 新用户默认 role-learner / 重复登录复用 | ✅ |
| cook-web tsc + jest | ✅（7 passed；login 页 200 热加载） |

## 四、遗留

见 `AAD-LOGIN-CONTROL-DESIGN.md`《实现记录》§3：email 通道独立路由、容器 env 重建生效、login_sms 测试改写、api.ts 残留声明清理、is_operator 退役、user_role_assignments 审计。
