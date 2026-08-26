# 分层触达方案 · P1-P3 实施计划（砍需求修订版）

> 2026-08-26 · 基于《wecom-ai-coach-分层触达设计方案》实施合理性分析，
> 砍掉非必要设计，重排 P1-P3。含数据收集步骤（满足测试要求）。
> 前置分析：三层职责方向正确；约 40% 内容为二期形态；2 项有落地风险需 spike 验证。

## 一、砍掉清单（本轮决策）

| 原设计项 | 砍因 | 替代 |
|----------|------|------|
| SCM 供应商/客户进中台 | 培训系统不需要 | — |
| WebSocket 双工 | HTTP 全覆盖 | — |
| FAILED/RETRY 状态 | 首版二值+重学足够 | COMPLETED / 未完成 |
| M1 批量 upsert API + M2 变更事件 | 三机制齐上是过度设计；智能表格变更事件开放支持有限、链路不可靠 | 手动脚本 + M3 定时拉取对账 |
| R1-R3 HTTP 回调架构 | 要求公网暴露/验签/重试，偏离企微自建应用惯例 | bot 轮询 + bot 主动发消息等价实现（已闭环） |
| C1 收集流 API 接入 | bot 轮询 smartsheet 已 B1-B4 闭环 | 维持 wecom-apply-processor.sh |
| 微盘个人文件夹归档 | 🔴 微盘 API 通常仅允许写应用空间，个人文件夹受权限限制 | 结果存 ai-coach + 消息推送证书页链接（待 P1-4 spike 最终确认） |
| AI 报告 PDF + 能力曲线 | PDF 渲染新增工作量；小数据量能力曲线无意义 | HTML 报告链接推送（report 页已有） |

## 二、P1-P3 计划

### P1（立即 · 本周~W5 上线窗口）
| # | 任务 | 内容 | 验收 |
|---|------|------|------|
| P1-1 | 身份三键打通 | person_master 加 employee_no 列；HR 花名册导入；TL-1 批量建档（5 人 user 账号+LearnerProfile+mentor 绑定）；gen-wecom-name-map.sh 重跑 | 5 人三键齐全：userid↔employee_no↔learner_bid；bot dry-run learner_bid 为真实 bid |
| P1-2 | L3/L4 进度契约统一 | POST /api/shifu/coach/learning-progress（progress_pct/video_position_sec/duration_sec/quiz_scores）+ GET learning-status/{learner_bid}；映射现有 course_enrollments/learn_progress_records | curl 样例通过；状态机 assigned/active/completed 输出 |
| P1-3 | 设计文档对齐修订 | 鉴权头改 Token；C1→bot 轮询；主数据载体=MySQL 快照；R 回调→轮询形态 | 设计方案 v2 标注生效 |
| P1-4 | 两项 spike 验证 | ①微盘写个人文件夹权限实测（半天）②智能表格变更事件调研（半天） | 各出可行性结论 → 决定 P3 是否纳入 |

### P2（9 月上旬 · W6-W7 后）
| # | 任务 | 内容 | 验收 |
|---|------|------|------|
| P2-1 | M3 同步 API 化 | GET /api/coach/learners?updated_after= 兜底拉取端点 + cron 每日全量对账脚本 | 中台↔ai-coach T+1 对账一致 |
| P2-2 | Onboarding T0~T+30 | 入职欢迎卡片、必修课包开班通知、未启动催办（O3 简化）、完成率看板（O2 简化） | 新员工从建档到首课全自动 |
| P2-3 | 结果通知链接化 | 完成→bot 推送 HTML 报告/证书页链接（report 页复用） | 学员企微点开即看 |

### P3（按需 · 视 spike 结论）
| # | 任务 | 前置条件 |
|---|------|---------|
| P3-1 | 微盘归档 | P1-4① spike 通过 |
| P3-2 | M2 变更事件 | P1-4② 调研确认可行且有实时诉求 |
| P3-3 | PDF 证书生成 | 业务提出合规留痕硬需求 |
| P3-4 | T+60/T+90 转正考核流 | 秘书室流程成熟 |

## 三、数据收集步骤（满足测试要求）

### Step 1｜HR 工号台账收集（人工 · 本周）
向 HR（凌云/杨萍）索取《员工花名册》CSV，必需列：

```csv
employee_no,name,department,position_name,onboarding_date,status,wecom_mobile
10001,凌云,人力资源行政部/人事课,人事主管,2026-08-25,active,138xxxx
```
> 最小集：前 5 人（刘佳怡/凌云/杨萍/陆蓓/陈珊）；后续新员工同表追加。

### Step 2｜person_master 结构升级（SQL · 5 分钟）
```sql
ALTER TABLE `ai-shifu_dev`.person_master
  ADD COLUMN employee_no VARCHAR(32) NULL,
  ADD UNIQUE KEY uk_pm_empno (employee_no);
-- 导入后核对：
SELECT name, employee_no, wecom_userid FROM person_master WHERE employee_no IS NOT NULL;
```

### Step 3｜批量建档 TL-1（SubAgent 产出脚本 · pi 实跑）
输入花名册 CSV → 自动：
1. 建 user_users 账号（employee 登录方式，工号即登录名）
2. 建 LearnerProfile（learner_bid/user_bid/employee_no/department/position_name/onboarding_date/status=active）
3. mentor 绑定（需先确定教练指派表：谁带谁——见 Step 4）
4. 重跑 gen-wecom-name-map.sh → 姓名→learner_bid 映射 ≥5 条

### Step 4｜教练指派表收集（人工）
| 字段 | 示例 |
|------|------|
| 学员姓名 | 凌云 |
| 教练（mentor）user_bid | devcoach 或真实教练账号 |
| 生效日期 | 2026-08-26 |

### Step 5｜测试数据集与用例（联调用）
| 用例 | 数据准备 | 操作 | 验收 |
|------|---------|------|------|
| T1 闭环-任务登记 | 企微任务登记表提交 1 条（学员填"凌云"） | bot 处理器实跑 | learner_tasks.learner_bid=真实 bid（非姓名透传）；记录关单 |
| T2 闭环-面谈/评分 | 面谈总结/评教练各 1 条 | 同上 | 对应表落库 |
| T3 L3 进度上报 | P1-2 端点就绪 | curl POST progress_pct=60/video_position_sec=300 | course_enrollments 更新；status=in_progress(active) |
| T4 L4 状态查询 | 同上 | curl GET status/{learner_bid} | 返回状态机当前值 |
| T5 映射兜底 | 映射文件留空 {} | 提交学员="未知甲" | 透传不报错（容错路径） |
| T6 Spike-微盘 | 授权人身份 | wecom-cli drive 尝试写个人文件夹 | 记录 成功/受限 结论 |
| T7 Spike-表格事件 | 文档调研 | 企微开放平台变更事件清单核对 | 有/无 可行结论 |

### Step 6｜执行顺序与责任
```
D+0  Step1 向 HR 要花名册（pi 起草需求发凌云）   ┐ 人工
D+0  Step4 教练指派表确认                        ┘
D+1  Step2 ALTER TABLE（pi 直接执行）
D+1  Step3 SubAgent 写 batch-init 脚本 → pi 实跑
D+2  P1-2 SubAgent 写 L3/L4 端点 → pi 部署自测
D+2  P1-4 双 spike（pi 执行）
D+3  Step5 测试用例 T1-T7 全量回归 → 出测试报告
```

## 四、关联文档
- 原设计方案：`coach-lab/docs/wecom-ai-coach-分层触达设计方案.md`（P1-3 修订对象）
- 建档设计：`ai-shifu-dev/docs/LEARNER-PROFILE-ONBOARDING.md`（TL-1/TL-2 并入本计划）
- 闭环验证：`ai-shifu-dev/docs/COACH-API-MAPPING.md`（六）