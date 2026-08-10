'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { ArrowLeft, FileText, Loader2, Route } from 'lucide-react';
import { coachApi } from '@/lib/coach-api';
import type {
  ChecklistItem,
  CoachSession,
  CoachStudent,
  PhaseDetail,
} from '@/lib/coach-api/types';
import { SessionPanel } from '@/components/coach/SessionPanel';
import { ScorePanel } from '@/components/coach/ScorePanel';
import {
  StageActionPanel,
  StageBadge,
  StageProgress,
  type LifecycleStage,
} from '@/components/coach/StageIndicator';
import { LearningPath } from '@/components/coach/LearningPath';
import { PhaseSummaryForm } from '@/components/coach/PhaseSummaryForm';

/**
 * 学员详情页（/admin/coach/students/[learner_bid]）。
 *
 * coach-lab app/coach/students/[learnerId]/page.tsx 迁移：
 *  - React 18 适配：`useParams()` 取代 React 19 `use(params)`；
 *  - 阶段明细（PhaseDetail[]）在 dev 后端无 live 端点 → v1 空态降级，
 *    阶段闭环/学习路径等组件数据源就绪后自动激活；
 *  - 1v1 三环闭环（SessionPanel）与待评分（ScorePanel）基于 live 数据工作。
 */

function stageFromStatus(status: string | null | undefined): LifecycleStage {
  if (status === 'in_progress') return 'mentorship';
  if (status === 'completed') return 'review';
  if (status === 'failed') return 'mentorship';
  return 'pending';
}

export default function CoachStudentDetailPage() {
  const params = useParams<{ learner_bid?: string }>();
  const searchParams = useSearchParams();
  const learnerBid = params?.learner_bid ?? '';
  const scoreParam = searchParams.get('score');

  const [student, setStudent] = useState<CoachStudent | null>(null);
  const [phases, setPhases] = useState<PhaseDetail[]>([]);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [sessions, setSessions] = useState<CoachSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scoringItem, setScoringItem] = useState<ChecklistItem | null>(null);
  const [summaryPhase, setSummaryPhase] = useState<PhaseDetail | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = () => setReloadKey(k => k + 1);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      coachApi.listStudents(),
      coachApi.listPhaseDetails(learnerBid),
      coachApi.listChecklistItems(learnerBid),
      coachApi.listSessions(learnerBid),
    ])
      .then(([students, phaseList, items, sessionList]) => {
        setStudent(
          students.find(s => s.learnerBid === learnerBid) ?? null
        );
        setPhases(phaseList);
        setChecklist(items);
        setSessions(sessionList);
        if (scoreParam) {
          const target = items.find(
            i => i.recordBid === scoreParam && i.status === 'submitted'
          );
          if (target) setScoringItem(target);
        }
      })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [learnerBid, scoreParam, reloadKey]);

  if (error)
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
        加载失败：{error}
      </div>
    );

  if (loading)
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        <Loader2 className="mr-2 size-5 animate-spin" /> 加载中…
      </div>
    );

  const stage = stageFromStatus(student?.currentPhaseStatus);
  const submittedItems = checklist.filter(i => i.status === 'submitted');

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/admin/coach"
          className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" /> 返回工作台
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {student?.name ?? learnerBid}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {student &&
                `${student.employeeNo} · ${student.department} · ${student.positionName}`}
            </p>
          </div>
          <Link
            href={`/admin/dept/report/${learnerBid}`}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-lighter"
          >
            <FileText className="size-4" /> 查看分析报告
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card p-4">
        <StageBadge stage={stage} />
        <StageProgress stage={stage} />
        <span className="ml-auto text-xs text-muted-foreground">
          {phases.filter(p => p.status === 'completed').length}/{phases.length}{' '}
          阶段完成
        </span>
      </div>

      {phases.length > 0 ? (
        <>
          <LearningPath phases={phases} onboardingDate={student?.onboardingDate} />
          <StageActionPanel stage={stage} />
        </>
      ) : (
        <div className="flex items-start gap-3 rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
          <Route className="mt-0.5 size-4 shrink-0 text-primary" />
          <div>
            <b className="text-foreground">带教阶段数据待接通</b>
            <p className="mt-1">
              后端暂无「每学员阶段明细」端点（v1 缺口，见
              docs/COACHLAB-MIGRATION-DESIGN.md §3.1）。阶段闭环、学习路径与
              阶段小结将在端点就绪后自动显示；1v1 面谈与待评分不受影响。
            </p>
          </div>
        </div>
      )}

      <SessionPanel
        learnerId={learnerBid}
        phases={phases}
        sessions={sessions}
        onChanged={reload}
      />

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground">
          待评分（{submittedItems.length}）
        </h2>
        {submittedItems.length === 0 ? (
          <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
            暂无待评分验收项
          </p>
        ) : (
          <div className="space-y-2">
            {submittedItems.map(item => (
              <div
                key={item.recordBid}
                className="flex items-center gap-3 rounded-xl border border-border bg-card p-4 text-sm"
              >
                <span className="min-w-0 flex-1 truncate font-mono text-xs">
                  {item.name}
                </span>
                {item.comment && (
                  <span className="max-w-48 truncate text-xs text-muted-foreground">
                    {item.comment}
                  </span>
                )}
                {item.submittedAt && (
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {new Date(item.submittedAt).toLocaleString('zh-CN')}
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => setScoringItem(item)}
                  className="shrink-0 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary-lighter"
                >
                  评分
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {scoringItem && (
        <ScorePanel
          item={scoringItem}
          onClose={() => setScoringItem(null)}
          onScored={() => {
            setScoringItem(null);
            reload();
          }}
        />
      )}
      {summaryPhase && (
        <PhaseSummaryForm
          phase={summaryPhase}
          onClose={() => setSummaryPhase(null)}
          onSaved={() => {
            setSummaryPhase(null);
            reload();
          }}
        />
      )}
    </div>
  );
}
