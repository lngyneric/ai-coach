# IVD Knowledge Lookup (医学垂类知识检索)

Authoritative operational reference for **L2 · knowledge layer** of medical-vertical
(IVD / 检验医学) segmentation. Active only when `delivery_constraints.domain == "medical_ivd"`.

## Purpose

Before segmenting medical-vertical material, confirm three facts from an
authoritative source rather than from prose or memory:

1. **Terminology** — canonical name / abbreviation for a test item.
2. **Reference values** — exact numeric range, unit, and exponent.
3. **System membership** — which of the six IVD systems (血液/凝血/尿液/免疫/生化/分子)
   the item belongs to.

A wrong reference value is a teaching incident (错误参考值 = 教学事故). This script
grounds the segmentation process so values are never invented.

## Quick Usage

```bash
# 分段前确认单个检验项目（输出 JSON）
python3 scripts/ivd-lookup.py "RBC"

# 人类可读输出
python3 scripts/ivd-lookup.py "血常规" --human

# 系统级检索：返回整套系统参考值（血液/凝血/尿液/免疫/生化/分子）
python3 scripts/ivd-lookup.py "凝血" --human

# 生成后校验已写入的参考值（PASS=与内置表一致；REVIEW=需人工确认）
python3 scripts/ivd-lookup.py --check "RBC 4.5-5.5×10¹²/L" --human

# 显式指定知识图谱路径（默认自动发现）
python3 scripts/ivd-lookup.py "WBC" --json /path/to/ivd-knowledge-tree.json
```

Exit codes: `0` = matched / valid check · `2` = not found / uncertain · `1` = usage error.

## Knowledge-Graph Source Resolution

`scripts/ivd-lookup.py` locates `ivd-knowledge-tree.json` in this order:

1. `--json <path>` argument (highest priority).
2. `$IVD_KNOWLEDGE_TREE` environment variable.
3. Auto-discovery of known locations, including the canonical copy at
   `/home/sysmex/worktrees/ai-shifu-dev/docs/generated/ivd-knowledge-tree.json`.
4. If none is readable, `knowledge_graph.status` becomes `not_found` and the
   script falls back to the built-in reference table only.

The knowledge graph is the course-structure ontology (domains → nodes → courses →
test_parameters). It does **not** contain reference values — those come from the
built-in table below.

## Output Contract

```json
{
  "query": "RBC",
  "matched": true,
  "uncertain": false,
  "human_review_required": false,
  "knowledge_graph": {
    "status": "found|no_match|not_found",
    "source": "ivd-knowledge-tree.json",
    "matched_domains": [{"id": "hematology", "name": "血液检验", "node_count": 4}],
    "matched_nodes": [{"id": "hematology-cbc", "name": "CBC 全血细胞计数", "test_parameters": [...]}],
    "matched_test_parameters": ["RBC", "WBC", "..."],
  },
  "reference_values": {
    "found": true,
    "match_kind": "parameter|system",
    "entries": [{"abbr": "RBC", "zh": "红细胞计数", "value": "4.5–5.5", "unit": "×10¹²/L", "confidence": "needs_medical_review"}]
  }
}
```

- `matched: false` + `uncertain: true` → the span is **not grounded by any source**;
  keep source wording verbatim, tag `uncertain(high)`, and flag for human confirmation.
- `confidence: needs_medical_review` → the value is a correct adult starting point,
  but MUST be re-verified against the authoritative textbook / clinical guideline /
  local laboratory reference interval before publish. All built-in values carry this tag.

## Built-in Reference-Value Table

All values are adult reference ranges (成人), `confidence = needs_medical_review`.

### 血液检验 (hematology / CBC)

| 缩写 | 中文全称 | 参考值 | 单位 |
|---|---|---|---|
| WBC | 白细胞计数 | 4.0–10.0 | ×10⁹/L |
| RBC | 红细胞计数 | 4.5–5.5 | ×10¹²/L |
| HGB | 血红蛋白 | 男 130–175 / 女 115–150 | g/L |
| HCT | 血细胞比容 | 男 40–50% / 女 35–45% | % |
| PLT | 血小板计数 | 125–350 | ×10⁹/L |
| MCV | 平均红细胞体积 | 80–100 | fL |
| MCH | 平均血红蛋白量 | 27–34 | pg |
| MCHC | 平均血红蛋白浓度 | 316–354 | g/L |
| RDW-CV | 红细胞体积分布宽度 | 11.6–14.6 | % |
| RET | 网织红细胞 | 0.5–1.5 | % |
| NRBC | 有核红细胞 | 0 | /100 WBC |
| NEUT | 中性粒细胞 | 40–75 | % |
| LYM | 淋巴细胞 | 20–40 | % |
| MONO | 单核细胞 | 3–8 | % |
| EO | 嗜酸性粒细胞 | 0.5–5 | % |
| BASO | 嗜碱性粒细胞 | 0–1 | % |

### 凝血检验 (coagulation)

| 缩写 | 中文全称 | 参考值 | 单位 |
|---|---|---|---|
| PT | 凝血酶原时间 | 11–14 | s |
| INR | 国际标准化比值 | 0.8–1.2 | — |
| APTT | 活化部分凝血活酶时间 | 25–35 | s |
| TT | 凝血酶时间 | 16–18 | s |
| FIB | 纤维蛋白原 | 2.0–4.0 | g/L |
| D-Dimer | D-二聚体 | <0.5 | mg/L |
| AT-III | 抗凝血酶Ⅲ | 80–120 | % |

### 尿液检验 (urinalysis)

| 缩写 | 中文全称 | 参考值 | 单位 |
|---|---|---|---|
| SG | 尿比重 | 1.003–1.030 | — |
| 尿pH | 尿酸碱度 | 4.5–8.0 | — |
| 尿蛋白 | 尿蛋白定性 | 阴性 | — |
| 尿糖 | 尿糖定性 | 阴性 | — |
| 尿酮体 | 尿酮体定性 | 阴性 | — |
| 尿胆原 | 尿胆原 | 阴性～弱阳性 | — |
| 尿胆红素 | 尿胆红素 | 阴性 | — |
| 尿RBC | 尿红细胞 | 0–3 | /HPF |
| 尿WBC | 尿白细胞 | 0–5 | /HPF |

### 生化检验 (biochemistry)

| 缩写 | 中文全称 | 参考值 | 单位 |
|---|---|---|---|
| ALT | 丙氨酸氨基转移酶 | 7–40 | U/L |
| AST | 天冬氨酸氨基转移酶 | 8–40 | U/L |
| TBIL | 总胆红素 | 3.4–17.1 | μmol/L |
| ALB | 白蛋白 | 40–55 | g/L |
| TP | 总蛋白 | 60–80 | g/L |
| Cr | 血肌酐 | 男 57–111 / 女 41–81 | μmol/L |
| BUN | 尿素氮 | 2.9–8.2 | mmol/L |
| FPG | 空腹血糖 | 3.9–6.1 | mmol/L |
| TC | 总胆固醇 | <5.2 | mmol/L |
| TG | 甘油三酯 | <1.7 | mmol/L |
| HDL-C | 高密度脂蛋白胆固醇 | >1.0 | mmol/L |
| LDL-C | 低密度脂蛋白胆固醇 | <3.4 | mmol/L |

### 免疫检验 (immunoassay)

| 缩写 | 中文全称 | 参考值 | 单位 |
|---|---|---|---|
| CRP | C反应蛋白 | <8 | mg/L |
| hs-CRP | 超敏C反应蛋白 | <3 | mg/L |
| AFP | 甲胎蛋白 | <7 | ng/mL |
| CEA | 癌胚抗原 | <5 | ng/mL |
| CA125 | 糖类抗原125 | <35 | U/mL |
| CA19-9 | 糖类抗原19-9 | <37 | U/mL |
| PSA | 前列腺特异性抗原 | <4 | ng/mL |
| HBsAg | 乙肝表面抗原 | 阴性 | — |
| HCV-Ab | 丙肝抗体 | 阴性 | — |

### 分子检验 (molecular)

Quantitative molecular reference values depend on the reagent kit / platform —
always resolve manually before publish (发布前必须人工确认).

## Fallback Flow (检索失败回退)

When a query returns `matched: false` / `uncertain: true`:

1. Keep the source wording **verbatim** (do not "fix" or round the value).
2. Mark the span `uncertain` (high) per
   `references/data-contracts.md#fallback-output-extensions`.
3. Record a `rerun_hint` telling the author which authoritative input would resolve
   it (e.g. 权威教材 / 临床指南 / 试剂说明书).
4. Never invent a reference value or unit.

## Segmentation Integration

See `references/pedagogy.md#medical-vertical-segmentation-rules` rule 6: run the
lookup for every reference-value / terminology span **before** segmenting, and for
each new test item to resolve its system membership.
