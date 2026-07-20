# 带教进度管理系统设计

## 核心逻辑

```
带教 ≠ 课程（Course）
带教 = 一对一带教进度 tracking + 评估 + 阶段小结

每个学员有独立带教计划
每个阶段有 checklist 验收项
导师评分 + 学员自评 → 阶段评估 → 小结报告
```

## 数据模型（已有）

| 表 | 用途 |
|------|------|
| `mentorship_phases` | 带教阶段定义（含通过分数线） |
| `learner_mentorship` | 学员带教进度（理论/实践/同伴/导师评分） |
| `mentorship_checklist` | 阶段验收清单项 |
| `learner_checklist_items` | 学员完成验收记录（含评分） |
| `mentor_sessions` | 带教面谈记录（需要新增） |

## 需要新增的 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/portal/mentor/phases/<learner_bid>` | GET | 查看学员各阶段进度详情 |
| `/api/portal/mentor/feedback` | POST | 提交阶段小结评估 |
| `/api/portal/mentor/report/<learner_bid>` | GET | 生成带教分析报表 |
| `/api/portal/mentor/sessions` | POST/GET | 记录/查看带教面谈 |
| `/api/portal/mentee/dashboard` | GET | 学员端学习看板 |

## 报表内容

带教分析报表包含：
1. 学员基本信息
2. 各阶段完成情况（进度条 + 状态标签）
3. 各阶段评分明细表（理论/实践/导师评分）
4. checklist 完成率统计
5. 面谈记录时间线
6. 导师评语汇总
7. 阶段小结 PDF 导出

## 实施步骤

### Phase 1 — API 扩展
- 新增 3 个 mentor API 端点（phase detail / feedback / report）
- 新增 `mentor_sessions` 表
- 扩展 `learner_mentorship` 支持阶段小结

### Phase 2 — 前端看板
- 扩展 `mentor.html`：学员阶段进度详情、评分表单、面谈记录
- 新增学员端 `mentee-dashboard.html`

### Phase 3 — 报表生成
- 实现带教分析报表 HTML 页面
- 支持打印/导出

## 流程

```
学员完成阶段 checklist 项
       ↓
导师评分（pending scores）
       ↓
学员自评（feedback）
       ↓
阶段小结 / 评估报告
       ↓
进入下一阶段 / 改进计划
```
