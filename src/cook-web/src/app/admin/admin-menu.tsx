import React from 'react';
import {
  BriefcaseIcon,
  DocumentIcon,
  PresentationChartLineIcon,
  ShoppingCartIcon,
} from '@heroicons/react/24/outline';

export type AdminMenuItem = {
  type?: string;
  icon?: React.ReactNode;
  label?: string;
  href?: string;
  id?: string;
  children?: AdminMenuItem[];
};

type BuildAdminMenuItemsOptions = {
  t: (key: string) => string;
  isOperator: boolean;
  /**
   * P0 5 级角色权限：manage_users（admin/hr）→ 运营/用户管理入口。
   * 传入 useCoachPermissions().canManageUsers；与 isOperator 取「或」，
   * 保证旧标志位兼容（无后端响应回退时 isOperator 仍生效）。
   */
  canManageUsers?: boolean;
};

export const buildAdminMenuItems = ({
  t,
  isOperator,
  canManageUsers = false,
}: BuildAdminMenuItemsOptions): AdminMenuItem[] => {
  const items: AdminMenuItem[] = [
    {
      id: 'shifu',
      icon: <DocumentIcon className='w-4 h-4' />,
      label: t('common.core.shifu'),
      href: '/admin',
    },
    {
      id: 'orders',
      icon: <ShoppingCartIcon className='w-4 h-4' />,
      label: t('module.order.title'),
      href: '/admin/orders',
    },
    {
      id: 'dashboard',
      icon: <PresentationChartLineIcon className='w-4 h-4' />,
      label: t('module.dashboard.title'),
      href: '/admin/dashboard',
    },
  ];

  if (isOperator || canManageUsers) {
    items.push({
      id: 'operations',
      icon: <BriefcaseIcon className='w-4 h-4' />,
      label: t('common.core.operations'),
      children: [
        {
          id: 'operations-course',
          label: t('common.core.courseManagement'),
          href: '/admin/operations',
        },
        {
          id: 'operations-user',
          label: t('common.core.userManagement'),
          href: '/admin/operations/users',
        },
        {
          id: 'operations-order',
          label: t('common.core.orderManagement'),
          href: '/admin/operations/orders',
        },
        {
          id: 'operations-promotion',
          label: t('common.core.promotionManagement'),
          href: '/admin/operations/promotions',
        },
        {
          id: 'operations-permissions',
          label: '权限示例',
          href: '/admin/operations/permissions',
        },
      ],
    });
  }

  return items;
};
