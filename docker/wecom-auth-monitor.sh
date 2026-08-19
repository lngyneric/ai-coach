#!/bin/bash
# ============================================================
# wecom-auth-monitor.sh — 企业微信 Ai-Coach 授权监控脚本
# 功能：
#   1. 检测各业务域授权状态（850002=未授权 / 850003=已过期 / 0=正常）
#   2. 发现异常时，提取授权链接并通过企业微信消息通知授权人（凌云）
#   3. 记录检测日志
# 用法：
#   ./wecom-auth-monitor.sh          # 手动运行
#   ./wecom-auth-monitor.sh --report # 仅输出报告不发消息
# cron 建议：每天 09:00 运行一次
# ============================================================

set -u

# ---------- 配置 ----------
AUTHORIZER_ID="wo_q0lCwAA6kLgnb0HparDT_MaqBbKEA"   # 授权人（凌云）userid
LOG_FILE="${HOME}/.local/state/wecom-auth-monitor.log"
NOTIFY_ONLY_REPORT="${1:-}"

# 业务域检测命令（只读操作，无副作用）
declare -A DOMAINS=(
  ["通讯录"]="contact users search --keywords 凌"
  ["待办"]="todo list"
  ["日程"]="calendar schedules list"
  ["邮件"]="mail search --keywords 测试"
  ["微盘"]="disk files list"
  ["文档"]="doc search --keywords 测试"
  ["会议"]="meeting list"
)

mkdir -p "$(dirname "$LOG_FILE")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

# ---------- 检测各域授权状态 ----------
report=""
issues=0
issue_list=""

for domain in "${!DOMAINS[@]}"; do
  cmd="${DOMAINS[$domain]}"
  # 跑检测命令，提取 errcode 和授权链接
  output=$(timeout 20 wecom-cli $cmd 2>&1)
  errcode=$(echo "$output" | grep -oE '"errcode": [0-9]+' | head -1 | grep -oE '[0-9]+')
  status="正常"

  case "$errcode" in
    850002) status="❌ 未授权" ;;
    850003) status="⚠️ 已过期" ;;
    ""|0) status="✅ 正常" ;;
    *) status="❓ 异常($errcode)" ;;
  esac

  # 提取授权链接（850002/850003 响应中的 help_message 里带链接）
  auth_url=""
  if [ "$errcode" = "850002" ] || [ "$errcode" = "850003" ]; then
    auth_url=$(echo "$output" | grep -oE 'https://work\.weixin\.qq\.com/ai/aiHelper/authorizationList[^"\\ )]*' | head -1)
  fi

  if [ "$errcode" = "850002" ] || [ "$errcode" = "850003" ]; then
    issues=$((issues + 1))
    issue_list="${issue_list}
- **${domain}**：${status}"
    [ -n "$auth_url" ] && issue_list="${issue_list}  → [点击授权](${auth_url})"
  fi

  report="${report}\n| ${domain} | ${status} |"
  log "域=${domain} errcode=${errcode:-0} 状态=${status}"
done

report=$(echo -e "$report" | sed 's/^\\n//')
echo "======== wecom 授权状态报告 $(date '+%Y-%m-%d %H:%M') ========"
echo -e "$report"
echo ""
echo "异常域数: $issues"

# ---------- 通知（有异常才发消息） ----------
if [ "$issues" -gt 0 ] && [ "$NOTIFY_ONLY_REPORT" != "--report" ]; then
  msg="### ⚠️ 企业微信 Ai-Coach 授权续期提醒

检测到 **${issues}** 个业务域授权需要处理（企业微信授权有效期 7 天）：

${issue_list}

**操作**：在企业微信中点击上方链接完成授权，或到「工作台 → 智能机器人 → Ai-Coach 智能助手 → 编辑 → 可使用权限」逐域授权。

> 此提醒由 wecom-auth-monitor 自动发送"
  result=$(timeout 25 wecom-cli message aibot send \
    --chat-id "$AUTHORIZER_ID" \
    --msg-type markdown \
    --markdown "$(python3 -c "import json,sys; print(json.dumps({'content': sys.argv[1]}))" "$msg")" 2>&1)
  if echo "$result" | grep -q '"success": true'; then
    log "已发送续期提醒消息给授权人"
    echo "✅ 已发送续期提醒消息"
  else
    log "发送提醒失败: $(echo "$result" | head -3)"
    echo "⚠️ 提醒消息发送失败（详见日志）"
  fi
else
  [ "$issues" -eq 0 ] && { echo "✅ 所有业务域授权正常，无需续期"; log "全部域授权正常"; }
fi
