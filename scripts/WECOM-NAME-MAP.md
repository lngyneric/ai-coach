# wecom-apply-processor.sh · 姓名 → learner_bid 映射说明

## 背景
真实闭环实测（`gFjWlW` 凌云）中，业务表单的"学员"列填的是**姓名**（如"凌云"），
`build_payload` 此前把该姓名直接当 `learner_bid` 透传，导致落库
`learner_tasks.learner_bid='凌云'`（非真实 bid）。本特性在 `build_payload` 内增加
**姓名 → learner_bid** 映射：提取到学员姓名时先查映射，命中用 learner_bid，
未命中则原样透传（容错，不破坏现有流程）。

## 映射机制（缺省行为不变）
- 命中映射 → `learner_bid` 用映射值。
- 未命中 / 映射缺失 / 映射为空 → `learner_bid` 原样透传（保持现状）。
- **映射文件缺失或为空** → 完全保持现状（透传），不引入新依赖。

### 来源优先级
1. 环境变量 `WECOM_NAME_MAP`：直接给 JSON，如 `{"凌云":"w3-ln-9"}`（最优先）。
2. 映射文件：`WECOM_NAME_MAP_FILE` 环境变量覆盖路径；**缺省路径**
   `scripts/wecom-name-map.json`（脚本同目录），由 `SCRIPT_DIR` 定位。

示例映射文件 `scripts/wecom-name-map.json`：
```json
{
  "凌云": "w3-ln-9",
  "张三": "w3-ln-1",
  "李四": "w3-ln-2"
}
```
缺省交付为空对象 `{}`（即默认完全透传，需启用时再填充）。

## 从主数据生成映射
主数据（`ai-shifu_dev` 库）：
- `person_master`：`wecom_userid`(主键) / `name`（企微姓名，如"凌云"）
- `learner_profiles`：`user_bid` / `learner_bid`（`user_bid=wecom_userid` 关联 learner）

无法关联（无 learner_profiles / 姓名空）的人不进入映射 → 脚本对这些姓名原样透传。

### 生成 SQL 示例
```sql
SELECT pm.name, lp.learner_bid
FROM person_master pm
JOIN learner_profiles lp ON lp.user_bid = pm.wecom_userid
WHERE pm.name IS NOT NULL AND pm.name <> ''
  AND lp.learner_bid IS NOT NULL AND lp.learner_bid <> ''
ORDER BY pm.name;
```

### 一键生成脚本 `scripts/gen-wecom-name-map.sh`
自动查主数据并写出 `scripts/wecom-name-map.json`（JSON 对象；空结果写 `{}`）：
```bash
bash scripts/gen-wecom-name-map.sh
# 覆盖输出路径 / 数据库参数：
# OUT=/tmp/map.json DB_USER=root DB_PASS=xxx DB_NAME=ai-shifu_dev bash scripts/gen-wecom-name-map.sh
```

### dev 环境手工维护（测试数据无真实姓名）
dev 中 `learner_profiles` 为 `w3-usr-1..4 → w3-ln-1..4`（无真实姓名），
可直接手工编辑 `scripts/wecom-name-map.json`：
```json
{
  "凌云": "w3-ln-9",
  "张三": "w3-ln-1",
  "李四": "w3-ln-2",
  "王五": "w3-ln-3",
  "赵六": "w3-ln-4"
}
```

## 自测（dry-run mock）
`WECOM_MOCK=1` + `--dry-run` 注入模拟记录，可验证映射：
```bash
cd scripts
WECOM_MOCK=1 COACH_API_TOKEN=test \
WECOM_MOCK_RECORDS='{"values":[{"rows":[{"RECORD_ID":"R-1","学员":"凌云","任务":"带教任务"}]}]}' \
WECOM_NAME_MAP='{"凌云":"w3-ln-9"}' \
bash wecom-apply-processor.sh --dry-run --table 任务登记
# → body: {"learner_bid": "w3-ln-9", ...}
```
预期：命中 → `learner_bid=w3-ln-9`；未命中/空映射 → 原样透传姓名。

覆盖模式：`任务登记`(task) / `面谈总结`(session) / `评教练`(rating) /
`带教终评`(final_rating) / `学习凭证`(credential) 的 `learner_bid` 均走同一 `learner()` 映射。
