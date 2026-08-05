'use client';

import React from 'react';
import { useCoachPermissions } from '@/hooks/useCoachPermissions';
import { COACH_ROLE_LABELS } from '@/constants/coach-roles';
import type { CoachRoleBid } from '@/constants/coach-roles';

/**
 * P0 权限示例页：展示当前登录用户的 5 级角色 / 12 权限 flags / 数据范围。
 *
 * 目的：证明 useCoachPermissions 端到端可用（GET /api/portal/permissions →
 * flags），并作为 dev 环境 5 类测试用户（admin/hr/dept_head/coach/learner）
 * 的验收台。任何已登录用户均可访问（/admin/operations/permissions）。
 */
const PERMISSION_FLAG_ROWS: Array<{
  flag: keyof ReturnType<typeof useCoachPermissions>;
  label: string;
}> = [
  { flag: 'canViewAllStudents', label: '全员列表 view_all_students' },
  { flag: 'canScore', label: '评分 0-5 score' },
  { flag: 'canEditSummary', label: '阶段小结 edit_summary' },
  { flag: 'canCreateSession', label: '发起面谈 create_session' },
  { flag: 'canViewAnyReport', label: '查看任意报告 view_any_report' },
  { flag: 'canConfirmChecklist', label: '确认清单 confirm_checklist' },
  { flag: 'canManageUsers', label: '用户管理 manage_users' },
  { flag: 'canCertifyContent', label: '课程认证上架 certify_content' },
  { flag: 'canViewKpi', label: '看板 KPI view_kpi' },
  { flag: 'canAudit', label: '合规审计 audit' },
  { flag: 'canCustomDashboard', label: '自定义看板 custom_dashboard' },
  { flag: 'canViewOwnReport', label: '仅自己报告 view_own_report' },
];

const roleLabel = (roleBid: string) =>
  COACH_ROLE_LABELS[roleBid as CoachRoleBid] ?? roleBid;

const Badge = ({ children }: { children: React.ReactNode }) => (
  <span className='inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700'>
    {children}
  </span>
);

const Row = ({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) => (
  <div className='flex items-center justify-between border-b border-gray-100 py-2'>
    <span className='text-sm text-gray-600'>{label}</span>
    <span className='text-sm font-medium text-gray-900'>{value}</span>
  </div>
);

const PermissionsPage = () => {
  const perms = useCoachPermissions();

  return (
    <div className='mx-auto max-w-3xl space-y-6 py-6'>
      <div>
        <h1 className='text-xl font-semibold text-gray-900'>权限示例</h1>
        <p className='mt-1 text-sm text-gray-500'>
          useCoachPermissions 接入示例：数据来自 GET /api/portal/permissions
          {perms.isFallback ? '（后端未响应，已回退 isOperator 逻辑）' : ''}
          {perms.isLoading ? '（加载中…）' : ''}
        </p>
      </div>

      <section className='rounded-lg border border-gray-200 bg-white p-4'>
        <h2 className='mb-2 text-sm font-semibold text-gray-900'>角色</h2>
        <div className='flex flex-wrap gap-2'>
          {perms.roles.length === 0 ? (
            <span className='text-sm text-gray-400'>无角色分配</span>
          ) : (
            perms.roles.map(role => (
              <Badge key={role.role_bid}>
                {roleLabel(role.role_bid)}（{role.role_bid}）
              </Badge>
            ))
          )}
        </div>
        <div className='mt-3 space-y-0'>
          <Row label='主角色 role_bid' value={perms.primaryRole || '—'} />
          <Row label='isAdmin' value={String(perms.isAdmin)} />
        </div>
      </section>

      <section className='rounded-lg border border-gray-200 bg-white p-4'>
        <h2 className='mb-2 text-sm font-semibold text-gray-900'>数据范围</h2>
        <div className='space-y-0'>
          <Row label='data_scope' value={perms.dataScope || '—'} />
          <Row label='scopeType' value={perms.scopeType || '—'} />
          <Row label='scopeValue' value={perms.scopeValue || '—'} />
          <Row label='canViewDeptOnly' value={String(perms.canViewDeptOnly)} />
        </div>
      </section>

      <section className='rounded-lg border border-gray-200 bg-white p-4'>
        <h2 className='mb-2 text-sm font-semibold text-gray-900'>
          权限 flags（12）
        </h2>
        {PERMISSION_FLAG_ROWS.map(({ flag, label }) => (
          <Row key={flag} label={label} value={String(perms[flag])} />
        ))}
      </section>
    </div>
  );
};

export default PermissionsPage;
