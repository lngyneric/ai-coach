#!/bin/bash
# ============================================================
# ai-shifu MySQL 数据库备份脚本（支持 prod / dev 多库）
# 用法:
#   bash scripts/db_backup.sh                     # 备份 prod 库（ai-shifu-mysql / ai-shifu）
#   bash scripts/db_backup.sh --dev               # 备份 dev 库（docker-ai-shifu-mysql-dev-1 / ai-shifu_dev）
#   bash scripts/db_backup.sh --all               # 备份 prod + dev 两个库
#   bash scripts/db_backup.sh --container <名称> --database <库> --dir <目录>
# 定时: cron 每天凌晨 1:00 触发（示例见文件末尾注释）
# ============================================================

set -euo pipefail

# ── 默认值（prod 容器）──
BACKUP_DIR="/home/sysmex/ai-shifu/docker/backups"
MYSQL_USER="root"
MYSQL_PASS="ai-shifu"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
RETENTION_COUNT=14        # 每个库保留的备份份数
LOG_FILE="$BACKUP_DIR/backup.log"
MODE="prod"

# ── 解析参数 ──
while [ $# -gt 0 ]; do
    case "$1" in
        --dev) MODE="dev"; shift ;;
        --all) MODE="all"; shift ;;
        --container) MYSQL_CONTAINER="$2"; shift 2 ;;
        --database) MYSQL_DATABASE="$2"; shift 2 ;;
        --dir) BACKUP_DIR="$2"; LOG_FILE="$BACKUP_DIR/backup.log"; shift 2 ;;
        --retention) RETENTION_COUNT="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 2 ;;
    esac
done

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

backup_one() {
    local container="$1"
    local database="$2"
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M")
    local backup_file="${BACKUP_DIR}/${database}_${timestamp}.sql.gz"

    log "开始备份: ${container}:${database} → ${backup_file}"

    # 容器不存在则跳过（如 dev 容器未启动）
    if ! docker inspect "$container" >/dev/null 2>&1; then
        log "  ⚠️ 容器 ${container} 不存在，跳过 ${database}"
        return 0
    fi

    if docker exec "$container" mysqldump \
        -u"$MYSQL_USER" \
        -p"$MYSQL_PASS" \
        -h"$MYSQL_HOST" \
        -P"$MYSQL_PORT" \
        --databases "$database" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --quick \
        --lock-tables=false \
        2>> "$LOG_FILE" | gzip > "$backup_file"; then

        local file_size
        file_size=$(du -h "$backup_file" | cut -f1)
        log "  ✅ 备份成功: ${backup_file} (${file_size})"
    else
        log "  ❌ 备份失败: ${container}:${database}"
        rm -f "$backup_file" 2>/dev/null || true
        return 1
    fi

    # 按份数保留：只留最近 RETENTION_COUNT 份
    local extra_count
    extra_count=$(ls -1t "${BACKUP_DIR}/${database}_"*.sql.gz 2>/dev/null | tail -n +$((RETENTION_COUNT + 1)) | wc -l)
    if [ "$extra_count" -gt 0 ]; then
        ls -1t "${BACKUP_DIR}/${database}_"*.sql.gz 2>/dev/null \
            | tail -n +$((RETENTION_COUNT + 1)) \
            | xargs -r rm -f
        log "  清理 ${database} 旧备份 ${extra_count} 份（保留最近 ${RETENTION_COUNT} 份）"
    fi
}

# ── 按模式选择备份目标 ──
FAILED=0
if [ -n "${MYSQL_CONTAINER:-}" ] && [ -n "${MYSQL_DATABASE:-}" ]; then
    # 显式指定 --container / --database 时优先使用
    backup_one "$MYSQL_CONTAINER" "$MYSQL_DATABASE" || FAILED=1
else
    case "$MODE" in
        prod)
            backup_one "ai-shifu-mysql" "ai-shifu" || FAILED=1
            ;;
        dev)
            backup_one "docker-ai-shifu-mysql-dev-1" "ai-shifu_dev" || FAILED=1
            ;;
        all)
            backup_one "ai-shifu-mysql" "ai-shifu" || FAILED=1
            backup_one "docker-ai-shifu-mysql-dev-1" "ai-shifu_dev" || FAILED=1
            ;;
    esac
fi

# 输出最近备份信息
log "备份完成。目录: ${BACKUP_DIR}"
ls -1t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | head -3 | while read -r f; do
    log "  📦 $(basename "$f") ($(du -h "$f" | cut -f1))"
done

if [ "$FAILED" = "1" ]; then
    log "❌ 部分备份失败"
    exit 1
fi

exit 0

# ============================================================
# cron 定时配置示例（生产机 crontab -e）:
#   0 1 * * * cd /home/sysmex/ai-shifu && bash scripts/db_backup.sh --all >> /home/sysmex/ai-shifu/docker/backups/cron.log 2>&1
# ============================================================
