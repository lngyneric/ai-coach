# 培训闭环总览（Training Loop Overview）

> 面向 dev 环境（`/home/sysmex/worktrees/ai-shifu-dev`，分支 dev）。
> 目的：把后端模块、前端页面、API 与数据表按"培训闭环"串起来，供逐点自测与后续维护。
> 生成日期：2026-10-09。配套逐测清单见 [`DEV-MODULE-TEST-CHECKLIST.md`](./DEV-MODULE-TEST-CHECKLIST.md)。

## 一、闭环定义（权威来源）

- 主定义：`docs/design-docs/DESIGN-OVERVIEW.md:32-36`
  - **6 阶段生命周期**：待入职 → 入职中 → 带教中 → 评估中 → 已完成 → 归档
  - **ph-000** 入职确认（19 项）/ **ph-001~003** "三个明白"（38 验收 / 四维评分）
  - **1v1 三环面谈**：课前准备 → 面谈交互 → 课后 AI 总结
  - 合规三控制点：导师签字 / 记录同步 / 改进计划
- 评分模型：`docs/coach-system-v2-design.md:52-58` = 教练 40% + 自评 20% + AI 20% + 课件完成度 20%
- 课程架构：`docs/onboarding-training-design.md`（Phase1 入职带教 / Phase2 三个明白 / Phase3 自学）
- 企微侧实测：`docs/COACH-API-MAPPING.md:46-64`（B1-B4 闭环全通过）

> ⚠️ **断链提示**：代码注释多处引用 `docs/TRAINING-LOOP-DESIGN.md §改造2`（`coach/routes.py:368`、`models.py:212`、前端 `coach-api/types.ts:187`），但该文件在 `docs/` 下**不存在**。本总览即为补齐该缺口。

## 二、闭环流程（文本图）

```
[待入职] 建档(learner_profiles) + 分配带教(coach_bid)
   │  POST /api/portal/admin/learners ; PUT .../<bid>
   ▼
[入职中] 开启带教阶段(mentorship/start → learner_coaching)
   │  ph-000 入职确认 19 项
   ▼
[带教中] 课程分配/报名(course_enrollments) → 学习(/api/learn) → 随堂测验(JEV)
   │      ph-001~003 三个明白（38 验收）
   ▼
[评估中] 面谈(coach_sessions) → 清单三态(签字/同步/改进) → 四维评分
   │      阶段推进(phases/advance, celery phase_auto_advance)
   ▼
[已完成] AI 跟踪报告(report) + 转正提醒(probation_check)
   │
   ▼
[归档] 后续课程推荐(recommendations)
```

## 三、后端模块清单（`src/api/flaskr/service/`）

| 模块 | 路由前缀 | 注册函数·落点 | 闭环角色 |
|------|---------|--------------|---------|
| `coach` | `/api/coach` | `register_coach_routes` `coach/routes.py:305`；`register_report_routes` `coach/report_routes.py:73` | 面谈/清单/评分/推进/报告 |
| `learning_portal` | `/api/portal` | `register_learning_portal_routes` `routes.py:180` | 学员档案/看板/报名/评分/权限/测验分析 |
| `myenroll` | `/api/shifu` | `register_my_enroll_routes` `routes.py:30` | 9 节点登记/课件/任务/学习凭证/评分/报告 |
| `learn` | `/api/learn` | `register_learn_routes` `routes.py:140` | 课程运行/记录/随堂测验 |
| `shifu` | `/api/shifu` | `register_shifu_routes` `shifu/route.py:310` | 课程内容管理/预览 |
| `dashboard` | `/api/dashboard` | `register_dashboard_routes` `route/__init__.py:24` | 管理层看板 |
| `profile` | `/api/profiles` | `register_profile_routes` `routes.py:17` | 用户资料 |
| `user` | `/api/user` | `register_user_handler` `route/__init__.py:19` | 登录/账号 |
| `billing` | `/api/billing` | `register_billing_routes` `routes.py:82` | 计费（内训站点已停用，门控保留） |
| `chat` | `/api` | `register_chat_routes` `routes.py:193` | 对话 |
| `metering` | `/api/metering` | `register_metering_routes` `routes.py:25` | 用量计量 |

其余为支撑/无路由模块：`active`、`check_risk`、`common`、`config`、`feedback`、`gen_mdf`、`llm`、`order`、`promo`、`resource`、`tts`。

> 注册机制：`coach`/`learning_portal`/`myenroll`/`learn`/`profile`/`shifu` 经**插件加载**（`framework/plugin/load_plugin.py`）扫描 `service/*/` 注册；`dashboard`/`user` 等在 `route/__init__.py` 显式注册。`myenroll` 与 `learning_portal` 曾端点撞名，已用 `endpoint="xxx_shifu"` 规避（`routes.py:39/487`）。

## 四、闭环环节 × API × 页面 × 表 映射

| # | 环节 | 前端页面 | 后端 API | 主要数据表 |
|---|------|---------|---------|-----------|
| 1 | 登录 | `/login` | `POST /api/user/login_employee` | `user_users` |
| 2 | 学员建档 | `/admin/hr`、`/admin/operations/users` | `POST /api/portal/admin/learners`、`PUT .../<learner_bid>` | `learner_profiles` |
| 3 | 课程分配/报名 | `/admin/operations` | `POST/DELETE /api/portal/admin/enroll`、`GET /api/portal/enrollments` | `course_enrollments` |
| 4 | 分配带教 | `/admin/coach` | `PUT /api/portal/admin/learners/<bid>`（coach_bid）、`POST /api/shifu/admin/reassign-coach` | `learner_profiles.coach_bid` |
| 5 | 开启阶段 | `/admin/coach` | `POST /api/portal/mentorship/start` | `learner_coaching`、`coach_phases` |
| 6 | 课程学习 | `/courses`、`/c/{id}` | `PUT /api/learn/shifu/<bid>/run/<outline_bid>`、`PUT /api/portal/courses/<bid>/progress` | `learn_progress_records`、`course_enrollments` |
| 7 | 随堂测验 | `/c/{id}` 内 | `GET /api/portal/quiz/analysis` | `learn_quiz_*`、`learn_followup_scores` |
| 8 | 面谈 | `/admin/coach` | `GET/POST/PUT /api/coach/sessions`、`POST .../summarize` | `coach_sessions` |
| 9 | 清单三态 | `/admin/coach` | `GET/POST /api/coach/checklist/<record_bid>`、`/sign`、`/sync`、`/improvements` | `coach_checklist`、`learner_checklist_items`、`coach_checklist_improvements` |
| 10 | 评分 | `/admin/coach` | `POST /api/portal/mentorship/items/<bid>/score`、`POST /api/shifu/coach/score`、`learner-rating`、`final-rating` | `learner_coaching` 四维分 |
| 11 | 阶段推进 | `/admin/coach` | `POST /api/coach/phases/advance`、celery `phase_auto_advance` | `learner_coaching`、`coach_phases` |
| 12 | 报告 | `/admin/coach`、`/admin/dept` | `GET /api/coach/report/<learner_bid>` | 汇总多表 |
| 13 | 结业/转正 | —（celery） | `probation_check`、`advance_completed_phases` | `learner_profiles.probation_end_date` |
| 14 | 后续推荐 | `/admin/coach` | `GET /api/shifu/coach/recommendations/<learner_bid>` | `course_position_tags`、`coach_feedback` |
| 15 | 管理层看板 | `/admin/dashboard` | `GET /api/dashboard/entry`、`/shifus/<bid>/detail` | 多表聚合 |
| 16 | 权限演示 | `/admin/operations/permissions` | `GET /api/portal/permissions` | `coach_roles`、`user_role_assignments` |

## 五、角色与可见页面

| 角色(role_bid) | 权限 | scope | 后端 admin 页 |
|---------------|------|-------|--------------|
| `role-admin` | `"all"`（12 key 全通） | `all` | 全部（含 operations） |
| `role-hr` | manage_users 等 9 | `all` | `/admin/hr` |
| `role-dept-head` | 6（含 custom_dashboard） | `department:<dept>` | `/admin/dept` |
| `role-coach` | 含 create_session/score | `mentored:<bid>` | `/admin/coach` |
| `role-learner` | view_own_report | `self:<bid>` | 无（重定向 `/courses`） |

后台运营页（`/admin/operations/*`）**仅 `is_operator` 可见**；`/admin/orders` 另需 `billingEnabled`。
前端派生：`useCoachPermissions` → `lib/coach-permissions.ts`；菜单：`admin/admin-menu.tsx`；守卫：`admin/layout.tsx`。

## 六、已实现 vs 缺口/TODO

**已实现**：建档 / 分配带教 / 课程学习 / 随堂测验(JEV) / 清单三态合规 / 阶段自动推进 / AI 报告(含规则兜底) / 后续推荐 / 转正提醒 / 企微推送 / 管理层看板 / 5 级权限模型。

**缺口/TODO**（逐测时按此预期失败或跳过）：
- **前端评分 UI 未实现**：`docs/improvement-audit.md:46` 导师评分仅有 API，无前端表单。
- **表/列缺失**：`docs/design-docs/coach-lab-validation.md:58-60` 称 `coach_sessions`/`coach_feedback` 在 dev 缺失、`learner_coaching` 缺 `coach_summary`/`learner_feedback`/`improvement_plan` 列（模型已补，`models.py:198`）；`/coach/phases` 元数据、per-learner checklist-detail 缺。
- **企微同步占位**：`coach_sync.py` 为占位；`myenroll/routes.py:540` SIMULATE SYNC。
- **AI 汇总/推荐为模拟**：`myenroll/routes.py:229/247` 标记 "simulated"。
- **建档映射**：`docs/LEARNER-PROFILE-ONBOARDING.md:32-49` TL-1/2/3 待办（批量建档、管理员建界面、企微触发建档）。
- **进度接通**：`learning_portal/progress.ts:15` 课程完成度"待接通"。
- **定时任务未验证**：`docs/improvement-audit.md:44` 4 个 celery beat 任务从未验证触发。
- **命名不一致遗留**：models 用 `coach_phases/learner_coaching`，而 `myenroll` SQL 仍写 `learner_coaching.mentor_bid`（`routes.py:394/429/478/500`）。
- **内容准入**：`shifu/route.py:3196` MDFlow run API `NotImplementedError`。

## 七、dev 环境速记

- 站点：`http://localhost:8082`（宿主）· `http://10.32.16.47:8082`（内网）；API `127.0.0.1:5800`。
- DB：容器 `docker-ai-shifu-mysql-dev-1`，库 `ai-shifu_dev`，宿主端口 3307。
- 登录：employee 方式 + `AAD_BYPASS=1`，`employee_no` = 账号名（devadmin/devhr/devdept/devcoach/devlearner），密码任意。
- 测试账号权限矩阵见 [`DEV-MODULE-TEST-CHECKLIST.md`](./DEV-MODULE-TEST-CHECKLIST.md) 第 0 节。
