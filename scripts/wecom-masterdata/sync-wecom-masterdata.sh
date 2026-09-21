#!/usr/bin/env bash
# =============================================================================
# sync-wecom-masterdata.sh —— 企微通讯录主数据全量同步（bash 入口）
#
# 流程：
#   1. 身份确认（wecom-cli authorized）
#   2. 调 sync_wecom_masterdata.py（内部走 wecom-cli contact users search --json
#     '{"search_mode":"list"}' 全量 → upsert person_master → 重建组织树 → 写日志）
#
# 用法：
#   bash sync-wecom-masterdata.sh                 # 全量同步（写库）
#   bash sync-wecom-masterdata.sh --dry-run        # 只拉取+解析，不写库
#   bash sync-wecom-masterdata.sh --users-json X  # 从本地 JSON 拉（调试）
#
# 依赖（授权环境）：
#   wecom-cli（已授权）、python3、PyMySQL
#
# 定时（cron 每日 07:30，见 install-cron.sh）：
#   30 7 * * * /path/to/sync-wecom-masterdata.sh >> /var/log/wecom-masterdata.log 2>&1
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── id 参数 ──────────────────────────────────────────────────────────────────
DRY=""
JSON_ARG=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY="--dry-run" ;;
    --users-json) JSON_ARG="--users-json" ;;
  esac
done
PY_ARGS=()
[ -n "$DRY" ] && PY_ARGS+=("$DRY")
[ -n "$JSON_ARG" ] && PY_ARGS+=("$JSON_ARG" "${2:-}")

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ── 1) 身份确认 ──────────────────────────────────────────────────────────────
if ! wecom-cli auth show --status 2>/dev/null | grep -q "authorized"; then
  log "❌ wecom-cli 未授权，停止（需先 wecom-cli auth 授权）"
  exit 1
fi
log "身份确认：wecom-cli 已授权"

# ── 2) 写库同步 ──────────────────────────────────────────────────────────────
log "开始全量同步 person_master + 组织树 ..."
python3 "${SCRIPT_DIR}/sync_wecom_masterdata.py" "${PY_ARGS[@]}"
log "✅ 同步完成"
