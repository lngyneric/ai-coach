# 上游差异分析 & 合并建议

> 对比: 本地代码 vs upstream/dev02 + upstream/dev | 2026-06

---

## 一、差异清单

### 差异 A：`listen_element_types.py` — 精确的 HTML 可读文字检测

| 对比项 | 上游 (dev02) | 我们 |
|--------|-------------|------|
| `_default_is_speakable` | 仅 TEXT 类型 | **TEXT + HTML** |
| `_text_has_speakable_content` | ✅ **有** — 剥掉 HTML 标签后检测是否有中英文文字 | ❌ 无 |
| `_strip_non_speech_markup` | ✅ **有** — 移除 style/script/comment/标签 | ❌ 无 |

**上游优点**：`"<div><style>...</style><p>你好</p></div>"` → 剥掉标签后检测到"你好"→ `True`。而我们直接 `bool(content_text)` 对纯标签内容也会返回 `True`，导致无文字可读时仍触发 TTS。

**建议**：✅ **合并** — 引入上游的 `_strip_html` 工具函数 + 保持我们的 **TEXT+HTML** 判断

### 差异 B：`listen_element_run_stream.py` — `_default_is_renderable` 参数

| 对比项 | 上游 | 我们磁盘 | 容器内（奇怪） |
|--------|------|---------|-------------|
| 调用方式 | `._renderable(state.element_type)` | 同上 ✅ | **有 `listen=True`** ❌ |

**Docker 镜像内置了某次构建的旧代码**，磁盘文件是干净的。我们的 `**kwargs` 修复已经兼容了。

**建议**：✅ **容器重启后需重新 docker cp**，或者把这个文件纳入持久化挂载

### 差异 C：`volcengine_provider.py` — TTS 认证方式（截然不同）

| 对比项 | 上游 | 我们 |
|--------|------|------|
| URL | `/api/v3/tts/bidirection` | `/api/v3/plan/tts/bidirection` |
| 认证头 | `X-Api-App-Key` + `X-Api-Access-Key` | `X-Api-Key` |
| 环境变量 | `VOLCENGINE_TTS_APP_KEY` + `VOLCENGINE_TTS_ACCESS_KEY` | `VOLCENGINE_TTS_API_KEY` |

**建议**：❌ **不合并** — 上游用的是旧的 code plan 认证方式，我们的 ark agent plan 认证是正确的

### 差异 D：`__init__.py` (TTS auto-detect)

| 对比项 | 上游 | 我们 |
|--------|------|------|
| volcengine 检测 | `ARK_ACCESS_KEY_ID` + `ARK_SECRET_ACCESS_KEY` | `VOLCENGINE_TTS_API_KEY` |
| volcengine_http | `VOLCENGINE_TTS_APP_KEY + ACCESS_KEY + CLUSTER_ID` | 同上 |

**建议**：✅ **部分合并** — 保留我们的 `VOLCENGINE_TTS_API_KEY` 检测，上游的其他逻辑不变

---

## 二、合并建议汇总

| 文件 | 操作 | 原因 | 优先级 |
|------|------|------|--------|
| `listen_element_types.py` | **合并上游** | 引入 `_strip_non_speech_markup` + `_text_has_speakable_content`，保留 TEXT+HTML 判断 | 🔴 P0 |
| `listen_element_run_stream.py` | **保持现状** | 磁盘文件已正确，容器内异常是镜像内置旧代码问题 | 🟡 P1 |
| `volcengine_provider.py` | **保留我们** | 上游用旧认证（不兼容 ark agent plan） | ✅ 已定 |
| `__init__.py` (TTS) | **保留我们** | 只加了 `VOLCENGINE_TTS_API_KEY` 检测，无冲突 | ✅ 已定 |
| `learn_funcs.py` | **可合并** | 但功能未变，非必要 | 🟢 低 |
| `cook-web/**/*` (Next.js) | **不合并** | 无法增量构建，需要整个重建 Docker 镜像 | 📋 待定 |

---

## 三、建议的执行顺序

```
Phase A: 合并 listen_element_types.py（~30min）
  ├── 引入 _strip_non_speech_markup()
  ├── 引入 _text_has_speakable_content()
  ├── 引入 _is_markup_only_text_fragment()
  ├── 修改 _default_is_speakable → 使用 _text_has_speakable_content
  ├── 修改 _normalized_is_speakable → 保持 TEXT+HTML
  └── 更新 _default_is_renderable → 加 **kwargs

Phase B: 文件持久化（~15min）
  ├── 将修改后的核心 Python 文件 git commit
  ├── 编写 deploy.sh 一键复制到容器
  └── 验证容器重启后改动不丢失

Phase C: 开发"固定预览内容"功能（~4-6h）
  ├── 后端 API: POST /api/learn/preview/save-generated
  ├── 预览页面: "固定为课程内容"按钮
  └── 保存后跳转编辑器
```
