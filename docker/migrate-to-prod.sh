#!/bin/bash
# ═══════════════════════════════════════════════
#  migrate-to-prod.sh — 将现有数据迁移到生产环境
#  1. 导出当前 MySQL 数据
#  2. 导入到新的生产 MySQL
#  3. 复制 Redis 数据（可选）
#
#  使用: bash migrate-to-prod.sh
# ═══════════════════════════════════════════════
set -e

PROD_COMPOSE="docker-compose.prod.yml"
BACKUP_FILE="/tmp/ai-shifu-prod-migration-$(date +%Y%m%d-%H%M%S).sql"

echo "=== 步骤 1: 导出当前数据库 ==="
docker exec ai-shifu-mysql mysqldump -u root -pai-shifu --databases ai-shifu 2>/dev/null > "$BACKUP_FILE"
echo "导出完成: $(du -h "$BACKUP_FILE" | cut -f1)"

echo ""
echo "=== 步骤 2: 启动生产容器（含独立 DB/Redis）==="
cd /home/sysmex/ai-shifu/docker
docker compose -f "$PROD_COMPOSE" up -d ai-shifu-mysql-prod ai-shifu-redis-prod
echo "等待 MySQL 就绪..."
for i in $(seq 1 30); do
  if docker exec ai-shifu-mysql-prod mysqladmin ping -u root -pai-shifu --silent 2>/dev/null; then
    echo "MySQL 就绪"
    break
  fi
  sleep 2
done

echo ""
echo "=== 步骤 3: 导入数据到生产数据库 ==="
docker exec -i ai-shifu-mysql-prod mysql -u root -pai-shifu 2>/dev/null < "$BACKUP_FILE"
echo "导入完成"

echo ""
echo "=== 步骤 4: 启动全部生产服务 ==="
docker compose -f "$PROD_COMPOSE" up -d
echo "生产环境已启动"

echo ""
echo "=== 验证 ==="
echo "HTTP:  http://10.32.16.47:8081/"
echo "HTTPS: https://10.32.16.47:444/  (或 https://eu.sysmex.com.cn:444/)"

echo ""
echo "=== 清理 ==="
rm -f "$BACKUP_FILE"
echo "临时备份已清理"
echo ""
echo "✅ 迁移完成"
