
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
