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

  test('includes operations + orders for operators when billing enabled', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: true,
      billingEnabled: true,
    });

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

  test('admin (isOperator + canViewDeptOnly) also gets dept dashboard', () => {
    // devadmin/全能账号：前端已把 isAdmin 归入 canViewDeptOnly，故 admin
    // 同时具备 HR/导师/部门三项工作台入口，便于逐测所有页面。
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: true,
      canManageUsers: true,
      canViewDeptOnly: true,
      canCreateSession: true,
    });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/dashboard',
      '/admin/hr',
      '/admin/dept',
      '/admin/coach',
      '/admin/ai',
      undefined,
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

  test('hides orders, operations-order and promotions when billing disabled', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: true,
      billingEnabled: false,
    });

    expect(menuItems.map(item => item.id)).not.toContain('orders');
    const operations = menuItems.find(item => item.id === 'operations');
    const childIds = operations?.children?.map(c => c.id);
    expect(childIds).not.toContain('operations-order');
    // 促销依附订单流程，计费关闭时一并隐藏（内训站点）。
    expect(childIds).not.toContain('operations-promotion');
  });
});
