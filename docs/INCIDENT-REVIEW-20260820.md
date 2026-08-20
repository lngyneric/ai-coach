# 事故复盘日志 — 企微主数据同步数据丢失（dev→prod 栈切换）

> 日期：2026-08-20 · 影响：person_master 等企微主数据丢失 · 状态：已定位，待重建
> 位置：PRD worktree（/home/sysmex/ai-shifu）

---

## 一、事故概述

企微主数据同步（person_master + departments + user_departments）完成后，因环境栈切换（dev → prod），原 dev 数据库容器被删除，**已同步的主数据全部丢失**。

## 二、时间线

| 时间 | 事件 |
|------|------|
| 08-18~19 | 企微授权设计确认 + 申请闭环 V1-V18 实测（成功） |
| 08-19 | 企微主数据同步：person_master 5人 + departments 组织树 5节点 + 关联（dev mysql） |
| 08-20 | **环境切换**：dev 栈（docker-ai-shifu-*-dev-*）被清理，替换为 prod 栈（ai-shifu-* docker-compose.yml） |
| 08-20 | 原 dev mysql 容器删除 → person_master/departments/user_departments 数据丢失 |
| 08-20 | 在当前库（ai-shifu 3306）重建 apply_registry + grant_log；**person_master 待重建** |

## 三、根因分析

| 因素 | 说明 |
|------|------|
| 直接原因 | dev 容器栈被 docker compose down 清理（dev.yml 栈 → docker-compose.yml 栈） |
| 数据持久化缺失 | person_master 等主数据表所在 dev mysql 无独立 volume 备份，容器删除即丢 |
| 未留 recovery | 同步后未立即固化到持久化位置（如 PRD 库/JSON 快照） |
| 能力边界 | wecom-cli 全量拉取需 keywords（非真全库），重拉需重新确认范围 |

## 四、事故影响

```
✅ apply_registry + grant_log（08-20 新建，当前库）—— 保留
❌ person_master（5 人：刘佳怡/凌云/杨萍/陆蓓/陈珊）—— 丢失
❌ departments（5 组织节点）—— 丢失
❌ user_departments（5 关联）—— 丢失
```

## 五、改进措施（防再发）

| 措施 | 状态 |
|------|:----:|
| 主数据同步后**立即导出 JSON 快照**存档（gitignore 保护） | 待做 |
| 主数据表建到**持久化库**（PRD ai-shifu / 独立 volume） | 待做 |
| 同步日志（wecom_sync_log）作为唯一事实源 + 可重建 | 待做 |
| 同步脚本支持 `--users-json` 离线重建（已有 mock/export 能力） | ✅ 已有 |
| 环境切换前**确认数据归属**（dev vs prod 库） | 待做 |

## 六、恢复计划（重建主数据）

```
1. 确认当前库（ai-shifu）为唯一主数据库
2. 重拉 5 人（wecom-cli 带 keywords）→ person_master upsert
3. 重建 departments 组织树 + user_departments 关联
4. 写 wecom_sync_log（重建记录）
5. 导出 JSON 快照存档（防再丢）
```

## 七、验证（当前状态核对）

- [x] apply_registry / grant_log 已在 ai-shifu 库（08-20 建）
- [x] wecom_sync_log 存在
- [x] person_master 缺失（确认丢失）
- [ ] person_master / departments / user_departments 重建（待执行）

---

*复盘完成；恢复动作见第六节。*
