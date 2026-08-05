import { buildAdminMenuItems } from './admin-menu';

describe('buildAdminMenuItems', () => {
  const t = (key: string) => key;

  test('excludes operations entry for non-operators', () => {
    const menuItems = buildAdminMenuItems({ t, isOperator: false });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/orders',
      '/admin/dashboard',
    ]);
  });

  test('includes operations entry for operators', () => {
    const menuItems = buildAdminMenuItems({ t, isOperator: true });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/orders',
      '/admin/dashboard',
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

  test('includes operations entry for canManageUsers (P0 5-level roles, e.g. hr)', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: false,
      canManageUsers: true,
    });

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

  test('excludes operations entry when neither isOperator nor canManageUsers', () => {
    const menuItems = buildAdminMenuItems({
      t,
      isOperator: false,
      canManageUsers: false,
    });

    expect(menuItems.map(item => item.href)).toEqual([
      '/admin',
      '/admin/orders',
      '/admin/dashboard',
    ]);
  });
});
