'use client';

import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  MessageSquare,
  PenLine,
  Send,
  Sparkles,
} from 'lucide-react';
import type { CoachReport } from '@/lib/coach-api/types';
import { cn } from '@/lib/utils';
import {
  DimensionChart,
  ReportCharts,
  ScoreTrendChart,
} from './ReportCharts';

/**
 * 报告增强组件（coach-lab ReportEnhancements.tsx 移植适配）。
 *
 * 与 coach-lab 版本的差异：
 *  - CustomReportCharts 修正原版缺陷：trend/dimension/both 三态分别渲染
 *    趋势线 / 维度构成 / 双图（原版 trend 误渲染整块 ReportCharts 双图，
 *    dimension 单态未实现）。
 *  - DepartmentFeedback 移除 coach-lab 的 MOCK 数据（王芳/销售经理等虚构
 *    内容），改为空列表 + 「后端意见接口 v1 缺口」占位；提交仅本地展示，
 *    不虚构、不上传。
 *  - 数据字段兜底（phases 空 / checklist 空）时显示占位说明而非空白。
 */

/** ── 展开式总结卡 ── */
export function ExpandableSummary({ report }: { report: CoachReport }) {
  const [open, setOpen] = useState(false);
  const total = report.totalPhases;
  const done = report.completedPhases;
  const active = report.inProgressPhases;
  const summarizedPhases = report.phases.filter(
    p => p.status !== 'not_started' && p.coachSummary,
  );

  return (
    <div className="rounded-xl border border-border bg-card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        aria-expanded={open}
      >
        <div className="flex items-center gap-3">
          <Sparkles className="size-4 text-primary" />
          <div>
            <span className="text-sm font-semibold">培训总结</span>
            <span className="ml-2 text-xs text-muted-foreground">
              {done}/{total} 阶段完成 · 验收通过率 {report.checklistPassRate}% ·{' '}
              {report.sessionCount} 场面谈
            </span>
          </div>
        </div>
        {open ? (
          <ChevronDown className="size-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="size-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="space-y-3 border-t border-border px-4 py-3">
          <p className="text-sm text-muted-foreground">
            {report.learnerName || report.learnerBid} 于{' '}
            {report.phases[0]?.startedAt?.slice(0, 10) ?? '—'} 开始入职培训，
            至今完成 {done} 个阶段（{report.checklistPassed}/{report.checklistTotal}{' '}
            项验收通过），累计参加 {report.sessionCount} 次 1v1 面谈。
            {active > 0 && ` 另有 ${active} 个阶段进行中。`}
          </p>
          {summarizedPhases.length === 0 ? (
            <p className="rounded-lg border border-dashed border-border bg-muted/30 p-3 text-xs text-muted-foreground">
              暂无带评语的阶段小结（阶段明细端点未接通时为空，接入后在此展开各阶段导师评语）。
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-2 text-sm">
              {summarizedPhases.map(p => (
                <div
                  key={p.phaseBid}
                  className="rounded-lg border border-border bg-muted/30 p-2.5"
                >
                  <span className="text-xs font-medium">{p.name}</span>
                  <p className="mt-1 text-xs text-muted-foreground">{p.coachSummary}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** ── 定制化图表面板 ── */
type ChartMode = 'trend' | 'dimension' | 'both';

export function CustomReportCharts({ report }: { report: CoachReport }) {
  const [mode, setMode] = useState<ChartMode>('both');
  const startedCount = report.phases.filter(
    p => p.status !== 'not_started' && p.passingScore > 0,
  ).length;

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs text-muted-foreground">图表定制：</span>
        {(['trend', 'dimension', 'both'] as ChartMode[]).map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={cn(
              'rounded-md px-2.5 py-1 text-xs transition-colors',
              mode === m
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-muted-foreground hover:bg-accent',
            )}
          >
            {m === 'trend' ? '趋势线' : m === 'dimension' ? '维度构成' : '全部'}
          </button>
        ))}
      </div>

      {startedCount === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-muted/30 p-6 text-sm text-muted-foreground">
          暂无已开始的阶段成绩数据（阶段明细端点未接通时为空）。趋势 / 维度图表将在
          GET /api/shifu/coach/phase-detail 就绪后自动显示。
        </div>
      ) : mode === 'trend' ? (
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="mb-1 text-sm font-medium">阶段成绩趋势</h3>
          <p className="mb-2 text-xs text-muted-foreground">各阶段总分变化（虚线为及格线）</p>
          <ScoreTrendChart report={report} />
        </div>
      ) : mode === 'dimension' ? (
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="mb-1 text-sm font-medium">能力维度构成</h3>
          <p className="mb-2 text-xs text-muted-foreground">理论 / 实操 / 导师评价对比</p>
          <DimensionChart report={report} />
        </div>
      ) : (
        <ReportCharts report={report} />
      )}
    </div>
  );
}

/** ── 部门意见征询组件（本地占位：后端意见接口 v1 缺口）── */
interface Feedback {
  author: string;
  role: string;
  date: string;
  content: string;
}

export function DepartmentFeedback({ report }: { report: CoachReport }) {
  // 不保留 coach-lab 的 MOCK 数据（虚构内容）；后端部门意见接口（v1 缺口）
  // 就绪前为空列表，提交仅本地展示。
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [newFeedback, setNewFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const submit = () => {
    if (!newFeedback.trim()) return;
    setFeedbacks(prev => [
      {
        author: '当前用户',
        role: '部门负责人',
        date: new Date().toISOString().slice(0, 10),
        content: newFeedback,
      },
      ...prev,
    ]);
    setNewFeedback('');
    setSubmitted(true);
  };

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <span className="flex items-center gap-1.5 text-sm font-medium">
          <MessageSquare className="size-4 text-primary" />
          部门意见征询
          <span className="ml-auto text-xs text-muted-foreground">
            {feedbacks.length} 条反馈
          </span>
        </span>
      </div>

      <div className="space-y-3 px-4 py-3">
        {feedbacks.length === 0 && (
          <p className="rounded-lg border border-dashed border-border bg-muted/30 p-3 text-xs text-muted-foreground">
            暂无部门意见。后端部门意见接口（v1 缺口）接通后，此处展示{' '}
            {report.learnerName || '该学员'} 各部门负责人的意见与转正建议；当前提交仅本地展示，不会上传。
          </p>
        )}
        {feedbacks.map((fb, i) => (
          <div key={i} className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium">{fb.author}</span>
              <span className="text-xs text-muted-foreground">
                {fb.role} · {fb.date}
              </span>
            </div>
            <p className="mt-1.5 text-muted-foreground">{fb.content}</p>
          </div>
        ))}

        <div className="border-t border-border pt-3">
          <div className="flex items-start gap-2">
            <PenLine className="mt-1.5 size-4 shrink-0 text-muted-foreground" />
            <textarea
              value={newFeedback}
              onChange={e => setNewFeedback(e.target.value)}
              rows={2}
              placeholder="作为部门负责人，对本报告的意见或转正建议…"
              className="flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-sm placeholder:text-muted-foreground focus:border-ring focus:outline-none"
            />
          </div>
          <div className="mt-2 flex justify-end">
            <button
              onClick={submit}
              disabled={!newFeedback.trim()}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
            >
              <Send className="size-3" />
              提交意见
            </button>
          </div>
          {submitted && (
            <p className="mt-1.5 text-xs text-emerald-600 dark:text-emerald-400">
              ✓ 意见已记录（本地展示，后端接口就绪后将随报告发送至 HR）
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export { ReportCharts };
