/**
 * AI-Coach 权限 flags 纯函数（无 React/SWR/store 依赖，可独立单测）。
 *
 * 供 hooks/useCoachPermissions.ts 使用；抽出独立模块是为了让
 * 5 级角色 × 12 flags 映射矩阵可被纯单测覆盖（lib/coach-permissions.test.ts），
 * 且不触发 React 组件 / store 副作用。
 */
import {
  DATA_SCOPE_PREFIX,
  PERMISSION_ALL,
  PERMISSION_KEYS,
  type CoachPermissionKey,
  type DataScopeType,
} from '@/constants/coach-roles';

// flag → 后端权限 key 映射（P0-PERMISSION-KEYS.md §四）。
const FLAG_PERMISSION_MAP = {
  canViewAllStudents: PERMISSION_KEYS.viewAllStudents,
  canScore: PERMISSION_KEYS.score,
  canEditSummary: PERMISSION_KEYS.editSummary,
  canCreateSession: PERMISSION_KEYS.createSession,
  canViewAnyReport: PERMISSION_KEYS.viewAnyReport,
  canConfirmChecklist: PERMISSION_KEYS.confirmChecklist,
  canManageUsers: PERMISSION_KEYS.manageUsers,
  canCertifyContent: PERMISSION_KEYS.certifyContent,
  canViewKpi: PERMISSION_KEYS.viewKpi,
  canAudit: PERMISSION_KEYS.audit,
  canCustomDashboard: PERMISSION_KEYS.customDashboard,
  canViewOwnReport: PERMISSION_KEYS.viewOwnReport,
} as const;

export type CoachPermissionFlag = keyof typeof FLAG_PERMISSION_MAP;

/** 12 个 flag 名（供遍历/渲染）。 */
export const COACH_PERMISSION_FLAGS: readonly CoachPermissionFlag[] =
  Object.keys(FLAG_PERMISSION_MAP) as CoachPermissionFlag[];

/**
 * 解析 data_scope："department:销售本部" → { type:'department', value:'销售本部' }。
 * "all" → { type:'all', value:'' }；空串/未知前缀 → { type:'', value:原样 }。
 */
export const parseScope = (
  dataScope: string,
): { type: DataScopeType | ''; value: string } => {
  if (!dataScope) {
    return { type: '', value: '' };
  }
  const [type, ...rest] = dataScope.split(':');
  const value = rest.join(':');
  if (
    type === DATA_SCOPE_PREFIX.all ||
    type === DATA_SCOPE_PREFIX.department ||
    type === DATA_SCOPE_PREFIX.mentored ||
    type === DATA_SCOPE_PREFIX.self
  ) {
    return { type, value };
  }
  return { type: '', value: dataScope };
};

/**
 * 由服务器 permissions key 列表 + 旧 isOperator 标志，计算 12 权限 flags。
 *
 * 规则（与后端 has_permission 对齐，P0-EXECUTION-7-ROUTES.md §3.1）：
 *  - isOperator=1 → 全 true（admin 兼容）；
 *  - 任一 key 命中，或 permissions 含 "all"（role-admin）→ true；
 *  - 其余 → false。
 */
export const resolvePermissionFlags = (
  permissions: string[] | undefined,
  isOperator: boolean,
): Record<CoachPermissionFlag, boolean> => {
  const hasPermission = (key: CoachPermissionKey | string): boolean => {
    if (!key) {
      return false;
    }
    if (isOperator) {
      return true;
    }
    if (permissions) {
      return (
        permissions.includes(key) || permissions.includes(PERMISSION_ALL)
      );
    }
    return false;
  };

  const flags = {} as Record<CoachPermissionFlag, boolean>;
  COACH_PERMISSION_FLAGS.forEach(flag => {
    flags[flag] = hasPermission(FLAG_PERMISSION_MAP[flag]);
  });
  return flags;
};
