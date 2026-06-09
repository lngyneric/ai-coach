# Skill: 知识图谱同步检查与更新

## 概述

当数据库新增课程后，需要手动关联到两个知识图谱之一。本 skill 提供：
- 自动检查数据库与知识图谱的差异
- 课程归属决策指南
- 更新流程

---

## 一、快速检查

运行以下命令对比数据库与图谱的差异：

```bash
cd /home/sysmex/ai-shifu
python3 scripts/kg_audit.py
```

输出示例：
```
=== 审计报告: 2026-06-09 ===

IVD 知识图谱: 39 节点, 9 课程
个人能力提升图谱: 25 节点, 8 课程
数据库课程总数: 18 门

✅ 已覆盖: 17 门
❌ 未关联: 0 门
⏭️ 跳过: Test Course (测试课程)
```

---

## 二、课程归属决策矩阵

新课程根据内容决定归属哪个图谱和节点：

### IVD 知识图谱归属

| 领域 | 适用课程类型 | 示例节点 |
|------|------------|---------|
| 通识基础 | 多种仪器/方法学通识课 | 六大检验系统总览 |
| 血液检验 | 血液分析仪、血细胞计数 | 血液学基础、CBC |
| 尿液检验 | 尿液分析仪、干化学 | 尿液检验基础 |
| 凝血检验 | 凝血分析仪、止血血栓 | 凝血检验基础 |
| 免疫检验 | 化学发光、传染病检测 | 免疫检验基础 |
| 生化检验 | 生化分析、肝功能肾功能 | 生化检验基础 |
| 分子/生科 | PCR、流式细胞术 | 分子检验基础 |
| 分子POCT | 即时分子检测设备 | 分子POCT基础 |
| 国产临床流式 | 国产流式细胞仪 | 临床流式细胞术应用 |
| 市场格局 | IVD行业/政策/竞品 | 中国IVD市场概览 |
| 销售策略 | 经销商/报价/客户 | 经销商管理与渠道 |
| 产品定位与卖点 | 各产品线卖点 | 血液/凝血/尿液产品卖点 |
| 商务能力 | 商务礼仪/KPI销售 | 商务礼仪与沟通 |

### 个人能力提升图谱归属

| 领域 | 适用课程类型 | 示例节点 |
|------|------------|---------|
| AI 智能体开发 | Claude/ChatGPT开发、Agent | 智能体基础、记忆系统 |
| AI 产品思维 | AI产品经理、AI产品设计 | AI产品经理基础、面试 |
| 企业数字化转型 | 企业架构、AI落地、流程 | 企业数字化架构、流程体系 |
| 知识管理与第二大脑 | Obsidian、知识管理 | Obsidian知识库搭建 |
| 个人效能与自动化 | 效率工具、自动化脚本 | 自动化工具与脚本 |
| 学习与成长方法论 | 学习方法、技能树 | 学习科学基础、技能树 |

---

## 三、更新流程（6 步）

### 步骤 1: 确认课程归属

新课程发布后，先决定归属哪个图谱、哪个节点。不确定时可以查看课程标题和描述做判断。

### 步骤 2: 编辑 HTML 文件

```bash
cd /home/sysmex/ai-shifu
# IVD 图谱
vim src/cook-web/public/ivd-knowledge-tree.html
# 或 个人能力提升图谱
vim src/cook-web/public/personal-growth-tree.html
```

### 步骤 3: 修改 TREE 数据（第129行附近）

找到目标节点，将 `"courses":[]` 替换为课程数据：

```json
// 修改前
"id": "target-node", "name": "目标节点", ..., "courses": [],

// 修改后  
"id": "target-node", "name": "目标节点", ..., 
"courses": [{
  "shifu_bid": "课程ID",
  "title": "课程标题",
  "description": "课程描述",
  "keywords": "关键词",
  "lesson_count": 12,
  "lesson_titles": [],
  "lessons": ["课节1", "课节2", ...]
}],
```

### 步骤 4: 修改 NODES 数据（同样逻辑）

找到 `const NODES = [...]` 中对应节点，同步修改：

```json
// 修改前
"has_course": false, "course_count": 0, "courses": [],

// 修改后
"has_course": true, "course_count": 1, "courses": [{...}],
```

### 步骤 5: 部署并提交

```bash
cd /home/sysmex/ai-shifu

# 热部署到 nginx
docker cp src/cook-web/public/ivd-knowledge-tree.html \
  ai-shifu-nginx:/usr/share/nginx/html/ivd-knowledge-tree.html

# 或个人能力提升图谱
docker cp src/cook-web/public/personal-growth-tree.html \
  ai-shifu-nginx:/usr/share/nginx/html/personal-growth-tree.html

# 提交到 git
git add src/cook-web/public/*.html
git commit -m "feat: 知识图谱关联课程 [课程标题]"
git push github main
```

### 步骤 6: 验证

```bash
# 确认页面可访问
curl -s -o /dev/null -w "%{http_code}" \
  "https://eu.sysmex.com.cn/ivd-knowledge-tree.html"

# 确认课程出现在页面中
curl -s "https://eu.sysmex.com.cn/ivd-knowledge-tree.html" \
  | grep -o "课程标题" | head -1
```

---

## 四、维护清单

- [ ] 每次新课程发布后执行 audit
- [ ] 决定课程归属（IVD or 个人能力）
- [ ] 找到对应的节点
- [ ] 更新 TREE + NODES 两处数据
- [ ] 热部署到 nginx
- [ ] 提交 git
- [ ] 验证前端生效
