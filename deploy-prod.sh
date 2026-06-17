#!/usr/bin/env bash
# deploy-prod.sh — 生产机一键拉取 + 部署
# 使用: bash deploy-prod.sh
set -euo pipefail

echo "══════════ 生产环境部署 ══════════"
echo ""

# 1. 检查 .env
echo "=== 1. 检查 .env ==="
if [ ! -f docker/.env ]; then
    echo "  ❌ docker/.env 不存在！"
    echo "  请: cp docker/.env.example.prod docker/.env"
    echo "  然后编辑 .env 填入实际密钥"
    exit 1
fi
echo "  ✅ .env 已存在"

# 2. 检查生产安全配置
echo ""
echo "=== 2. 安全检查 ==="
# 检查 AAD_BYPASS
if grep -q "^AAD_BYPASS=\"1\"\|^AAD_BYPASS=1" docker/.env 2>/dev/null; then
    echo "  ⚠️  WARNING: AAD_BYPASS=1 (生产环境应关闭)"
fi
# 检查 SECRET_KEY 是否为默认值
if grep -q "SECRET_KEY=\"ai-shifu\"\|SECRET_KEY=ai-shifu" docker/.env 2>/dev/null; then
    echo "  ⚠️  WARNING: SECRET_KEY 为默认值 (应改为随机密钥)"
fi
echo "  ✅ 安全检查完成"

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
