# 环境隔离规则 · main vs dev（同一台服务器）

> 目标：修改 dev 配置不影响 main，杜绝 API 访问冲突

## 1. 当前冲突（已确认）

| 项 | main 容器 | dev 容器 | 冲突 |
|----|----------|---------|------|
| nginx 配置 | `/home/sysmex/ai-shifu/docker/nginx.conf` | `/home/sysmex/ai-shifu/docker/nginx.dev.conf` | ⚠️ dev 挂载了 main 目录 |
| 静态 HTML | `/home/sysmex/ai-shifu/docker/*.html` | 同左（同一目录） | 🔴 完全共享 |
| Flask API | `ai-shifu-api:5800`(容器内) | `127.0.0.1:5800`(host) | ⚠️ host 5800 被 dev 占用 |
| MySQL | `127.0.0.1:3306` | `127.0.0.1:3307` | ✅ 已隔离 |
| 端口 | 8080/443/80 | 8082 | ✅ 已隔离 |

## 2. 隔离目标矩阵

| 资源 | main 路径 | dev 路径 | 隔离方式 |
|------|----------|---------|---------|
| nginx 配置 | `ai-shifu/docker/nginx.conf` | `worktrees/ai-shifu-dev/docker/nginx.dev.conf` | 各自挂载自己的文件 |
| 静态 HTML | `ai-shifu/docker/*.html` | `worktrees/ai-shifu-dev/docker/*.html` | dev 挂载 worktree 目录 |
| Flask API | 容器内 `:5800`（无 host 映射） | host `127.0.0.1:5800` | main 不暴露 host 端口 |
| MySQL | `:3306` | `:3307` | 独立容器 |
| coach-mysql | — | `:3308` | 独立容器 |

## 3. 修改规则（铁律）

1. **改 dev 的 nginx/HTML** → 只改 `/home/sysmex/worktrees/ai-shifu-dev/docker/`，然后 `git -C worktrees/ai-shifu-dev commit`
2. **改 main 的 nginx/HTML** → 只改 `/home/sysmex/ai-shifu/docker/`，然后 `git -C ai-shifu commit`
3. **禁止**在 dev worktree 中编辑 main 目录的文件，反之亦然
4. **静态 HTML 新增文件** → 先同步到两个 worktree 各自的 docker 目录，再分别提交
5. **迁移 SQL** → dev 先执行（幂等）→ 验证 → main 执行
6. **API 端口** → main 保持容器内 5800；dev 独占 host 5800；如需 main 暴露改 5801

## 4. 执行清单

- [ ] 修正 dev docker-compose.dev.yml：nginx 挂载路径指向 worktree docker 目录
- [ ] 同步新 HTML（portal/digital-human/brand-vi/dashboard 等）到 dev worktree
- [ ] dev worktree 提交新文件
- [ ] 重建 dev nginx 容器验证隔离生效
- [ ] 验证 main 8080 与 dev 8082 独立工作
