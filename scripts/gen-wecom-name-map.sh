#!/bin/bash
# =============================================================================
# gen-wecom-name-map.sh — 从主数据生成「姓名 → learner_bid」映射文件
#
# 用途：为 wecom-apply-processor.sh 提供 learner_bid 映射来源。
#   原理：person_master.name（企微姓名）+ learner_profiles（user_bid=wecom_userid 关联）
#         → 姓名 → learner_bid，写为 JSON（{"姓名":"learner_bid"}）。
#
# 主数据：
#   ai-shifu_dev 库
#     person_master:    wecom_userid(主键) / name（企微姓名，如"凌云"）
#     learner_profiles: user_bid / learner_bid（user_bid=wecom_userid 关联 learner）
#   无法关联（无 learner_profiles 记录 / 姓名空）的人不会进入映射 → 脚本对未命中姓名
#   原样透传，不影响这些人的现有流程。
#
# 用法：
#   bash gen-wecom-name-map.sh                     # 写入本目录 wecom-name-map.json
#   OUT=/path/to/wecom-name-map.json bash ...      # 覆盖输出路径
#   DB_USER=root DB_PASS=xxx DB_NAME=ai-shifu_dev bash ...
# 幂等：直接覆盖输出文件；映射为空时写入 {}（脚本按"缺失/空映射 → 完全透传"处理）。
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
OUT="${OUT:-$SCRIPT_DIR/wecom-name-map.json}"
DB_USER="${DB_USER:-root}"
DB_PASS="${DB_PASS:-}"
DB_NAME="${DB_NAME:-ai-shifu_dev}"
DB_HOST="${DB_HOST:-127.0.0.1}"

# 生成 SQL：person_master.name + learner_profiles（user_bid=wecom_userid）→ 姓名→learner_bid
SQL="SELECT pm.name, lp.learner_bid
FROM person_master pm
JOIN learner_profiles lp ON lp.user_bid = pm.wecom_userid
WHERE pm.name IS NOT NULL AND pm.name <> ''
  AND lp.learner_bid IS NOT NULL AND lp.learner_bid <> ''
ORDER BY pm.name;"

# 组装 mysql 客户端参数（密码可选）
MYSQL_ARGS=(-u"$DB_USER" -h"$DB_HOST" -N -B --batch "$DB_NAME" -e "$SQL")
if [ -n "$DB_PASS" ]; then
  MYSQL_ARGS=(-u"$DB_USER" -p"$DB_PASS" -h"$DB_HOST" -N -B --batch "$DB_NAME" -e "$SQL")
fi

# 查询并把「name \t learner_bid」行转成 JSON（空结果写 {}）
mysql "${MYSQL_ARGS[@]}" 2>/dev/null | python3 -c '
import sys, json
m = {}
for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    name, _, bid = line.partition("\t")
    name = name.strip(); bid = bid.strip()
    if name and bid:
        m[name] = bid
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(m, f, ensure_ascii=False, indent=2)
print("已生成 %d 条姓名→learner_bid 映射 -> %s" % (len(m), sys.argv[1]))
' "$OUT"
