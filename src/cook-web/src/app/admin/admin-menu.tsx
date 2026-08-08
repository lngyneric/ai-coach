import React from 'react';
import {
  BriefcaseIcon,
  DocumentIcon,
  PresentationChartLineIcon,
  ShoppingCartIcon,
  UsersIcon,
  AcademicCapIcon,
  ChatBubbleLeftRightIcon,
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
   * P0 5 级角色权限（useCoachPermissions flags）。
   * 运营子菜单（course/user/order/promotion）仅 admin（isOperator）可见——
   * HR（manage_users）不再看到进不去的 admin 专属运营页（W3 缺口 4）。
   * 各角色独立工作台按对应 flag 显示：
   *  - canManageUsers   → HR 工作台 /admin/hr
   *  - canViewDeptOnly  → 部门看板 /admin/dept（dept_head）
   *  - canCreateSession → 导师工作台 /admin/coach（coach）
   */
  canManageUsers?: boolean;
  canViewDeptOnly?: boolean;
  canCreateSession?: boolean;
};

export const buildAdminMenuItems = ({
  t,
  isOperator,
  canManageUsers = false,
  canViewDeptOnly = false,
  canCreateSession = false,
}: BuildAdminMenuItemsOptions): AdminMenuItem[] => {
  const items: AdminMenuItem[] = [
    {
      id: 'shifu',
      icon: <DocumentIcon className='w-4 h-4' />,
      label: t('common.core.shifu'),
      href: '/admin',
    },
  ];

  // 订单管理：admin 专属（is_operator 守卫的运营页）。
  if (isOperator) {
    items.push({
      id: 'orders',
      icon: <ShoppingCartIcon className='w-4 h-4' />,
      label: t('module.order.title'),
      href: '/admin/orders',
    });
  }

  items.push({
    id: 'dashboard',
    icon: <PresentationChartLineIcon className='w-4 h-4' />,
    label: t('module.dashboard.title'),
    href: '/admin/dashboard',
  });

  // HR 工作台（admin/hr 均可管理用户，manage_users）。
  if (canManageUsers) {
    items.push({
      id: 'hr',
      icon: <UsersIcon className='w-4 h-4' />,
      label: 'HR 工作台',
      href: '/admin/hr',
    });
  }

  // 部门看板（dept_head 数据范围）。
  if (canViewDeptOnly) {
    items.push({
      id: 'dept',
      icon: <PresentationChartLineIcon className='w-4 h-4' />,
      label: '部门看板',
      href: '/admin/dept',
    });
  }

  // 导师工作台（coach 面谈管理）。
  if (canCreateSession) {
    items.push({
      id: 'coach',
      icon: <AcademicCapIcon className='w-4 h-4' />,
      label: '导师工作台',
      href: '/admin/coach',
    });
  }

  // AI 问答助手：任何可进入 /admin 的角色可见。
  items.push({
    id: 'ai',
    icon: <ChatBubbleLeftRightIcon className='w-4 h-4' />,
    label: 'AI 问答助手',
    href: '/admin/ai',
  });

  // 运营后台：仅 admin（isOperator）。HR 不再看到进不去的运营菜单。
  if (isOperator) {
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
