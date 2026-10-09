# dev 模块逐测清单（DEV-MODULE-TEST-CHECKLIST）

> 配套总览：[`TRAINING-LOOP-OVERVIEW.md`](./TRAINING-LOOP-OVERVIEW.md)。
> 用途：在 dev 环境**逐点自测**每个模块的页面与 API。勾选框供你逐个打勾。
> 生成日期：2026-10-09。dev 站点 `http://localhost:8082`，API `127.0.0.1:5800`。

## 0. 测试账号矩阵（employee 登录，`AAD_BYPASS=1`，密码任意）

| 账号(employee_no) | user_bid | 角色 | 可测范围 |
|---|---|---|---|
| `devadmin` | dev-admin-bid | role-admin（全通）+is_operator+is_creator | **全部**（含 operations；dept 看板已随 A1 放开） |
| `devhr` | dev-hr-bid | role-hr | `/admin/hr`、建档 |
| `devdept` | dev-dept-bid | role-dept-head | `/admin/dept`（部门看板） |
| `devcoach` | dev-coach-bid | role-coach | `/admin/coach`（面谈/评分） |
| `devlearner` | dev-learner-bid | role-learner | `/courses`、`/c/{id}` 学习 |

**登录取 token（curl）**：
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:5800/api/user/login_employee \
  -H 'Content-Type: application/json' \
  -d '{"employeeNo":"devadmin","password":"x"}' | jq -r '.data.token')
echo "$TOKEN"
```
后续 API 请求带 `-H "Token: $TOKEN"`（后端鉴权头为 `Token`）。

---

## 1. 登录与会话
- [ ] 页面 `/login` → 员工 tab，输 `devadmin` + 任意密码 → 进入 `/admin`
- [ ] API `POST /api/user/login_employee` → `code:0` 且返回 token
- [ ] API `GET /api/user/info`（带 Token）→ 返回 devadmin 资料

## 2. 权限（P0 5 级模型）
- [ ] API `GET /api/portal/permissions` → `roles=[role-admin]`、`permissions` 含 `all`+12 key、`data_scope=all`
- [ ] 页面 `/admin/operations/permissions` → 展示 5 角色 × 权限矩阵
- [ ] 菜单核对（devadmin）：可见 `首页/看板/HR工作台/部门看板/导师工作台/AI/运营*`

## 3. 学员建档（onboarding）
- [ ] 页面 `/admin/hr` 或 `/admin/operations/users` → 学员列表可见
- [ ] API `GET /api/portal/admin/learners` → 返回 items
- [ ] API `POST /api/portal/admin/learners`（devhr/devadmin）→ 建档成功（`learner_profiles` 新增）
- [ ] API `PUT /api/portal/admin/learners/<learner_bid>` → 更新成功
- [ ] ⚠️ 已知缺口：**无前端"新增学员"界面**（`LEARNER-PROFILE-ONBOARDING.md` TL-2）

## 4. 课程分配 / 报名
- [ ] 页面 `/admin/operations`（课程管理）→ 可见
- [ ] API `POST /api/portal/admin/enroll` → `course_enrollments` 写入
- [ ] API `GET /api/portal/enrollments` → 返回分配列表
- [ ] API `DELETE /api/portal/admin/enroll` → 取消成功

## 5. 分配带教 + 开启阶段
- [ ] API `PUT /api/portal/admin/learners/<bid>`（含 `coach_bid`）→ 教练指派落库
- [ ] API `POST /api/shifu/admin/reassign-coach` → 改派成功
- [ ] API `POST /api/portal/mentorship/start` → `learner_coaching` 生成
- [ ] API `GET /api/portal/mentor/students`（devcoach）→ 返回所带学员

## 6. 课程学习
- [ ] 页面 `/courses` → 课程目录三态分组可见
- [ ] 页面 `/c/{shifu_bid}` → 课程播放器可打开
- [ ] API `PUT /api/portal/courses/<shifu_bid>/progress` → 进度更新
- [ ] API `PUT /api/learn/shifu/<bid>/run/<outline_bid>` → 运行记录
- [ ] ⚠️ 已知缺口：完成度"待接通"（`learning_portal/progress.ts:15`）

## 7. 随堂测验（JEV）
- [ ] 页面 `/c/{id}` 学习到第 2 个内容块 → 弹出 flashcard 测验（需 `QUIZ_ENABLED=true`，dev 已开）
- [ ] API `GET /api/portal/quiz/analysis?shifu_bid=<shifu_bid>` → 返回测验分析（**`shifu_bid` 必填**，缺则 `code=2001 paramsError`）
- [ ] API `GET /api/portal/mentor/quiz-analysis/<learner_bid>?shifu_bid=<shifu_bid>`（devcoach）
- [ ] API `GET /api/portal/admin/quiz-stats?shifu_bid=<shifu_bid>`（devadmin，**`shifu_bid` 必填**）
- [ ] 备注：JEV 依赖出海代理，dev 已配（见记忆 `reference_jev_typesafe_proxy`）

## 8. 面谈（1v1 三环）
- [ ] 页面 `/admin/coach` → 导师工作台可见
- [ ] API `GET /api/coach/sessions` → 会话列表
- [ ] API `POST /api/coach/sessions`（devcoach）→ `coach_sessions` 新增
- [ ] API `POST /api/coach/sessions/<bid>/summarize` → AI 汇总
- [ ] ⚠️ 已知缺口：dev 可能缺 `coach_sessions` 表（`coach-lab-validation.md:58`）——如报错记录之

## 9. 清单三态（签字 / 同步 / 改进）
- [ ] API `GET /api/coach/checklist/<record_bid>` → 清单状态
- [ ] API `POST /api/coach/checklist/<record_bid>/sign` → 导师签字（`sign_at`）
- [ ] API `POST /api/coach/checklist/<record_bid>/sync` → 记录同步（`sync_at`）
- [ ] API `POST /api/coach/checklist/<record_bid>/improvements` → 改进计划
- [ ] API `POST .../improvements/<bid>/done` → 完成改进

## 10. 评分
- [ ] API `POST /api/portal/mentorship/items/<record_bid>/score`（devcoach）→ 四维分落库
- [ ] API `POST /api/shifu/coach/score` → 评分成功
- [ ] API `POST /api/shifu/coach/learner-rating` / `final-rating` → 评教练 / 带教终评
- [ ] ⚠️ 已知缺口：**导师评分前端表单未实现**（`improvement-audit.md:46`），仅 API

## 11. 阶段推进
- [ ] API `POST /api/coach/phases/advance`（devadmin/devcoach）→ `advanced`/`finished`/`skipped`
- [ ] API `GET /api/portal/admin/phases` → 阶段列表
- [ ] ⚠️ 已知缺口：4 个 celery beat 任务从未验证触发（`improvement-audit.md:44`）

## 12. 报告
- [ ] API `GET /api/coach/report/<learner_bid>`（devadmin）→ 返回报告
- [ ] API `GET /api/shifu/coach/report/<learner_bid>` → 同上（myenroll 侧）
- [ ] 页面 `/admin/coach` 报告视图可见

## 13. 结业 / 转正 / 推荐
- [ ] API `GET /api/shifu/coach/recommendations/<learner_bid>` → 课程推荐
- [ ] celery `probation_check` / `advance_completed_phases`（触发方式见 tasks.py）
- [ ] ⚠️ 已知缺口：推荐为 "simulated"（`myenroll/routes.py:247`）

## 14. 管理层看板
- [ ] 页面 `/admin/dashboard` → 看板可见
- [ ] API `GET /api/dashboard/entry?page_index=1&page_size=20`（devadmin）→ 20 items
- [ ] API `GET /api/dashboard/shifus/<bid>/detail` → 明细

## 15. 部门看板（A1 后 devadmin 可见）
- [ ] 页面 `/admin/dept`（devadmin）→ 可见（本次 A1 改动）
- [ ] 页面 `/admin/dept`（devdept）→ 可见（原本即可）
- [ ] API `GET /api/portal/admin/learners`（devdept）→ 仅本部门学员

## 16. 运营后台（仅 is_operator）
- [ ] 页面 `/admin/operations`（课程管理）→ 可见
- [ ] 页面 `/admin/operations/users` → 用户管理
- [ ] 页面 `/admin/operations/permissions` → 权限示例
- [ ] API `GET /api/shifu/shifus?page_index=1&page_size=5` → 课程列表
- [ ] API `GET /api/shifu/admin/operations/courses?page_index=1&page_size=5` → 运营-课程
- [ ] API `GET /api/shifu/admin/operations/users?page_index=1&page_size=5` → 运营-用户
- [ ] 页面 `/admin/orders` → 计费停用时应重定向/隐藏（`billingEnabled=false`）

---

## 逐测注意事项
- **鉴权头**：后端用 `Token`（非 `Authorization`/`X-WECOM-TOKEN`）。
- **已知环境缺口**：带 ⚠️ 的条目可能因表/列/前端缺失而失败——属**环境现状**，非本次改动引入。
- **权限唯一变更**：本次仅改前端 `canViewDeptOnly`（admin 也可见部门看板），后端权限逻辑未动。
- 逐测若发现**非缺口清单**内的失败，记为真实 bug 并回报。

---

## 实测结果（2026-10-09，devadmin，API 只读部分）

以 `devadmin` 登录（`employeeNo=devadmin`、密码任意）逐项打 API，**17 PASS / 0 FAIL / 3 SKIP(写操作未实发)**。

| 环节 | 检查项 | 结果 |
|------|--------|------|
| 1 登录/会话 | `GET /api/user/info` | ✅ code=0 |
| 2 权限 | `GET /api/portal/permissions` | ✅ role-admin + `all` + 12 key + scope=all |
| 3 建档 | `GET /api/portal/admin/learners` | ✅ code=0 |
| 4 分配/报名 | `GET /api/portal/enrollments` | ✅ code=0 |
| 5 带教 | `GET /api/portal/mentor/students` | ✅ code=0 |
| 6 学习 | `GET /api/portal/courses` | ✅ code=0 |
| 7 测验 | `GET /api/portal/quiz/analysis?shifu_bid=…` | ✅ code=0（attempts=2, accuracy=0.5） |
| 7 测验 | `GET /api/portal/admin/quiz-stats?shifu_bid=…` | ✅ code=0 |
| 8 面谈 | `GET /api/coach/sessions` | ✅ code=0 |
| 10 评分 | `GET /api/portal/mentor/pending-scores` | ✅ code=0 |
| 11 推进 | `GET /api/portal/admin/phases` | ✅ code=0 |
| 12 报告 | `GET /api/shifu/coach/report/dev-learner-bid` | ✅ code=0 |
| 14 看板 | `GET /api/dashboard/entry` | ✅ code=0 |
| 15 部门看板 | `GET /api/portal/admin/learners` | ✅ code=0 |
| 16 运营 | `GET /api/shifu/shifus` | ✅ code=0 |
| 16 运营 | `GET /api/shifu/admin/operations/courses` | ✅ code=0 |
| 16 运营 | `GET /api/shifu/admin/operations/users` | ✅ code=0 |

**首次误报的 2 类（已澄清，非 bug）**：
- `quiz/analysis`、`admin/quiz-stats` 缺 `shifu_bid` → `code=2001 paramsError`（上文 URL 已补必填参数）。
- shifu 列表误用 `/api/shifu`、`/api/shifu/list` → 404；正确为 `/api/shifu/shifus`、`/api/shifu/admin/operations/*`。

**未实发的写操作**（会改 dev 数据，默认 dry-run）：`POST /api/user/login_employee`（登录已隐式验证）、`POST /api/portal/admin/learners`、`POST /api/coach/phases/advance`。
