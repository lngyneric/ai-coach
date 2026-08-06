'use client';

import React, { useCallback, useEffect, useState } from 'react';
import api from '@/api';
import { useCoachPermissions } from '@/hooks/useCoachPermissions';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
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
 * 导师工作台（/admin/coach）。
 *
 * 面谈记录（coach_sessions）完整 CRUD 前端：
 *  - GET  /api/coach/sessions        → 列表（数据域：coach=mentored）
 *  - POST /api/coach/sessions        → 新建面谈（create_session + 数据域）
 *  - PUT  /api/coach/sessions/<bid>  → 更新 notes/topic
 *  - POST /api/coach/sessions/<bid>/summarize → AI 总结
 *
 * 报告与推荐入口（W2 已就绪的 AI 能力）：
 *  - GET /api/coach/report/<learner_bid>   → AI 报告
 *  - GET /api/portal/recommend             → 岗位推荐课程
 */

type SessionItem = {
  session_bid: string;
  learner_bid: string;
  mentor_bid: string;
  session_type: string;
  session_date: string | null;
  topic: string | null;
  mentor_notes: string | null;
  status: string | null;
  ai_summary: string | null;
  next_action: string | null;
};

type RecommendCourse = {
  shifu_bid: string;
  title: string;
  position_name: string | null;
  tag: string | null;
};

export default function CoachPage() {
  const { toast } = useToast();
  const perms = useCoachPermissions();

  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [createLearner, setCreateLearner] = useState('');
  const [createTopic, setCreateTopic] = useState('');
  const [creating, setCreating] = useState(false);

  const [recommend, setRecommend] = useState<RecommendCourse[]>([]);

  const loadSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const data = (await api.getCoachSessions({
        page: 1,
        size: 50,
      })) as { items?: SessionItem[]; total?: number };
      setSessions(data?.items || []);
    } catch (e) {
      console.error('[coach] sessions failed', e);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!perms.isLoading) {
      loadSessions();
    }
  }, [loadSessions, perms.isLoading]);

  useEffect(() => {
    if (perms.isLoading) {
      return;
    }
    api
      .getPortalRecommend({ limit: 6 })
      .then((data: any) => setRecommend(data?.courses || []))
      .catch(e => console.error('[coach] recommend failed', e));
  }, [perms.isLoading]);

  const handleCreate = async () => {
    if (!createLearner.trim() || !createTopic.trim()) {
      toast({ title: '请填写 learner_bid 和主题' });
      return;
    }
    setCreating(true);
    try {
      await api.createCoachSession({
        learner_bid: createLearner.trim(),
        topic: createTopic.trim(),
      });
      toast({ title: '面谈记录已创建' });
      setCreateLearner('');
      setCreateTopic('');
      await loadSessions();
    } catch (e: any) {
      toast({
        title: e?.message || '创建失败（可能需要 create_session 权限）',
        variant: 'destructive',
      });
    } finally {
      setCreating(false);
    }
  };

  const handleSummarize = async (sessionBid: string) => {
    try {
      const res = (await api.summarizeCoachSession({
        session_bid: sessionBid,
      })) as { summary_generated?: boolean };
      toast({
        title: res?.summary_generated
          ? 'AI 总结已生成'
          : '总结未生成（LLM 降级）',
      });
      await loadSessions();
    } catch (e: any) {
      toast({ title: e?.message || '总结失败', variant: 'destructive' });
    }
  };

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-xl font-semibold text-gray-900'>导师工作台</h1>
        <p className='mt-1 text-sm text-gray-500'>
          coach_sessions CRUD（数据域：{perms.dataScope || '—'}）
          {perms.isFallback ? '（后端未响应，回退 isOperator）' : ''}
        </p>
      </div>

      <Card className='border-slate-200'>
        <CardContent className='p-4'>
          <h2 className='mb-3 text-sm font-semibold text-gray-900'>
            新建面谈记录
          </h2>
          <div className='flex flex-col gap-2 sm:flex-row'>
            <Input
              placeholder='learner_bid（带教学员）'
              value={createLearner}
              onChange={e => setCreateLearner(e.target.value)}
              className='sm:max-w-[240px]'
            />
            <Input
              placeholder='主题（如：月度辅导）'
              value={createTopic}
              onChange={e => setCreateTopic(e.target.value)}
              className='flex-1'
            />
            <Button onClick={handleCreate} disabled={creating}>
              {creating ? '创建中…' : '创建'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className='border-slate-200'>
        <CardContent className='p-4'>
          <h2 className='mb-3 text-sm font-semibold text-gray-900'>
            面谈记录列表
          </h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>日期</TableHead>
                <TableHead>learner</TableHead>
                <TableHead>主题</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>AI 总结</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sessionsLoading ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className='text-center text-sm text-slate-400'
                  >
                    加载中…
                  </TableCell>
                </TableRow>
              ) : sessions.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className='text-center text-sm text-slate-400'
                  >
                    暂无面谈记录（coach 仅能看到带教学员的数据）
                  </TableCell>
                </TableRow>
              ) : (
                sessions.map(s => (
                  <TableRow key={s.session_bid}>
                    <TableCell>
                      {s.session_date?.slice(0, 10) || '—'}
                    </TableCell>
                    <TableCell>{s.learner_bid}</TableCell>
                    <TableCell className='max-w-[160px] truncate'>
                      {s.topic || '—'}
                    </TableCell>
                    <TableCell>{s.session_type}</TableCell>
                    <TableCell>
                      <Badge variant='secondary'>{s.status || '—'}</Badge>
                    </TableCell>
                    <TableCell className='max-w-[200px]'>
                      {s.ai_summary ? (
                        <span className='line-clamp-2 text-xs text-gray-500'>
                          {s.ai_summary.slice(0, 80)}…
                        </span>
                      ) : (
                        <span className='text-xs text-gray-400'>无</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className='flex gap-2'>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => handleSummarize(s.session_bid)}
                        >
                          AI 总结
                        </Button>
                        <a
                          href={`/admin/dept/report/${s.learner_bid}`}
                          className='text-xs text-blue-600 hover:underline'
                        >
                          报告
                        </a>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card className='border-slate-200'>
        <CardContent className='p-4'>
          <h2 className='mb-3 text-sm font-semibold text-gray-900'>
            为你推荐（/api/portal/recommend）
          </h2>
          <div className='grid grid-cols-1 gap-3 md:grid-cols-3'>
            {recommend.length === 0 ? (
              <p className='text-sm text-slate-400'>暂无推荐课程</p>
            ) : (
              recommend.map((course, idx) => (
                <div
                  key={`${course.shifu_bid}-${idx}`}
                  className='rounded-lg border border-slate-200 p-3'
                >
                  <p className='text-sm font-medium text-slate-800'>
                    {course.title}
                  </p>
                  <p className='mt-1 text-xs text-slate-500'>
                    {course.position_name || '—'}
                    {course.tag ? ` · ${course.tag}` : ''}
                  </p>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
