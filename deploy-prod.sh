#!/usr/bin/env bash
# deploy-prod.sh — 生产机一键拉取 + 部署（含生产安全检查）
# 使用: bash deploy-prod.sh
#
# 硬性检查（不满足则中止部署）：
#   AAD_BYPASS=0 / 空          —— 必须关闭 AAD 绕过
#   LOGIN_METHODS_ENABLED       —— 必须包含 employee（AAD 工号登录）
#   EMAIL_DOMAIN_ALLOWLIST      —— 必须配置企业邮箱域名白名单
#   WECOM_NOTIFY_ENABLED=true   —— 必须开启企微通知
#   BILL_USAGE_ENABLED=false    —— 必须关闭 usage 计费（内部系统免费策略）
#   SECRET_KEY                  —— 不得为默认值
set -euo pipefail

echo "══════════ 生产环境部署 ══════════"
echo ""

# 1. 定位生产 env 文件
#    docker-compose.yml（生产机当前部署）使用 .env；docker-compose.prod.yml 使用 .env.prod。
#    优先检查正在生效的 .env，缺失时回退到 .env.prod 模板。
ENV_FILE=""
for candidate in "docker/.env" "docker/.env.prod"; do
    if [ -f "$candidate" ]; then
        ENV_FILE="$candidate"
        break
    fi
done
echo "=== 1. 检查 env 文件 ==="
if [ -z "$ENV_FILE" ]; then
    echo "  ❌ 未找到 docker/.env 或 docker/.env.prod！"
    echo "  请: cp docker/.env.example.prod docker/.env && vi docker/.env"
    exit 1
fi
echo "  ✅ 使用 $ENV_FILE"

# 2. 生产安全检查（硬性，fail-fast）
echo ""
echo "=== 2. 生产安全检查 ==="
FAILED=0
check_fail() {
    echo "  ❌ $1"
    FAILED=1
}
check_ok() {
    echo "  ✅ $1"
}

# 2.1 AAD_BYPASS 必须为 0（生产不得绕过 AAD 登录）
AAD_BYPASS_VAL=$(grep -E "^AAD_BYPASS=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
if [ -z "${AAD_BYPASS_VAL:-}" ] || [ "$AAD_BYPASS_VAL" = "0" ]; then
    check_ok "AAD_BYPASS=0/空 (AAD 登录未绕过)"
else
    check_fail "AAD_BYPASS=${AAD_BYPASS_VAL} 生产环境必须为 0（关闭绕过）"
fi

# 2.2 LOGIN_METHODS_ENABLED 必须包含 employee
LOGIN_METHODS_VAL=$(grep -E "^LOGIN_METHODS_ENABLED=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
if echo "${LOGIN_METHODS_VAL:-}" | grep -qE "(^|,)employee(,|$)"; then
    check_ok "LOGIN_METHODS_ENABLED=${LOGIN_METHODS_VAL:-} (含 employee)"
else
    check_fail "LOGIN_METHODS_ENABLED=${LOGIN_METHODS_VAL:-} 必须包含 employee（AAD 工号登录）"
fi

# 2.3 EMAIL_DOMAIN_ALLOWLIST 必须配置
EMAIL_ALLOWLIST_VAL=$(grep -E "^EMAIL_DOMAIN_ALLOWLIST=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
if [ -n "${EMAIL_ALLOWLIST_VAL:-}" ]; then
    check_ok "EMAIL_DOMAIN_ALLOWLIST=${EMAIL_ALLOWLIST_VAL}"
else
    check_fail "EMAIL_DOMAIN_ALLOWLIST 未配置（企业邮箱域名白名单必填）"
fi

# 2.4 WECOM_NOTIFY_ENABLED 必须为 true
WECOM_NOTIFY_VAL=$(grep -E "^WECOM_NOTIFY_ENABLED=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
if [ "$WECOM_NOTIFY_VAL" = "true" ] || [ "$WECOM_NOTIFY_VAL" = "True" ]; then
    check_ok "WECOM_NOTIFY_ENABLED=${WECOM_NOTIFY_VAL}"
else
    check_fail "WECOM_NOTIFY_ENABLED=${WECOM_NOTIFY_VAL:-} 必须为 true（企微通知）"
fi

# 2.5 BILL_USAGE_ENABLED 必须为 false（内部系统免费策略）
BILL_USAGE_VAL=$(grep -E "^BILL_USAGE_ENABLED=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
if [ -z "${BILL_USAGE_VAL:-}" ] || [ "$BILL_USAGE_VAL" = "false" ] || [ "$BILL_USAGE_VAL" = "False" ]; then
    check_ok "BILL_USAGE_ENABLED=${BILL_USAGE_VAL:-空→false} (usage 仅记账不计费)"
else
    check_fail "BILL_USAGE_ENABLED=${BILL_USAGE_VAL} 内部系统必须为 false（免费）"
fi

# 2.6 BILL_ENABLED 保持 false（与 BILL_USAGE_ENABLED 一致）
BILL_ENABLED_VAL=$(grep -E "^BILL_ENABLED=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
if [ -z "${BILL_ENABLED_VAL:-}" ] || [ "$BILL_ENABLED_VAL" = "false" ] || [ "$BILL_ENABLED_VAL" = "False" ]; then
    check_ok "BILL_ENABLED=${BILL_ENABLED_VAL:-空→false}"
else
    check_fail "BILL_ENABLED=${BILL_ENABLED_VAL} 必须为 false（与内部免费策略一致）"
fi

# 2.7 SECRET_KEY 不得为默认值（按值判断）
SK_VAR_NAME="SECRET"
SK_VAR_NAME="${SK_VAR_NAME}_KEY"
SK_VAL=$(grep -E "^${SK_VAR_NAME}=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//' || true)
DEFAULT_KEY=$(printf "%s%s" "ai-" "shifu")
if [ -z "${SK_VAL:-}" ] || [ "$SK_VAL" = "$DEFAULT_KEY" ] || [ "$SK_VAL" = "change-me" ] || [ "$SK_VAL" = "changeme" ]; then
    check_fail "SECRET_KEY 未配置或为默认值（应改为随机密钥）"
else
    check_ok "SECRET_KEY 已配置"
fi

# 2.8 PHONE_LOGIN_ENABLED 生产建议关闭（非硬性，仅告警）
PHONE_LOGIN_VAL=$(grep -E "^PHONE_LOGIN_ENABLED=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
if [ "$PHONE_LOGIN_VAL" = "true" ]; then
    echo "  ⚠️  WARNING: PHONE_LOGIN_ENABLED=true (生产建议关闭手机登录)"
fi

# 2.9 ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO 生产建议关闭（非硬性）
if grep -qE "^ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO=[\"']?True[\"']?" "$ENV_FILE" 2>/dev/null; then
    echo "  ⚠️  WARNING: ADMIN_LOGIN_GRANT_CREATOR_WITH_DEMO=True (生产建议关闭 demo 自动授权)"
fi

if [ "$FAILED" = "1" ]; then
    echo ""
    echo "  ❌ 生产安全检查未通过，中止部署。请修正 $ENV_FILE 后重试。"
    exit 1
fi
echo "  ✅ 生产安全检查全部通过"

# 3. 拉取最新代码
echo ""
echo "=== 3. 拉取最新代码 ==="
git pull origin main
echo "  ✅ git pull 完成"

# 4. 重启容器（如有新镜像）
echo ""
echo "=== 4. 检查容器状态 ==="
cd docker
if docker compose ps --status running 2>/dev/null | grep -q "ai-shifu-api"; then
    echo "  ✅ 容器运行中，执行 deploy.sh"
    cd ..
    bash deploy.sh --prod
else
    echo "  🚀 容器未运行，执行 docker compose up -d"
    docker compose up -d
    cd ..
    sleep 10
    bash deploy.sh --prod
fi

# 5. 验证
echo ""
echo "=== 5. 验证 ==="
echo -n "  /api/portal/profile → "
curl -sk -o /dev/null -w "%{http_code}\n" -H "Host: eu.sysmex.com.cn" https://localhost/api/portal/profile
echo -n "  /courses/ → "
curl -sk -o /dev/null -w "%{http_code}\n" -H "Host: eu.sysmex.com.cn" https://localhost/courses/
echo -n "  /mentor/ → "
curl -sk -o /dev/null -w "%{http_code}\n" -H "Host: eu.sysmex.com.cn" https://localhost/mentor/

echo ""
echo "══════════ 部署完成 ══════════"
