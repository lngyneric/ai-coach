'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import api from '@/api';
import { useCoachPermissions } from '@/hooks/useCoachPermissions';
import { useUserStore } from '@/store';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table';
import { useToast } from '@/hooks/useToast';

/**
 * HR 工作台（/admin/hr）。
 *
 * 数据源：已就绪的 portal admin API（后端 manage_users / view_kpi / audit
 * 守卫已按 5 级角色放行 admin + hr）：
 *  - GET /api/portal/admin/learners  → 学员花名册（manage_users）
 *  - GET /api/portal/admin/stats     → KPI 概览（view_kpi）
 *  - GET /api/portal/admin/roles     → 角色分配视图（manage_users）
 *  - GET /api/coach/report/<bid>     → AI 报告跳转（view_any_report）
 *
 * 注意：后端 API 是真正的权限边界；本页仅为前端 UI 层。
 */

type Learner = {
  learner_bid: string;
  user_bid: string;
  employee_no: string | null;
  department: string | null;
  position_name: string | null;
  level: string | null;
  coach_bid: string | null;
  status: string | null;
  onboarding_date: string | null;
};

type Stats = {
  total_learners: number;
  active_learners: number;
  in_progress_mentorships: number;
  passed_mentorships: number;
};

const StatCard = ({
  label,
  value,
  accent,
}: {
  label: string;
  value: number | string;
  accent?: string;
}) => (
  <Card className='border-slate-200'>
    <CardContent className='p-4'>
      <p className='text-xs text-slate-500'>{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${accent || 'text-slate-900'}`}>
        {value}
      </p>
    </CardContent>
  </Card>
);

export default function HrWorkbenchPage() {
  const { toast } = useToast();
  const perms = useCoachPermissions();
  const isOperator = useUserStore(state =>
    Boolean(state.userInfo?.is_operator),
  );

  const [learners, setLearners] = useState<Learner[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [roles, setRoles] = useState<Array<Record<string, unknown>>>([]);
  const [rolesLoading, setRolesLoading] = useState(false);

  const canManage = isOperator || perms.canManageUsers;

  const fetchLearners = useCallback(async () => {
    if (!canManage) {
      return;
    }
    try {
      const data = (await api.getPortalAdminLearners({
        page: 1,
        size: 50,
      })) as { items?: Learner[]; total?: number };
      setLearners(data?.items || []);
    } catch (e) {
      console.error('[hr] learners failed', e);
    } finally {
      setLoading(false);
    }
  }, [canManage]);

  const fetchStats = useCallback(async () => {
    try {
      const data = (await api.getPortalAdminStats({})) as Stats;
      setStats(data);
    } catch (e) {
      console.error('[hr] stats failed', e);
    }
  }, []);

  const fetchRoles = useCallback(async () => {
    setRolesLoading(true);
    try {
      const data = (await api.getPortalAdminRoles({
        page: 1,
        size: 50,
      })) as { items?: Array<Record<string, unknown>> };
      setRoles(data?.items || []);
    } catch (e) {
      console.error('[hr] roles failed', e);
    } finally {
      setRolesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!perms.isLoading) {
      fetchLearners();
      fetchStats();
    }
  }, [fetchLearners, fetchStats, perms.isLoading]);

  const handleLoadRoles = () => {
    fetchRoles().then(() => {
      toast({ title: '角色分配数据已加载' });
    });
  };

  const rosterBody = useMemo(() => {
    if (!canManage) {
      return (
        <TableRow>
          <TableCell colSpan={7} className='text-center text-sm text-slate-400'>
            需要 manage_users 权限（admin / HR）
          </TableCell>
        </TableRow>
      );
    }
    if (loading) {
      return (
        <TableRow>
          <TableCell colSpan={7} className='text-center text-sm text-slate-400'>
            加载中…
          </TableCell>
        </TableRow>
      );
    }
    if (learners.length === 0) {
      return (
        <TableRow>
          <TableCell colSpan={7} className='text-center text-sm text-slate-400'>
            暂无学员数据
          </TableCell>
        </TableRow>
      );
    }
    return learners.map(learner => (
      <TableRow key={learner.learner_bid}>
        <TableCell>{learner.employee_no || '—'}</TableCell>
        <TableCell>{learner.user_bid}</TableCell>
        <TableCell>{learner.department || '—'}</TableCell>
        <TableCell>{learner.position_name || '—'}</TableCell>
        <TableCell>{learner.coach_bid || '—'}</TableCell>
        <TableCell>
          <Badge
            variant='secondary'
            className={learner.status === 'active' ? '' : 'opacity-60'}
          >
            {learner.status || '—'}
          </Badge>
        </TableCell>
        <TableCell>
          <Link
            href={`/admin/hr/report/${learner.learner_bid}`}
            className='text-xs text-blue-600 hover:underline'
          >
            AI 报告
          </Link>
        </TableCell>
      </TableRow>
    ));
  }, [canManage, learners, loading]);

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-xl font-semibold text-gray-900'>HR 工作台</h1>
        <p className='mt-1 text-sm text-gray-500'>
          manage_users / view_kpi / audit 数据（数据源 /api/portal/admin/*）
          {perms.isFallback ? '（后端未响应，回退 isOperator）' : ''}
        </p>
      </div>

      <div className='grid grid-cols-2 gap-4 lg:grid-cols-4'>
        <StatCard
          label='学员总数'
          value={stats?.total_learners ?? '—'}
        />
        <StatCard
          label='在册学员'
          value={stats?.active_learners ?? '—'}
          accent='text-emerald-600'
        />
        <StatCard
          label='进行中带教'
          value={stats?.in_progress_mentorships ?? '—'}
          accent='text-blue-600'
        />
        <StatCard
          label='已通过'
          value={stats?.passed_mentorships ?? '—'}
          accent='text-purple-600'
        />
      </div>

      <Card className='border-slate-200'>
        <CardContent className='p-4'>
          <div className='mb-3 flex items-center justify-between'>
            <h2 className='text-sm font-semibold text-gray-900'>学员花名册</h2>
            <Button size='sm' variant='outline' onClick={handleLoadRoles}>
              {rolesLoading ? '加载中…' : '查看角色分配'}
            </Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>工号</TableHead>
                <TableHead>user_bid</TableHead>
                <TableHead>部门</TableHead>
                <TableHead>岗位</TableHead>
                <TableHead>coach</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>报告</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>{rosterBody}</TableBody>
          </Table>
          {roles.length > 0 && (
            <div className='mt-4'>
              <h3 className='mb-2 text-xs font-semibold text-gray-500'>
                角色分配（前 10 位用户）
              </h3>
              <div className='max-h-48 space-y-1 overflow-y-auto text-xs text-gray-600'>
                {roles.slice(0, 10).map((user: any) => (
                  <div key={user.user_bid} className='flex gap-2'>
                    <span className='w-40 truncate'>
                      {user.nickname || user.user_bid}
                    </span>
                    <span>
                      {(user.roles || [])
                        .map((r: any) => r.name || r.role_bid)
                        .join(', ') || '未分配'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
