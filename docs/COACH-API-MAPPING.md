
## 四、自测记录（2026-08-25）

| 端点 | 方法 | 结果 | 说明 |
|------|------|:----:|------|
| /coach/courses | POST | ✅ 0 | material_bid 落库 ai-shifu_dev.coach_course_materials |
| /coach/tasks/{bid} | PUT | ✅ 0 | learner_tasks 状态更新 |
| /coach/learning-records | POST | ✅ 0 | course_enrollments 写入 |
| /coach/phase-detail/{bid} | GET | ✅ 0 | 回归通过 |
| /coach/report/{bid} | GET | ✅ 0 | 回归通过 |
| /coach/students | GET | ⚠️ -1 | 业务层（登录用户无带教数据） |

### 故障修复记录（本次联调发现）
1. **端点撞名**：learning_portal 与 myenroll 均定义 `my_enrollments`/`admin_learners`
   → Flask endpoint 冲突 → myenroll 插件加载被 AssertionError 拦截 → 全部 coach 端点 404
   → 修复：myenroll 端点显式 `endpoint="xxx_shifu"` 唯一化
2. **gunicorn --reload 双加载**：reload 重 import 触发插件重复注册（容器反复重启）
   → 修复：docker-compose.dev.yml 移除 `--reload`，改动后手动重启容器
3. **courses/tasks 端点回滚丢失**：git checkout 回滚时连带丢失新增端点
   → 修复：从 patch 重新提取恢复
4. **表落库位置**：dev API 实际连 `ai-shifu-mysql-dev:3306/ai-shifu_dev`（非 prod ai-shifu）
   → coach_course_materials 建表于 ai-shifu_dev；误建 prod 表已清理

## 五、Bot 脚本 dry-run 验证（2026-08-25）

WECOM_MOCK=1 + 注入模拟记录 + --dry-run，7 张业务表逐一验证：

| 表 | 端点 | body 提取 | 结果 |
|----|------|-----------|:----:|
| 课件上传 | POST /coach/courses | name/link_url/course_bid | ✅ |
| 面谈总结 | POST /coach/session | learner_bid/phase_bid/topic/mentor_notes/session_type | ✅ |
| 任务登记 | POST /coach/tasks/{RID} | {RID}→rid 替换 + learner_bid/title/task_type | ✅ |
| 评教练 | POST /coach/learner-rating | learner_bid/phase_bid/score | ✅ |
| 教练评学员 | POST /coach/phase-summary | record_bid/coach_summary/learner_feedback/improvement_plan/complete | ✅ |
| 带教终评 | POST /coach/final-rating | learner_bid/phase_bid + 4 分项 | ✅ |
| 学习凭证 | POST /coach/learning-records | learner_bid/course_bid | ✅ |

### 已知小问题（非阻塞，可选优化）
1. **任务登记 status 语义**：body.status 取自表单"状态"列当前值（"待处理"），
   非目标完成状态——建议表单增加"完成状态"列或钻调时固定传"已完成"。
2. **call_coach 一律 POST**：tasks 端点更新语义应为 PUT（POST 也支持首次登记，
   不影响闭环）。可给 call_coach 增加 method 参数。
3. **COACH_API_TOKEN 未配置时钻调跳过**（默认空）——生产 cron 前需在环境注入
   X-WECOM-TOKEN 对应值。

## 六、真实闭环实测（2026-08-25，B1-B4 全通过）

真实记录 gFjWlW（凌云/完成产品知识课件学习/进行中）全链路：

| 步骤 | 结果 |
|------|:----:|
| B1 读取待处理记录 | ✅ 状态过滤扩展 IN('待处理','进行中') |
| B2 Coach API 调用 | ✅ PUT /coach/tasks/gFjWlW → {"ok":true,"task_bid":"gFjWlW"} |
| B3 落库 | ✅ learner_tasks 新增（task_bid=gFjWlW, status=已完成） |
| B4 关单+通知 | ✅ 记录状态→已处理 + 企微通知 |

### 实测发现并修复
1. **后端鉴权头是 Token**（非 X-WECOM-TOKEN）→ 脚本 curl 头一致化
2. **业务表状态枚举**：任务登记用"进行中"（申请类才"待处理"）→ SQL 过滤适配
3. **call_coach 误判**：API 返回 {"code":0,"data":{"error":...}} 曾被视为成功→关单丢数据
   → 修复：响应含 "error" 即失败（保留待处理不关单）
4. **title 提取缺"任务内容"列** → pick 名单补充
5. **姓名→learner_bid 映射缺失**（凌云姓名透传当 bid 落库）——接主数据后补
