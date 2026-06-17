# 身份验证系统 — 服务端分析报告

> 仅从服务端认证与授权机制分析，不涉及前端页面差异

---

## 一、认证体系全景

### 1.1 已注册的认证 Provider（6个）

| Provider | 注册文件 | 验证方式 | 前端入口 |
|----------|----------|----------|----------|
| `employee` | `providers/employee.py` | 工号+密码 → 内网 AAD 服务器校验 | 静态页 `login.html` / `course-entry.html` |
| `password` | `providers/password.py` | 邮箱/手机号 + 本地密码校验 | Next.js 登录页（被 nginx 阻断） |
| `phone` | `providers/phone.py` | 手机号 + 短信验证码 | Next.js 登录页 |
| `email` | `providers/email.py` | 邮箱 + 邮件验证码 | Next.js 登录页 |
| `google` | `providers/google.py` | Google OAuth | Next.js 登录页 |
| `wecom` | `providers/wecom.py` | 企业微信 OAuth | 独立入口 |

### 1.2 Provider 无关的统一层

| 组件 | 路径 | 说明 |
|------|------|------|
| `AuthProvider` 基类 | `auth/base.py` | 统一基类，所有 Provider 继承 |
| `AuthResult` | `auth/base.py:65` | 统一认证输出：`UserInfo` + `UserToken` |
| `generate_token()` | `utils.py:74` | **统一签发** — 所有 Provider 调用同一函数 |
| `validate_user()` | `utils.py` | **统一验证** — 无差别对待所有 token |
| `optional_token_validation` | `route/user.py:73` | **统一中间件** — parsing token 逻辑不分来源 |
| `token_store` | `token_store.py` | 统一 token 存储，共享黑名单 |

---

## 二、核心结论：认证层是统一的

### 2.1 Token 无差别

```
任何 Provider 签发 → generate_token() → jwt(token, user_id)
                                       → token_store.set(user_id, token)
                                       → 返回字符串 token

任何 API 验证 → optional_token_validation()
            → token_store.get(token) → user_id
            → request.user = user_id ✅
```

**Token 格式、签发、存储、验证路径完全一致。不存在"两套认证体系"。**

### 2.2 但授权策略有重大差异

| Provider | 用户创建 | 自动授权 | 使用场景 |
|----------|----------|----------|----------|
| `employee` | `ensure_user_for_identifier()` | **自动 `mark_user_roles(is_creator=True, is_operator=True)`** | 静态登录页 |
| `password` | —（用户已存在） | **不自动授权** | Next.js 登录页 |
| `phone` | `ensure_user_for_identifier()` | **不自动授权** | Next.js 登录页 |
| `email` | `ensure_user_for_identifier()` | **不自动授权** | Next.js 登录页 |

**关键代码**（`employee.py:139-144`）：

```python
# Auto-grant creator + operator roles for all employee-login users.
# Employees authenticate against enterprise AAD and are trusted.
needs_roles = not bool(aggregate.is_creator) or not bool(aggregate.is_operator)
if needs_roles:
    mark_user_roles(aggregate.user_bid, is_creator=True, is_operator=True)
```

**效果**：任何通过工号+密码登录的用户 → 自动成为 creator（课程创建者）+ operator（系统管理员）。

---

## 三、路由上的差异

### 3.1 `login_employee` API（静态页使用）

```python
# route/user.py:937-946
resp = make_response(make_common_response(auth_result.token))
resp.set_cookie("token", auth_result.token.token, httponly=False, samesite="Lax", path="/")
return resp
```

- ✅ 返回 JSON + 设置 cookie
- ✅ 静态页面直接读取 cookie 认证

### 3.2 `login_password` API（Next.js 使用）

```python
# route/user.py:857
return make_common_response(auth_result.token)
```

- ✅ 仅返回 JSON，不设置 cookie
- ✅ Next.js 前端由 JS 写入 localStorage 和 cookie

**差异本质**：cookie 由谁设置的问题 —— 后端设置 vs 前端设置。两种方式生成的 token 完全相同，只是传输通道不同。

---

## 四、问题定性

### 4.1 认证层（Authentication）：✅ 统一

```
Token 签发     → generate_token()       ✅
Token 格式     → jwt(UserToken)         ✅  
Token 存储     → token_store            ✅
Token 验证     → validate_user()        ✅
Token 中间件   → optional_token_validation ✅
```

**结论**：不存在两套认证体系。所有 Provider 走同一套 token 机制。

### 4.2 授权层（Authorization）：⚠️ 有差异

| Provider | 自动成为 admin | 影响 |
|----------|---------------|------|
| employee | ✅ 是（自动 `creator+operator`） | 所有工号登录用户都是管理员 |
| 其他 5 个 | ❌ 否 | 普通用户权限 |

**风险**：如果项目是面向全体员工的在线学习平台，绝大多数用户应该是"学员"而非"管理员"——`employee` 的自动授权过于宽松。

### 4.3 Cookie 设置方案：🟢 可优化

两套 API 最终都读写同一个 `token` cookie，只是设置时机不同。前端统一通过 `courses.html` 等静态页面登录时，cookie 由后端设置（`login_employee`）；通过 Next.js 登录时，cookie 由前端 JS 设置（`login_password`）——两种方式最终结果一致。

---

## 五、建议措施

### 5.1 必须做：修复授权逻辑

删除 `employee.py` 中的自动授权（或改为条件授予）：

```diff
# employee.py
- needs_roles = not bool(aggregate.is_creator) or not bool(aggregate.is_operator)
- if needs_roles:
-     mark_user_roles(aggregate.user_bid, is_creator=True, is_operator=True)
```

改为：员工登录默认只给学员角色，creator 和 operator 通过管理后台手动分配。

### 5.2 可选的统一：cookie 设置

让 `login_password` 也设置 cookie，消除两个 API 的行为差异：

```python
# 在 login_password 末尾加上
resp = make_response(make_common_response(auth_result.token))
resp.set_cookie("token", auth_result.token.token, httponly=False, samesite="Lax", path="/")
return resp
```

这样无论通过哪个 API 登录，cookie 总是由后端设置，统一且安全。

### 5.3 前端登录页建议

| 废弃 | 保留 | 新建 | 说明 |
|------|------|------|------|
| `sysmex-login.html` | — | — | 功能被 `login.html` 替代 |
| `course-entry.html` | — | — | 同上 |
| — | `login.html` | **新建** | 统一登录页，`login_employee` API |

---

## 六、总结

```diff
- ❌ 认为：两套登录页产生了两套认证体系
+ ✅ 事实：服务端认证体系是统一的，6 个 Provider 共享 token 机制
- ⚠️ 问题：employee 自动授权过于宽松，所有工号登录用户都成为管理员
+ ✅ 修复：去掉 employee 的自动授权即可消除风险
```

关键就一件事：**删除 `employee.py` 中的第 139-144 行的自动授权代码**，让所有用户登录后默认获得学员权限，需要管理权限的走后台手动分配。
