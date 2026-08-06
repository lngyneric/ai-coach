import { buildAdminMenuItems } from './admin-menu';

describe('buildAdminMenuItems', () => {
  const t = (key: string) => key;

  test('excludes operations/orders for non-operators without role flags', () => {
    const menuItems = buildAdminMenuItems({ t, isOperator: false });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/dashboard',
      '/admin/ai',
    ]);
  });

  test('includes operations + orders for operators', () => {
    const menuItems = buildAdminMenuItems({ t, isOperator: true });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/orders',
      '/admin/dashboard',
      '/admin/ai',
      undefined,
    ]);
    expect(menuItems.at(-1)).toMatchObject({
      id: 'operations',
      label: 'common.core.operations',
      children: [
        {
          id: 'operations-course',
          label: 'common.core.courseManagement',
          href: '/admin/operations',
        },
        {
          id: 'operations-user',
          label: 'common.core.userManagement',
          href: '/admin/operations/users',
        },
        {
          id: 'operations-order',
          label: 'common.core.orderManagement',
          href: '/admin/operations/orders',
        },
        {
          id: 'operations-promotion',
          label: 'common.core.promotionManagement',
          href: '/admin/operations/promotions',
        },
        {
          id: 'operations-permissions',
          label: '权限示例',
          href: '/admin/operations/permissions',
        },
      ],
    });
  });

  test('HR (canManageUsers) gets HR workbench, NOT admin-only operations', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: false,
      canManageUsers: true,
    });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/dashboard',
      '/admin/hr',
      '/admin/ai',
    ]);
    // operations is admin-only; HR must not see it (W3 gap 4 fix)
    expect(menuItems.find(item => item.id === 'operations')).toBeUndefined();
  });

  test('dept_head (canViewDeptOnly) gets dept dashboard', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: false,
      canViewDeptOnly: true,
    });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/dashboard',
      '/admin/dept',
      '/admin/ai',
    ]);
  });

  test('coach (canCreateSession) gets coach workbench', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: false,
      canCreateSession: true,
    });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/dashboard',
      '/admin/coach',
      '/admin/ai',
    ]);
  });

  test('excludes everything extra when neither isOperator nor role flags', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: false,
      canManageUsers: false,
      canViewDeptOnly: false,
      canCreateSession: false,
    });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/dashboard',
      '/admin/ai',
    ]);
  });
});
