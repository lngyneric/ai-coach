# 身份验证规则调整方案

> 基于当前系统的可配置能力分析 | 2026-06

---

## 一、需求与现状对照

| 需求 | 当前状态 | 实现方式 |
|------|---------|---------|
| ① 管理后台关闭/开启手机登录验证 | ✅ 已支持（env var） | `LOGIN_METHODS_ENABLED=phone,email,employee` |
| ② 管理后台关闭/开启 AAD 工号密码强验证 | ✅ 已支持（env var） | 同上，控制 `employee` 是否在列表中 |
| ③ 知识图谱页面无需登录 | ✅ 已完成 | nginx 静态文件，不经过 token 校验 |
| ④ 课程和 AI 对话需登录 | ✅ 已完成 | `/c/` 和 `/api/chat/` 均需 token |

---

## 二、当前配置机制

### 2.1 登录方法控制（已存在）

**环境变量**：`LOGIN_METHODS_ENABLED`（定义在 `flaskr/common/config.py:271`）

```
取值: phone,email,employee,google 的逗号分隔组合
默认: phone
```

**运行时暴露**：`GET /api/runtime-config`

```json
{
  "loginMethodsEnabled": ["phone", "email", "employee"]
}
```

**前端消费方**（`cook-web`）：

| 文件 | 用途 |
|------|------|
| `ShifuSetting.tsx:205` | 读取列表，决定显示哪些登录方式 |
| `OrderDetailSheet.tsx:59` | 联系用户模式选择 |
| `ImportActivationDialog.tsx:222` | 同上 |

### 2.2 各路径的认证要求（当前）

| 路径 | 目标 | 认证要求 | 机制 |
|------|------|---------|------|
| `/ivd-knowledge-tree.html` | 知识图谱 | ❌ 无需登录 | nginx 直接服务静态文件 |
| `/courses/` | 课程首页 | ✅ 需要登录 | 前端 JS 检查 token cookie |
| `/course-entry.html` | 登录页 | ❌ 无需登录 | 登录页本身 |
| `/login` | 统一登录 | ❌ 无需登录 | 登录页本身 |
| `/c/{bid}` | 课程播放器 | ✅ 需要登录 | Next.js + API token 校验 |
| `/api/chat/` | AI 对话 | ✅ 需要登录 | nginx 转发 + API token 校验 |
| `/api/` | 全部 API | ✅ 需要登录 | `optional_token_validation` |

---

## 三、推荐配置方案

### 3.1 企业内训场景的推荐配置

```env
# 只启用 AAD 工号登录，关闭手机/邮箱/谷歌登录
LOGIN_METHODS_ENABLED=employee
```

效果：

| 登录方式 | 开启/关闭 |
|---------|-----------|
| 工号+密码（AAD） | ✅ 开启 |
| 手机号+验证码 | ❌ 关闭 |
| 邮箱+验证码 | ❌ 关闭 |
| Google OAuth | ❌ 关闭 |

### 3.2 配置变更方式

**当前（开发/演示环境）**：
```env
LOGIN_METHODS_ENABLED=phone,email,employee
```

**推荐（正式企业环境）**：
```env
LOGIN_METHODS_ENABLED=employee
```

---

## 四、后续管理后台开关（开发计划）

当前登录方法控制通过环境变量实现。后续可增加管理后台动态开关：

### API 设计

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /api/admin/auth/methods` | GET | 查看当前启用的登录方式 |
| `PUT /api/admin/auth/methods` | PUT | 更新启用的登录方式 |

### 前端管理面板

```
┌─────────────────────────────────────┐
│  身份验证配置                        │
│                                     │
│  ☑ AAD 工号密码验证（推荐）          │
│  ☐ 手机号验证码登录                  │
│  ☐ 邮箱验证码登录                    │
│  ☐ Google OAuth 登录                 │
│                                     │
│  [保存]                              │
└─────────────────────────────────────┘
```

### 存储方案

当前 `LOGIN_METHODS_ENABLED` 是环境变量，重启才生效。后续可：

1. **优先**：存入 `redis`（运行时配置，立即生效）
2. **可选**：存入数据库表 `system_config`（持久化）

---

## 五、知识图谱页面说明

当前 `/ivd-knowledge-tree.html` 已经是 nginx 直接服务的静态文件：

```nginx
location = /ivd-knowledge-tree.html { root /usr/share/nginx/html; }
```

**不需要 token、不经过 Flask API、不校验身份**。完全符合"无需登录"的要求。

---

## 六、课程和 AI 对话的认证链路

### 课程访问认证链

```
用户访问 /c/{bid}
    │
    ├── nginx → proxy_pass → Next.js
    │
    ├── Next.js useUserStore
    │     ├── isInitialized? → 否 → 等待
    │     ├── isGuest?       → 是 → 302 → /login?redirect=当前路径
    │     └── isGuest?       → 否 → 正常渲染
    │
    └── API 调用时 optional_token_validation
          ├── 有 token → request.user = user_id ✅
          └── 无 token → request.user = None（API 返回 403/401）
```

### AI 对话访问认证链

```
用户调用 /api/chat/
    │
    ├── nginx → proxy_pass → Ark API
    │
    ├── 前端在请求中附带 Authorization: Bearer {token}
    │
    └── 无 token → 前端阻止发送请求
```

---

## 七、实施步骤

| 步骤 | 内容 | 时间 |
|------|------|------|
| 1 | 修改 `.env` → `LOGIN_METHODS_ENABLED=employee` | 1min |
| 2 | 重启 api 容器生效 | 1min |
| 3 | 验证登录页只显示工号登录 | 2min |
| 4 | 验证知识图谱可匿名访问 | 2min |
| 5 | 验证课程播放器跳转登录 | 2min |
| 合计 | | **~8min** |

---

## 八、与 RACI 矩阵的衔接

此配置变更不涉及角色权限修改：

| 活动 | RACI 中的责任方 | 说明 |
|------|---------------|------|
| 修改登录方式配置 | System Admin (R/A) | 环境变量变更 |
| 知识图谱匿名访问 | 系统默认 (R/A) | nginx 配置已固定 |
| 课程/AI对话登录验证 | 系统默认 (R/A) | 已有机制，无需变更 |
