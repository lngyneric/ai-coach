/**
 * AI-Coach 5 级角色与权限 key 常量（P0 权限模型升级）。
 *
 * 对应设计：docs/P0-PERMISSION-KEYS.md（12 权限 key）与
 * docs/P0-PERMISSION-MODEL-UPGRADE.md（5 级角色）。
 * 后端权威来源：src/api/flaskr/service/coach/permissions.py
 * （ROLE_PRIORITY / ALL_PERMISSION_KEYS / SCOPE_*）。
 *
 * role_bid 必须与 `coach_roles.role_bid`（role-admin / role-hr /
 * role-dept-head / role-coach / role-learner）一致，前端不做任何改写。
 */

// ---- 5 级角色：key → role_bid ----
export const COACH_ROLES = {
  admin: 'role-admin',
  hr: 'role-hr',
  dept_head: 'role-dept-head',
  coach: 'role-coach',
  learner: 'role-learner',
} as const;

export type CoachRoleKey = keyof typeof COACH_ROLES;
export type CoachRoleBid = (typeof COACH_ROLES)[CoachRoleKey];

/** 固定角色优先级（最高优先在前），与后端 ROLE_PRIORITY 一一对应。 */
export const COACH_ROLE_PRIORITY: readonly CoachRoleBid[] = [
  COACH_ROLES.admin,
  COACH_ROLES.hr,
  COACH_ROLES.dept_head,
  COACH_ROLES.coach,
  COACH_ROLES.learner,
];

/** 角色显示名（中文，与 coach_roles.name 对齐）。 */
export const COACH_ROLE_LABELS: Record<CoachRoleKey, string> = {
  admin: '超级管理员',
  hr: 'HR',
  dept_head: '部门负责人',
  coach: '培训师',
  learner: '学员',
};

/** role_bid → 角色 key 的反查表。 */
export const COACH_ROLE_KEY_BY_BID: Record<CoachRoleBid, CoachRoleKey> = {
  [COACH_ROLES.admin]: 'admin',
  [COACH_ROLES.hr]: 'hr',
  [COACH_ROLES.dept_head]: 'dept_head',
  [COACH_ROLES.coach]: 'coach',
  [COACH_ROLES.learner]: 'learner',
};

// ---- 12 权限 key（后端 permissions JSON 值）----
export const PERMISSION_KEYS = {
  viewAllStudents: 'view_all_students',
  score: 'score',
  editSummary: 'edit_summary',
  createSession: 'create_session',
  viewAnyReport: 'view_any_report',
  confirmChecklist: 'confirm_checklist',
  manageUsers: 'manage_users',
  certifyContent: 'certify_content',
  viewKpi: 'view_kpi',
  audit: 'audit',
  customDashboard: 'custom_dashboard',
  viewOwnReport: 'view_own_report',
} as const;

export type CoachPermissionKey =
  (typeof PERMISSION_KEYS)[keyof typeof PERMISSION_KEYS];

/** 12 key 全集（admin 的 “all” 展开后即此集合，后端已展开）。 */
export const ALL_PERMISSION_KEYS: readonly CoachPermissionKey[] =
  Object.values(PERMISSION_KEYS);

/** 通配权限（role-admin / is_operator 拥有）。 */
export const PERMISSION_ALL = 'all';

// ---- data_scope 前缀（GET /api/portal/permissions → data_scope）----
export const DATA_SCOPE_PREFIX = {
  all: 'all',
  department: 'department',
  mentored: 'mentored',
  self: 'self',
} as const;

export type DataScopeType = keyof typeof DATA_SCOPE_PREFIX;
