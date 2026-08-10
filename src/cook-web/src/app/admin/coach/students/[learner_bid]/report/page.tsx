'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowLeft,
  BadgeCheck,
  CalendarDays,
  ClipboardCheck,
  FileText,
  Loader2,
  MessageSquare,
  Sparkles,
  TrendingUp,
  Wand2,
} from 'lucide-react';
import { coachApi } from '@/lib/coach-api';
import type { CoachReport, CoachSession } from '@/lib/coach-api/types';
import { cn } from '@/lib/utils';
import { statusLabel } from '@/components/coach/ReportCharts';
import {
  CustomReportCharts,
  DepartmentFeedback,
  ExpandableSummary,
} from '@/components/coach/ReportEnhancements';
import api from '@/api';

/**
 * 学员分析报告页（/admin/coach/students/[learner_bid]/report）。
 *
 * coach-lab app/report/[learnerId]/page.tsx 迁移适配：
 *  - React 18 适配：`useParams()` 取代 React 19 `use(params)`；
 *  - 4 统计卡 / 趋势·维度图表 / 阶段明细 / 面谈时间线 / AI 改进建议；
 *  - AI 改进建议调用真实后端 GET /api/coach/report/<learner_bid>（source=auto：
 *    LLM 优先，规则降级），失败时展示降级文案，不虚构内容；
 *  - 阶段明细（PhaseDetail[]）在 dev 后端无 live 端点 → v1 空态降级，
 *    统计卡/图表/阶段列表在端点就绪后自动激活；面谈时间线与 AI 建议基于
 *    实时数据工作。
 */

const statusStyle: Record<string, string> = {
  completed: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  in_progress: 'bg-primary/10 text-primary',
  not_started: 'bg-secondary text-muted-foreground',
  failed: 'bg-destructive/10 text-destructive',
};

function OverviewCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof BadgeCheck;
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Icon className="size-4" />
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-tight tabular-nums">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

/** 后端 GET /api/coach/report/<learner_bid> 响应（make_common_response.data） */
interface AiReportPayload {
  learner_bid?: string;
  generated_by?: string;
  markdown?: string;
  report?: {
    summary?: string;
    strengths?: string[];
    improvements?: string[];
    suggestions?: string[];
    next_actions?: string[];
    overall_status?: string;
  };
  context?: {
    session_count?: number;
    mentorship_count?: number;
    enrollment_count?: number;
  };
}

function AiAdviceCard({
  ai,
  loading,
  error,
}: {
  ai: AiReportPayload | null;
  loading: boolean;
  error: string | null;
}) {
  const structured = ai?.report;
  const summary = structured?.summary;
  const overallStatus = structured?.overall_status;
  const strengths = structured?.strengths ?? [];
  const improvements = structured?.improvements ?? [];
  const suggestions = structured?.suggestions ?? [];
  const nextActions = structured?.next_actions ?? [];
  const hasStructured =
    structured &&
    (summary ||
      strengths.length ||
      improvements.length ||
      suggestions.length ||
      nextActions.length);

  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
        <Wand2 className="size-4 text-primary" /> AI 改进建议
      </h2>

      {loading && (
        <div className="flex items-center gap-2 rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" /> 正在生成 AI 建议（真实 LLM 或规则降级）…
        </div>
      )}

      {!loading && error && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-sm text-muted-foreground">
          <b className="text-amber-600 dark:text-amber-400">AI 建议暂不可用</b>
          <p className="mt-1">
            {error}。降级说明：报告页其余内容（统计卡 / 面谈时间线）仍基于实时数据展示。
          </p>
        </div>
      )}

      {!loading && !error && hasStructured && (
        <div className="space-y-3 rounded-xl border border-border bg-card p-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-medium">
              <Sparkles className="size-4 text-primary" />
              {ai?.generated_by === 'llm' ? 'LLM 个性化建议' : '规则生成建议'}
            </span>
            {overallStatus && (
              <span className="rounded-full bg-secondary px-2 py-0.5 text-xs text-muted-foreground">
                总评：{overallStatus}
              </span>
            )}
          </div>

          {summary && (
            <div className="rounded-lg border border-border bg-muted/30 p-3">
              <span className="text-xs font-medium text-muted-foreground">整体评价</span>
              <p className="mt-1">{summary}</p>
            </div>
          )}

          {strengths.length > 0 && (
            <SectionLines title="优势亮点" tone="emerald" lines={strengths} />
          )}
          {improvements.length > 0 && (
            <SectionLines title="待改进" tone="amber" lines={improvements} />
          )}
          {suggestions.length > 0 && (
            <SectionLines title="提升建议" tone="primary" lines={suggestions} />
          )}
          {nextActions.length > 0 && (
            <SectionLines title="下一步行动计划" tone="primary" lines={nextActions} />
          )}
        </div>
      )}

      {!loading && !error && !hasStructured && ai?.markdown && (
        <div className="whitespace-pre-wrap rounded-xl border border-border bg-card p-4 text-sm leading-relaxed text-muted-foreground">
          {ai.markdown}
        </div>
      )}

      {!loading && !error && !hasStructured && !ai?.markdown && (
        <div className="flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4 text-sm">
          <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
          <div>
            <b>暂无可用建议</b>
            <p className="mt-1 text-muted-foreground">
              后端尚未返回报告内容（可能学员暂无带教数据）。建议先建立学习档案并安排首次面谈。
            </p>
          </div>
        </div>
      )}
    </section>
  );
}

function SectionLines({
  title,
  tone,
  lines,
}: {
  title: string;
  tone: 'emerald' | 'amber' | 'primary';
  lines: string[];
}) {
  const dot =
    tone === 'emerald'
      ? 'text-emerald-500'
      : tone === 'amber'
        ? 'text-amber-500'
        : 'text-primary';
  return (
    <div>
      <span className="text-xs font-medium text-muted-foreground">{title}</span>
      <ul className="mt-1 space-y-1">
        {lines.map((item, i) => (
          <li key={i} className="flex items-start gap-1.5">
            <span className={cn('mt-1.5 size-1.5 shrink-0 rounded-full', dot)} />
            <span className="text-muted-foreground">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function CoachStudentReportPage() {
  const params = useParams<{ learner_bid?: string }>();
  const learnerBid = params?.learner_bid ?? '';

  const [report, setReport] = useState<CoachReport | null>(null);
  const [sessions, setSessions] = useState<CoachSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI 改进建议（真实后端 /api/coach/report，LLM 或规则降级）
  const [ai, setAi] = useState<AiReportPayload | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    if (!learnerBid) {
      setLoading(false);
      return () => {
        alive = false;
      };
    }
    setLoading(true);
    setError(null);
    Promise.all([
      coachApi.getReport(learnerBid),
      coachApi.listSessions(learnerBid).catch(() => [] as CoachSession[]),
    ])
      .then(([r, s]) => {
        if (!alive) return;
        setReport(r);
        setSessions(s);
      })
      .catch(e => {
        if (alive) setError(String(e));
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [learnerBid]);

  useEffect(() => {
    let alive = true;
    if (!learnerBid) return () => {
      alive = false;
    };
    setAiLoading(true);
    setAiError(null);
    api
      .getCoachReport({ learner_bid: learnerBid, source: 'auto' })
      .then((res: unknown) => {
        if (alive) setAi(res as AiReportPayload);
      })
      .catch(e => {
        if (alive) setAiError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (alive) setAiLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [learnerBid]);

  if (error)
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
        报告加载失败：{error}
      </div>
    );

  if (loading || !report)
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 size-5 animate-spin" /> 生成报告中…
      </div>
    );

  const summarizedPhases = report.phases.filter(p => p.coachSummary);
  const startedScore = report.phases.filter(p => p.status !== 'not_started').at(-1);

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <Link
            href={`/admin/coach/students/${learnerBid}/progress`}
            className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-4" /> 返回进度详表
          </Link>
          <Link
            href={`/admin/coach/students/${learnerBid}`}
            className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            学员详情 <ArrowLeft className="size-4 rotate-180" />
          </Link>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight">
          {report.learnerName || learnerBid} 的带教分析报告
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          生成于{' '}
          {report.generatedAt
            ? new Date(report.generatedAt).toLocaleString('zh-CN')
            : '—'}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <OverviewCard
          icon={BadgeCheck}
          label="阶段完成"
          value={`${report.completedPhases}/${report.totalPhases}`}
          sub={
            report.inProgressPhases > 0
              ? `${report.inProgressPhases} 个进行中`
              : undefined
          }
        />
        <OverviewCard
          icon={ClipboardCheck}
          label="验收通过率"
          value={`${report.checklistPassRate}%`}
          sub={`${report.checklistPassed}/${report.checklistTotal} 项已通过`}
        />
        <OverviewCard
          icon={MessageSquare}
          label="面谈次数"
          value={report.sessionCount}
        />
        <OverviewCard
          icon={TrendingUp}
          label="最新阶段总分"
          value={startedScore?.totalScore ?? '—'}
        />
      </div>

      {report.phases.length === 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground">
          <FileText className="mt-0.5 size-4 shrink-0 text-primary" />
          <div>
            <b className="text-foreground">阶段明细数据待接通</b>
            <p className="mt-1">
              后端暂无「每学员阶段明细」端点（v1 缺口，见
              docs/COACHLAB-MIGRATION-DESIGN.md §3.1）。阶段完成 / 验收通过率 /
              成绩趋势图表将在 GET /api/shifu/coach/phase-detail 就绪后自动激活；
              面谈次数、面谈时间线与 AI 建议基于实时数据。
            </p>
          </div>
        </div>
      )}

      <ExpandableSummary report={report} />
      <CustomReportCharts report={report} />
      <DepartmentFeedback report={report} />
      <AiAdviceCard ai={ai} loading={aiLoading} error={aiError} />

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground">
            阶段明细与导师评语
          </h2>
          {report.phases.length === 0 ? (
            <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
              暂无阶段明细（阶段明细端点未接通时为空）。
            </p>
          ) : (
            report.phases.map(p => (
              <div key={p.phaseBid || p.name} className="rounded-xl border border-border bg-card p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{p.name}</span>
                  <span
                    className={cn(
                      'rounded-full px-2 py-0.5 text-xs',
                      statusStyle[p.status] ?? statusStyle.not_started,
                    )}
                  >
                    {statusLabel[p.status] ?? p.status}
                  </span>
                  {p.status !== 'not_started' && (
                    <span className="ml-auto text-sm font-semibold tabular-nums">
                      {p.totalScore}
                      <span className="ml-1 text-xs font-normal text-muted-foreground">
                        / 及格 {p.passingScore}
                      </span>
                    </span>
                  )}
                </div>
                {p.startedAt && (
                  <p className="mt-1.5 text-xs text-muted-foreground">
                    {p.startedAt.slice(0, 10)} 开始
                    {p.completedAt && ` · ${p.completedAt.slice(0, 10)} 完成`}
                  </p>
                )}
                {p.coachSummary && (
                  <p className="mt-2 border-t border-border pt-2 text-sm text-muted-foreground">
                    {p.coachSummary}
                  </p>
                )}
              </div>
            ))
          )}

          {summarizedPhases.length > 0 && (
            <div className="flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 p-4 text-sm">
              <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" />
              <div>
                <b>AI 改进建议</b>
                <p className="mt-1 text-muted-foreground">
                  已根据各阶段评语与成绩趋势在上方生成个性化改进建议（真实后端 LLM 或规则降级）。
                </p>
              </div>
            </div>
          )}
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground">面谈时间线</h2>
          {sessions.length === 0 && (
            <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
              暂无面谈记录
            </p>
          )}
          <ol className="space-y-3">
            {[...sessions].reverse().map(s => (
              <li
                key={s.sessionBid}
                className="rounded-xl border border-border bg-card p-4 text-sm"
              >
                <div className="flex items-center gap-2 font-medium">
                  <MessageSquare className="size-4 text-primary" />
                  {s.topic || '未命名面谈'}
                </div>
                <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <CalendarDays className="size-3.5" />
                    {s.sessionDate ? s.sessionDate.slice(0, 10) : '—'}
                  </span>
                  {s.duration && <span>{s.duration} 分钟</span>}
                  <span className="rounded bg-secondary px-1.5 py-0.5">{s.sessionType}</span>
                  {s.status === 'summarized' && (
                    <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-emerald-600 dark:text-emerald-400">
                      已总结
                    </span>
                  )}
                </div>
                {s.coachNotes && <p className="mt-2 text-muted-foreground">{s.coachNotes}</p>}
                {s.actionItems && (
                  <p className="mt-1.5 text-xs text-foreground">
                    <b>行动项：</b>
                    {s.actionItems}
                  </p>
                )}
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
}
