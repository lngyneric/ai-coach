#!/usr/bin/env bash
# deploy.sh — 将本地 Python 改动同步到 ai-shifu-api 容器并重载
# 用法: ./deploy.sh [--recreate]
#   --recreate: 同时重启容器（用于 docker-compose up -d --force-recreate 后全量恢复）

set -euo pipefail

# ── 生产模式检查 ──
if [ "${1:-}" = "--prod" ]; then
    PROD_MODE=true
    echo "  [生产模式] 启用安全检查"
    # 检查 AAD_BYPASS
    if grep -q "^AAD_BYPASS=\"1\"\|^AAD_BYPASS=1" docker/.env 2>/dev/null; then
        echo "  ⚠️  WARNING: AAD_BYPASS=1 生产环境应关闭"
    fi
    # 检查 SECRET_KEY 是否为默认值
    if grep -q "SECRET_KEY=\"ai-shifu\"" docker/.env 2>/dev/null; then
        echo "  ❌ ERROR: SECRET_KEY 仍为默认值，请修改"
        exit 1
    fi
else
    PROD_MODE=false
fi

API="ai-shifu-api"
ROOT="/home/sysmex/ai-shifu/src/api/flaskr"

echo "=== 同步 Python 文件到 $API ==="

# 确保学习门户模块目录存在
docker exec $API mkdir -p /app/flaskr/service/learning_portal

# 核心 TTS 文件
echo "  TTS..."
docker cp "$ROOT/api/tts/volcengine_provider.py" $API:/app/flaskr/api/tts/volcengine_provider.py
docker cp "$ROOT/api/tts/__init__.py" $API:/app/flaskr/api/tts/__init__.py
docker cp "$ROOT/api/tts/volcengine_protocol.py" $API:/app/flaskr/api/tts/volcengine_protocol.py

# 学习相关（listen 元素类型修复）
echo "  learn..."
docker cp "$ROOT/service/learn/listen_element_types.py" $API:/app/flaskr/service/learn/listen_element_types.py
docker cp "$ROOT/service/learn/listen_element_run_stream.py" $API:/app/flaskr/service/learn/listen_element_run_stream.py

# 学习门户模块（新增）
echo "  learning_portal..."
docker cp "$ROOT/service/learning_portal/__init__.py" $API:/app/flaskr/service/learning_portal/__init__.py
docker cp "$ROOT/service/learning_portal/models.py" $API:/app/flaskr/service/learning_portal/models.py
docker cp "$ROOT/service/learning_portal/routes.py" $API:/app/flaskr/service/learning_portal/routes.py
docker cp "$ROOT/service/learning_portal/tasks.py" $API:/app/flaskr/service/learning_portal/tasks.py

# 用户认证（employee 自动授权删除）
echo "  auth..."
docker cp "$ROOT/service/user/auth/providers/employee.py" $API:/app/flaskr/service/user/auth/providers/employee.py

# route（logout 新增）
echo "  route..."
docker cp "$ROOT/route/user.py" $API:/app/flaskr/route/user.py

# config（VOLCENGINE_TTS_API_KEY 注册）
echo "  config..."
docker cp "$ROOT/common/config.py" $API:/app/flaskr/common/config.py
docker cp "$ROOT/common/celery_app.py" $API:/app/flaskr/common/celery_app.py

# 清除 python 缓存
echo "  clean cache..."
docker exec $API sh -c 'rm -rf /app/flaskr/service/learning_portal/__pycache__ /app/flaskr/service/learn/__pycache__ /app/flaskr/api/tts/__pycache__'

# 重载 gunicorn
echo "  reload gunicorn..."
docker exec $API python3 -c "import os, signal; os.kill(1, signal.SIGHUP)"
sleep 2

# 日志轮转配置（如尚未安装）
echo "  logrotate..."
docker exec $API sh -c 'which logrotate >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq logrotate 2>/dev/null)' 2>/dev/null || true
docker cp /home/sysmex/ai-shifu/docker/logrotate.conf $API:/etc/logrotate.d/ai-shifu 2>/dev/null || true
docker exec $API sh -c 'chown root:root /etc/logrotate.d/ai-shifu 2>/dev/null' || true
echo ""
echo "✅ Python 文件同步完成"

# 同步 nginx 静态文件
echo ""
echo "=== 同步静态文件到 nginx ==="
NGINX="ai-shifu-nginx"
for f in courses.html mentor.html login.html logout.html; do
  docker cp "/home/sysmex/ai-shifu/docker/$f" $NGINX:/usr/share/nginx/html/$f 2>/dev/null && echo "  ✅ $f" || echo "  ⚠️  $f (忽略)"
done
docker exec $NGINX nginx -s reload 2>/dev/null && echo "  nginx reloaded"
echo "✅ 静态文件同步完成"

# 验证
echo ""
echo "=== 验证 ==="
curl -sk -o /dev/null -w "  /api/portal/profile → HTTP %{http_code}\n" -H "Host: eu.sysmex.com.cn" https://localhost:443/api/portal/profile
curl -sk -o /dev/null -w "  /api/portal/dashboard → HTTP %{http_code}\n" -H "Host: eu.sysmex.com.cn" https://localhost:443/api/portal/dashboard
echo "✅ 全部完成"
