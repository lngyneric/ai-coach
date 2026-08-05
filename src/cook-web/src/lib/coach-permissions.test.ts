import {
  resolvePermissionFlags,
  parseScope,
  COACH_PERMISSION_FLAGS,
  type CoachPermissionFlag,
} from '@/lib/coach-permissions';

// 5 级角色 permissions 目标值（docs/P0-PERMISSION-KEYS.md §二）
const rolePermissions: Record<string, string[]> = {
  admin: ['all'],
  hr: [
    'view_all_students',
    'view_any_report',
    'confirm_checklist',
    'manage_users',
    'certify_content',
    'view_kpi',
    'audit',
    'custom_dashboard',
    'view_own_report',
  ],
  dept_head: [
    'view_all_students',
    'view_any_report',
    'certify_content',
    'view_kpi',
    'custom_dashboard',
    'view_own_report',
  ],
  coach: [
    'coach:read',
    'coach:write',
    'learner:read',
    'view_all_students',
    'score',
    'edit_summary',
    'create_session',
    'view_any_report',
    'confirm_checklist',
    'view_kpi',
    'custom_dashboard',
    'view_own_report',
  ],
  learner: ['learner:read', 'learner:write', 'view_own_report'],
};

const ALL_FLAGS: CoachPermissionFlag[] = [...COACH_PERMISSION_FLAGS];

describe('resolvePermissionFlags — P0 12 flags 映射矩阵', () => {
  test('admin（permissions 含 "all"）→ 12 flags 全 true', () => {
    const flags = resolvePermissionFlags(rolePermissions.admin, false);
    for (const flag of ALL_FLAGS) {
      expect(flags[flag]).toBe(true);
    }
  });

  test('hr → 9 true（无 score/edit_summary/create_session）', () => {
    const flags = resolvePermissionFlags(rolePermissions.hr, false);
    expect(flags.canViewAllStudents).toBe(true);
    expect(flags.canViewAnyReport).toBe(true);
    expect(flags.canConfirmChecklist).toBe(true);
    expect(flags.canManageUsers).toBe(true);
    expect(flags.canCertifyContent).toBe(true);
    expect(flags.canViewKpi).toBe(true);
    expect(flags.canAudit).toBe(true);
    expect(flags.canCustomDashboard).toBe(true);
    expect(flags.canViewOwnReport).toBe(true);
    expect(flags.canScore).toBe(false);
    expect(flags.canEditSummary).toBe(false);
    expect(flags.canCreateSession).toBe(false);
  });

  test('dept_head → 6 true（无 score/manage_users/confirm/audit）', () => {
    const flags = resolvePermissionFlags(rolePermissions.dept_head, false);
    expect(flags.canViewAllStudents).toBe(true);
    expect(flags.canViewAnyReport).toBe(true);
    expect(flags.canCertifyContent).toBe(true);
    expect(flags.canViewKpi).toBe(true);
    expect(flags.canCustomDashboard).toBe(true);
    expect(flags.canViewOwnReport).toBe(true);
    expect(flags.canScore).toBe(false);
    expect(flags.canEditSummary).toBe(false);
    expect(flags.canCreateSession).toBe(false);
    expect(flags.canConfirmChecklist).toBe(false);
    expect(flags.canManageUsers).toBe(false);
    expect(flags.canAudit).toBe(false);
  });

  test('coach → 9 true（无 manage_users/certify_content/audit）', () => {
    const flags = resolvePermissionFlags(rolePermissions.coach, false);
    expect(flags.canViewAllStudents).toBe(true);
    expect(flags.canScore).toBe(true);
    expect(flags.canEditSummary).toBe(true);
    expect(flags.canCreateSession).toBe(true);
    expect(flags.canViewAnyReport).toBe(true);
    expect(flags.canConfirmChecklist).toBe(true);
    expect(flags.canViewKpi).toBe(true);
    expect(flags.canCustomDashboard).toBe(true);
    expect(flags.canViewOwnReport).toBe(true);
    expect(flags.canManageUsers).toBe(false);
    expect(flags.canCertifyContent).toBe(false);
    expect(flags.canAudit).toBe(false);
  });

  test('learner → 仅 canViewOwnReport true', () => {
    const flags = resolvePermissionFlags(rolePermissions.learner, false);
    for (const flag of ALL_FLAGS) {
      expect(flags[flag]).toBe(flag === 'canViewOwnReport');
    }
  });

  test('旧标志位回退：isOperator=true 且无服务器权限 → 全 true', () => {
    const flags = resolvePermissionFlags(undefined, true);
    for (const flag of ALL_FLAGS) {
      expect(flags[flag]).toBe(true);
    }
  });

  test('无权限数据且非 operator → 全 false', () => {
    const flags = resolvePermissionFlags(undefined, false);
    for (const flag of ALL_FLAGS) {
      expect(flags[flag]).toBe(false);
    }
  });
});

describe('parseScope — data_scope 解析', () => {
  test('"all" → type=all, value=""', () => {
    expect(parseScope('all')).toEqual({ type: 'all', value: '' });
  });

  test('"department:销售本部" → type=department, value=销售本部', () => {
    expect(parseScope('department:销售本部')).toEqual({
      type: 'department',
      value: '销售本部',
    });
  });

  test('"mentored:dev-coach-bid" → type=mentored', () => {
    const parsed = parseScope('mentored:dev-coach-bid');
    expect(parsed.type).toBe('mentored');
    expect(parsed.value).toBe('dev-coach-bid');
  });

  test('"self:dev-learner-bid" → type=self', () => {
    const parsed = parseScope('self:dev-learner-bid');
    expect(parsed.type).toBe('self');
    expect(parsed.value).toBe('dev-learner-bid');
  });

  test('空串/未知前缀 → 空 type', () => {
    expect(parseScope('')).toEqual({ type: '', value: '' });
    expect(parseScope('unknown:xyz').type).toBe('');
  });
});
