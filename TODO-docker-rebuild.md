# Docker 镜像重建 TODO

## 背景

大纲树查询缓存优化已通过 `docker cp` 热部署到运行中的 `ai-shifu-api` 容器，代码如下：

| 文件 | 改动 |
|------|------|
| `src/api/flaskr/service/learn/learn_funcs.py` | +98 行，大纲树缓存（Redis, 5min TTL） |
| `src/api/flaskr/service/shifu/shifu_publish_funcs.py` | 发布时失效缓存 |
| `src/api/flaskr/service/shifu/shifu_outline_funcs.py` | 增/改/删/重排大纲时失效缓存 |
| `src/api/flaskr/service/shifu/shifu_mdflow_funcs.py` | 保存 MDFlow 时失效缓存 |
| `src/api/flaskr/common/cache_provider.py` | `FallbackCacheProvider.get()` 内存缓存回退修复 |

## 为什么需要重建

`docker cp` 只修改了运行时容器的文件，**容器重启后这些修改会丢失**（回退到镜像内的旧代码）。

## 操作步骤（维护窗口执行）

```bash
cd /home/sysmex/ai-shifu

# 1. 确认所有修改已提交到 git
git log --oneline -5

# 2. 重新构建 API 镜像
docker compose -f docker/docker-compose.dev.yml build ai-shifu-api

# 3. 重建并重启（不中断其他服务）
docker compose -f docker/docker-compose.dev.yml up -d --no-deps ai-shifu-api

# 4. 验证新容器运行正常
docker logs --tail 20 ai-shifu-api

# 5. 验证缓存功能正常
curl -s "http://localhost:8080/api/learn/shifu/<课程ID>/outline-item-tree" | head -c 200
```

## 验证清单

- [ ] API 容器启动正常
- [ ] Redis 缓存写入正常（`docker exec ai-shifu-redis redis-cli KEYS "query:*"`）
- [ ] 大纲树加载正常
- [ ] 发布课程后缓存自动失效

---

## 2026-08-06 追加：PDF 水印品牌名 "AI 师傅" → "AI-Coach"

| 文件 | 改动 |
|------|------|
| `src/api/flaskr/service/learn/pdf_export.py` | 第 31 行 `PDF_EXPORT_BRAND_NAME = "AI 师傅"` → `"AI-Coach"` |

影响：
- PDF 水印 brand_name（`pdf_export.py:161` 构建 `PdfExportWatermark`）
- PDF 导出文件名前缀（`pdf_export.py:1036` `build_pdf_file_name`）

已通过 docker cp 同步到 dev 运行容器并重启：
- `docker-ai-shifu-api-dev-1`
- `docker-ai-shifu-celery-worker-dev-1`
- `docker-ai-shifu-celery-beat-dev-1`

验证（dev 环境）：
- 容器内 md5 = `e59d2aeb268b1646b7349e4027da6b78`，第 31 行 = `"AI-Coach"`
- 真实导出 `export-pdf` 返回 200 + application/pdf
- Content-Disposition 文件名 = `AI-Coach--AI师傅教学引导--从这里开始.pdf`
- 真实 PDF 水印文本 = `AI-Coach / AI师傅教学引导 / 从这里开始`

说明：worktree（dev 分支）已改，后续镜像重建自动包含。
