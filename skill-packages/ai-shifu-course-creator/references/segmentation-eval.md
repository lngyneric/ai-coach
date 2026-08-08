# Segmentation Evaluation（L3 反馈闭环 · 分解质量评估）

> 医学垂类分解强化三层中的 **L3**：用课件验收数据（learn_progress_records）作为
> reward signal，评估每个课节的分解质量，卡课率高的课节 → 建议重新分段
> （衔接 L1 垂类分段规则）。衔接：`pedagogy.md#medical-vertical-segmentation-rules`
> （L1）+ `ivd-knowledge.md`（L2）。

## 1. 用途与工作流

1. 运行 `python3 scripts/segmentation-eval.py` 生成 `segmentation-eval.tsv`
   （课节 × 指标 × 质量分）。
2. 解析输出：`grade == "poor"` 的课节为「分解不佳」候选。
3. 对 `poor` 课节，用 L1 垂类规则检查：是否未按检验系统切分 / 参考值 span 是否
   immutable / 切分单元是否仍是「知识本体」粒度（每课一个可考核知识点）。
4. 需要知识事实时用 L2 检索：`python3 scripts/ivd-lookup.py "<项目/术语>"`。
5. 修订大纲 → 重新发布 → 下轮评估对比质量分变化（闭环迭代）。

## 2. 运行

直连 MySQL（需 `pymysql`，dev 环境可在 api 容器内运行）：

```bash
python3 scripts/segmentation-eval.py \
  --dsn "mysql://root:ai-shifu@ai-shifu-mysql-dev:3306/ai-shifu_dev?charset=utf8mb4" \
  --out segmentation-eval.tsv \
  --min-users 1 \
  --stick-penalty 1.0
```

- `--min-users N`：过滤总学习人数 < N 的课节（样本太小评分不稳定，默认 1）。
- `--stick-penalty P`：卡课率惩罚权重，越大越强调卡课（默认 1.0）。
- 也可仅设环境变量 `SEG_EVAL_DB_DSN` 后不带 `--dsn` 运行。

## 3. 指标口径

按 `(shifu_bid, outline_item_bid)` 聚合 `learn_progress_records`，每个用户取其
**最新一条**记录的状态（按 `updated_at ASC, id ASC` 升序取最后一条）：

| 指标 | 计算 | 说明 |
|---|---|---|
| `total_users` | 该课节有进度记录的去重用户数 | 分母 |
| `completed` | 最新状态 = 603（完成）的用户数 | |
| `in_progress` | 最新状态 = 602（进行中）的用户数 | 停留/卡课 |
| `not_started` | 最新状态 = 601（未开始） | |
| `reset` | 最新状态 = 608（重置） | 学习被重置 |
| `completion_rate` | `completed / total_users` | 完成率 |
| `stick_rate` | `in_progress / total_users` | 卡课率 |

状态码与后端 `flaskr/service/order/consts.py` 一致（601/602/603/608）。

## 4. 质量分公式（可配置）

```
quality_score = round( 100 * completion_rate − 100 * stick_rate * STICK_PENALTY )
```

- `STICK_PENALTY` 默认 `1.0`，`--stick-penalty` 可调。
- 完成率高 + 卡课率低 → 高分（分解良好）；卡课率高 → 负分（分解不佳）。

分级（脚本顶部常量，可改）：

| grade | 条件 | 含义 |
|---|---|---|
| `good` | `score >= 60` | 分解良好 |
| `fair` | `0 <= score < 60` | 一般（卡课率 ≥ 0.5 时 remark 提示检查粒度/顺序） |
| `poor` | `score < 0` | 分解不佳 → 建议重新分段 |

> `item_type == "chapter"` 的行是章节聚合（非叶子课节），remark 已标注，评估时应
> 以 `lesson` 叶子课节为主。

## 5. 输出列

```
shifu_bid  shifu_title  outline_item_bid  outline_title  item_type
parent_title  position  total_users  completed  in_progress  not_started  reset
completion_rate  stick_rate  quality_score  grade  remark
```

## 6. dev 实测结论（2026-08-06 · ai-shifu_dev）

运行 `segmentation-eval.py` 生成 213 行：`good=44 / fair=13 / poor=156`。
样本均为 dev 测试数据（全量用户少、大部分停留在 602 进行中），故 poor 比例偏高，
**不代表线上质量**——本工具价值在于对比口径：同课节两轮间完成率/卡课率变化。

医学垂类课程（血液/免疫/尿液/医学检验通识/学术基础）`lesson` 课节大多 `poor`
（completion 0~0.2、stick 0.7~1.0），是最典型的「分解不佳 → 重新分段」候选，
可直接用 L1 六条规则复核并重切。

## 7. 闭环建议（衔接 L1）

对 `poor` 课节按 L1 顺序自查：

1. 是否**按检验系统先行切分**（血液/凝血/尿液/免疫/生化/分子），而不是叙事流。
2. 每课是否**恰好一个可考核知识点**（核心问题可分级作答）。
3. 参考值 span 是否 `immutable` + `preserve_block: true`，术语是否统一表命名。
4. 无法映射到 `exam/review/practice` 验收项的课节直接否决重切。
5. 重切后发布，下轮 `segmentation-eval.py` 对比 `quality_score` 是否回正。

> 验收项 / 反馈可进一步接入 `learn_lesson_feedbacks`（score/comment）作为第二路
> reward（当前表无数据，脚本预留状态码聚合，未接反馈）。
