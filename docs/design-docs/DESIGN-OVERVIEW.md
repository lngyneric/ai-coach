# AI-Coach 企业大学 · 设计规划总览

> 统一门户 · 培训全流程 · 开放平台 · AI 驱动
> 更新：2026-08-04 · 对应 coach-lab/docs 设计文档集

## 需求总览

| # | 需求 | 文档 | 状态 |
|---|------|------|------|
| 1 | 统一门户招牌 | portal.html + brand-vi.html + design-system.css | ✅ |
| 2 | 数据/人员可选 + 三平台合一 + 企微提醒 + 看板 | req3-consolidated.md + management-dashboard.html | ✅ |
| 3 | 全员覆盖 + 领导可查 + 历史归档 + 数据库重整 | req3-full-coverage.md + data-migration-plan.md | 🟡 |
| 4 | 分析报告（总结→展开 + 部门征询 + 定制化） | req4-report-engine.md + ReportEnhancements.tsx | 🟡 |
| 5 | 人·课件·报告整合 + 角色定制 | req5-consolidated.md + ProfileView(规划) | 🟡 |
| 6 | 版面美化 + 分权限查看 | req6-theme-permissions.md + permissions.ts | 🟡 |
| 7 | 开放平台 + 微服务 + 标准接口 | req7-external-integration.md | ⏳ |
| 8 | AI 功能（课件/对话/推荐/路径/问答/ASR） | req8-ai-capabilities.md | 🟡 |

## 核心设计决策

### 1. 统一门户（招牌）
- `portal.html` 单入口：品牌 Logo + 愿景 + 课程推介 + 角色入口
- `design-system.css`：5 个 CSS 变量全局换装（品牌色/名称/域名/字体/圆角）
- 三平台（学习/教练/看板）整合为单系统壳，按角色动态渲染菜单

### 2. 数据与权限
- 单一 MySQL 实例（main:3306 / dev:3307 / coach:3308 隔离）
- 5 角色 RBAC：admin / hr / dept_head / coach / learner（9 个能力标志）
- 组织穿透：`supervisor_bid` 递归查询，领导可查下属培训
- 内容准入：`is_certifier` + 课程认证状态机（draft→pending→certified）

### 3. 培训闭环
- 6 阶段生命周期：待入职→入职中→带教中→评估中→已完成→归档
- ph-000 入职确认（19 项）/ ph-001~003 三个明白（38 验收 / 四维评分）
- 1v1 三环面谈（课前→面谈→课后 AI 总结）
- 合规控制点：导师签字 / 记录同步 / 改进计划

### 4. 报告体系
- 分层引擎：L2 KPI 看板 → L1 部门/角色明细 → L0 个体报告
- 总结→展开：ExpandableSummary + CustomReportCharts
- 部门征询：DepartmentFeedback（建表闭环，规划中）
- 角色定制：report_templates JSON（5 角色 × 模块列表，规划中）

### 5. 企业微信集成
- SmartSheet 3 子表（阶段进度/验收明细/面谈记录）实时同步
- SmartPage 报告自动生成分发
- 催办/提醒统一走企业微信消息（wecom-cli）

### 6. AI 能力
- 课件生成：MarkdownFlow → 6 节课已发布（读模式 + 听模式 TTS）
- 智能推荐：岗位 40% + 能力差距 40% + 学习历史 20%
- 学习路径：阶段时间线自动生成（薄弱维度标注）
- 智能问答：KB 13 条（培训政策/产品知识）
- 流式 ASR：MediaRecorder → WebSocket 增量文本
- Pi Agent：SSE 流式对话（deepseek-v4-pro）

### 7. 开放平台
- 统一 Webhook：`POST /api/webhook`（HRIS/ERP/OA 接入）
- 标准接口：`/api/hr/sync` / `/api/finance/cost` / `/api/biz/certification`
- 开放查询：`GET /api/lookup`（人·课件·报告三合一）
- 扩展机制：`coach_roles.permissions` JSON 零代码加权限位

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 16 + Tailwind v4 + shadcn/ui + echarts |
| 后端 | Flask + MySQL 8 + Redis + Celery |
| AI | deepseek-v4-pro/flash（Opencode） |
| 企微 | wecom-cli + SmartSheet + SmartPage |
| 部署 | Docker + Nginx + Git Worktree（main/dev 隔离） |

## 参考文档

见 `WECOM-DOCS-INDEX.md`（全部设计文档的企业微信 SmartPage 索引）
