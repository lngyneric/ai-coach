# 企业学习平台 — 系统架构说明

> 版本 2.0 | 基于 ai-shifu 培训体系改造 | 2026-06

---

## 一、整体架构

```
用户浏览器
    │
    ├── https://eu.sysmex.com.cn/
    │
    ▼
nginx (反向代理)
    │
    ├── /c/{bid} ───────────→ Next.js (课程播放器)
    ├── /shifu/{bid} ──────→ Next.js (课程编辑器)
    ├── /admin ────────────→ Next.js (管理员后台)
    │
    ├── /courses/ ─────────→ courses.html (课程首页 / 学员+导师看板)
    ├── /course-entry.html ─→ course-entry.html (登录页)
    ├── /logout.html ──────→ logout.html (登出页)
    │
    ├── /api/ ─────────────→ Flask API (ai-shifu-api:5800)
    │     ├── /api/user/ ───────→ route/user.py
    │     ├── /api/learn/ ──────→ service/learn/
    │     ├── /api/shifu/ ──────→ service/shifu/
    │     ├── /api/portal/ ────→ service/learning_portal/  ← 学习门户
    │     └── /api/... ────────→ 其他服务模块
    │
    └── /api/user/logout ──→ 清除 token + 302 → /logout.html
```

---

## 二、新增模块结构

```
flaskr/service/learning_portal/
├── __init__.py          # 模块入口（空）
├── models.py            # 7 张表的 ORM 模型
├── routes.py            # 所有 API 路由（学员/导师/管理员）
└── tasks.py             # 4 个 celery 定时任务

flaskr/common/celery_app.py  # 修改：引入学习门户任务 + beat 调度
flaskr/route/user.py         # 修改：新增 /api/user/logout
```

---

## 三、数据库新增结构

### 3.1 `user_users` — 扩展字段（原表增加 8 列，DEFAULT NULL）

| 字段 | 类型 | 说明 |
|------|------|------|
| `employee_no` | VARCHAR(50) | 工号 |
| `department` | VARCHAR(100) | 部门 |
| `position_name` | VARCHAR(100) | 岗位名称 |
| `level` | VARCHAR(20) | 职级：普通员工/管理层/一线营业/二线支援 |
| `mentor_bid` | VARCHAR(32) | 带教责任人 user_bid |
| `supervisor_bid` | VARCHAR(32) | 上司 user_bid |
| `onboarding_date` | DATE | 入职日期 |
| `probation_end_date` | DATE | 试用期结束日期 |

**影响**: 零破坏性，所有字段 DEFAULT NULL，存量用户不受影响。

---

### 3.2 `learner_profiles` — 学员档案

| 字段 | 类型 | 说明 |
|------|------|------|
| learner_bid | VARCHAR(32) PK | 主键 |
| user_bid | VARCHAR(32) | 关联 user_users |
| employee_no | VARCHAR(50) | 工号 |
| department | VARCHAR(100) | 部门 |
| position_name | VARCHAR(100) | 岗位 |
| level | VARCHAR(20) | 职级 |
| mentor_bid | VARCHAR(32) | 带教人 |
| supervisor_bid | VARCHAR(32) | 上司 |
| onboarding_date | DATE | 入职日期 |
| probation_end_date | DATE | 试用期截止 |
| status | VARCHAR(20) | active/probation/completed/resigned |

---

### 3.3 `mentorship_phases` — 带教阶段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| phase_bid | VARCHAR(32) PK | 主键 |
| name | VARCHAR(100) | 阶段名 |
| code | VARCHAR(20) | 标识（phase_1/phase_2/phase_3） |
| description | TEXT | 阶段描述 |
| sort_order | INT | 排序 |
| duration_days | INT | 阶段时长（默认 60 天） |
| passing_score | DECIMAL(5,2) | 及格线（默认 60 分）|
| theory_weight | DECIMAL(3,2) | 理论权重（默认 0.40）|
| practice_weight | DECIMAL(3,2) | 实操权重（默认 0.30）|
| review_weight | DECIMAL(3,2) | 互评权重（默认 0.20）|
| mentor_weight | DECIMAL(3,2) | 经理评价权重（默认 0.10）|
| is_active | TINYINT(1) | 是否启用 |

---

### 3.4 `learner_mentorship` — 学员带教记录

每个学员在每个阶段有一条记录，跟踪状态和四个维度的得分。

```
total_score = theory_score × theory_weight 
            + practice_score × practice_weight 
            + peer_review_score × review_weight 
            + mentor_score × mentor_weight
```

| 状态流转 | 说明 |
|----------|------|
| pending → in_progress | 通过 POST /mentorship/start 开启 |
| in_progress → passed | 全部验收项评分后自动重算，达标自动通过 |
| in_progress → failed | 未达及格线，retry_count +1 |

自动重算由 `_recalc_phase_score()` 函数在每次评分提交后触发。

---

### 3.5 `mentorship_checklist` — 验收项模板

每个阶段下的验收项定义（如"血球产品三个明白考试"），
分为 exam / practice / review / mentor 四类，对应四个评分维度。

### 3.6 `learner_checklist_items` — 学员验收项得分

记录评分人、评语、提交/评分时间。状态流转：pending → submitted → scored。

### 3.7 `learner_tasks` — 学员待办任务

| 字段 | 说明 |
|------|------|
| task_type | course/exam/review/meeting/submission |
| related_bid | 关联对象（课程/阶段/验收项）|
| due_at | 截止时间 |
| created_by | 创建人（系统自动/导师/HR）|

### 3.8 `task_notifications` — 任务通知

| 字段 | 说明 |
|------|------|
| notif_type | task_assign/score_reminder/phase_start/phase_end/system |
| is_read | 已读/未读 |

### 3.9 `course_categories` — 课程分类（新增 4 条录入）

| category_bid | name | slug | 说明 |
|-------------|------|------|------|
| cat-006 | 新人入学 | onboarding | 新员工入职引导 |
| cat-007 | 学分制带教 | mentorship | 系统化导师带教 |
| cat-008 | 小灶教学 | intensive | 精品小班实战 |
| cat-009 | 领导力课程 | leadership | 管理层发展 |

已有 5 个旧分类（医学检验/产品管理/企业数字化/AI基础/自动化工具）不受影响。
通过 `shifu_category_map` 表实现课程-分类的多对多关联。

---

## 四、API 接口一览

### 4.1 学员端

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/portal/profile` | GET | 获取当前用户学习档案 |
| `/api/portal/profile` | PUT | 更新学习档案 |
| `/api/portal/dashboard` | GET | 学员看板（待办/进度/带教/通知数/导师身份）|
| `/api/portal/courses` | GET | 课程列表（可选 `?category=slug` 精确过滤）|
| `/api/portal/notifications` | GET | 通知列表（20 条） |
| `/api/portal/notifications/read` | POST | 全部标为已读 |
| `/api/portal/mentorship/start` | POST | 开启一个带教阶段 |

### 4.2 导师端

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/portal/mentor/students` | GET | 名下学员列表（含阶段状态 + 待评分计数） |
| `/api/portal/mentor/pending-scores` | GET | 待评分项列表 |
| `/api/portal/mentorship/items/{record_bid}/score` | POST | 提交评分（自动重算总学分） |
| `/api/portal/tasks` | POST | 创建学员任务（自动发通知） |

### 4.3 管理员端

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/portal/admin/learners` | GET | 学员列表（分页） |
| `/api/portal/admin/learners` | POST | 新增学员档案 |
| `/api/portal/admin/learners/{learner_bid}` | PUT | 编辑学员 |
| `/api/portal/admin/phases` | GET | 阶段配置列表 |
| `/api/portal/admin/phases/{phase_bid}` | PUT | 更新阶段配置 |
| `/api/portal/admin/checklist/{phase_bid}` | GET | 阶段验收项列表 |
| `/api/portal/admin/checklist` | POST | 新增验收项 |
| `/api/portal/admin/stats` | GET | 全局统计（学员数/进行中/已完成） |

### 4.4 通用

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/user/info` | GET | 当前用户信息（已有）|
| `/api/shifu/shifus?page_index=1&page_size=50` | GET | 课程列表（已有）|
| `/api/user/logout` | GET/POST | **新增** 清除 token cookie，302 → `/logout.html` |

---

## 五、定时任务（celery beat）

### 5.1 任务定义

文件：`flaskr/service/learning_portal/tasks.py`

| 任务 | 频率 | 说明 |
|------|------|------|
| `daily_task_push` | 每日 09:00 | 推送当天待办 + 逾期项汇总给学员 |
| `score_reminder` | 每小时 30分 | 检查提交超48h未评分的验收项，催办导师 |
| `phase_deadline_reminder` | 每日 08:00 | 检查进行中阶段，截止前7/3/1天推送提醒 |
| `probation_check` | 每日 07:00 | 试用期到期前14天预检，通知转正评定 |

### 5.2 注册方式

在 `flaskr/common/celery_app.py` 中：

1. `include` 数组增加 `"flaskr.service.learning_portal.tasks"`
2. `beat_schedule` 合并 `_build_portal_beat_schedule()` 返回值
3. `_register_default_tasks()` 增加 `importlib.import_module("flaskr.service.learning_portal.tasks")`

---

## 六、前端页面结构

### 6.1 `courses.html` — 课程首页/学员+导师看板

```
/courses/ (或 /courses)
    │
    ├── 检查 cookie token
    │    ├── 无 → 重定向 /course-entry.html?redirect=/courses/
    │    └── 有 → 并行请求 3 个 API
    │
    ├── GET /api/user/info
    ├── GET /api/shifu/shifus?page_index=1&page_size=50
    └── GET /api/portal/dashboard
          └── 如果 mentor_student_count > 0，显示导师工作台入口
    │
    ├── viewMode === 'learner'
    │    └── render(): Header + Hero + Stats + Dashboard + Categories + CourseSections + Footer
    │
    └── viewMode === 'mentor'
         └── renderMentorView(): Header + 学员列表 + 待评分项 + Footer
```

**学员视图**:
```
shifus 数组
  ├── renderStats: shifus.length → 在学数
  ├── renderDashboard: dash.pending_tasks → 待办
  ├── renderCategories: getCoursesByCategory(id).length → 分类计数
  └── renderCourseSections: 
        ├── getCoursesByCategory(onboarding)  = /新人|入职|入门|...|.test(name+desc+kw)
        ├── getCoursesByCategory(mentorship)  = /带教|学分|导师|...|.test(name+desc+kw)
        ├── getCoursesByCategory(intensive)   = /小灶|实战|案例|...|.test(name+desc+kw)
        ├── getCoursesByCategory(leadership)  = /领导|管理|战略|...|.test(name+desc+kw)
        └── 不匹配任一分类 → "其他课程"
```

**导师视图**（新增）:
```
GET /api/portal/mentor/students       → 学员卡片列表（含阶段状态 + 待评分红点）
GET /api/portal/mentor/pending-scores → 待评分项
```

### 6.2 登录/登出页面

```
/course-entry.html          → 登录页（员工号 + 密码）
  ├── 已登录 → 跳转至 redirect 参数指定 URL
  └── 未登录 → 显示登录表单（登录后跳回 /courses/）

/api/user/logout            → 清除 token cookie
  └── 302 跳转 → /logout.html（登出完成页）
        ├── "已安全登出" 提示
        ├── 重新登录 → /login?redirect=/courses/
        └── 返回首页 → /courses/
```

---

## 七、Nginx 路由

| 路径 | 目标 | 类型 |
|------|------|------|
| `/courses/` | `/usr/share/nginx/html/courses.html` | 静态文件 |
| `/courses` | `/usr/share/nginx/html/courses.html` | 静态文件 |
| `/mentor/` | `/usr/share/nginx/html/mentor.html` | 静态文件（导师工作台）|
| `/mentor` | `/usr/share/nginx/html/mentor.html` | 静态文件 |
| `/login` | `/usr/share/nginx/html/login.html` | 静态文件（统一登录）|
| `/login.html` | `/usr/share/nginx/html/login.html` | 静态文件 |
| `/logout.html` | `/usr/share/nginx/html/logout.html` | 静态文件 |
| `/courses.html` | `/usr/share/nginx/html/courses.html` | 静态文件 |
| `/api/` | `ai-shifu-api:5800/api` | 反向代理 |
| `/c/` | `ai-shifu-cook-web:5000` | Next.js 代理 |
| `/` | `ai-shifu-cook-web:5000` | Next.js 代理（回退） |

---

## 八、docker-compose 挂载

```yaml
volumes:
  - ./nginx.conf:/etc/nginx/nginx.conf
  - ./default.conf:/etc/nginx/conf.d/default.conf
  - ./course-entry.html:/usr/share/nginx/html/course-entry.html:ro
  - ./courses.html:/usr/share/nginx/html/courses.html:ro
  - ./logout.html:/usr/share/nginx/html/logout.html:ro
  - ./certs2:/etc/nginx/certs:ro
```

bind mount 特性：修改宿主机文件立即生效，无需重启容器。

---

## 九、关键设计要点

1. **课程分类**：利用已有的 `course_categories` 表和 `shifu_category_map` 多对多关联。前台 `courses.html` 目前通过关键字匹配，后续可改为 API 参数 `?category=onboarding` 后端过滤。

2. **学分权重可配置**：`mentorship_phases` 表存四维权重，HR 可直接改库或通过 API 调整。

3. **评分标准化**：按三方评分（自评20%+带教人50%+总监30%），各自独立录入后 `_recalc_phase_score()` 自动算分，达标自动通过。

4. **渐进式迁移**：现有系统不受影响，所有新功能以"插件式"新增，可随时回退。

5. **docker-compose 持久化**：静态页面通过 bind mount 挂载，修改宿主机文件立即生效。

6. **导师自动识别**：`GET /api/portal/dashboard` 返回 `mentor_student_count`，前端据此显示导师工作台入口。

7. **定时任务独立**：4 个 celery 任务各自独立，不影响现有 billing 任务的运行。
