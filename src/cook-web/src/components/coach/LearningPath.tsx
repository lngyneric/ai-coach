'use client';

import { useMemo } from 'react';
import { CalendarDays, CheckCircle2, Clock, Route, Sparkles } from 'lucide-react';
import type { PhaseDetail } from '@/lib/coach-api/types';
import { cn } from '@/lib/utils';

interface Milestone {
  phaseName: string;
  phaseBid: string;
  status: string;
  durationDays: number;
  startedAt: string;
  estimatedEnd: string;
  gaps: string[];
  isCurrent: boolean;
}

function parseDate(d: string): Date | null {
  if (!d) return null;
  const dt = new Date(d);
  return isNaN(dt.getTime()) ? null : dt;
}

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

export function LearningPath({
  phases,
  onboardingDate,
}: {
  phases: PhaseDetail[];
  onboardingDate?: string | null;
}) {
  const milestones = useMemo<Milestone[]>(() => {
    const start = parseDate(onboardingDate ?? phases[0]?.startedAt) ?? new Date();
    let cursor = new Date(start);

    return phases.map((p, i) => {
      const phaseStart = parseDate(p.startedAt) || new Date(cursor);
      cursor = new Date(phaseStart);
      cursor.setDate(cursor.getDate() + p.durationDays);

      const gaps: string[] = [];
      if (p.status !== 'pending' && p.totalScore > 0 && p.totalScore < p.passingScore) {
        if (p.theoryScore < p.passingScore * 0.4) gaps.push('理论');
        if (p.practiceScore < p.passingScore * 0.3) gaps.push('实操');
        if (p.reviewScore < p.passingScore * 0.2) gaps.push('任务确认');
      }

      return {
        phaseName: p.phaseName,
        phaseBid: p.phaseBid,
        status: p.status,
        durationDays: p.durationDays,
        startedAt: p.startedAt || formatDate(phaseStart),
        estimatedEnd: p.completedAt || formatDate(cursor),
        gaps,
        isCurrent: p.status === 'in_progress',
      };
    });
  }, [phases, onboardingDate]);

  const totalDays = milestones.reduce((a, m) => a + m.durationDays, 0);
  const completedDays = milestones
    .filter(m => m.status === 'completed')
    .reduce((a, m) => a + m.durationDays, 0);
  const pct = totalDays > 0 ? Math.round((completedDays / totalDays) * 100) : 0;

  const statusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle2 className="size-4 text-emerald-500" />;
    if (status === 'in_progress') return <Clock className="size-4 text-primary" />;
    return <div className="size-2 rounded-full bg-muted-foreground/30 ml-1" />;
  };

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <span className="flex items-center gap-1.5 text-sm font-medium">
          <Route className="size-4 text-primary" />
          <Sparkles className="size-3.5 text-amber-500" />
          AI 生成学习路径
          <span className="ml-auto text-xs text-muted-foreground">
            预计 {totalDays} 天 · 已用 {completedDays} 天 ({pct}%)
          </span>
        </span>
      </div>
      <div className="px-4 py-3">
        {/* Progress bar */}
        <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
        </div>

        {/* Milestones */}
        <ol className="relative space-y-0">
          {milestones.map((m, i) => (
            <li key={m.phaseBid} className="relative flex gap-3 pb-4 last:pb-0">
              {i < milestones.length - 1 && (
                <span className={cn(
                  'absolute left-[7px] top-5 h-full w-px',
                  m.status === 'completed' ? 'bg-emerald-500/30' : 'bg-border'
                )} />
              )}
              {statusIcon(m.status)}
              <div className="min-w-0 flex-1">
                <div className={cn('text-sm', m.isCurrent && 'font-semibold')}>
                  {m.phaseName}
                  {m.isCurrent && (
                    <span className="ml-1.5 rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">当前</span>
                  )}
                </div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                  <CalendarDays className="size-3" />
                  {m.startedAt.slice(0, 10)} → {m.estimatedEnd.slice(0, 10)}
                  <span>· {m.durationDays} 天</span>
                </div>
                {m.gaps.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {m.gaps.map(g => (
                      <span key={g} className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-600 dark:text-amber-400">
                        ⚠ {g}薄弱
                      </span>
                    ))}
                    <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                      AI 推荐补充课件
                    </span>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
