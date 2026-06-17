# 开发 → 生产推送机制

> 基于当前架构的轻量级方案 | 2026-06

---

## 一、总体架构

```
┌─────────────────┐     git push     ┌──────────────────┐
│   开发机 (Ubuntu) │ ──────────────→ │  GitHub (ai-coach) │
│   Dev Environment │                  │    main 分支      │
└─────────────────┘                  └────────┬─────────┘
                                              │ git pull
                                              ▼
                                     ┌──────────────────┐
                                     │  生产机 (macOS)    │
                                     │  Prod Environment  │
                                     │  bash deploy.sh    │
                                     └──────────────────┘
```

**核心原则**：
- 所有代码改动通过 **git push/pull** 传递
- `.env` 不经过 git，各环境独立维护
- `deploy.sh` 是连接代码和运行容器的桥梁
- 生产机主动拉取（pull model），不做自动推送

---

## 二、分支策略

```
main ─── 稳定版本，用于生产
   │
   ├── dev ─── 日常开发
   ├── feat/xxx ─── 功能分支
   └── hotfix/xxx ─── 紧急修复
```

| 分支 | 用途 | 谁推送 | 自动部署 |
|------|------|--------|---------|
| `main` | 生产就绪代码 | Dev → PR → 合并 | ❌ 手动 pull |
| `dev` | 日常开发 | Dev 直接推送 | ❌ 仅在开发机运行 |
| `feat/*` | 功能开发 | Dev 直接推送 | ❌ |

---

## 三、完整流程

### 日常开发 → 部署

```bash
# ── 开发机（Ubuntu）──

# 1. 基于 dev 分支开发
git checkout dev
# 修改代码...
git add .
git commit -m "feat: xxx"

# 2. 本地验证（在开发机容器中运行）
bash deploy.sh          # 注入到开发容器
# 验证功能正常...

# 3. 合并到 main 并推送
git checkout main
git merge dev
git push origin main

# ── 生产机（macOS）──

# 4. 拉取最新代码
ssh user@mac-prod
cd /path/to/ai-coach
git pull origin main

# 5. 部署到生产容器
bash deploy.sh

# 6. 验证
curl -s https://prod-domain/courses/ | head -5
```

---

## 四、`.env` 环境管理

| 环境 | 位置 | 管理方式 |
|------|------|----------|
| **开发机** | `docker/.env` | 本地维护，不提交 git |
| **生产机** | `docker/.env` | 首次手动配置，后续只更新变更项 |

**生产机 `.env` 关键差异**：

```bash
# 开发机（可调试）
AAD_BYPASS="1"
LOG_LEVEL="debug"

# 生产机（安全加固）
AAD_BYPASS=""              # 必须通过真实 AAD 验证
LOG_LEVEL="warning"
SECRET_KEY="<生产随机密钥>"  # 必须与开发机不同
```

建议在 git 中维护一个 `.env.example.prod` 模板（不含真实密钥）：

```bash
# .env.example.prod — 生产环境配置模板
# 复制为 .env 后填写实际值
LOGIN_METHODS_ENABLED=employee
AAD_AUTH_URL=http://10.40.20.195:8082
AAD_BYPASS=
SECRET_KEY=<替换为生成值>
ARK_API_KEY=<替换为实际密钥>
VOLCENGINE_TTS_API_KEY=<替换为实际密钥>
```

---

## 五、部署脚本差异化

生产机的 `deploy.sh` 可以加一个 `--prod` 参数，执行额外的生产检查：

```bash
# deploy.sh 新增:
if [ "${1:-}" = "--prod" ]; then
    echo "  running production checks..."
    # 检查 SECRET_KEY 是否已变更
    # 检查 AAD_BYPASS 是否为关
    # 检查日志级别
fi
```

---

## 六、快速部署命令（生产机操作）

将常用操作写成 Makefile 或简单的 deploy-prod.sh：

```bash
#!/bin/sh
# deploy-prod.sh — 一键拉取 + 部署
set -e
echo "=== Pulling latest code ==="
git pull origin main

echo "=== Deploying ==="
bash deploy.sh --prod

echo "=== Verifying ==="
curl -s -o /dev/null -w "API: %{http_code}\n" https://localhost/api/portal/dashboard
curl -s -o /dev/null -w "Courses: %{http_code}\n" https://localhost/courses/
echo "=== Done ==="
```

---

## 七、注意事项

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 开发机和生产机 `.env` 不一致 | 🟡 | 维护 `.env.example.prod` 模板，每季度巡检 |
| deploy.sh 依赖本地文件路径 | 🟢 | 所有路径都是相对路径，git 仓库结构一致 |
| 容器镜像版本不一致 | 🟡 | 生产机固定 `image: aishifu/ai-shifu-api:v2.0.1` |
| 生产机 443 端口需 sudo | 🟢 | 改为 8443 端口 + nginx 反向代理 |
| 生产机 pull 后忘记 deploy | 🟢 | `deploy-prod.sh` 脚本一步完成 |
