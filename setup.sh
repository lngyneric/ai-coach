#!/usr/bin/env bash
# setup.sh — 新开发机一键初始化
# 使用: bash setup.sh
set -euo pipefail

echo "══════ 开发机初始化 ══════"
echo ""

# 1. 检查依赖
echo "=== 1. 检查依赖 ==="
for cmd in docker git; do
    which $cmd >/dev/null 2>&1 && echo "  ✅ $cmd" || { echo "  ❌ $cmd 未安装"; exit 1; }
done

# 2. 检查 .env
echo ""
echo "=== 2. 检查 .env ==="
if [ ! -f docker/.env ]; then
    echo "  ❌ docker/.env 不存在！"
    echo "  请从另一台机器复制或手动创建。"
    echo "  必填项: ARK_API_KEY, VOLCENGINE_TTS_API_KEY, LOGIN_METHODS_ENABLED"
    exit 1
fi
echo "  ✅ docker/.env 已存在"

# 3. 启动服务
echo ""
echo "=== 3. 启动服务 ==="
cd docker
docker compose up -d
echo "  ✅ 服务已启动"

# 4. 等待就绪
echo ""
echo "=== 4. 等待 MySQL + API 就绪 ==="
sleep 15
echo "  ✅ 就绪"

# 5. 注入自定义代码
echo ""
echo "=== 5. 注入 Python 改动 ==="
cd ..
bash deploy.sh
echo "  ✅ deploy.sh 完成"

# 6. 种子数据
echo ""
echo "=== 6. 初始化种子数据 ==="
docker exec ai-shifu-api python3 -c "
import pymysql, uuid
from datetime import datetime
conn = pymysql.connect(host='ai-shifu-mysql',user='root',password='ai-shifu',database='ai-shifu')
cur = conn.cursor(); now = datetime.utcnow()
phases = [
    ('ph-001','第一阶段: 血球/尿液/凝血','phase_1',1,60,60.00,0.40,0.30,0.20,0.10),
    ('ph-002','第二阶段: 免疫/生化/糖化/Alifax','phase_2',2,60,60.00,0.40,0.30,0.20,0.10),
    ('ph-003','第三阶段: 生命科学/招标/压货','phase_3',3,60,60.00,0.40,0.30,0.20,0.10),
]
for p in phases:
    cur.execute('INSERT IGNORE INTO mentorship_phases (phase_bid,name,code,sort_order,duration_days,passing_score,theory_weight,practice_weight,review_weight,mentor_weight,is_active,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s)', p+(now,now))
conn.commit()
print('  ✅ 带教阶段: 3 rows')
conn.close()
"

echo ""
echo "══════════ 初始化完成 ══════════"
echo "  访问地址: https://localhost"
echo "  课程首页: https://localhost/courses/"
echo "  导师工作台: https://localhost/mentor/"
echo "  知识图谱: https://localhost/ivd-knowledge-tree.html"
echo ""
echo "  管理后台: https://localhost/admin"  
echo "  (第一个登录用户自动成为管理员)"
echo ""
echo "  容器重建后只需: bash deploy.sh"
