# P1 · 业务任务拆解（Task-Driven Design）

> 配套 skill：`course-designer`（主）/ `ai-shifu-course-creator`（生成）
> 入口：`docs/P1P2-DESIGN.md` §1 问答决策树（Entry Q&A）→ `entry_summary`
> 出口：本文件 §4 课程 tag 对接（`lesson_type` / `task` / `role` → `course_position_tags`）
> 方法论来源：TeachAny PBL 拆解引擎（业务目标 → 知识网络 → 学习路径），企业培训化改造。

---

## 一、为什么需要任务拆解

企业培训课程最普遍的失败模式是「知识点堆砌」——讲师按资料目录平铺内容，
学员学完「知道了很多」却「不会做」。任务驱动设计（Task-Driven Design）反过来：

**从业务任务出发，倒推课程应该教什么、练什么、考什么。**

```
业务目标（Business Goal）
   └─ 能力缺口（Capability Gaps）        ← 目标 vs 现状的差距（要补什么）
        └─ 知识网络（Knowledge Network） ← 支撑各能力项的知识点/概念
             └─ 课程路径（Course Path）  ← 必修 / 选修 / 实操，映射 MDF 每课
```

核心原则：**一门课程的价值 = 它让学员在真实业务任务上的表现提升，而不是「学完了」。**

---

## 二、拆解方法（五步）

### Step 1 · 定义业务目标

用一句话写清楚课程要支撑的业务结果，必须是**可观察、可衡量**的：

- 好：`新销售在入职 30 天内独立完成首单成交`
- 好：`检验人员在 2 周内能独立出具 10 项常规检验报告并正确判读`
- 差：`提升销售能力`（不可衡量） / `学习检验知识`（无业务指向）

### Step 2 · 识别能力缺口

业务目标 − 学员现状 = 能力缺口。逐项列出，每项写清楚 **当前是什么 → 期望是什么**：

| 能力项 | 当前状态 | 期望状态 | 缺口性质 |
|---|---|---|---|
| 产品知识 | 说不出产品卖点 | 能讲清 3 大卖点 + 适用边界 | 认知缺口 |
| 开场话术 | 只会自我介绍 | 能在 1 分钟内建立专业信任 | 行为缺口 |
| 异议处理 | 遇到价格异议就卡壳 | 能按「先共情→再举证→后引导」应对 | 行为缺口 |
| 成交动作 | 不会主动要求下单 | 能自然推进到成交确认 | 行为缺口 |

### Step 3 · 构建知识网络

把每个能力项展开成它需要支撑的知识点，形成「知识点 → 能力项」的支撑网络。

```
能力项：能讲清 3 大卖点 + 适用边界
  ├─ 知识点1：产品核心参数与优势
  ├─ 知识点2：与竞品的差异对比
  ├─ 知识点3：适用场景与边界（哪些情况不适用）
  └─ 知识点4：常见客户画像与痛点
```

- 每个知识点必须回答：**它支撑哪个能力项？** 找不到支撑的知识点 → 删除（避免知识点堆砌）。
- 知识点之间允许前置依赖（A 学完才能学 B），在课程路径中体现。

### Step 4 · 规划课程路径

把知识点分组为课程，标注重修/选修/实操：

| 课 | 课型（P2） | 支撑能力项 | 性质 | 课程目标（Bloom，可测） |
|---|---|---|---|---|
| L01 产品认知 | product | 产品知识 | 必修 | [Understand] 能列出 3 大卖点并解释其客户价值 |
| L02 客户分析与开场 | practice | 开场话术 | 必修 | [Apply] 能针对给定客户画像写出 30 秒开场话术 |
| L03 异议处理演练 | practice | 异议处理 | 必修 | [Apply] 能对 3 类常见异议各给出 1 种应对 |
| L04 成交与跟进 | practice | 成交动作 | 必修 | [Apply] 能完成一次完整的成交模拟对话 |
| L05 竞品对比深潜 | product | 产品知识（深） | 选修 | [Analyze] 能对比 2 个竞品并给出差异化打法 |

**路径规则**：
- 必修课覆盖核心能力缺口，选修课覆盖深化/扩展，实操课验证行为层能力。
- 路径顺序遵循「认知 → 行为 → 考核」递进（先懂再会再达标）。
- 一门课的课程目标 = 能力项达成的可测结果，写作用 Bloom 动词（与 course-designer 的 Bloom 目标写法完全一致）。

### Step 5 · 每课目标映射（对接 course-designer）

课程路径确定后，每课的教学目标直接成为 course-designer 的模块目标输入：

```
任务拆解输出                    course-designer 输入
能力项「异议处理」        →    Module: 异议处理演练
知识点「共情-举证-引导」 →    学习目标（Bloom）+ 教学活动 + 评估
课程目标（可测）         →    Assessment rubric（评估标准）
```

> 一致性校验：course-designer 产出 syllabus 后，逐课核对「本课学习目标是否可测地对应任务拆解里的能力项」。
> 出现「学了但能力项没覆盖到」或「能力项无对应课程」→ 回 Step 2/4 修正，不允许静默通过。

---

## 三、内置企业场景示例

### 示例 A · 销售首单成交（task:new-sales / role:sales / 主课型 practice + product）

**业务目标**：新销售入职 30 天内独立完成首单成交。

**能力缺口**：产品知识（认知）/ 开场话术（行为）/ 异议处理（行为）/ 成交动作（行为）。

**知识网络**：产品 3 大卖点 + 适用边界 → 客户画像与痛点 → 竞品差异 → 话术模板 → 异议类型库 → 成交信号识别。

**课程路径**：
| 课 | 课型 | 性质 | 课程目标（Bloom） |
|---|---|---|---|
| L01 产品认知 | product | 必修 | [Understand] 能解释 3 大卖点并说明适用边界 |
| L02 客户分析与开场 | practice | 必修 | [Apply] 能为给定画像写出 30 秒开场话术 |
| L03 异议处理演练 | practice | 必修 | [Apply] 能应对 3 类常见异议 |
| L04 首单成交模拟 | practice | 必修 | [Apply] 能完成一次完整成交模拟并复盘 |
| L05 竞品对比深潜 | product | 选修 | [Analyze] 能给出差异化打法 |

### 示例 B · 新员工入职（task:onboarding / role:general / 主课型 onboarding）

**业务目标**：新员工入职第 1 周完成公司文化、制度、岗位基本流程认知，具备独立办理日常事务能力。

**能力缺口**：公司制度认知（认知）/ 关键流程操作（行为）/ 安全与合规红线（认知+行为）。

**知识网络**：企业文化与价值观 → 考勤/报销/请假制度 → 岗位主流程 → 安全与合规红线 → 常用系统操作。

**课程路径**：
| 课 | 课型 | 性质 | 课程目标（Bloom） |
|---|---|---|---|
| L01 认识公司 | onboarding | 必修 | [Understand] 能说出企业文化与组织架构 |
| L02 制度速通 | onboarding | 必修 | [Apply] 能在 3 个日常场景中选对制度处理方式 |
| L03 岗位流程演练 | practice | 必修 | [Apply] 能独立走完主流程的关键步骤 |
| L04 安全与合规红线 | compliance | 必修 | [Analyze] 能识别红线场景并做出合规决策 |
| L05 常用系统实操 | practice | 选修 | [Apply] 能完成常用系统的标准操作 |

### 示例 C · IVD 检验报告解读（task:ivd-report / role:medical / 主课型 practice + product）

> 医疗垂类：必须叠加 `delivery_constraints.domain == "medical_ivd"`，参考值/术语走 `pedagogy.md#medical-vertical-segmentation-rules` + `scripts/ivd-lookup.py`，零误差容忍。

**业务目标**：检验人员能独立、正确解读常规检验报告（血液/凝血/尿液等），给出临床意义与复检建议。

**能力缺口**：报告结构认知（认知）/ 参考值判读（认知+行为）/ 异常结果临床意义（认知）/ 复检决策（行为）。

**知识网络**：报告项目与单位 → 各系统参考值 → 异常模式 → 临床意义 → 复检指征。

**课程路径**：
| 课 | 课型 | 性质 | 课程目标（Bloom） |
|---|---|---|---|
| L01 报告结构认知 | product | 必修 | [Understand] 能识别报告各项目与单位 |
| L02 参考值判读 | practice | 必修 | [Apply] 能对给定 CBC 报告判断正常/异常 |
| L03 异常结果临床意义 | product | 必修 | [Analyze] 能解释常见异常模式的临床意义 |
| L04 复检决策演练 | practice | 必修 | [Evaluate] 能依据规则给出复检/备注建议 |
| L05 疑难报告案例 | case | 选修 | [Evaluate] 能对综合案例给出完整判读结论 |

---

## 四、出口 · 课程 tag 与推荐对接

### 4.1 三类 tag 生成

课程生成/更新后自动生成（入口问答已采集 Q1/Q2/Q3）：

| Tag | 取值 | 示例 |
|---|---|---|
| `lesson_type:<课型>` | 主课型（Q1×Q3 决策） | `lesson_type:practice` |
| `task:<业务任务>` | 业务任务 code | `task:new-sales` / `task:onboarding` / `task:ivd-report` |
| `role:<岗位>` | 学员角色码（对齐推荐 position 码） | `role:sales` / `role:medical` / `role:general` |

任务 code 建议（可扩展）：
`new-sales` / `onboarding` / `compliance` / `ops`（操作技能）/ `knowledge-update` / `management` / `ivd-report` / `product-knowledge`。

### 4.2 写表方案（course_position_tags，零代码改动）

```
course_position_tags 行：
  shifu_bid      = <课程 BID>
  position       = role tag（sales/production/hr/qc/management/medical/general）
  position_name  = role 中文名
  tag            = "lesson_type:<type>|task:<task>"    ← 组合串（竖线分隔）
  weight         = 基础 10；task 契合 +5；lesson_type 契合 +3（见 4.3）
  is_active      = 1
```

- 推荐引擎现有逻辑 `position` 精确匹配 → `weight` DESC 排序，**无需改代码**。
- 多岗位课程写多行（position 不同）；同一 (shifu_bid, position) 更新时 upsert。

### 4.3 推荐权重规则表

| 匹配层 | 匹配条件 | weight | 排序效果 |
|---|---|---|---|
| L1 岗位精确 | 学员岗位 = position | 10 | 基线 |
| L2 课型契合 | 学员阶段命中 tag 内 lesson_type | 13 | 优先于 L1 |
| L3 任务契合 | 学员业务线命中 tag 内 task | 15 | 最优先 |
| 兜底 | 岗位不可识别 → general 桶 | — | 现有逻辑 |

### 4.4 扩展建议（文档化，不落代码）

若需学员侧动态推荐（按学习阶段），可在 recommend.py 读取 `learner_profiles.onboarding_date /
probation_end_date` 推断「新员工/在职」，再据 `tag` 内 `lesson_type` 二次加权。**当前版本仅文档化，不实现。**

---

## 五、与现有 skill 的一致性

- 拆分出的知识点/每课，必须满足 `course-designer` 的 Bloom 目标 + syllabus 输出规范（每课目标 = 能力项达成的可测结果）。
- 课型选择必须与 `lesson-type-templates.md` 的 5 课型一致；特殊场景可组合（主课型 + 强化课型）。
- 医疗垂类示例 C 强制叠加 `medical_ivd` 领域规则，不得绕过参考值/术语校验。
- 教学法约束（ABT/五透镜/脚手架/诊断反馈）在每课生成时由 `pedagogy.md` 统一约束，本文档不重复定义。
