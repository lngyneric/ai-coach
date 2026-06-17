# 学员档案系统整合方案

> 基于 suggest.md 培训体系设计 | 2026-06

---

## 一、现状 vs 目标

| 维度 | 当前（courses.html） | 目标 |
|------|---------------------|------|
| 数据 | 全部硬编码、模拟数据 | 从数据库/API 实时读取 |
| 角色 | 只有学员视角 | 学员、导师、HR/管理员 三端 |
| 课程分类 | 前端关键字匹配 | 数据库 category 字段精确分类 |
| 带教流程 | 无 | 完整的学分制带教跟踪（三阶段） |
| 评分验收 | 无 | 理论40%+实操30%+互评20%+经理10% |
| 定时任务 | 无 | 阶段提醒、带教推送、转正判定 |

---

## 二、角色权限矩阵

| 角色 | 范围 | 核心职责 |
|------|------|----------|
| **学员** | 个人 | 查看课程/学习/查看进度/待办/通知 |
| **导师/带教经理** | 所带学员 | 学员列表/阶段评分/创建任务/跟进计划 |
| **HR/管理员** | 全部 | 学员档案/学分配置/带教配置/统计看板 |

---

## 三、数据库结构

### 3.1 `user_users` — 扩展字段

| 字段 | 类型 | 说明 |
|------|------|------|
| employee_no | VARCHAR(50) | 工号 |
| department | VARCHAR(100) | 部门 |
| position_name | VARCHAR(100) | 岗位 |
| level | VARCHAR(20) | 职级 |
| mentor_bid | VARCHAR(32) | 带教责任人 |
| supervisor_bid | VARCHAR(32) | 上司 |
| onboarding_date | DATE | 入职日期 |
| probation_end_date | DATE | 试用期截止 |

### 3.2 新增 7 张表

| 表名 | 说明 | 行数 |
|------|------|------|
| learner_profiles | 学员档案 | 0 |
| mentorship_phases | 带教阶段定义 | 0 |
| learner_mentorship | 学员带教记录 | 0 |
| mentorship_checklist | 验收项模板 | 0 |
| learner_checklist_items | 学员验收项得分 | 0 |
| learner_tasks | 学员待办任务 | 0 |
| task_notifications | 任务通知 | 0 |

### 3.3 课程分类（新增 4 条录入）

| slug | 名称 | 说明 |
|------|------|------|
| onboarding | 新人入学 | 新员工入职引导 |
| mentorship | 学分制带教 | 系统化导师带教 |
| intensive | 小灶教学 | 精品小班实战 |
| leadership | 领导力课程 | 管理层发展 |

---

## 四、API 总览

| 分类 | 接口 | 状态 |
|------|------|------|
| 学员 | `GET/PUT /api/portal/profile` | ✅ |
| 学员 | `GET /api/portal/dashboard` | ✅（含导师身份识别） |
| 学员 | `GET /api/portal/notifications` | ✅ |
| 学员 | `POST /api/portal/notifications/read` | ✅ |
| 学员 | `POST /api/portal/mentorship/start` | ✅ |
| 学员 | `GET /api/portal/courses?category=` | ✅ |
| 导师 | `GET /api/portal/mentor/students` | ✅ |
| 导师 | `GET /api/portal/mentor/pending-scores` | ✅ |
| 导师 | `POST /api/portal/mentorship/items/{bid}/score` | ✅（自动重算学分） |
| 导师 | `POST /api/portal/tasks` | ✅ |
| 管理员 | `GET/POST /api/portal/admin/learners` | ✅ |
| 管理员 | `PUT /api/portal/admin/learners/{bid}` | ✅ |
| 管理员 | `GET/PUT /api/portal/admin/phases` | ✅ |
| 管理员 | `GET/POST /api/portal/admin/checklist` | ✅ |
| 管理员 | `GET /api/portal/admin/stats` | ✅ |
| 管理员 | `GET/PUT /api/portal/admin/roles` | ✅ |
| 通用 | `GET/POST /api/user/logout` | ✅ |

---

## 五、定时任务

| 任务 | 频率 | 状态 |
|------|------|------|
| daily_task_push（待办推送） | 每日 09:00 | ✅ |
| score_reminder（评分催办） | 每小时 30分 | ✅ |
| phase_deadline_reminder（阶段截止提醒） | 每日 08:00 | ✅ |
| probation_check（转正预检） | 每日 07:00 | ✅ |

---

## 六、前端页面结构

| 页面 | 功能 | 状态 |
|------|------|------|
| `/courses/` | 学员首页 + 导师工作台入口 | ✅ |
| `/mentor/` | 导师工作台（独立页面） | ✅ |
| `/login` | 统一登录页 | ✅ |
| `/logout.html` | 登出 | ✅ |

---

## 七、实施路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| ✅ Phase 1 | 数据库迁移：7 张表 + user_users 扩展 + 4 分类 | ✅ 已完成 |
| ✅ Phase 2 | 后端 API：/api/portal/ 模块 | ✅ 已完成 |
| ✅ Phase 3 | courses.html 接入真实 API | ✅ 已完成 |
| ✅ Phase 4 | 导师 API + 前端导师工作台 | ✅ 已完成 |
| ✅ Phase 5 | 管理员 API（学员/阶段/验收项/统计） | ✅ 已完成 |
| ✅ Phase 6 | celery 定时任务（4 个） | ✅ 已完成 |
| ✅ Phase 7 | 学分换算 + 自动转正判定逻辑 | ✅ 已完成 |

---

## 八、关键设计决策

1. **学分权重可配置**：`mentorship_phases` 表存四维权重，HR 可直接改库或通过 API 调整
2. **自动学分重算**：每次评分提交后触发 `_recalc_phase_score()`，达标自动通过
3. **导师自动识别**：`/dashboard` 返回 `mentor_student_count`，前端据此显示导师入口
4. **渐进式迁移**：现有系统完全不动，所有新功能以"插件式"新增
