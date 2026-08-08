'use client';

import { useMemo } from 'react';
import useSWR from 'swr';
import api from '@/api';
import { useUserStore } from '@/store';
import {
  COACH_ROLES,
  DATA_SCOPE_PREFIX,
  PERMISSION_ALL,
  type CoachPermissionKey,
} from '@/constants/coach-roles';
import { parseScope, resolvePermissionFlags } from '@/lib/coach-permissions';
import type { PortalPermissions, PortalRole } from '@/types/coach-permissions';

export type { CoachPermissionFlag } from '@/lib/coach-permissions';
export { parseScope, resolvePermissionFlags } from '@/lib/coach-permissions';

export type CoachPermissions = {
  // ---- 12 权限 flags（P0-PERMISSION-KEYS.md §四 映射表）----
  canViewAllStudents: boolean;
  canScore: boolean;
  canEditSummary: boolean;
  canCreateSession: boolean;
  canViewAnyReport: boolean;
  canConfirmChecklist: boolean;
  canManageUsers: boolean;
  canCertifyContent: boolean;
  canViewKpi: boolean;
  canAudit: boolean;
  canCustomDashboard: boolean;
  canViewOwnReport: boolean;
  // ---- 数据范围派生 ----
  /** data_scope 以 "department:" 开头（dept_head 仅本部门）。 */
  canViewDeptOnly: boolean;
  /** 原始 data_scope 字符串。 */
  dataScope: string;
  /** 解析后的范围类型（无数据/无法识别为 ''）。 */
  scopeType: ReturnType<typeof parseScope>['type'];
  /** 范围附加值：department 名 / user_bid（"all" 时为 ''）。 */
  scopeValue: string;
  // ---- 角色 ----
  roles: PortalRole[];
  roleBids: string[];
  /** 主角色 role_bid（后端已按 ROLE_PRIORITY 排序，取首个）。 */
  primaryRole: string;
  isAdmin: boolean;
  // ---- 状态 ----
  /** 权限接口加载中（首次 fetch 未返回）。 */
  isLoading: boolean;
  /** 是否回退到旧 isOperator 逻辑（后端无响应 / 未登录时 true）。 */
  isFallback: boolean;
  hasPermission: (key: CoachPermissionKey | string) => boolean;
};

/**
 * useCoachPermissions —— AI-Coach 5 级角色权限 hook。
 *
 * 数据来源：GET /api/portal/permissions（SWR 全局缓存，组件间共享一次请求）。
 *
 * 兼容策略（无后端响应时回退到旧 isOperator 逻辑，与现有行为一致）：
 *  - is_operator=1 视为 admin → 12 权限 flags 全开、data_scope="all"；
 *  - 其余用户 → 全 false、无角色（不把 is_creator 当 coach，与后端
 *    has_permission 的决策一致：is_creator 不自动授权）。
 *
 * 未登录 / 游客时不发起请求（SWR key 为 null），直接按空权限处理，
 * 避免对未鉴权接口产生 401/冗余请求。
 */
export function useCoachPermissions(): CoachPermissions {
  const isOperator = useUserStore(state =>
    Boolean(state.userInfo?.is_operator),
  );
  const isLoggedIn = useUserStore(state => state.isLoggedIn);
  const isGuest = useUserStore(state => state.isGuest);
  const canFetch = isLoggedIn && !isGuest;

  const { data, isLoading } = useSWR<PortalPermissions>(
    canFetch ? ['coach-permissions'] : null,
    async () => (await api.getPortalPermissions({})) as PortalPermissions,
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    },
  );

  return useMemo(() => {
    const hasPermission = (key: CoachPermissionKey | string): boolean => {
      if (!key) {
        return false;
      }
      // 旧标志位回退：is_operator=1 视为 admin 全通（P0-PERMISSION-MODEL-UPGRADE §四）
      if (isOperator) {
        return true;
      }
      if (data) {
        const keys = data.permissions ?? [];
        return keys.includes(key) || keys.includes(PERMISSION_ALL);
      }
      return false;
    };

    const flags = resolvePermissionFlags(data?.permissions, isOperator);

    const dataScope =
      data?.data_scope ?? (isOperator ? DATA_SCOPE_PREFIX.all : '');
    const { type: scopeType, value: scopeValue } = parseScope(dataScope);

    const roles: PortalRole[] =
      data?.roles ??
      (isOperator ? [{ role_bid: COACH_ROLES.admin, name: 'admin' }] : []);
    const roleBids = roles.map(role => role.role_bid);
    const primaryRole = roleBids[0] ?? '';

    const isAdmin =
      isOperator ||
      roleBids.includes(COACH_ROLES.admin) ||
      (data?.permissions ?? []).includes(PERMISSION_ALL);

    return {
      ...flags,
      canViewDeptOnly: scopeType === DATA_SCOPE_PREFIX.department,
      dataScope,
      scopeType,
      scopeValue,
      roles,
      roleBids,
      primaryRole,
      isAdmin,
      isLoading,
      isFallback: !data,
      hasPermission,
    };
  }, [data, isLoading, isOperator]);
}
