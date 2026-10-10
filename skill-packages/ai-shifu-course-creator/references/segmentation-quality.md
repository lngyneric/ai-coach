# Segmentation Quality Pre-check（JEV 分段质量提前判断）

> **在分段之后、编排/生成之前**，用 JEV（TypeSafe System One，typed-judgment 模型）
> 对分段结果提前打分，把可疑段（粒度过粗/边界生硬/preserve 标记错误）标出来，供人工
> 确认或触发 re-segmentation。与 L3（`segmentation-eval.md`，**部署后**用学习数据做反馈）
> 互补：本工具是**部署前的静态质量门**，无需等学习数据。
>
> 衔接：`data-contracts.md#segment-schema`（输入契约）、`pedagogy.md#segmentation-methodology`
> （分段方法论）、`segmentation-eval.md`（L3 部署后反馈）。

## 1. 定位与三层关系

| 层 | 时机 | 数据源 | 工具 |
|---|---|---|---|
| L1 规则 | 分段时 | 垂类规则 | `pedagogy.md#medical-vertical-segmentation-rules` |
| L2 知识 | 分段时 | 知识图谱 | `scripts/ivd-lookup.py` |
| **本工具（预检）** | **分段后·生成前** | **分段结果本身** | **`scripts/segmentation-quality.py`（JEV）** |
| L3 反馈 | 部署后 | `learn_progress_records` | `scripts/segmentation-eval.py` |

JEV 是**判定模型**（返回 `noul` 概率 / `score` 分值 / `choice`），**不生成文本**，
因此这里把它当作「分段质量分类器」：一次请求批量提交多个问项。

## 2. 运行

```bash
# 最小：只传分段结果（segment-schema 列表或 {"segments": [...]}）
python3 scripts/segmentation-quality.py --segments seg.json

# 推荐：附源材料以提高覆盖度判断准确度
python3 scripts/segmentation-quality.py \
  --segments seg.json --source raw-material.md \
  --threshold 2.0 --out seg-quality.json
```

- `TYPESAFE_API_KEY` 解析顺序：进程环境变量 → skill 根 `.env`（`scripts/../.env`）。两者都没有时输出 `{"status":"skipped"}` 并 **退出码 0**（fail-open，绝不阻塞）。
- 出海网络：需可达 `api.typesafe.ai`（dev 走宿主代理，见 skill 外部的部署说明）。
- `--threshold`：可疑判定阈值（`score < 该值` 即 `flag`，默认 `2.0`）。

## 3. 问项与量表

一次请求提交（`state` = 源材料）：

| 问项 | 类型 | 维度 |
|---|---|---|
| `coverage` | `score` 0..4 | 分段整体是否完整覆盖源材料核心要点（无遗漏/无冗余） |
| `gran_<i>` | `score` 0..4 | 第 i 段是否只承载单一可教点、粒度是否合适 |
| `bnd_<i>` | `score` 0..4 | 第 i 段边界是否落在自然语义边界（不切断概念/步骤） |
| `pres_<i>` | `noul` | 第 i 段 `preserve_block` 标记是否正确 |

- `score` 量表 0..4，数值越高越好（各档描述见脚本顶部 `_*_LEVELS` 常量）。
- `noul`：`true` 表示 `preserve_block` 标记与内容相符（含逐字保留内容则 true，否则 false 亦正确）。
- 段数上限 `_JEV_MAX_SEGMENTS`（默认 40），超出的段不评估（防 token 爆炸）。

## 4. 输出

```json
{
  "status": "ok",
  "model": "jev-1.13.0",
  "coverage": { "score": 3.2, "grade": "good" },
  "segments": [
    { "segment_id": "s2", "granularity": 1.64, "boundary": 2.92,
      "preserve_ok": 0.88, "weakest": 1.64, "flag": true }
  ],
  "summary": { "n": 3, "mean": 2.59, "min": 1.64, "flagged": 2 },
  "uncertainty": "high",
  "rerun_hints": ["2/3 段质量可疑，建议复核 core_point 粒度与边界"]
}
```

- `flag`：段内 `min(granularity, boundary) < threshold`，或 `preserve_ok < 0.5`。
- `uncertainty` / `rerun_hints`：对齐 `data-contracts.md#segmentation-fallback-fields`，
  可回填到分段输出的 fallback 字段。
- `status == "skipped"` 时附 `reason`（无 key / 无段 / 调用失败），调用方应继续流程。

## 5. dev 实测结论（2026-10 · jev-1.13.0）

对 3 段构造样本（其中 s2 故意把「五分类+电阻抗法+仪器维护」塞进一段、s3 是表格但
`preserve_block:false`）：

| 段 | granularity | boundary | preserve_ok | flag | 判读 |
|---|---|---|---|---|---|
| s1 正常概念段 | 3.60 | 3.36 | 0.92 | false | 通过 |
| s2 过粗 | **1.64** | 2.92 | 0.88 | **true** | 正确识别「一段多点」 |
| s3 表格未标记保留 | 3.01 | 2.77 | **0.16** | **true** | 正确识别 `preserve_block` 错误 |

→ JEV 能准确区分「粒度过粗」与「保留标记错误」两类问题，`rerun_hints` 可直接指导重切。

## 6. 闭环建议

1. 分段产出后先跑本预检；`flag:true` 的段先按 `pedagogy.md#segmentation-methodology` 复核。
2. `granularity` 低 → 拆段（一段一可教点）；`boundary` 低 → 调整段边界；
   `preserve_ok` 低 → 修正 `preserve_block`（代码/图片/表格/引用应 true）。
3. 覆盖度 `coverage` 低 → 回源材料补齐要点或重新分段。
4. 重切后再跑一次，对比 `summary.mean` / `flagged` 是否改善（与 L3 的 `quality_score` 同构）。
