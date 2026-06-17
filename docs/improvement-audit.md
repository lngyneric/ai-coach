# ai-coach 项目改善点全面审计

> 更新于 2026-06-17 | 基于代码 + 数据库 + 运行状态

---

## 已完成的改善（v2.1 核心上线版）

| 改善项 | 状态 |
|--------|------|
| TTS 切换 ark agent plan（X-Api-Key + /plan/ 端点） | ✅ |
| 7 张新数据库表（学员档案/带教/任务/通知） | ✅ |
| 17 个 API 路由（学员/导师/管理员三端） | ✅ |
| 统一登录页（废弃 sysmex-login + course-entry） | ✅ |
| `LOGIN_METHODS_ENABLED=employee`（仅 AAD 登录） | ✅ |
| 删除 employee 自动授权（默认 Learner 角色） | ✅ |
| 角色管理 API（grant/revoke creator/operator） | ✅ |
| 导师工作台独立页面 `/mentor/` | ✅ |
| 课程分类 API（`GET /api/portal/courses?category=`） | ✅ |
| 登出页 + API（`/api/user/logout`） | ✅ |
| 学员看板首页（统计/待办/成长曲线/AI建议） | ✅ |
| 代码/文档同步至飞书（共 6 篇） | ✅ |

---

## 📋 待改善点（按优先级排列）

### 🔴 P0 — 上线阻塞项（4 项）

| # | 问题 | 当前状况 | 建议方案 | 预估 |
|---|------|---------|---------|------|
| **1** | **容器重建导致代码丢失** | `docker cp` 进去的 Python 文件在 `docker compose up -d --force-recreate` 后全部丢失。已发生的丢失包括：`employee.py` 自动授权删除、`listen_element_types.py` 修复、`learning_portal/` 模块、`celery_app.py`、`config.py` 等 | **创建 `deploy.sh` 脚本**，一键将本地源码复制到容器 + HUP 重载。或者在 `docker-compose.yml` 中用 bind mount 挂载源码目录覆盖容器内文件 | 1h |
| **2** | **学习门户数据库无初始化数据** | 7 张新表全空（0 行）。带教阶段、验收项模板、学员档案等均无任何数据，管理后台无法使用 | **创建种子数据脚本**：插入 mentorship_phases（三阶段）、mentorship_checklist（常见验收项）。`docker exec` 执行一次即可 | 30min |
| **3** | **课程未绑定到培训分类** | 已创建 4 个培训分类（新人入学/学分制带教/小灶教学/领导力课程），但 0 门课程绑定。当前课程只绑定了旧分类（医学检验/AI基础等） | 按课程名称/描述，通过 `shifu_category_map` 表绑定课程到对应培训分类。已有 37 门启用 TTS 的课程可用 | 1h |
| **4** | **容器内 listen_element_run_stream.py 有脏代码** | Docker 镜像内置的 `listen_element_run_stream.py` 第 427 行传了 `listen=True`，但第 226/845 行的 `is_renderable` 值也被改为 `True`（上游是 `False`）。这可能是镜像构建时混入了未完成的修改 | 覆盖容器内该文件为磁盘上干净的版本（我们的磁盘文件已通过 `**kwargs` 兼容 fix） | 5min |

### 🟡 P1 — 功能完善（6 项）

| # | 问题 | 当前状况 | 建议方案 | 预估 |
|---|------|---------|---------|------|
| **5** | **"固定预览内容为课程"功能缺失** | `PreviewCopyButton` 只支持手动复制粘贴到编辑器，没有一键将 LLM 生成内容写入草稿的功能 | 开发 `POST /api/learn/preview/save-generated` API + 前端按钮 | 4-6h |
| **6** | **上游 `listen_element_types.py` 的 HTML 检测未合并** | 上游有 `_strip_non_speech_markup` + `_text_has_speakable_content` 精确判断，我们是简单的 `bool(content_text)` | 合入上游的 HTML 文字检测函数 | 30min |
| **7** | **Docker 镜像未包含我们的改动** | 当前使用上游构建的 `aishifu/ai-shifu-api:v2.0.1` 镜像，我们的所有 Python 改动都靠 `docker cp` 临时注入 | **方案 A**（推荐）：用 bind mount 覆盖关键源码目录。**方案 B**：fork 后自行构建镜像 | 2h |
| **8** | **celery beat 定时任务未验证** | 4 个定时任务已注册（每日待办/评分催办/阶段截止/转正预检），但从未验证是否真正触发 | 手动运行一次各任务，检查日志输出 | 30min |
| **9** | **SECURITY_KEYS 和生产环境配置缺失** | `SECRET_KEY=ai-shifu`（默认值！）、`AAD_BYPASS` 未配置、`ARK_API_KEY` 硬编码在 `.env` 中 | 生成强随机 `SECRET_KEY`，配置 `AAD_AUTH_URL` 和 `AAD_BYPASS=False` | 30min |
| **10** | **导师评分 UI 未实现** | 导师工作台显示"待评分"和"去评分"按钮，但评分需要通过 API 调用（`POST /api/portal/mentorship/items/{bid}/score`），没有前端表单 | 在导师工作台增加评分弹窗表单（打分 + 评语） | 3h |

### 🟢 P2 — 体验优化（6 项）

| # | 问题 | 当前状况 | 建议 | 预估 |
|---|------|---------|------|------|
| **11** | **废弃页面仍被 nginx 挂载** | `course-entry.html` 和 `sysmex-login.html` 仍在 `docker-compose.yml` 中挂载，但已被 `login.html` 替代 | 从 compose 中移除挂载（仅保留文件不删除） | 5min |
| **12** | **Nginx `nginx_current.conf` 未同步** | 备份配置文件未包含新路由（`/mentor/`、`/login`、`/courses/` 等） | 用当前 `nginx.conf` 覆盖备份 | 5min |
| **13** | **`docker-compose.yml` 中的 `&id001` anchor 有重复** | `LOGIN_METHODS_ENABLED` 和 `VOLCENGINE_TTS_API_KEY` 同时出现在 `&id001` anchor 和 api 的 `environment:` 中 | 统一使用 `&id001` anchor，避免散落 | 10min |
| **14** | **没有 `.gitignore` 对 `docker/.env` 的保护** | `.env` 文件包含 API Key 等敏感信息，但未被 gitignore | 确认 `.env` 已在 `.gitignore` 中 | 2min |
| **15** | **日志增长不受限** | `/app/logs/ai-shifu.log` 无轮转配置，长期运行会占满磁盘 | 配置 logrotate 或 Flask 日志轮转 | 30min |
| **16** | **AI 学习建议是硬编码文案** | 看板中的 AI 建议区域显示固定文案，未基于实际学习数据生成 | 后续接入 AI 推荐引擎 | 待定 |

---

## 改善建议汇总表

| 优先级 | 数量 | 总预估 |
|--------|------|--------|
| 🔴 P0 上线阻塞 | 4 项 | **~3h** |
| 🟡 P1 功能完善 | 6 项 | **~11h** |
| 🟢 P2 体验优化 | 6 项 | **~1h** |
| **合计** | **16 项** | **~15h** |

### 建议立即处理（P0）的实施顺序

```
P0-4 → P0-1 → P0-2 → P0-3
(容器脏代码) (持久化脚本) (种子数据) (课程分类绑定)
```

### 注意事项

1. **持久化是核心问题**：在没解决 `docker cp` 丢失问题前，容器一重启所有 Python 改动都会消失。建议 **立即写 `deploy.sh` 脚本**，这才是其他所有改动能留存的基础。
2. **上游代码持续更新**：上游 `dev` 分支已有 8 个新提交，`ops/fix-*` 分支有 3 个新修复，与 TTS/预览相关。建议定期（每周）拉取评估。
3. **不要合并 Next.js 前端**：cook-web 是预构建的 Docker 镜像，合入代码也无法生效，需重建整个镜像。
