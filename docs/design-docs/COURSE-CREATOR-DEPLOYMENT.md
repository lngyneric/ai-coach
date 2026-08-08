# Course Creator Skill · Agent 部署手册

> 生成：2026-08-06 · 用途：把 ai-shifu-course-creator 打包部署到任意智能体 agent
> 供 Pi 读取评估 · 原文：`/home/sysmex/worktrees/coach-lab/docs/COURSE-CREATOR-DEPLOYMENT.md`

---

## 一、Skill 资源位置

| 位置 | 版本/用途 |
|------|-----------|
| `~/.agents/skills/ai-shifu-course-creator/` | 官方版（516 行 SKILL.md + 1390 行 CLI + 9 references） |
| `~/.reasonix/skills/sysmex-course-creator/` | Sysmex 定制版（含 setup.sh 部署脚本） |
| `~/.fastclaw/skills/sysmex-course-creator/` | FastClaw 版 |
| `~/.trae/skills/ai-shifu-course-creator/` | Trae 版 |
| `~/.openclaw/skills/ai-shifu-course-creator/` | OpenClaw 版 |
| `worktrees/ai-shifu-dev/skill-packages/ai-shifu-course-creator.tar.gz` | **打包分发版（68KB）** |

## 二、API 调用分解（如何生成课件）

### Pipeline

```
素材 → 编排 → 生成 → 优化 → 部署 → 分析
```

### 核心 API（shifu-cli.py 封装，base = {SHIFU_BASE_URL}/api/shifu）

| 步骤 | CLI 命令 | HTTP 调用 | 说明 |
|------|----------|-----------|------|
| 登录 | `login_employee` | `POST /api/user/login_employee` | employeeNo+password → JWT |
| 建课 | `create` | `PUT /shifus` | {name, description} → shifu_bid |
| 建章 | `add-chapter` | `PUT /shifus/{bid}/outlines` | 章节节点 |
| 建课 | `add-lesson` | `PUT /shifus/{bid}/outlines` | 课节节点（teaching_prompt） |
| 更新 | `update_lesson` | `PUT /shifus/{bid}/outlines` | 课件内容更新 |
| 导入 | `import` | `PUT /shifus` + `PUT /shifus/{bid}/outlines` | 批量导入 JSON |
| 发布 | `publish` | `POST /shifus/{bid}/publish` | 上线 |
| 查询 | `list` | `GET /shifus` | 课件列表 |
| 明细 | `show` | `GET /shifus/{bid}/detail` | 课件详情 |
| 权限 | `permissions` | `GET/POST /shifus/{bid}/permissions*` | 授权管理 |
| 分析 | `analytics-query` | `POST /api/creator-analytics/query` | DSL 数据查询 |

### 课件生成本质

1. **本地 build**：MarkdownFlow 素材目录（lesson-*.md + course prompt）→ import JSON（无网络）
2. **远端 import + publish**：PUT 到平台 + 发布

### 认证

- `.env` 存 `SHIFU_TOKEN` + `SHIFU_BASE_URL`
- employee 登录自动授予 is_creator + is_operator

## 三、打包结构（tar.gz 68KB）

```
ai-shifu-course-creator/
├── SKILL.md              ← agent 认知层（触发词+流程+规则）
├── scripts/
│   ├── shifu-cli.py      ← API 封装（唯一网络入口）
│   └── mdf-proxy.py      ← MDF 渲染代理（可选）
├── references/           ← 知识库（MDF 语法/教学法/数据契约/CLI 参考）
├── examples/             ← 6 种使用场景示例
├── evals/                ← 触发评估
├── .env                  ← SHIFU_TOKEN + SHIFU_BASE_URL
├── setup.sh              ← 一键部署（pip + env + chmod + 连通性检查）
└── requirements.txt      ← 依赖（仅 requests）
```

## 四、部署到各 Agent

| Agent | 部署路径 | 机制 |
|-------|----------|------|
| Reasonix | `~/.reasonix/skills/<name>/` | SKILL.md + scripts，run_skill 调用 |
| FastClaw | `~/.fastclaw/skills/<name>/` | 同上（已有 sysmex 版） |
| Trae | `~/.trae/skills/` | 同上（已有） |
| OpenClaw | `~/.openclaw/skills/` | 同上（已有） |
| **Pi** | `~/.pi/agent/skills/` 或插件机制 | Pi extension + slash 命令（**待部署**） |

### 部署步骤（每个新 agent）

```bash
# 1. 解包
tar xzf ai-shifu-course-creator.tar.gz -C <agent_skills_dir>/
# 2. 初始化
cd <agent_skills_dir>/ai-shifu-course-creator && bash setup.sh
# 3. 配置
vi .env   # 设 SHIFU_TOKEN + SHIFU_BASE_URL
# 4. 验证
python3 scripts/shifu-cli.py list
```

## 五、待评估事项（供 Pi）

1. **Pi 的 skill 加载机制**：Pi (earendil-works/pi) 是否支持 skill 目录直读，还是需要 extension 封装
2. **token 管理**：Pi 部署时 SHIFU_TOKEN 存放与刷新策略
3. **多 agent 共用 token**：reasonix/fastclaw/trae/pi 是否共用同一 .env 或各自独立
4. **本地端点**：sysmex 版 base_url = http://eu.sysmex.com.cn（或本地 8082 dev 环境）
5. **是否需 Docker 化**：把 skill + CLI 打包成镜像，agent 通过容器调用

---

*待 Pi 读取并输出部署融合计划。*
