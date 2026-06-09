#!/bin/bash
# ============================================================
# ai-shifu MySQL 数据库每日备份脚本
# 用法: bash scripts/db_backup.sh
# 定时: 每天凌晨 1:00 由 cron 触发
# ============================================================

set -euo pipefail

BACKUP_DIR="/home/sysmex/ai-shifu/docker/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M")
LOG_FILE="/home/sysmex/ai-shifu/docker/backups/backup.log"
MYSQL_USER="root"
MYSQL_PASS="ai-shifu"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_DATABASE="ai-shifu"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

BACKUP_FILE="${BACKUP_DIR}/${MYSQL_DATABASE}_${TIMESTAMP}.sql.gz"

log "开始备份: ${MYSQL_DATABASE} → ${BACKUP_FILE}"

# 执行备份
if docker exec ai-shifu-mysql mysqldump \
    -u"$MYSQL_USER" \
    -p"$MYSQL_PASS" \
    -h"$MYSQL_HOST" \
    -P"$MYSQL_PORT" \
    --databases "$MYSQL_DATABASE" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --quick \
    --lock-tables=false \
    2>> "$LOG_FILE" | gzip > "$BACKUP_FILE"; then

    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✅ 备份成功: ${BACKUP_FILE} (${FILE_SIZE})"
else
    log "❌ 备份失败: ${MYSQL_DATABASE}"
    exit 1
fi

# 清理旧备份（保留 RETENTION_DAYS 天）
log "清理 ${RETENTION_DAYS} 天前的备份..."
find "$BACKUP_DIR" -name "${MYSQL_DATABASE}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
DELETED=$(find "$BACKUP_DIR" -name "${MYSQL_DATABASE}_*.sql.gz" -type f -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
log "清理完成，剩余备份文件数: $(ls -1 ${BACKUP_DIR}/*.sql.gz 2>/dev/null | wc -l)"

# 输出最近一次备份的信息
LATEST=$(ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    log "最新备份: $(basename $LATEST) ($(du -h $LATEST | cut -f1))"
fi

exit 0
