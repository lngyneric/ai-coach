# 3000 端口冲突解决 · 状态与后续 TODOs

> 日期：2026-08-03

## 1. 问题根因

Host **3000 端口**被一个 **Express 静态服务**占用：

```
进程: node server.js  (PID 1272361)
位置: /home/sysmex/ai-coach/server.js  (2026-08-03 03:42 创建)
行为: 监听 *:3000，302 → /portal.html，serve AI-Coach 门户静态页
```

这是 **deprecated ai-coach 桥接系统**的残留进程（曾被重命名为 `.deprecated`，但被再次启动）。它占用了 host 3000，与容器生态隔离，且 serve 的是静态门户（与 nginx 提供的门户重复）。

## 2. 解决动作

| 步骤 | 操作 | 结果 |
|------|------|------|
| 1 | 定位占用者 | `lsof -i:3000` → Express server.js（X-Powered-By: Express） |
| 2 | 停止进程 | `kill 1272361` |
| 3 | 释放确认 | `ss -tlnp | grep :3000` → 空 |
| 4 | 生产验证 | `:8080/`=200, `:8080/admin`=200 |
| 5 | dev 验证 | `:8082/login`=200, `:8082/courses`=200 |

## 3. 解决后端口状态

```
0.0.0.0:8080   ← 生产 nginx（Next.js cook-web :3000 容器内部）
0.0.0.0:8082   ← dev nginx（dev cook-web :5000 容器内部）
127.0.0.1:5800 ← dev Flask API
127.0.0.1:3307 ← dev MySQL
0.0.0.0:3308   ← coach-mysql
:3000          ← 已释放（无监听）
```

> 注意：cook-web 容器内部端口 3000（`ai-shifu-cook-web:3000`）是 Next.js，位于 docker 网络内，**不占用 host 3000**。Host 3000 此前被 Express 残留占用，已释放。

## 4. 后续 TODOs

### P0 · 立即
- [ ] 防止 ai-coach Express 服务再次自启：检查 systemd/cron/启动脚本是否有 `node server.js` 引用
- [ ] 清理 `/home/sysmex/ai-coach/` 残留（server.js 已确认无用，移入 deprecated 或删除）

### P1 · 本周
- [ ] 生产门户确认：`http://10.32.16.47:8080/` 由 nginx→Next.js 提供（不是静态 Express）
- [ ] 校验生产 cook-web 容器 `ai-shifu-cook-web` 稳定性（3000 内部端口正常）
- [ ] 若需要独立静态门户服务，改用 nginx 静态路由（`/portal.html`），不再起 Express

### P2 · 规划
- [ ] 建立端口占用监控脚本（每 5 分钟检查 3000/8080/8082/5800/3307 占用）
- [ ] 把 `/home/sysmex/ai-coach/` 完整归档到 `services/deprecated/`，并从 PATH/启动链移除
- [ ] 更新 WORKTREE-DEV-SETUP.md 的"常见修复"章节，加入端口冲突处理

## 5. 验证命令

```bash
# 端口状态
ss -tlnp | grep -E ':3000|:8080|:8082'

# 生产
curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/
curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/admin

# dev
curl -s -o /dev/null -w '%{http_code}' http://localhost:8082/login
curl -s -o /dev/null -w '%{http_code}' http://localhost:8082/courses
```
