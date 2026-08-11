'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  CirclePlay,
  ClipboardCheck,
  Loader2,
  Users,
} from 'lucide-react';
import api from '@/api';
import { coachApi } from '@/lib/coach-api';
import type { CoachStudent, PendingScore } from '@/lib/coach-api/types';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';
import { useToast } from '@/hooks/useToast';
import { cn } from '@/lib/utils';

/**
 * 导师工作台（/admin/coach）。
 *
 * coach-lab 迁移后整合为三 Tab：
 *  - Tab1 学员看板：统计卡 + 学员列表 + 待评分明细（coach-lab coach/page 迁入，
 *    数据源 /api/portal/mentor/students + /api/portal/mentor/pending-scores）
 *  - Tab2 面谈记录：coach_sessions 完整 CRUD + AI 总结（原有功能，保留不回归）
 *  - Tab3 为你推荐：/api/portal/recommend（原有功能，保留）
 *
 * 权限：菜单入口由 admin-menu（create_session → /admin/coach）控制；
 * 数据域由后端 visible_students_scope 过滤。
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

function hoursSince(iso: string | null): number {
  if (!iso) return 0;
  return (Date.now() - new Date(iso).getTime()) / 3600_000;
}

const phaseStatusLabel: Record<string, { text: string; className: string }> = {
  in_progress: { text: '进行中', className: 'bg-primary/10 text-primary' },
  completed: {
    text: '已通过',
    className: 'bg-success/15 text-emerald-600 dark:text-emerald-400',
  },
  failed: { text: '未通过', className: 'bg-destructive/10 text-destructive' },
};

function StatCard({
  icon: Icon,
  label,
  value,
  tone = 'default',
}: {
  icon: typeof Users;
  label: string;
  value: number;
  tone?: 'default' | 'danger';
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Icon className={cn('size-4', tone === 'danger' && 'text-destructive')} />
        {label}
      </div>
      <div
        className={cn(
          'mt-2 text-3xl font-semibold tracking-tight',
          tone === 'danger' && value > 0 && 'text-destructive'
        )}
      >
        {value}
      </div>
    </div>
  );
}

function StudentCard({ student }: { student: CoachStudent }) {
  const phase = student.currentPhaseStatus
    ? phaseStatusLabel[student.currentPhaseStatus]
    : undefined;
  return (
    <Link
      href={`/admin/coach/students/${student.learnerBid}`}
      className="group flex items-center gap-4 rounded-xl border border-border bg-card p-4 transition-shadow hover:shadow-md"
    >
      <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-base font-semibold text-primary">
        {student.name.slice(0, 1)}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium">{student.name}</span>
          <span className="text-xs text-muted-foreground">
            {student.employeeNo}
          </span>
          {phase && (
            <span className={cn('rounded-full px-2 py-0.5 text-xs', phase.className)}>
              {phase.text}
            </span>
          )}
          {student.pendingScoreCount > 0 && (
            <span className="rounded-full bg-destructive/10 px-2 py-0.5 text-xs text-destructive">
              {student.pendingScoreCount} 项待评分
            </span>
          )}
        </div>
        <div className="mt-1 text-sm text-muted-foreground">
          {student.department} · {student.positionName}
          {student.onboardingDate && ` · ${student.onboardingDate} 入职`}
        </div>
      </div>
      <ArrowRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
    </Link>
  );
}

/** Tab1 学员看板（coach-lab coach/page 迁入） */
function StudentDashboardTab() {
  const [students, setStudents] = useState<CoachStudent[] | null>(null);
  const [pending, setPending] = useState<PendingScore[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([coachApi.listStudents(), coachApi.listPendingScores()])
      .then(([s, p]) => {
        setStudents(s);
        setPending(p);
      })
      .catch(e => setError(String(e)));
  }, []);

  const sorted = useMemo(() => {
    if (!students) return [];
    return [...students].sort((a, b) => {
      if (b.pendingScoreCount !== a.pendingScoreCount)
        return b.pendingScoreCount - a.pendingScoreCount;
      const order = (s: string | null) => (s === 'in_progress' ? 0 : s ? 1 : 2);
      return order(a.currentPhaseStatus) - order(b.currentPhaseStatus);
    });
  }, [students]);

  if (error)
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
        数据加载失败：{error}
      </div>
    );

  if (!students || !pending)
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 size-5 animate-spin" /> 加载中…
      </div>
    );

  const overdueCount = pending.filter(p => hoursSince(p.submittedAt) > 48).length;
  const inProgress = students.filter(
    s => s.currentPhaseStatus === 'in_progress'
  ).length;
  const completed = students.filter(s => !s.currentPhaseStatus).length;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard icon={Users} label="在带学员" value={students.length} />
        <StatCard
          icon={ClipboardCheck}
          label="待评分"
          value={pending.length}
          tone={overdueCount > 0 ? 'danger' : 'default'}
        />
        <StatCard icon={CirclePlay} label="进行中阶段" value={inProgress} />
        <StatCard icon={BadgeCheck} label="已完成带教" value={completed} />
      </div>

      {pending.length > 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-warning/40 bg-warning/10 p-4 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" />
          <div>
            <b>{pending.length} 项验收待评分</b>
            {overdueCount > 0 && (
              <span className="text-muted-foreground">
                ，其中 {overdueCount} 项已超过 48 小时，将触发系统催办
              </span>
            )}
          </div>
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground">学员列表</h2>
        {sorted.length === 0 && (
          <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
            暂无带教学员（数据域由后端控制）
          </p>
        )}
        {sorted.map(s => (
          <StudentCard key={s.learnerBid} student={s} />
        ))}
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground">待评分明细</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
                <th className="px-4 py-2.5 font-medium">学员</th>
                <th className="px-4 py-2.5 font-medium">验收项</th>
                <th className="px-4 py-2.5 font-medium">提交时间</th>
                <th className="px-4 py-2.5 font-medium">学员备注</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {pending.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-6 text-center text-muted-foreground"
                  >
                    暂无待评分验收项
                  </td>
                </tr>
              )}
              {pending.map(p => {
                const student = students.find(s => s.learnerBid === p.learnerBid);
                const overdue = hoursSince(p.submittedAt) > 48;
                return (
                  <tr
                    key={p.recordBid}
                    className="border-b border-border last:border-0"
                  >
                    <td className="px-4 py-3">
                      {student?.name ?? p.learnerBid}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{p.itemBid}</td>
                    <td className="px-4 py-3">
                      {overdue && <span title="超过48小时">🔴 </span>}
                      {p.submittedAt
                        ? new Date(p.submittedAt).toLocaleString('zh-CN')
                        : '—'}
                    </td>
                    <td className="max-w-48 truncate px-4 py-3 text-muted-foreground">
                      {p.comment}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        href={`/admin/coach/students/${p.learnerBid}?score=${p.recordBid}`}
                        className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary-lighter"
                      >
                        去评分
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

/** Tab2 面谈记录（原 admin/coach 页面 sessions CRUD，保留不回归） */
function SessionsTab() {
  const { toast } = useToast();
  const perms = useCoachPermissions();

  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  // Training-loop（TRAINING-LOOP-DESIGN §改造1）：面谈学员必须从"我的学员"
  // 下拉选择（GET /api/portal/mentor/students，仅当前导师带教），禁止手工
  // 输入 learner_bid。
  const [students, setStudents] = useState<CoachStudent[]>([]);
  const [studentsLoading, setStudentsLoading] = useState(true);
  const [createLearner, setCreateLearner] = useState('');
  const [createTopic, setCreateTopic] = useState('');
  const [creating, setCreating] = useState(false);

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
    if (perms.isLoading) {
      return;
    }
    coachApi
      .listStudents()
      .then(setStudents)
      .catch(e => {
        console.error('[coach] students failed', e);
        toast({ title: '学员列表加载失败', variant: 'destructive' });
      })
      .finally(() => setStudentsLoading(false));
    loadSessions();
  }, [loadSessions, perms.isLoading, toast]);

  const handleCreate = async () => {
    const selectedStudent = students.find(
      s => s.learnerBid === createLearner
    );
    if (!createLearner || !createTopic.trim()) {
      toast({ title: '请选择学员并填写主题' });
      return;
    }
    setCreating(true);
    try {
      await api.createCoachSession({
        learner_bid: createLearner,
        topic: createTopic.trim(),
        // 可选关联学员当前阶段 learner_coaching.record_bid（闭环，改造2）
        phase_record_bid: selectedStudent?.currentPhaseRecordBid ?? undefined,
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
        title: res?.summary_generated ? 'AI 总结已生成' : '总结未生成（LLM 降级）',
      });
      await loadSessions();
    } catch (e: any) {
      toast({ title: e?.message || '总结失败', variant: 'destructive' });
    }
  };

  return (
    <div className="space-y-6">
      <Card className="border-slate-200">
        <CardContent className="p-4">
          <h2 className="mb-3 text-sm font-semibold text-gray-900">
            新建面谈记录
          </h2>
          <div className="flex flex-col gap-2 sm:flex-row">
            {studentsLoading ? (
              <Input
                value="加载学员…"
                disabled
                className="sm:max-w-[240px]"
              />
            ) : students.length === 0 ? (
              <div className="flex h-8 items-center gap-2 rounded-md border border-warning/40 bg-warning/10 px-3 text-sm text-amber-600 sm:max-w-[240px]">
                无学员，请先分配
              </div>
            ) : (
              <Select value={createLearner} onValueChange={setCreateLearner}>
                <SelectTrigger className="sm:max-w-[240px]">
                  <SelectValue placeholder="选择学员（仅带教）" />
                </SelectTrigger>
                <SelectContent>
                  {students.map(s => (
                    <SelectItem key={s.learnerBid} value={s.learnerBid}>
                      {s.name || s.employeeNo || s.learnerBid}
                      {s.employeeNo ? `（${s.employeeNo}）` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Input
              placeholder="主题（如：月度辅导）"
              value={createTopic}
              onChange={e => setCreateTopic(e.target.value)}
              className="flex-1"
            />
            <Button
              onClick={handleCreate}
              disabled={creating || !createLearner || students.length === 0}
            >
              {creating ? '创建中…' : '创建'}
            </Button>
          </div>
          {!studentsLoading &&
            students.length > 0 &&
            createLearner &&
            (() => {
              const selected = students.find(
                s => s.learnerBid === createLearner
              );
              return (
                <p className="mt-2 text-xs text-slate-400">
                  {selected?.currentPhaseRecordBid
                    ? '面谈将自动关联该学员当前阶段记录'
                    : '该学员未纳入阶段计划，面谈将不关联阶段记录'}
                </p>
              );
            })()}
          <p className="mt-2 text-xs text-slate-400">
            coach_sessions CRUD（数据域：{perms.dataScope || '—'}
            {perms.isFallback ? '（后端未响应，回退 isOperator）' : ''}）
          </p>
        </CardContent>
      </Card>

      <Card className="border-slate-200">
        <CardContent className="p-4">
          <h2 className="mb-3 text-sm font-semibold text-gray-900">
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
                  <TableCell colSpan={7} className="text-center text-sm text-slate-400">
                    加载中…
                  </TableCell>
                </TableRow>
              ) : sessions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-sm text-slate-400">
                    暂无面谈记录（coach 仅能看到带教学员的数据）
                  </TableCell>
                </TableRow>
              ) : (
                sessions.map(s => (
                  <TableRow key={s.session_bid}>
                    <TableCell>{s.session_date?.slice(0, 10) || '—'}</TableCell>
                    <TableCell>
                      <Link
                        href={`/admin/coach/students/${s.learner_bid}`}
                        className="text-blue-600 hover:underline"
                      >
                        {s.learner_bid}
                      </Link>
                    </TableCell>
                    <TableCell className="max-w-[160px] truncate">
                      {s.topic || '—'}
                    </TableCell>
                    <TableCell>{s.session_type}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{s.status || '—'}</Badge>
                    </TableCell>
                    <TableCell className="max-w-[200px]">
                      {s.ai_summary ? (
                        <span className="line-clamp-2 text-xs text-gray-500">
                          {s.ai_summary.slice(0, 80)}…
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">无</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleSummarize(s.session_bid)}
                        >
                          AI 总结
                        </Button>
                        <a
                          href={`/admin/dept/report/${s.learner_bid}`}
                          className="text-xs text-blue-600 hover:underline"
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
    </div>
  );
}

/** Tab3 为你推荐（原 admin/coach 页面推荐区，保留不回归） */
function RecommendTab() {
  const perms = useCoachPermissions();
  const [recommend, setRecommend] = useState<RecommendCourse[]>([]);

  useEffect(() => {
    if (perms.isLoading) {
      return;
    }
    api
      .getPortalRecommend({ limit: 6 })
      .then((data: any) => setRecommend(data?.courses || []))
      .catch(e => console.error('[coach] recommend failed', e));
  }, [perms.isLoading]);

  return (
    <Card className="border-slate-200">
      <CardContent className="p-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-900">
          为你推荐（/api/portal/recommend）
        </h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {recommend.length === 0 ? (
            <p className="text-sm text-slate-400">暂无推荐课程</p>
          ) : (
            recommend.map((course, idx) => (
              <div
                key={`${course.shifu_bid}-${idx}`}
                className="rounded-lg border border-slate-200 p-3"
              >
                <p className="text-sm font-medium text-slate-800">
                  {course.title}
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {course.position_name || '—'}
                  {course.tag ? ` · ${course.tag}` : ''}
                </p>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function CoachPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">导师工作台</h1>
        <p className="mt-1 text-sm text-gray-500">
          学员带教进度、验收评分与 1v1 面谈闭环
        </p>
      </div>

      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList>
          <TabsTrigger value="dashboard">学员看板</TabsTrigger>
          <TabsTrigger value="sessions">面谈记录</TabsTrigger>
          <TabsTrigger value="recommend">为你推荐</TabsTrigger>
        </TabsList>
        <TabsContent value="dashboard">
          <StudentDashboardTab />
        </TabsContent>
        <TabsContent value="sessions">
          <SessionsTab />
        </TabsContent>
        <TabsContent value="recommend">
          <RecommendTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
