# Coach 系统进阶设计

## 1. 1v1 互动模型

```
┌────────────────────────────────────────────────────────────┐
│                     Coach Session                          │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐   │
│  │ 课前准备     │ → │ 面谈交互    │ → │ 课后总结      │   │
│  │ - 课件推荐   │   │ - 教练辅导   │   │ - AI 汇总     │   │
│  │ - 目标设定   │   │ - 学员追问   │   │ - 进度跟踪    │   │
│  └─────────────┘    └─────────────┘    └──────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### 数据模型扩展

```sql
-- 面谈记录（现有 coach_sessions）
-- 扩展字段
ALTER TABLE coach_sessions ADD COLUMN pre_course_bids TEXT;       -- 课前推荐课件
ALTER TABLE coach_sessions ADD COLUMN learner_questions TEXT;     -- 学员追问内容
ALTER TABLE coach_sessions ADD COLUMN ai_summary TEXT;            -- AI 自动汇总
ALTER TABLE coach_sessions ADD COLUMN coach_rating INT;           -- 本场评分 1-100
ALTER TABLE coach_sessions ADD COLUMN next_action TEXT;           -- 后续行动建议

-- 新增学员反馈表
CREATE TABLE coach_feedback (
  feedback_bid VARCHAR(32) PRIMARY KEY,
  session_bid VARCHAR(32) NOT NULL,
  learner_bid VARCHAR(32) NOT NULL,
  question TEXT NOT NULL,           -- 追问内容
  category VARCHAR(20),             -- 技术/管理/产品等分类
  ai_answer TEXT,                   -- AI 辅助回答
  resolved TINYINT DEFAULT 0,       -- 是否已解决
  created_at DATETIME
);
```

## 2. AI 跟踪报告

每个阶段完成时自动生成报告：

| 报告项 | 数据来源 |
|--------|----------|
| 学员参与度 | 面谈次数、时长、提问数 |
| 知识点覆盖 | 课件学习进度、追问分类 |
| 能力提升曲线 | 评分变化趋势（多阶段对比） |
| 待改进项 | AI 分析面谈记录提取 |
| 建议行动 | AI 基于历史数据生成 |

## 3. 百分比评分体系

```
总评 = 教练评分(40%) + 学员自评(20%) + AI 评估(20%) + 课件完成度(20%)
```

每个维度满分 100，加权计算最终分数。

## 4. 课程推荐引擎

带教完成后，AI 根据以下维度推荐后续课程：
- 带教期间的知识薄弱点（追问分类分析）
- 学员岗位需求（从 learner_profiles 获取）
- 同阶段学员的后续课程选择（协同过滤）

## 实施步骤

### Phase 1 — 数据库扩展
- 扩展 `coach_sessions` 表字段
- 创建 `coach_feedback` 表

### Phase 2 — API 扩展
- `POST /api/coach/session` — 创建面谈记录（含推荐课件）
- `POST /api/coach/feedback` — 学员提交追问
- `GET /api/coach/report/{id}` — AI 跟踪报告
- `GET /api/coach/recommendations/{id}` — 课程推荐

### Phase 3 — AI 集成
- 面谈后自动调用 LLM 生成汇总
- 阶段完成时自动生成评分报告
- 带教结业时自动推荐课程

### Phase 4 — 前端
- 教练端：面谈记录表单 + 评分面板
- 学员端：提问入口 + 进度看板
- 报表页：可视化报告
