'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Clock,
  FileText,
  Loader2,
  MessageSquare,
  Route,
  Sparkles,
  Users,
} from 'lucide-react';
import { StageBadge, StageProgress } from '@/components/coach/StageIndicator';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import {
  FOCUS_MODULES,
  collectProgressTable,
  type FocusModulePlaceholder,
  type ProgressTable,
  type TaskCompletion,
  type TimelineEvent,
} from '@/lib/coach-api/progress';
import type { LifecycleStage } from '@/components/coach/StageIndicator';

/**
 * 学员带教进度详表（/admin/coach/students/[learner_bid]/progress）。
 *
 * 独立页面（非现有详情页 Tab），展示：
 *  1. 三大重点模块占位卡（入职 / 三个明白 / 小灶培训）—— 规则后续加入，完成度 0%
 *  2. 任务完成百分比（阶段完成度 / 面谈闭环率 / 验收完成度 / 课程完成度）——
 *     由现有状态字段聚合计算（learner_coaching.status / coach_sessions.status /
 *     learner_checklist_items.status），无数据时 0% + 占位提示，不虚构数据
 *  3. 带教进度详表 7 区块：学员信息 / 阶段进度 / 验收明细 / 面谈记录 /
 *     三态合规 / 任务课程 / 时间线
 *
 * 数据源：现有 coachApi 适配器（/api/portal/mentor/students、/api/coach/sessions、
 * checklist 三态、课程分配）。阶段明细端点（v1 缺口）未注册时对应区块显示占位。
 */

function stageFromStatus(status: string | null | undefined): LifecycleStage {
  if (status === 'in_progress') return 'mentorship';
  if (status === 'completed') return 'review';
  if (status === 'failed') return 'mentorship';
  return 'pending';
}

function ProgressBar({
  pctValue,
  tone = 'primary',
}: {
  pctValue: number;
  tone?: 'primary' | 'emerald';
}) {
  return (
    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
      <div
        className={cn(
          'h-full rounded-full transition-all',
          tone === 'emerald' ? 'bg-emerald-500' : 'bg-primary'
        )}
        style={{ width: `${Math.min(100, Math.max(0, pctValue))}%` }}
      />
    </div>
  );
}

/** 任务完成百分比卡片 */
function CompletionCard({ item }: { item: TaskCompletion }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">{item.label}</span>
        <span className="text-lg font-semibold tabular-nums">{item.pct}%</span>
      </div>
      <div className="mt-2">
        <ProgressBar pctValue={item.pct} tone={item.pct >= 100 ? 'emerald' : 'primary'} />
      </div>
      <div className="mt-2 text-xs text-muted-foreground">
        {item.placeholder ? (
          <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
            <Clock className="size-3" /> {item.placeholderNote ?? '数据源待接通'}
          </span>
        ) : (
          <>
            已完成 {item.done}/{item.total}
            <span className="ml-1.5 text-muted-foreground/60">· {item.source}</span>
          </>
        )}
      </div>
    </div>
  );
}

/** 三大重点模块占位卡 */
function FocusModuleCard({ module }: { module: FocusModulePlaceholder }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-muted/30 p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-medium">
            {module.name}
            <Badge variant="outline" className="text-[10px] text-muted-foreground">
              {module.placeholderNote}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{module.subtitle}</p>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-xl font-semibold text-muted-foreground">
            {module.pct}%
          </div>
          <div className="text-[10px] text-muted-foreground/60">完成度占位</div>
        </div>
      </div>
    </div>
  );
}

function EmptyBlock({ text }: { text: string }) {
  return (
    <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
      {text}
    </p>
  );
}

/** ① 学员信息 */
function LearnerInfoBlock({ table }: { table: ProgressTable }) {
  const l = table.learner;
  if (!l) return <EmptyBlock text="未在导师学员列表中找到该学员（数据域可能不覆盖）" />;
  const rows: Array<[string, string]> = [
    ['工号', l.employeeNo || '—'],
    ['部门', l.department || '—'],
    ['岗位', l.positionName || '—'],
    ['入职日期', l.onboardingDate || '—'],
    ['待评分', `${l.pendingScoreCount} 项`],
    ['待办任务', `${l.pendingTaskCount} 项`],
  ];
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {rows.map(([k, v]) => (
        <div key={k} className="rounded-lg border border-border bg-card p-3">
          <div className="text-xs text-muted-foreground">{k}</div>
          <div className="mt-0.5 truncate text-sm font-medium">{v}</div>
        </div>
      ))}
    </div>
  );
}

/** ③ 阶段进度明细 */
function PhasesBlock({ table }: { table: ProgressTable }) {
  if (table.phases.length === 0) {
    return (
      <EmptyBlock text="阶段明细数据待接通（v1 缺口：每学员阶段明细端点未注册）。接入后显示各阶段状态 / 四维评分 / 三态合规。" />
    );
  }
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
            <th className="px-4 py-2.5 font-medium">阶段</th>
            <th className="px-4 py-2.5 font-medium">状态</th>
            <th className="px-4 py-2.5 font-medium">总分</th>
            <th className="px-4 py-2.5 font-medium">验收进度</th>
            <th className="px-4 py-2.5 font-medium">开始</th>
            <th className="px-4 py-2.5 font-medium">完成</th>
          </tr>
        </thead>
        <tbody>
          {table.phases.map(p => (
            <tr key={p.recordBid} className="border-b border-border last:border-0">
              <td className="px-4 py-3 font-medium">{p.phaseName}</td>
              <td className="px-4 py-3">
                <Badge
                  variant={
                    p.status === 'completed'
                      ? 'default'
                      : p.status === 'in_progress'
                        ? 'secondary'
                        : 'outline'
                  }
                >
                  {p.status}
                </Badge>
              </td>
              <td className="px-4 py-3 tabular-nums">
                {p.totalScore > 0 ? p.totalScore : '—'}
              </td>
              <td className="px-4 py-3 text-muted-foreground">{p.checklistProgress}</td>
              <td className="px-4 py-3 text-muted-foreground">
                {p.startedAt ? p.startedAt.slice(0, 10) : '—'}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {p.completedAt ? p.completedAt.slice(0, 10) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** ④ 验收评分明细 */
function ChecklistBlock({ table }: { table: ProgressTable }) {
  if (table.checklist.length === 0) {
    return <EmptyBlock text="暂无验收项提交（pending-scores 派生）。scored/pending 全量需 checklist 全量端点（v1 缺口）。" />;
  }
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
            <th className="px-4 py-2.5 font-medium">验收项</th>
            <th className="px-4 py-2.5 font-medium">状态</th>
            <th className="px-4 py-2.5 font-medium">得分</th>
            <th className="px-4 py-2.5 font-medium">提交时间</th>
          </tr>
        </thead>
        <tbody>
          {table.checklist.map(c => (
            <tr key={c.recordBid} className="border-b border-border last:border-0">
              <td className="px-4 py-3 font-mono text-xs">{c.name}</td>
              <td className="px-4 py-3">
                <Badge variant={c.status === 'scored' ? 'default' : 'secondary'}>
                  {c.status}
                </Badge>
              </td>
              <td className="px-4 py-3 tabular-nums">
                {c.score != null ? `${c.score}/${c.maxScore}` : '—'}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {c.submittedAt
                  ? new Date(c.submittedAt).toLocaleString('zh-CN')
                  : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** ⑤ 面谈记录 */
function SessionsBlock({ table }: { table: ProgressTable }) {
  if (table.sessions.length === 0) {
    return <EmptyBlock text="暂无面谈记录" />;
  }
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
            <th className="px-4 py-2.5 font-medium">日期</th>
            <th className="px-4 py-2.5 font-medium">类型</th>
            <th className="px-4 py-2.5 font-medium">主题</th>
            <th className="px-4 py-2.5 font-medium">状态</th>
            <th className="px-4 py-2.5 font-medium">评分</th>
          </tr>
        </thead>
        <tbody>
          {table.sessions.map(s => (
            <tr key={s.sessionBid} className="border-b border-border last:border-0">
              <td className="px-4 py-3">
                {s.sessionDate ? s.sessionDate.slice(0, 10) : '—'}
              </td>
              <td className="px-4 py-3">{s.sessionType}</td>
              <td className="max-w-56 truncate px-4 py-3">{s.topic || '—'}</td>
              <td className="px-4 py-3">
                <Badge
                  variant={
                    s.status === 'summarized'
                      ? 'default'
                      : s.status === 'done'
                        ? 'secondary'
                        : 'outline'
                  }
                >
                  {s.status}
                </Badge>
              </td>
              <td className="px-4 py-3 tabular-nums">
                {s.coachRating != null ? s.coachRating : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** ⑧ 时间线 */
function TimelineBlock({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return <EmptyBlock text="暂无时间线事件（阶段 / 验收 / 面谈数据就绪后自动生成）" />;
  }
  const iconFor = (t: TimelineEvent['type']) => {
    if (t === 'phase_completed' || t === 'session_summarized') {
      return <CheckCircle2 className="size-4 text-emerald-500" />;
    }
    if (t === 'phase_started' || t === 'session_created') {
      return <Route className="size-4 text-primary" />;
    }
    if (t === 'session_done') return <MessageSquare className="size-4 text-primary" />;
    return <ClipboardList className="size-4 text-amber-500" />;
  };
  return (
    <ol className="space-y-0">
      {events.slice(0, 12).map((e, i) => (
        <li key={`${e.type}-${e.ref}-${i}`} className="relative flex gap-3 pb-4 last:pb-0">
          {i < Math.min(events.length, 12) - 1 && (
            <span className="absolute left-[7px] top-5 h-full w-px bg-border" />
          )}
          <span className="mt-0.5">{iconFor(e.type)}</span>
          <div className="min-w-0 flex-1 text-sm">
            <div className="flex flex-wrap items-center gap-x-2">
              <span className="truncate">{e.note}</span>
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <CalendarDays className="size-3" />
                {e.at ? new Date(e.at).toLocaleString('zh-CN') : '—'}
              </span>
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}

export default function LearnerProgressPage() {
  const params = useParams<{ learner_bid?: string }>();
  const learnerBid = params?.learner_bid ?? '';
  const [table, setTable] = useState<ProgressTable | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    collectProgressTable(learnerBid)
      .then(setTable)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [learnerBid]);

  // 仅在详表数据就绪后用于生命周期标识（table 为空时回退 pending，不参与渲染）。
  const stage = stageFromStatus(table?.learner?.currentPhaseStatus);

  return (
    <div className="space-y-6">
      {/* ── 返回 + 学员信息头 ── */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Link
            href={`/admin/coach/students/${learnerBid}`}
            className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-4" /> 返回学员详情
          </Link>
          <Link
            href={`/admin/coach/students/${learnerBid}/report`}
            className="mb-2 inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary-lighter"
          >
            <FileText className="size-4" /> 查看报告
          </Link>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {table?.learner?.name ?? learnerBid}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">带教进度详表</p>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          加载失败：{error}
        </div>
      )}

      {loading && (
        <div className="flex h-64 items-center justify-center text-muted-foreground">
          <Loader2 className="mr-2 size-5 animate-spin" /> 加载中…
        </div>
      )}

      {!loading && !error && table && (
        <>
          {/* ── 生命周期标识 ── */}
          <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card p-4">
            <StageBadge stage={stage} />
            <StageProgress stage={stage} />
            <span className="ml-auto text-xs text-muted-foreground">
              {table.summary.completedPhases}/{table.summary.totalPhases} 阶段完成
            </span>
          </div>

          {/* ── 三大重点模块占位（规则后续加入）── */}
          <section className="space-y-3">
            <h2 className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
              <Sparkles className="size-4 text-amber-500" /> 三大重点模块
            </h2>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {FOCUS_MODULES.map(m => (
                <FocusModuleCard key={m.key} module={m} />
              ))}
            </div>
          </section>

          {/* ── 任务完成百分比 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">任务完成百分比</h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {table.completion.map(c => (
                <CompletionCard key={c.key} item={c} />
              ))}
            </div>
          </section>

          {/* ── ① 学员信息 ── */}
          <section className="space-y-3">
            <h2 className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
              <Users className="size-4 text-primary" /> 学员信息
            </h2>
            <LearnerInfoBlock table={table} />
          </section>

          {/* ── ② 阶段进度总览 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">阶段进度总览</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {[
                ['总阶段', table.summary.totalPhases],
                ['已完成', table.summary.completedPhases],
                ['进行中', table.summary.inProgressPhases],
                ['面谈次数', table.summary.sessionCount],
                ['验收提交', table.summary.checklistTotal],
                ['已评分', table.summary.checklistScored],
              ].map(([k, v]) => (
                <div key={String(k)} className="rounded-xl border border-border bg-card p-4">
                  <div className="text-xs text-muted-foreground">{k}</div>
                  <div className="mt-1 text-2xl font-semibold tabular-nums">{v}</div>
                </div>
              ))}
            </div>
          </section>

          {/* ── ③ 阶段进度明细 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">阶段进度明细</h2>
            <PhasesBlock table={table} />
          </section>

          {/* ── ④ 验收评分明细 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">验收评分明细</h2>
            <ChecklistBlock table={table} />
          </section>

          {/* ── ⑤ 面谈记录 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">面谈记录</h2>
            <SessionsBlock table={table} />
          </section>

          {/* ── ⑥ 三态合规 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">三态合规</h2>
            <EmptyBlock text="三态合规（学员签字 / 导师同步 / 改进计划）需阶段 record_bid 逐条查询 /api/coach/checklist/<record_bid>；阶段明细端点未接通前显示占位。" />
          </section>

          {/* ── ⑦ 任务与课程 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">任务与课程</h2>
            <EmptyBlock text="课程分配 / learner_tasks 完成度需 manage_users 数据域接口（coach 不可达），待接通后显示课程任务完成明细。" />
          </section>

          {/* ── ⑧ 时间线 ── */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-muted-foreground">时间线</h2>
            <div className="rounded-xl border border-border bg-card p-4">
              <TimelineBlock events={table.timeline} />
            </div>
          </section>
        </>
      )}
    </div>
  );
}
