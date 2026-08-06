-- ============================================================================
-- P0 · AAD 强登录控制 · 存量用户默认角色兜底迁移（幂等）
-- 目标：让每个未分配任何 5 级角色的存量用户至少拥有一个角色（D14）
-- 迁移矩阵（对齐 P0-PERMISSION-MODEL-UPGRADE §八 + P0-REVIEW A2/D8）：
--   is_operator=1                    → role-admin
--   is_creator=1（且非 operator）     → role-coach
--   其余（无任何角色）                → role-learner（默认学员）
-- 幂等性：NOT EXISTS 守卫 + INSERT IGNORE，重复执行无副作用
-- 执行方式（dev 真库）：
--   docker exec -i docker-ai-shifu-mysql-dev-1 mysql -uroot -pai-shifu ai-shifu_dev < backfill_role_learner.sql
-- 前置：user_role_assignments 表已存在（P0 DDL 已建），coach_roles 已播种 5 行
-- ============================================================================

-- 1) is_operator=1 且尚无角色 → role-admin
INSERT IGNORE INTO user_role_assignments (user_bid, role_bid)
SELECT u.user_bid, 'role-admin'
FROM user_users u
WHERE u.deleted = 0
  AND u.is_operator = 1
  AND NOT EXISTS (
      SELECT 1 FROM user_role_assignments r
      WHERE r.user_bid = u.user_bid
  );

-- 2) is_creator=1 且非 operator 且尚无角色 → role-coach
INSERT IGNORE INTO user_role_assignments (user_bid, role_bid)
SELECT u.user_bid, 'role-coach'
FROM user_users u
WHERE u.deleted = 0
  AND u.is_creator = 1
  AND u.is_operator = 0
  AND NOT EXISTS (
      SELECT 1 FROM user_role_assignments r
      WHERE r.user_bid = u.user_bid
  );

-- 3) 其余尚无任何角色的非删除用户 → role-learner（默认学员）
INSERT IGNORE INTO user_role_assignments (user_bid, role_bid)
SELECT u.user_bid, 'role-learner'
FROM user_users u
WHERE u.deleted = 0
  AND NOT EXISTS (
      SELECT 1 FROM user_role_assignments r
      WHERE r.user_bid = u.user_bid
  );

-- 4) 自检：应无"无角色"的非删除用户
-- SELECT COUNT(*) AS orphan_users
-- FROM user_users u
-- WHERE u.deleted = 0
--   AND NOT EXISTS (
--       SELECT 1 FROM user_role_assignments r
--       WHERE r.user_bid = u.user_bid
--   );
