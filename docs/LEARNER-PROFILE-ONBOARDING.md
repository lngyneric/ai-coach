# Learner Profile 建档设计（自动 vs 手动 · 打通企微姓名→bid）

> 2026-08-25 · 背景：wecom 闭环实测发现真实学员（凌云等 5 人）无 learner_profiles，
> 姓名→learner_bid 映射为空。本文档梳理建档途径与打通方案，并登记 TODO。

## 一、现状：LearnerProfile 创建点（代码仅 3 处）

| 途径 | 触发 | 位置 | 权限 | 前置条件 | 字段 |
|------|------|------|------|----------|------|
| **自动·懒建** | 学员首次更新自己档案 `PUT /api/portal/profile` | routes.py:225 | 任意登录用户（改自己） | 无 | user_bid + 后续逐字段补 |
| **手动·管理员 API** | `POST /api/portal/admin/learners` | routes.py:696 | `manage_users`（admin/hr） | **需 user_bid**（先有系统账号） | employee_no/dept/position/level/coach_bid/status=active |
| 管理更新/列表 | `PUT /api/portal/admin/learners/<bid>`、`GET ...` | routes.py:654/618 | `manage_users`/`view_all_students` | — | — |

> 注意：`admin/operations/profile-onboard` 页面是**平台级入职 onboarding**（手机/头像等 user 资料，
> `/api/shifu/profile-onboarding`），与 LearnerProfile 无关，勿混淆。

## 二、自动 vs 手动 差别

| 维度 | 自动（懒建） | 手动（管理员 API） |
|------|------------|------------------|
| 使用场景 | 学员自助完善档案 | HR/管理员批量/个别建档 |
| 数据完整性 | 低（先壳后补） | 高（一次建全 + coach 指派） |
| 风险 | 无 user_bid 映射的账号无法关联企微 | 不会误建重复（已查重） |
| 界面 | ✅ 学员中心档案页 | ❌ **无前端界面**（api.ts 仅 GET 列表） |

## 三、真实 5 人建档卡点

- person_master 5 人（刘佳怡/凌云/杨萍/陆蓓/陈珊）为**企微账号**（wecom_userid wo_...）
- 系统 user_users **无对应登录账号** → 手动 API 需要 user_bid，自动懒建需登录 → **两条路都走不通**
- learner_profiles 现仅有 dev 测试数据（w3-usr-1..4 → w3-ln-1..4、dev-learner-bid → w23-ln-1）

## 四、打通方案（待办）

### TL-1【P1】批量初始化脚本（立即可行）
- 为 person_master 5 人创建 dev 用户账号（user_users）+ wecom_userid 绑定
- 建 LearnerProfile（employee_no=企微职务、department=组织树、position_name、status=active）
- 产出：姓名→learner_bid 映射自动可查（gen-wecom-name-map.sh）
- 涉及：`src/api/flaskr/service/learning_portal/routes.py`（或迁移/脚本）+ `scripts/`
- 验收：5 人 learner_profiles 存在；gen 脚本生成 5 条映射；wecom 闭环任务登记的 learner_bid 为真实 bid

### TL-2【P2】管理员创建界面
- admin/hr（花名册）页面加"新增学员"表单→ 调 `POST /api/portal/admin/learners`
- api.ts 补 `createPortalAdminLearner: 'POST /portal/admin/learners'`
- 权限：manage_users（后台已守卫）
- 验收：HR 账号可视化建档，成功后列表出现

### TL-3【P2】(可选) 企微对接建档触发器
- 申请闭环通过后自动建档案（新员工入职审批通过 → 建 LearnerProfile + 分 coach）
- 或首次企微交互（报名/任务）时懒建

## 五、关联
- `scripts/gen-wecom-name-map.sh`（姓名→bid 生成，COLLATE 已修）
- `scripts/wecom-apply-processor.sh`（build_payload 姓名映射：env/文件/透传）
- `docs/COACH-API-MAPPING.md`（六、真实闭环）
- person_master/departments（企微主数据，应随 user 创建同步）