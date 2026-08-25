#!/bin/bash
# =============================================================================
# wecom-apply-processor.sh — 企微业务表单批量处理（多表轮询 + 类型分发 + Coach API 钻调）
#
# 流程：对每张业务收集表，读"待处理"记录 → 解析提交人 → 按类型分发调 Coach API
#       → 关单 → 通知（保留通用关单+通知兜底，单张表可关闭钻调）
#
# 覆盖：11 张表（申请 4 + 业务 7），表清单可扩展（加一行配置）
#
# 依赖：wecom-cli 1.1.0+（机器人代授权人执行）；可选的 Coach API（config 段）
# 用法：
#   bash wecom-apply-processor.sh            # 处理全部表一次
#   bash wecom-apply-processor.sh --dry-run  # 预览 Coach API 调用（不执行写操作/网络请求）
#   bash wecom-apply-processor.sh --table 文档权限 # 只处理指定表
#   cron 每 30 分钟：*/30 * * * * bash .../wecom-apply-processor.sh
# 环境变量：
#   COACH_API_BASE     Coach API 地址（默认 http://localhost:8082）
#   COACH_API_TOKEN    Coach API 令牌（Token 头；默认空→不钻调纯关单）
# =============================================================================
set -uo pipefail

# ── Coach API 配置（可被环境变量覆盖）────────────────────────────────────────
COACH_API_BASE="${COACH_API_BASE:-http://localhost:8082}"
COACH_API_TOKEN="${COACH_API_TOKEN:-}"

# ── 表清单（name|docid|sheet|coach_endpoint|pipe_mode|method）
#    coach_endpoint 空 = 不钻调（走通用关单+通知兜底）
#    pipe_mode: raw=逐字段透传 | learner=带面谈学员等字段
#    method: 可选第 6 列（PUT/POST），缺省 POST；
#            任务登记（/coach/tasks/{RID} 端点）配 PUT 表示更新已有任务（首次登记仍 POST 兼容）
#    新增业务表只需加一行，并把 coach_endpoint 设为对应 /api/shifu/coach/* 路径
# ─────────────────────────────────────────────────────────────────────────────
TABLES=(
  # ── 申请类（兜底：关单 + 通知，不调 Coach API）──
  "申请收集表|s3_AIAAjHiMALACNYGUbyQ9rR9GeQCrY_a|申请记录||"
  "文档权限申请|s3_AIAAjHiMALACNt9VLr1EzRjGKWg6V_a|申请记录||"
  "资源申请|s3_AIAAjHiMALACNczyyMvF2SBq2BY0W_a|申请记录||"
  "培训报名|s3_AIAAjHiMALACNPB2lGB71QBSfZG8B_a|申请记录||"
  # ── 业务 9 节点（钻调 Coach API）──
  "课件上传|s3_AIAAjHiMALACNRh2KyehaR0yqhXjE_a|业务记录|/api/shifu/coach/courses|material"
  "面谈总结|s3_AIAAjHiMALACNIbEirTTVR5i6ZyjO_a|业务记录|/api/shifu/coach/session|session"
  "任务登记|s3_AIAAjHiMALACNiJW0ZvFES8KsqMcL_a|业务记录|/api/shifu/coach/tasks/{RID}|task|PUT"
  "评教练|s3_AIAAjHiMALACNRD1J91ZhT6Cf1hab_a|业务记录|/api/shifu/coach/learner-rating|rating"
  "教练评学员|s3_AIAAjHiMALACNeKjBscVhRYSJK2w6_a|业务记录|/api/shifu/coach/phase-summary|phase_summary"
  "带教终评|s3_AIAAjHiMALACNxm2xBdT0Q262RHDG_a|业务记录|/api/shifu/coach/final-rating|final_rating"
  "学习凭证|s3_AIAAjHiMALACNOYMLbsLnTvuVPtQm_a|业务记录|/api/shifu/coach/learning-records|credential"
)

# ── 参数 ────────────────────────────────────────────────────────────────────
DRY_RUN=0
ONLY_TABLE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --table) ONLY_TABLE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# ── 日志 ────────────────────────────────────────────────────────────────────
LOG_DIR="${LOG_DIR:-$HOME/.local/state/wecom-apply}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/apply-$(date +%Y%m%d).log"
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

# ── 身份确认（每次至少一次）────────────────────────────────────────────────
# WECOM_MOCK=1（自测）：跳过 wecom-cli，身份视为机器人
if [ "${WECOM_MOCK:-0}" != "1" ]; then
  whoami=$(wecom-cli identity whoami 2>&1)
  if ! echo "$whoami" | grep -q "机器人"; then
    log "❌ 身份获取失败，停止"
    exit 1
  fi
  log "身份确认：机器人代授权真人执行"
else
  log "身份确认：[MOCK] 跳过（WECOM_MOCK=1）"
fi

# ── 基础函数：解析记录（保留整行字段）+ 状态更新 + 通知 ─────────────────────
# 输入：记录行 JSON（RECORD_ID + 全部业务字段）
parse_records() {
  local RESP="$1"
  WECOM_PARSE_INPUT="$RESP" python3 - "$COACH_API_BASE" "$COACH_API_TOKEN" <<'PY'
import sys, json, os
base, token = sys.argv[1], sys.argv[2]
try:
    d = json.loads(os.environ.get("WECOM_PARSE_INPUT", "{}"))
    vals = d.get('values') or []
    rows = vals[0].get('rows', []) if vals else []
    out = []
    for r in rows:
        out.append(r)  # 保留整行（含 RECORD_ID 与字段）
    print(json.dumps(out, ensure_ascii=False))
except Exception:
    print('[]')
PY
}

# 将一条记录按 pipe_mode 组装成 Coach API 请求 JSON（到 stdout）
# 字段名按常见中文 + 英文别名兜底提取，避免依赖各表完整 schema。
build_payload() {
  local RID="$1" MODE="$2"
  local ROW_JSON="${3:-}"
  [ -z "$ROW_JSON" ] && ROW_JSON='{}'
  local TMPF
  TMPF=$(mktemp "${TMPDIR:-/tmp}/wecom-row.XXXXXX")
  printf '%s' "$ROW_JSON" > "$TMPF"
  python3 - "$RID" "$MODE" "$TMPF" "$COACH_API_BASE" "$COACH_API_TOKEN" <<'PY'
import sys, json, os
rid, mode = sys.argv[1], sys.argv[2]
tmpf = sys.argv[3]
row = {}
try:
    with open(tmpf, "r", encoding="utf-8") as f:
        row = json.load(f)
except Exception:
    row = {}
finally:
    try:
        os.remove(tmpf)
    except OSError:
        pass
base, token = sys.argv[4], sys.argv[5]

def pick(*names):
    for n in names:
        if n in row and row[n] not in (None, ""):
            v = row[n]
            if isinstance(v, dict):
                return json.dumps(v, ensure_ascii=False)
            return str(v)
    return ""

payload = {}
if mode == "material":            # 课件上传：name/link_url/course_bid
    payload = {"name": pick("课件名称","名称","name","标题"),
               "link_url": pick("链接","下载链接","link_url","link","url"),
               "course_bid": pick("课程","课程编号","course_bid","course")}
elif mode == "session":           # 面谈总结：learner_bid/topic/mentor_notes
    payload = {"learner_bid": pick("学员","学员编号","learner_bid","learner","学员ID"),
               "phase_bid": pick("阶段","phase_bid","phase"),
               "topic": pick("主题","面谈主题","topic"),
               "mentor_notes": pick("教练记录","总结","mentor_notes","summary"),
               "session_type": "wecom"}
elif mode == "task":              # 任务登记/完成：status + learner_bid + title
    # status 优先取表单"完成状态"/"任务状态"列；缺省固定"已完成"（表单提交即意味着登记/完成动作）。
    # 注意：表单"状态"列是流转状态（待处理），不作为 API status 传入。
    payload = {"learner_bid": pick("学员","学员编号","learner_bid","learner","学员ID"),
               "title": pick("任务","任务名称","任务内容","title","name"),
               "description": pick("说明","描述","description","备注"),
               "task_type": pick("类型","task_type","type") or "coach",
               "status": pick("完成状态","任务状态") or "已完成"}
elif mode == "rating":            # 评教练：learner_bid/phase_bid/score
    payload = {"learner_bid": pick("学员","学员编号","learner_bid","learner","学员ID"),
               "phase_bid": pick("阶段","phase_bid","phase"),
               "score": pick("评分","分值","score","rating")}
elif mode == "phase_summary":     # 教练评学员：record_bid + 小结
    payload = {"record_bid": pick("记录编号","record_bid","record"),
               "coach_summary": pick("教练评价","总结","coach_summary"),
               "learner_feedback": pick("学员反馈","learner_feedback"),
               "improvement_plan": pick("改进计划","improvement_plan"),
               "complete": pick("完成","complete") == "是"}
elif mode == "final_rating":      # 带教终评：learner_bid/phase_bid + 分项
    payload = {"learner_bid": pick("学员","学员编号","learner_bid","learner","学员ID"),
               "phase_bid": pick("阶段","phase_bid","phase"),
               "theory_score": pick("理论分","theory_score"),
               "practice_score": pick("实操分","practice_score"),
               "peer_score": pick("互评分","peer_score"),
               "coach_score": pick("导师分","coach_score")}
elif mode == "credential":        # 学习凭证：learner_bid/course_bid
    payload = {"learner_bid": pick("学员","学员编号","learner_bid","learner","学员ID"),
               "course_bid": pick("课程","课程编号","course_bid","course")}
print(json.dumps(payload, ensure_ascii=False))
PY
}

# 调用 Coach API（HTTP 方法由第 3 参数指定，缺省 POST）。dry-run 只打印不请求。
call_coach() {
  local ENDPOINT="$1" PAYLOAD="$2" METHOD="${3:-POST}"
  if [ -z "$COACH_API_TOKEN" ]; then
    log "    [skip] COACH_API_TOKEN 未配置，钻调跳过"
    return 0
  fi
  if [ "$DRY_RUN" = "1" ]; then
    log "    [dry-run] $METHOD $COACH_API_BASE$ENDPOINT"
    log "        body: $PAYLOAD"
    return 0
  fi
  local RESP
  RESP=$(curl -s -m 15 -X "$METHOD" "$COACH_API_BASE$ENDPOINT" \
      -H "Content-Type: application/json" \
      -H "Token: $COACH_API_TOKEN" \
      -d "$PAYLOAD" 2>&1)
  if echo "$RESP" | grep -q '"code": 0' && ! echo "$RESP" | grep -q '"error"'; then
    log "    ✅ Coach API ${ENDPOINT##*/} → $RESP"
    return 0
  else
    log "    ⚠️ Coach API 异常(${ENDPOINT}) → ${RESP:0:160}"
    return 1
  fi
}

TOTAL_NEW=0; TOTAL_DONE=0
for entry in "${TABLES[@]}"; do
  IFS='|' read -r TNAME TDOCID TSHEET CENDPOINT CMODE TMETHOD <<< "$entry"
  TMETHOD="${TMETHOD:-POST}"
  [ -n "$ONLY_TABLE" ] && [ "$ONLY_TABLE" != "$TNAME" ] && continue
  [ -z "$TDOCID" ] && continue

  log "── 表[$TNAME] $TDOCID ──"
  # ① 读待处理记录（保留整行字段）
  if [ "${WECOM_MOCK:-0}" = "1" ]; then
    # 自测：用 WECOM_MOCK_RECORDS 模拟 records query 的返回值
    if [ -n "${WECOM_MOCK_RECORDS:-}" ]; then
      RESP="$WECOM_MOCK_RECORDS"
    else
      RESP='{"values":[{"rows":[]}]}'
    fi
    log "    [MOCK] records query（注入模拟记录）"
  else
    RESP=$(wecom-cli smartsheet records query --json "{\"docid\":\"$TDOCID\",\"sql\":\"SELECT * FROM ${TSHEET} WHERE 状态 IN ('待处理','进行中')\"}" 2>&1)
  fi
  ROWS_JSON=$(parse_records "$RESP")
  # 兼容旧版脚本：依旧输出行数
  CNT=$(echo "$ROWS_JSON" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(len(d))" 2>/dev/null || echo 0)
  [ -z "$CNT" ] && CNT=0
  log "  待处理: $CNT 条"
  TOTAL_NEW=$((TOTAL_NEW + CNT))

  # ② 按类型分发调 Coach API + 关单 + 通知
  if [ "$CNT" = "0" ]; then continue; fi
  echo "$ROWS_JSON" | python3 -c "
import sys, json
rows = json.loads(sys.stdin.read())
for r in rows:
    print(r.get('RECORD_ID',''))
" 2>/dev/null | while IFS= read -r rid; do
    [ -z "$rid" ] && continue
    log "  处理 $TNAME/$rid"
    ROW_JSON=$(ROWS_JSON_IN="$ROWS_JSON" RID_IN="$rid" python3 -c "
import sys, json, os
rows = json.loads(os.environ.get('ROWS_JSON_IN', '[]'))
rid = os.environ.get('RID_IN', '')
for r in rows:
    if r.get('RECORD_ID', '') == rid:
        print(json.dumps(r, ensure_ascii=False)); break
" 2>/dev/null)
    # Coach API 钻调（CENDPOINT + CMODE 都有才发起）
    COACH_OK=0
    if [ -n "$CENDPOINT" ] && [ -n "$CMODE" ]; then
      PAYLOAD=$(build_payload "$rid" "$CMODE" "$ROW_JSON")
      # 任务登记：RID 注入端点路径（python 参数化替换，避免 / & \ 破坏）
      EP=$(EP_IN="$CENDPOINT" RID_IN="$rid" python3 -c "
import sys, os
ep = os.environ.get('EP_IN', '')
print(ep.replace('{RID}', os.environ.get('RID_IN', '')))
" 2>/dev/null)
      call_coach "$EP" "$PAYLOAD" "$TMETHOD"
      COACH_OK=$?
    else
      log "    [兜底]该表未配置 Coach API，仅关单 + 通知"
      COACH_OK=0
    fi
    # Coach API 真实失败时不关单（保留待处理以便重试），避免数据丢失
    if [ "${DRY_RUN:-0}" != "1" ] && [ "$COACH_OK" != "0" ]; then
      log "    ⚠️ Coach API 未成功（code=$COACH_OK），跳过关单保留待处理"
      continue
    fi

    if [ "$DRY_RUN" = "1" ]; then
      log "    [dry-run] records update 状态→已处理 + 通知"
      continue
    fi
    # 更新状态（评教练/评学员/终评/凭证 无"已拒绝"选项，用"已处理"）
    UPDATE=$(wecom-cli smartsheet records update --json "{\"docid\":\"$TDOCID\",\"sheet_title\":\"$TSHEET\",\"records\":[{\"record_id\":\"$rid\",\"fields\":{\"状态\":\"已处理\"}}]}" 2>&1)
    if echo "$UPDATE" | grep -q '"errcode": 0'; then
      TOTAL_DONE=$((TOTAL_DONE + 1))
      log "    ✅ $TNAME/$rid 已处理"
    else
      log "    ⚠️ 更新失败：$(echo "$UPDATE" | head -c 100)"
      continue
    fi
    # 通知授权人（汇总）
    wecom-cli message aibot send --json '{"chat_id":"wo_q0lCwAA6kLgnb0HparDT_MaqBbKEA","msgtype":"markdown","content":"**'$TNAME' 已处理**\n记录: '$rid'\n状态: 已处理"}' >/dev/null 2>&1
    log "    📨 已通知"
  done
done

log "══ 完成：新处理 $TOTAL_NEW 条，已关单 $TOTAL_DONE 条 ══"