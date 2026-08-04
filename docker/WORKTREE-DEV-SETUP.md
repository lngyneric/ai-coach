# Worktree Dev 环境配置手册

> 从零配置 dev 分支的独立开发环境（:8082），与 main（:8080）完全隔离
> 适用：/home/sysmex 单服务器双环境

## 0. 前置条件

```bash
# 已有 main 仓库
cd /home/sysmex/ai-shifu

# 创建 dev 分支 worktree（若已存在可跳过）
git worktree add /home/sysmex/worktrees/ai-shifu-dev dev
```

## 1. 初始化 worktree 配置

```bash
cd /home/sysmex/worktrees/ai-shifu-dev/docker

# 复制环境变量（含 AI_SHIFU_WEB_PORT=8082）
cp /home/sysmex/ai-shifu/docker/.env ./.
echo 'AI_SHIFU_WEB_PORT=8082' >> .env
```

## 2. 启动 dev 容器栈

```bash
cd /home/sysmex/worktrees/ai-shifu-dev/docker

# 启动完整 dev 栈（MySQL/api/cook-web/nginx）
docker compose -f docker-compose.dev.yml up -d
```

> 如果只需重建单个容器：
> ```bash
> docker compose -f docker-compose.dev.yml up -d ai-shifu-nginx-dev-dev    # nginx
> docker compose -f docker-compose.dev.yml up -d ai-shifu-cook-web-dev     # 前端
> docker compose -f docker-compose.dev.yml up -d ai-shifu-api-dev          # 后端
> ```

## 3. 验证 dev 环境

```bash
curl -s http://localhost:8082/api/config        # → {"apiBaseUrl":""}
curl -s -o /dev/null -w '%{http_code}' http://localhost:8082/login        # 200
curl -s -o /dev/null -w '%{http_code}' http://localhost:8082/courses      # 200
curl -s -o /dev/null -w '%{http_code}' http://localhost:8082/video-player.html   # 200
curl -s -o /dev/null -w '%{http_code}' http://localhost:8082/ivd-knowledge-tree.html # 200
```

## 4. 日常开发流程

### 修改 HTML/静态页面
```bash
# 编辑文件（worktree 目录）
vim /home/sysmex/worktrees/ai-shifu-dev/docker/xxx.html

# 使生效（HTML 挂载是实时的，改完即生效，无需重启 nginx）
# 如果改了 docker-compose.dev.yml 的挂载列表才需要：
docker compose -f docker-compose.dev.yml up -d ai-shifu-nginx-dev-dev
```

### 修改前端源码 (src/)
```bash
# 编辑源码 → 容器挂载 /app/src 是实时的
# Next.js dev 模式自动热更新，无需重启
# 若改了路由结构或想彻底清缓存：
docker restart docker-ai-shifu-cook-web-dev-1
```

### 修改后端 (Flask API)
```bash
docker restart docker-ai-shifu-api-dev-1
```

### 数据库
```bash
# dev 专用 MySQL（:3307）
docker exec docker-ai-shifu-mysql-dev-1 mysql -uroot -p$MYSQL_ROOT_PASSWORD ai-shifu

# 独立 MySQL（:3308，coach 专用）
docker exec coach-mysql mysql -uroot -pcoach123 coach_db
```

## 5. 提交与同步

```bash
cd /home/sysmex/worktrees/ai-shifu-dev
git add docker/ src/
git commit -m "描述"
# 需要同步到 main 时：
git push origin dev
cd /home/sysmex/ai-shifu
git merge dev
```

## 6. 隔离规则（铁律）

| 资源 | main 用 | dev 用 | 冲突 |
|------|---------|--------|------|
| nginx 端口 | 8080 | 8082 | ✅ 隔离 |
| nginx 配置 | `ai-shifu/docker/nginx.conf` | `worktrees/ai-shifu-dev/docker/nginx.dev.conf` | ✅ 隔离 |
| 静态 HTML | `ai-shifu/docker/*.html` | `worktrees/ai-shifu-dev/docker/*.html` | ✅ 隔离 |
| MySQL | `:3306` | `:3307` | ✅ 隔离 |
| coach-mysql | — | `:3308` | ✅ 独立 |

**禁止**：在 dev worktree 编辑 main 目录文件，反之亦然。

## 7. 常见修复

| 症状 | 处理 |
|------|------|
| 页面 404 | 检查 HTML 是否已挂载（compose 挂载列表） |
| JS 报旧代码错误 | nginx 已加 no-cache；浏览器 Ctrl+Shift+R |
| cook-web 崩溃循环 | `docker compose up -d ai-shifu-cook-web-dev`（NODE_OPTIONS 已移除 patched-watcher） |
| 端口被占 | `ss -tlnp | grep 8082` 查占用 |
| 外网访问不了 | 确认 nginx 绑 0.0.0.0（`ss -tlnp | grep 8082`） |

## Subagent 运行看板

- 访问：`http://<host>:8082/subagent-dashboard.html`（每 10s 自动刷新）
- 数据：`subagent-status.json`（采集自 `~/.reasonix/projects/*/sessions/*.goal-state.json` + `ps` + P0 产物）
- 手动刷新数据：`cd docker && python3 gen-subagent-status.py`
- 自动刷新：cron 需 root 权限（当前用户无 crontab 权限）；如部署到有权限环境可加
  `*/1 * * * * cd /home/sysmex/worktrees/ai-shifu-dev/docker && python3 gen-subagent-status.py >/dev/null 2>&1`
