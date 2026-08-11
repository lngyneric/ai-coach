---
name: course-designer
description: "Design structured courses including syllabi, learning objectives using Bloom's taxonomy, lesson plans, and assessment rubrics. Includes task-driven design (P1) — breaking a business goal into capability gaps, knowledge network, and course path — and lesson-type templates (P2). Use when the user asks about course design, needs to create a curriculum, write learning objectives, structure educational modules, build assessment plans, or design a course around a business task."
---

# 课程设计技能

Create structured course designs with learning objectives, lesson plans, and assessments.

## 任务驱动设计（P1）· 从业务任务出发

**入口**：设计新课程时，先通过与导师的过程问答（Entry Q&A）确定课程要解决的业务任务。完整决策规则见 `references/task-driven-design.md` 与 `docs/P1P2-DESIGN.md`。

问答速查（4 问）：
- Q1 业务任务：新员工上岗 / 销售能力提升 / 合规要求 / 操作技能 / 知识更新 / 管理能力
- Q2 学员角色：sales / production / hr / qc / management / medical / general
- Q3 期望产出：能独立完成操作 / 通过考核 / 改变行为 / 掌握知识体系
- Q4 课程规模：single / series / system

**拆解流程**（五步，详见 `references/task-driven-design.md#二、拆解方法`）：

```
业务目标（Business Goal）
   └─ 能力缺口（Capability Gaps）
        └─ 知识网络（Knowledge Network）
             └─ 课程路径（Course Path：必修 / 选修 / 实操）
                  └─ 每课目标 = 能力项达成的可测结果（Bloom）
```

1. **定义业务目标** — 一句话写清可观察、可衡量的业务结果。
2. **识别能力缺口** — 目标 − 现状 = 缺口，逐项列出（当前状态 → 期望状态 → 缺口性质）。
3. **构建知识网络** — 每个能力项展开为支撑知识点；找不到支撑的知识点删除。
4. **规划课程路径** — 分组为课程，标注重修/选修/实操；顺序遵循「认知 → 行为 → 考核」。
5. **每课目标映射** — 每课学习目标用 Bloom 动词书写，可测地对应能力项达成。

**内置场景示例**（`references/task-driven-design.md#三、内置企业场景示例`）：
销售首单成交 / 新员工入职 / IVD 检验报告解读（医疗垂类强制叠加医学分段规则）。

## 课型分类模板（P2）· 按课型套用结构

课程路径中的每门课按课型模板生成结构。5 种企业课型（`references/lesson-type-templates.md`）：

| 课型 | key | MDF 骨架 | 核心交互 | 评估 |
|---|---|---|---|---|
| 入职型 | `onboarding` | 规则 → 流程演示 → 情景判断 → 承诺确认 | 单选情景判断 + 承诺 | 情景题 ≥80% |
| 产品型 | `product` | 认知 → 机制 → 对比 → 应用 → 话术演练 | 对比单选 + 应用输入 | 应用输出检查 |
| 合规型 | `compliance` | 规则 → 红线案例 → 边界判断 → 场景决策 → 签署 | 边界判断 + 签署 | 决策 100% + 回执 |
| 演练型 | `practice` | 拆解 → 示范 → 提示练习 → 独立演练 → 诊断反馈 | 输入 + 三层脚手架 | 独立演练评分 |
| 案例研讨型 | `case` | 案例 → 分析引导 → 决策选项 → 复盘对比 | 分支决策 + 复盘输入 | 决策理由 + 复盘质量 |

每种课型模板含：适用场景 / MDF 骨架 / 推荐交互 / 评估方式 / 禁止事项（详见 `references/lesson-type-templates.md`）。
课型选择由 Entry Q&A 决策树决定（`docs/P1P2-DESIGN.md#决策规则表`），可主课型 + 强化课型组合。

## 出口 · 课程 Tag

课程设计/生成完成后，按 `entry_summary` 生成 3 类 tag（`lesson_type` / `task` / `role`），
写入 `course_position_tags` 对接岗位推荐。规则与写表方案见 `references/task-driven-design.md#四、出口`。

## Workflow

1. **需求分析** - Gather requirements:
   - 运行 Entry Q&A（4 问）确定业务任务、学员角色、期望产出、课程规模
   - 明确目标受众和学习需求
   - 确定课程目标和预期成果
   - 分析现有资源和约束条件

2. **任务拆解** - Run task-driven design (P1):
   - 定义业务目标 → 识别能力缺口 → 构建知识网络 → 规划课程路径
   - 参照 `references/task-driven-design.md` 的拆解方法与内置示例

3. **内容规划** - Structure the curriculum:
   - 划分课程模块和单元
   - 确定每个模块的核心知识点
   - 按课型模板（P2）规划每课结构

4. **活动设计** - Design teaching activities:
   - 为每个知识点设计教学活动
   - 规划实践练习和项目
   - 设计互动和讨论环节

5. **评估设计** - Build assessment plan:
   - 设计评估方式和标准
   - 创建评估工具和 rubric
   - 规划评估时间点

### Example: Learning Objective (Bloom's Taxonomy)

```markdown
## Module 3: REST API Design

**Learning Objective:** By the end of this module, students will be able to:
- [Remember] List the HTTP methods and their idempotency properties
- [Understand] Explain the difference between PUT and PATCH
- [Apply] Design a RESTful API for a given resource with proper status codes
- [Analyze] Evaluate an existing API design for REST compliance violations

**Assessment:** Design a REST API for a library management system (rubric below)

| Criteria          | Excellent (4)                    | Good (3)              | Needs Work (2)         |
|-------------------|----------------------------------|-----------------------|------------------------|
| Resource naming   | Consistent plural nouns          | Mostly consistent     | Inconsistent naming    |
| HTTP methods      | Correct methods, idempotent      | Minor method misuse   | Incorrect methods      |
| Status codes      | Appropriate codes for all cases  | Missing edge cases    | Generic 200/500 only   |
```
**任务驱动版本示例**（P1 输出的能力项 → Bloom 目标）：

```markdown
## Module: 异议处理演练（支撑能力项：异议处理）

**Learning Objective:** By the end of this module, learners will be able to:
- [Apply] 能对 3 类常见异议（价格/竞品/时间）各给出 1 种应对话术
- [Evaluate] 能在模拟对话中按「共情 → 举证 → 引导」顺序完成异议处理

**Assessment:** 模拟客户提出「太贵了」，要求学员独立完成一段完整话术
| Criteria | 达标 (3) | 需练习 (2) | 未达标 (1) |
|---|---|---|---|
| 共情先行 | 先认可感受再回应 | 直接反驳 | 忽略客户情绪 |
| 举证支撑 | 用产品价值举证 | 泛泛而谈 | 无依据 |
| 引导推进 | 主动引导下一步 | 被动等待 | 话题中断 |
```

## 输出格式

课程设计应包含以下部分：

- **课程基本信息**: 课程名称、目标受众、总时长、课型（lesson_type）、业务任务（task）、学员角色（role）
- **课程目标**: 总体目标和具体学习目标（Bloom）
- **课程大纲**: 模块划分和内容概览（对应任务拆解的课程路径）
- **详细教学计划**: 每节课的教学安排（按课型模板）
- **评估方案**: 评估方式和标准
- **资源清单**: 所需的教学资源

## 最佳实践

- 从业务任务出发设计课程，避免知识点堆砌（P1）
- 按课型模板套用结构，避免所有课程长一样（P2）
- 确保学习目标清晰、可测量（使用 Bloom 动词）
- 保持内容递进，由浅入深
- 平衡理论学习和实践应用
- 评估方式应与学习目标对齐

## References

- `references/task-driven-design.md` — P1 业务任务拆解（五步方法 + 3 场景示例 + 出口 tag）
- `references/lesson-type-templates.md` — P2 课型分类模板（5 课型 × MDF 骨架 × 交互 × 评估 × 禁止事项）
- `docs/P1P2-DESIGN.md` — 设计总览（入口问答树 + 出口 tag 表 + 推荐策略）

## Keywords

课程设计, 教学大纲, 学习目标, 教学计划, 课程规划, 业务任务拆解, 课型模板, course design, syllabus, curriculum, learning objectives, Bloom's taxonomy, task-driven design, lesson types
