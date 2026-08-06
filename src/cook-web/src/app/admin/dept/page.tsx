'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/api';
import { useCoachPermissions } from '@/hooks/useCoachPermissions';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table';

/**
 * 部门负责人看板（/admin/dept）。
 *
 * dept_head 的数据范围由后端 visible_students_scope 决定（department:<dept>），
 * /api/portal/admin/learners 已按该范围过滤，本页无需自行过滤。
 *
 * 部门级 6 key（P0-PERMISSION-KEYS.md §二 role-dept-head）：
 *  view_all_students / view_any_report / certify_content / view_kpi /
 *  custom_dashboard / view_own_report
 */

type Learner = {
  learner_bid: string;
  user_bid: string;
  employee_no: string | null;
  department: string | null;
  position_name: string | null;
  coach_bid: string | null;
  status: string | null;
};

export default function DeptHeadPage() {
  const perms = useCoachPermissions();
  const [learners, setLearners] = useState<Learner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (perms.isLoading) {
      return;
    }
    api
      .getPortalAdminLearners({ page: 1, size: 50 })
      .then(data => {
        setLearners((data as { items?: Learner[] })?.items || []);
        setError(null);
      })
      .catch(e => {
        console.error('[dept] learners failed', e);
        setError('数据加载失败（可能需要 view_all_students 权限）');
      })
      .finally(() => setLoading(false));
  }, [perms.isLoading]);

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-xl font-semibold text-gray-900'>部门看板</h1>
        <p className='mt-1 text-sm text-gray-500'>
          数据范围：{perms.dataScope || '—'}（后端
          visible_students_scope 部门过滤）
        </p>
      </div>

      <div className='grid grid-cols-2 gap-4 lg:grid-cols-3'>
        <Card className='border-slate-200'>
          <CardContent className='p-4'>
            <p className='text-xs text-slate-500'>本部门学员</p>
            <p className='mt-1 text-2xl font-semibold text-slate-900'>
              {loading ? '—' : learners.length}
            </p>
          </CardContent>
        </Card>
        <Card className='border-slate-200'>
          <CardContent className='p-4'>
            <p className='text-xs text-slate-500'>canViewDeptOnly</p>
            <p className='mt-1 text-2xl font-semibold text-slate-900'>
              {String(perms.canViewDeptOnly)}
            </p>
          </CardContent>
        </Card>
        <Card className='border-slate-200'>
          <CardContent className='p-4'>
            <p className='text-xs text-slate-500'>部门名</p>
            <p className='mt-1 text-2xl font-semibold text-slate-900'>
              {perms.scopeValue || '—'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className='border-slate-200'>
        <CardContent className='p-4'>
          <h2 className='mb-3 text-sm font-semibold text-gray-900'>
            本部门学员
          </h2>
          {error && <p className='mb-2 text-xs text-red-600'>{error}</p>}
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
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className='text-center text-sm text-slate-400'
                  >
                    加载中…
                  </TableCell>
                </TableRow>
              ) : learners.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className='text-center text-sm text-slate-400'
                  >
                    暂无本部门学员
                  </TableCell>
                </TableRow>
              ) : (
                learners.map(learner => (
                  <TableRow key={learner.learner_bid}>
                    <TableCell>{learner.employee_no || '—'}</TableCell>
                    <TableCell>{learner.user_bid}</TableCell>
                    <TableCell>{learner.department || '—'}</TableCell>
                    <TableCell>{learner.position_name || '—'}</TableCell>
                    <TableCell>{learner.coach_bid || '—'}</TableCell>
                    <TableCell>
                      <Badge variant='secondary'>
                        {learner.status || '—'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/admin/dept/report/${learner.learner_bid}`}
                        className='text-xs text-blue-600 hover:underline'
                      >
                        AI 报告
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
