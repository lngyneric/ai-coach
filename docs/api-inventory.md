# AI-Shifu API 完整清单

## 1. 用户认证 (prefix: `/api/user`)

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/user/login_employee` | 工号+密码登录 |
| POST | `/api/user/login_phone` | 手机号登录 |
| GET | `/api/user/info` | 获取当前用户信息 |
| POST | `/api/user/update_info` | 更新用户信息 |
| POST | `/api/user/logout` | 退出登录 |
| GET | `/api/user/captcha` | 获取验证码 |
| POST | `/api/user/captcha/verify` | 验证码校验 |
| POST | `/api/user/send_sms_code` | 发送短信验证码 |
| POST | `/api/user/ensure_admin_creator` | 确保管理员账号 |
| GET | `/api/user/onboarding/status` | 新手引导状态 |
| POST | `/api/user/onboarding/complete` | 完成新手引导 |
| GET | `/api/user/profile-onboarding` | 档案填写状态 |
| POST | `/api/user/profile-onboarding/complete` | 完成档案填写 |
| POST | `/api/user/require_tmp` | 临时密码请求 |

## 2. 课件内容 (prefix: `/api/shifu`)

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/shifu/shifus` | 课件列表 |
| GET | `/api/shifu/shifus/{bid}` | 课件详情 |
| POST | `/api/shifu/drafts` | 创建草稿 |
| PUT | `/api/shifu/drafts/{bid}` | 更新草稿 |
| POST | `/api/shifu/drafts/{bid}/publish` | 发布课件 |
| DELETE | `/api/shifu/drafts/{bid}` | 删除草稿 |
| POST | `/api/shifu/drafts/{bid}/mdflow` | 保存 MDF 内容 |
| GET | `/api/shifu/drafts/{bid}/outline` | 大纲树 |
| POST | `/api/shifu/drafts/{bid}/outline/item` | 新增章节 |
| PUT | `/api/shifu/drafts/{bid}/outline/item/{iid}` | 修改章节 |
| DELETE | `/api/shifu/drafts/{bid}/outline/item/{iid}` | 删除章节 |
| POST | `/api/shifu/drafts/{bid}/outline/reorder` | 重新排序 |
| POST | `/api/shifu/admin/operations/courses` | 管理端课件列表 |
| GET | `/api/shifu/admin/operations/courses/overview` | 管理端课件概览 |
| POST | `/api/shifu/admin/operations/users` | 管理端用户列表 |
| GET | `/api/shifu/admin/operations/users/overview` | 管理端用户概览 |
| POST | `/api/shifu/admin/operations/orders` | 管理端订单列表 |
| GET | `/api/shifu/admin/operations/orders/{bid}` | 管理端订单详情 |

## 3. 学习 (prefix: `/api/learn`)

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/learn/shifu/{bid}/outline-item-tree` | 大纲树(含缓存) |
| POST | `/api/learn/shifu/{bid}/run/{lid}` | 运行课时 |
| GET | `/api/learn/shifu/{bid}/progress` | 学习进度 |
| POST | `/api/learn/shifu/{bid}/bookmark` | 书签 |
| GET | `/api/learn/shifu/{bid}/blocks` | 生成块列表 |
| POST | `/api/learn/ask` | 追问/对话 |
| GET | `/api/learn/listen/{bid}` | 听学模式内容 |
| POST | `/api/learn/listen/element` | 听学元素朗读 |

## 4. 学习门户 (prefix: `/api/portal`)

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/portal/profile` | 学员档案 |
| PUT | `/api/portal/profile` | 更新档案 |
| GET | `/api/portal/dashboard` | 学习驾驶舱 |
| GET | `/api/portal/courses` | 按分类课程列表 |
| GET | `/api/portal/notifications` | 通知列表 |
| POST | `/api/portal/notifications/read` | 标记已读 |
| GET | `/api/portal/mentor/students` | 导师学员列表 |
| GET | `/api/portal/mentor/pending-scores` | 待评分列表 |
| POST | `/api/portal/coach/items/{bid}/score` | 提交评分 |
| POST | `/api/portal/tasks` | 创建任务 |
| GET | `/api/portal/tasks` | 任务列表 |
| PUT | `/api/portal/tasks/{bid}` | 更新任务 |
| POST | `/api/portal/admin/enroll` | 管理员分配课程 |
| GET | `/api/portal/admin/enrollments` | 管理员查看分配 |

## 5. 带教系统 (prefix: `/api/shifu/coach`)

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/shifu/coach/students` | 教练学员列表 |
| GET | `/api/shifu/coach/pending-scores` | 待评分列表 |
| POST | `/api/shifu/coach/score` | 提交评分 |
| GET | `/api/shifu/coach/phase-detail/{bid}` | 阶段进度详情 |
| POST | `/api/shifu/coach/phase-summary` | 提交阶段小结 |
| GET | `/api/shifu/coach/report/{bid}` | 带教分析报表 |
| POST | `/api/shifu/coach/session` | 创建面谈记录 |
| POST | `/api/shifu/coach/feedback` | 学员反馈/追问 |
| POST | `/api/shifu/coach/ai-summary/{sid}` | AI 面谈汇总 |
| GET | `/api/shifu/coach/recommendations/{bid}` | 课程推荐 |
| POST | `/api/shifu/coach/learner-rating` | 学员自评 |
| POST | `/api/shifu/coach/final-rating` | 终评百分制 |
| POST | `/api/shifu/coach/learning-records` | 学习记录同步 |
| GET | `/api/shifu/enrollments` | 我的课程列表 |
| GET | `/api/shifu/dashboard` | 我的驾驶舱 |

## 6. 管理员 (prefix: `/api/shifu/admin`)

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/shifu/admin/roles` | 角色清单 |
| POST | `/api/shifu/admin/role-assign` | 为用户分配角色 |
| GET | `/api/shifu/admin/coaches` | 教练清单 |
| POST | `/api/shifu/admin/coach-profiles` | 新增教练 |
| GET | `/api/shifu/admin/learners` | 学员清单(含教练) |
| POST | `/api/shifu/admin/reassign-coach` | 调换学员教练 |
| POST | `/api/shifu/admin/sync-now` | 手动同步 |
| GET | `/api/shifu/admin/sync-history` | 同步历史 |

## 7. 运行时/系统

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/runtime-config` | 运行时配置(登录方式/Logo等) |
| GET | `/api/config` | 前端配置 |
| GET | `/api/i18n` | 国际化词条 |

## 8. 外部代理

| Method | Path | 目标 |
|--------|------|------|
| POST | `/api/chat/chat/completions` | → opencode.ai/zen/go/v1 (AI 对话) |
| GET/POST | `/vod/{path}` | → video.sysmex.com.cn (视频) |
| GET/POST | `/ignis/{path}` | → Obsidian 知识库 (172.18.0.1:8899) |
| GET/POST | `/wecom/{path}` | → 企业微信 Bridge (127.0.0.1:8800) |
| GET/POST | `/ws` | → Ignis WebSocket |
