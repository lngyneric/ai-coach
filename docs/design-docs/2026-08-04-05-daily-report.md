# AI-Coach 工作日报 · 2026-08-04/05

> 生成时间：2026-08-05 01:10 · 更新人：Reasonix（dev 分支）
> 覆盖：WeCom 文档发布 / 需求文档补齐 / Subagent 看板 / dev-prd 数据库隔离 / metering 修复 / P0 协作

---

## 一、企业微信文档发布（全部完成）

### 1.1 设计文档批量发布
- **30 份设计文档**全部发布为企业微信 SmartPage（含 DESIGN-OVERVIEW 总览）
- 索引：`WECOM-DOCS-INDEX.md`（34 条，docid + URL 全表）
- 批量脚本：`scripts/gen-wecom-smartpages.sh`（可复用，间隔 1s 防限流）

### 1.2 req1/req2 需求分析补充
- **req1-unified-portal.md**：统一门户招牌（品牌首页/主题系统/课程市场/i18n）
  - SmartPage：https://doc.weixin.qq.com/smartpage/a1_AIAAjHiMALACN6ikb1icrTQeSCbL3_a
- **req2-data-permissions.md**：数据/人员可选 + 三平台合一 + 企微提醒 + 看板
  - SmartPage：https://doc.weixin.qq.com/smartpage/a1_AIAAjHiMALACNn0aHSepoSnO5ZDHe_a
- DESIGN-OVERVIEW 映射修正（req2 → req2-data-permissions.md），企微版已重新发布
  - https://doc.weixin.qq.com/smartpage/a1_AIAAjHiMALACNCVKtP8qDSZ0Nt1uX_a

### 1.3 8 条需求全覆盖 ✅
req1 ✅ req2 ✅ req3 ✅ req4 ✅ req5 ✅ req6 ✅ req7 ✅ req8 ✅ —— 全部有独立文档 + 企微 SmartPage

---

## 二、Subagent 运行看板（新增）

### 2.1 实现
| 文件 | 作用 |
|------|------|
| `docker/gen-subagent-status.py` | 采集器：reasonix goal-state + ps + P0 产物 + **Pi 会话解析** |
| `docker/subagent-dashboard.html` | 看板页：运行中/会话/Pi 调用/P0 产物，10s 自动刷新 |
| `docker/subagent-status.json` | 采集结果（nginx serve，no-store） |

### 2.2 访问
**http://10.32.16.47:8082/subagent-dashboard.html**

### 2.3 Pi × Reasonix 协作识别
- Pi 会话中解析出 **8 次 subagent 调用**（全部 p0-permission-designer，06:00→06:39）
- P0 产物 6 份：DESIGN-REVIEW / DESIGN-CORRECTION / PERMISSION-MODEL-UPGRADE / EXECUTION-1-LOGIN-FIX / EXECUTION-3-ORM / REVIEW-PI-EXECUTION / PERMISSION-KEYS

---

## 三、dev-prd 数据库隔离（方案 B · 重大安全修复）

### 3.1 背景
dev api 的 `SQLALCHEMY_DATABASE_URI` 指向 `ai-shifu-mysql:3306/ai-shifu`，容器 DNS 解析到**生产库**（172.18.0.3），dev 开发直接读写生产数据。

### 3.2 修复
| 项 | 生产 (PRD) | 开发 (DEV) |
|----|-----------|-----------|
| MySQL 容器 | ai-shifu-mysql (172.18.0.3) | docker-ai-shifu-mysql-dev-1 (172.18.0.4) |
| 数据库 | ai-shifu | **ai-shifu_dev**（新建） |
| 表结构 | 76 表 + 47 用户 | 76 表（schema 导出导入，**数据全空**） |
| API 连接 | ai-shifu-mysql:3306/ai-shifu | ai-shifu-mysql-dev:3306/ai-shifu_dev |

### 3.3 验证
- dev 登录 sch11111 → 数据落 **dev 库**（user_users=1）
- **生产库 47 条不变**（零污染）✅
- api/worker/beat 三服务全部连 dev 库 ✅

### 3.4 提交
- `efe5549cc`（compose URI 隔离）
- `9a4abb4ff`（WORKTREE-DEV-SETUP.md 隔离说明）

---

## 四、metering trace_id 修复

### 4.1 根因
`MockClient.__getattr__` 对任何属性返回**函数对象** → `getattr(span, "trace_id")` 拿到函数 → 写 bill_usage 报 `Data too long`。

### 4.2 修复
`src/api/flaskr/api/langfuse.py`：MockClient 增加 `_scalar_attrs`（14 个标量属性返回 `""`），保留链式调用。

### 4.3 验证
- `Usage metering persist failed` → **0**（修复前每次 LLM 调用都报）
- 登录 code=0 ✅ · courses/login 200 ✅
- 镜像重建：aishifu/ai-shifu-api:patched（新 ID 106b447b669d）
- 提交：`ccbfaf36d`

### 4.4 配套：dev 库补列（dev 代码领先生产 schema）
- `user_users.is_certifier`（TINYINT default 0）
- `user_users.creator_activated_at`（DATETIME NULL）

---

## 五、端口核查结论

| 端口 | 归属 | 状态 |
|------|------|------|
| 80/443/8080 | PRD nginx | ✅ 与 dev 分离 |
| 3306 | PRD MySQL | ✅ |
| 8082/5800/3307/6380 | DEV | ✅ |
| 3100 | dev loki 配置（未运行）| ⚠️ 被 next-server 占用 |
| 3106/3107 | coach-lab 双实例 | ⚠️ 疑似残留 |
| 3308 | coach-mysql（P0 审查专用）| ✅ 独立 |

---

## 六、今日提交（dev 分支）

```
ccbfaf36d fix MockClient scalar attrs ... (trace_id)
9a4abb4ff docs: record dev DB isolation setup
efe5549cc isolate dev DB ... away from production
b03396ca4 dashboard: show Pi-invoked subagent calls
211a7012f document subagent dashboard usage
cc09852ea add subagent monitoring dashboard
0a49060fd fix req2 doc mapping; refresh WeCom smartpage
438aeb989 add req1/req2 design docs to WeCom index
f1ce394f6 add WeCom SmartPage index + design overview
```

---

## 七、遗留 TODO

1. **P0 登录授权修复**（Pi 协作中）：P0-EXECUTION-1-LOGIN-FIX 已产出，ORM 阶段（EXECUTION-3）进行中
2. **plugin 加载错误**（非本次引入）：
   - `course_enrollments already defined`（learning_portal 插件）
   - `admin.py:1529 '(' was never closed`（shifu 插件语法错误）
   - `flaskr/plugins 目录不存在`
3. **cron 自动刷新**：subagent-status 需 root 权限；当前手动刷新
4. **coach-lab 3107 残留**：确认后关闭释放端口
5. **loki 3100 冲突**：若启用需处理占用进程

---

*文档路径：/home/sysmex/ai-coach/docs/2026-08-04-05-daily-report.md*
