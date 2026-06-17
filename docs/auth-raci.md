# 授权层级规划 & RACI 矩阵

> 基于现有代码的完整授权链路审计 | 2026-06

---

## 一、当前授权模型

### 1.1 两个角色位

| 字段 | 表 | 含义 | 当前自动授予方式 |
|------|-----|------|-----------------|
| `is_creator` | `user_users` | 课程创建者（后台权限） | employee登录时自动授予、phone首次用户自动授予 |
| `is_operator` | `user_users` | 系统运营者（管理后台权限） | employee登录时自动授予 |

### 1.2 角色在各模块的强制校验点

| 模块（文件） | is_creator | is_operator | 无权限时的行为 |
|------------|-----------|------------|---------------|
| `shifu/route.py` — 课程CRUD | ✅ 强制 | ✅ 强制（admin列表） | 返回 `noPermission` 错误 |
| `shifu/route.py` — 课程查看 | ✅ 强制（3处） | — | 返回 `noPermission` |
| `learn/routes.py` — 学习路由 | ✅ 强制 | — | 返回 `noPermission` |
| `billing/routes.py` — 计费 | ✅ 强制 | — | 返回 `noPermission` |
| `billing/trials.py` — 试用 | ✅ 强制（3处） | — | 返回错误 |
| `billing/cli.py` — CLI | ✅ 强制 | — | 返回错误 |
| `order/route.py` — 订单 | ✅ 强制 | — | 返回错误 |
| `admin/page.tsx` — 前端管理页 | ⚠️ 自动调用 ensureAdminCreator | — | 强制跳转登录 |

### 1.3 自动授权代码路径（共 4 处）

| # | 文件 | 行号 | 条件 | 授予的角色 | 风险 |
|---|------|------|------|-----------|------|
| 1 | `employee.py` | 145-147 | **所有**工号密码登录 | creator + operator | 🔴 **所有人都是管理员** |
| 2 | `phone_flow.py` | 237-238 | **首个**手机号验证用户 | creator + operator | 🟢 仅首次，可接受 |
| 3 | `user/utils.py` | 291-294 | ensure_creator_demo_permissions | creator | 🟢 条件性 |
| 4 | `billing/cli.py` | 764-765 | CLI 调用 | creator | 🟢 仅 CLI |

---

## 二、目标授权层级设计

### 2.1 新角色定义

```
系统级别（全局权限）
  ├── System Admin（系统管理员）← 原 is_operator
  │     └── 系统配置、全局管理、用户管理
  │
  ├── Creator（课程创建者）← 原 is_creator
  │     └── 创建/编辑/发布课程、管理自己的课程
  │
  └── Learner（学员）← 新增默认角色
        └── 学习课程、查看学习档案

业务级别（学习门户）
  ├── Mentor（导师）
  │     └── 名下学员管理、验收评分、创建任务
  │
  └── HR Admin（HR管理员）
        └── 学员档案管理、带教阶段配置、转正判定
```

### 2.2 角色与现有字段的映射关系

| 新角色 | 现有字段 | 对应关系 |
|--------|---------|----------|
| `System Admin` | `is_operator = true` | 直接映射，不变更字段 |
| `Creator` | `is_creator = true` | 直接映射，不变更字段 |
| `Learner` | 两者均为 `false` | **新增概念**，当前无此角色 |
| `Mentor` | `learner_profiles.mentor_bid` 关联 | **新增业务角色**，表驱动 |
| `HR Admin` | 手动分配 `is_operator` | **新增业务角色**，与 System Admin 共用权限位 |

### 2.3 角色层级图

```
                    ┌──────────────┐
                    │ System Admin │  ← is_operator = true
                    │  系统管理员    │
                    └──────┬───────┘
                           │ 继承所有权限
                    ┌──────▼───────┐
                    │   Creator    │  ← is_creator = true
                    │  课程创建者    │
                    └──────┬───────┘
                           │ 继承所有权限
                    ┌──────▼───────┐
                    │   Learner    │  ← 默认角色（两者皆 false）
                    │    学员       │
                    └──────────────┘

    业务角色（独立于系统角色）：
      Mentor   → learner_profiles.mentor_bid 指向此人
      HR Admin → 由 System Admin 手动分配 is_operator
```

---

## 三、授予流程

### 3.1 新增场景：员工首次登录（最频繁）

```
员工 A 首次登录 /login
    │
    ├── POST /api/user/login_employee
    │
    ├── AAD 验证成功
    │
    ├── ensure_user_for_identifier() → 创建用户
    │
    ├── [修改前] mark_user_roles(bid, creator=True, operator=True)  🔴
    │                                   ↓
    │   [修改后] 不再自动授予任何角色    ✅
    │            用户默认角色 = Learner
    │
    └── 签发 token → 返回前端
```

**影响**：
- 新用户默认没有课程创建和管理权限
- 需要创建课程 → 由现有 Creator 在后台手动分配 `is_creator`
- 需要系统管理 → 由 System Admin 在后台手动分配 `is_operator`

### 3.2 提权场景：学员 → Creator

```
发起人：Creator / System Admin
    │
    ├── 在管理后台找到目标用户
    ├── 操作：授予"课程创建者"权限
    │
    ├── API: PUT /api/portal/admin/learners/{bid}
    │         { "grant_creator": true }
    │
    ├── 后端：mark_user_roles(bid, is_creator=True)
    │
    └── 通知：推送给用户"你已被授予课程创建者权限"
```

### 3.3 提权场景：Creator → System Admin

```
发起人：System Admin
    │
    ├── 在管理后台找到目标用户
    ├── 操作：授予"系统管理员"权限
    │
    ├── API: PUT /api/portal/admin/learners/{bid}
    │         { "grant_operator": true }
    │
    ├── 后端：mark_user_roles(bid, is_operator=True)
    │
    └── 通知：推送给用户
```

### 3.4 指派场景：学员 → 导师

```
发起人：HR Admin / System Admin
    │
    ├── 在学员档案中设置 mentor_bid
    │
    ├── API: PUT /api/portal/admin/learners/{bid}
    │         { "mentor_bid": "导师的user_bid" }
    │
    └── 导师工作台自动可见 → 无需独立授权

    注：导师不需要 is_creator 或 is_operator
        mentor_bid 关联即获得导师权限
```

---

## 四、移除流程

### 4.1 移除 Creator

```
发起人：System Admin
    │
    ├── API: PUT /api/portal/admin/learners/{bid}
    │         { "revoke_creator": true }
    │
    ├── 后端：mark_user_roles(bid, is_creator=False)
    │
    └── 效果：立刻失去课程创建/编辑权限
              已有课程不受影响（保留只读）
```

### 4.2 移除 System Admin

```
发起人：另一 System Admin
    │
    ├── API: PUT /api/portal/admin/learners/{bid}
    │         { "revoke_operator": true }
    │
    └── 效果：立刻失去系统管理权限
              保留 Creator/Learner 权限
```

### 4.3 移除导师指派

```
发起人：HR Admin
    │
    ├── 在学员档案中清空 mentor_bid
    │
    └── 效果：导师工作台不再显示该学员
              已有评分记录保留
```

### 4.4 用户离职

```
触发条件：HR 将用户状态改为 resigned
    │
    ├── API: PUT /api/portal/admin/learners/{bid}
    │         { "status": "resigned" }
    │
    └── 自动：不删除角色（保留审计痕迹）
              前端登录后显示"账户已停用"
```

---

## 五、全流程 RACI 矩阵

### 5.1 图例

| 字母 | 含义 | 中文 |
|------|------|------|
| **R** | Responsible | 执行者 |
| **A** | Accountable | 批准者（最终责任人） |
| **C** | Consulted | 咨询者（需征求意见） |
| **I** | Informed | 知会者（需告知结果） |

### 5.2 RACI 矩阵

| 活动 \ 角色 | System Admin | Creator | Learner | HR Admin | 系统(自动) | 备注 |
|------------|:-----------:|:-------:|:-------:|:--------:|:---------:|------|
| **入职流程** | | | | | | |
| 创建学员档案 | R/A | — | — | C | — | HR提供数据，Admin执行 |
| 员工首次登录 | I | — | R | — | A | 系统自动完成验证 |
| 默认角色 = Learner | — | — | — | — | R/A | 修改后：不再自动授予 |
| **角色授予** | | | | | | |
| 授予 Creator | A | R | — | C | — | Creator 提名，Admin 批准 |
| 授予 System Admin | R/A | — | — | — | — | 至少2名Admin互相制衡 |
| 指派导师(mentor_bid) | C | — | — | R/A | — | HR操作，Admin可调 |
| **角色移除** | | | | | | |
| 移除 Creator | R/A | I | I | — | — | 需告知相关人 |
| 移除 System Admin | R/A | I | — | — | — | 另一Admin执行 |
| 清空导师指派 | C | — | I | R/A | — | 告知学员和导师 |
| 用户离职停用 | R/A | — | I | C | — | HR提交，Admin执行 |
| **日常运营** | | | | | | |
| 创建/编辑课程 | — | R/A | — | — | — | 无需审批 |
| 发布课程 | I | R/A | — | — | — | 通知学员 |
| 管理带教阶段 | C | — | — | R/A | — | HR配置，Admin审核 |
| 配置验收项 | — | — | — | R/A | — | HR按计划配置 |
| 验收项评分 | I | — | C | — | R/A | 学员提交→系统提醒→导师评分 |
| 创建学员任务 | — | C | I | R/A | R | 导师/HR/系统 均可创建 |
| **系统任务** | | | | | | |
| 每日待办推送 | — | — | I | — | R/A | 定时任务上午9点 |
| 阶段截止提醒 | — | I | I | — | R/A | 定时任务早8点 |
| 评分催办 | — | I | — | — | R/A | 超48h提醒导师 |
| 转正预判 | I | — | I | A | R | 系统计算→HR确认 |
| 月度学习报告 | — | — | I | — | R/A | 每月1日生成 |
| 带教积分结算 | A | I | — | R | R | 每季度末 |
| **审计与安全** | | | | | | |
| 查看操作日志 | R/A | — | — | C | — | 仅Admin可看 |
| 角色变更审计 | I | I | — | — | R/A | 系统记录所有变更 |
| 权限回收审计 | R/A | I | — | — | I | 定期检查超期授权 |

### 5.3 关键活动放大

#### 活动：员工首次登录（修改前后对比）

| 步骤 | 角色 | 修改前 | 修改后 |
|------|------|--------|--------|
| AAD 验证 | 系统 | R/A | R/A |
| 创建用户记录 | 系统 | R/A | R/A |
| 自动授予 creator | 系统 | R/A | **移除** |
| 自动授予 operator | 系统 | R/A | **移除** |
| 默认 Learner 角色 | 系统 | ❌ 不存在 | ✅ R/A |
| 通知新用户 | 系统 | — | I |

#### 活动：创建学员 → 导师指派

| 步骤 | 角色 | 操作 |
|------|------|------|
| 1. HR 确认学员导师分配 | HR Admin | 提供 mentor_bid |
| 2. 更新学员档案 | System Admin (R) | 执行 UPDATE |
| 3. 通知导师 | 系统 (R) | 推送通知 |
| 4. 通知学员 | 系统 (R) | 推送通知 |
| 5. 导师工作台可见 | 系统 (R) | 自动生效 |

---

## 六、影响分析

### 6.1 影响范围

| 受影响项 | 修改前 | 修改后 | 影响程度 |
|---------|--------|--------|---------|
| employee.py | 自动授予 creator+operator | 不自动授予 | 🔴 所有员工登录后权限变更 |
| phone_flow.py | 首次用户自动授予 | 保留（首次引导） | 🟢 仅在首次部署有用 |
| admin/page.tsx | ensureAdminCreator 自动创建 | **需改** — 改为检查权限 | 🟡 前端需调整 |
| 前端 admin 入口 | 所有员工可见 | 仅 is_operator 可见 | 🟡 权限校验前移至前端 |
| 已有用户角色 | 所有人都是 creator | 需重新分配 | 🟡 需批量调整存量用户 |

### 6.2 存量用户处理

```sql
-- 修改前：所有 user_users 的 is_creator 和 is_operator 可能为 1
-- 修改后：需要将真正需要管理权限的用户保留，其余清空

-- 保留权限：当前实际使用 admin 功能的用户（通过操作日志识别）
-- 清空权限：从未使用过 admin 功能的用户
UPDATE user_users SET is_creator = 0, is_operator = 0 
WHERE is_creator = 1 AND is_operator = 1
  AND user_bid NOT IN (
    -- 实际使用过 admin 功能的白名单
    SELECT DISTINCT user_bid FROM shifu_draft_shifus WHERE deleted = 0
  );
```

### 6.3 需修改的代码清单

| 文件 | 修改内容 | 风险 |
|------|---------|------|
| `employee.py:145-147` | **删除** 自动授权代码 | 🔴 核心变更 |
| `admin/page.tsx:419` | ensureAdminCreator → check current role | 🟡 前端已部署无需重建？→ 静态页 |
| `routes.py` (portal) | 增加 grant/revoke 角色 API | 🟢 新增即可 |

### 6.4 项目未上线的策略优势

```
✅ 无存量用户 → 不需要处理存量数据迁移
✅ 无生产流量 → 改完即可测试，无影响
✅ 无第三方依赖 → 不需要协调其他系统
✅ 前端无需构建 → 静态页可直接更新
```

---

## 七、变更实施步骤

| 步骤 | 操作 | 责任人 | 所需时间 |
|------|------|--------|---------|
| 1 | 删除 employee.py 自动授权代码 | 开发 | 5min |
| 2 | 增加 portal admin 角色管理 API | 开发 | 30min |
| 3 | 验证所有 API 权限校验仍正确 | 开发 | 30min |
| 4 | 更新文档 | 开发 | 15min |
| 5 | 测试全链路（登录→学员→创建课程） | 开发 | 30min |
| 合计 | | | **~2h** |
