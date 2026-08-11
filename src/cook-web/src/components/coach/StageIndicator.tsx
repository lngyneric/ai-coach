'use client';

import { cn } from '@/lib/utils';
import type { PhaseDetail } from '@/lib/coach-api/types';

/**
 * 学员生命周期阶段标识。
 * 与 docs/user-lifecycle-stages.md 的阶段定义完全对齐。
 */

export type LifecycleStage = 'pending' | 'onboarding' | 'mentorship' | 'review' | 'completed' | 'archived';

const STAGE_CONFIG: Record<LifecycleStage, { label: string; color: string; bgClass: string; textClass: string; step: number }> = {
  pending:    { label: '待入职',   color: '#3e84f4', bgClass: 'bg-blue-500/15',  textClass: 'text-blue-600 dark:text-blue-400',    step: 1 },
  onboarding: { label: '入职中',   color: '#10b981', bgClass: 'bg-emerald-500/15', textClass: 'text-emerald-600 dark:text-emerald-400', step: 2 },
  mentorship: { label: '带教中',   color: '#f59e0b', bgClass: 'bg-amber-500/15',  textClass: 'text-amber-600 dark:text-amber-400',   step: 3 },
  review:     { label: '评估中',   color: '#8b5cf6', bgClass: 'bg-purple-500/15', textClass: 'text-purple-600 dark:text-purple-400',  step: 4 },
  completed:  { label: '已完成',   color: '#10b981', bgClass: 'bg-emerald-500/15', textClass: 'text-emerald-600 dark:text-emerald-400', step: 5 },
  archived:   { label: '已归档',   color: '#94a3b8', bgClass: 'bg-slate-400/15',  textClass: 'text-slate-500 dark:text-slate-400',    step: 6 },
};

/** 根据阶段数据推断学员生命周期阶段 */
export function deriveStage(phases: PhaseDetail[]): LifecycleStage {
  const allCompleted = phases.every((p) => p.status === 'completed');
  const hasActive = phases.some((p) => p.status === 'in_progress');
  const allPending = phases.every((p) => p.status === 'pending' || p.status === 'not_started');
  const hasOnboarding = phases.some((p) => p.phaseBid === 'ph-000' && p.status === 'completed');
  const hasMentorship = phases.some((p) => p.phaseBid !== 'ph-000' && p.status !== 'pending');

  if (allPending) return 'pending';
  if (!hasOnboarding && phases.some((p) => p.phaseBid === 'ph-000' && p.status === 'in_progress')) return 'onboarding';
  if (hasOnboarding && hasMentorship && !allCompleted) return 'mentorship';
  if (allCompleted) return 'review';
  return 'pending';
}

/** 阶段标识徽章 */
export function StageBadge({ stage }: { stage: LifecycleStage }) {
  const cfg = STAGE_CONFIG[stage];
  return (
    <span className={cn('inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold', cfg.bgClass, cfg.textClass)}>
      <span className="size-2 rounded-full" style={{ backgroundColor: cfg.color }} />
      {cfg.label}
    </span>
  );
}

/** 阶段进度条：6 步视觉管线 */
export function StageProgress({ stage }: { stage: LifecycleStage }) {
  const current = STAGE_CONFIG[stage].step;
  return (
    <div className="flex items-center gap-1">
      {(['pending', 'onboarding', 'mentorship', 'review', 'completed'] as LifecycleStage[]).map((s, i) => {
        const cfg = STAGE_CONFIG[s];
        const active = i + 1 <= current;
        return (
          <div key={s} className="flex items-center">
            {i > 0 && <span className={cn('mx-0.5 h-0.5 w-3 rounded', active ? 'bg-primary' : 'bg-border')} />}
            <span
              className={cn(
                'flex size-4 items-center justify-center rounded-full text-[9px] font-bold',
                active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
              )}
              title={cfg.label}
            >
              {i + 1}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** 阶段操作建议：管理员和导师需要在当前阶段做什么 */
export interface StageActions {
  admin: string[];
  coach: string[];
  learner: string[];
}

export const STAGE_ACTIONS: Record<LifecycleStage, StageActions> = {
  pending: {
    admin: ['录入员工信息', '分配导师和上司', '建 learner_profiles', '分配 onboarding 课程'],
    coach: ['确认接收带教任务', '准备一周带教计划', '与 HR 确认学员背景'],
    learner: [],
  },
  onboarding: {
    admin: ['完成 HR 讲解 7 项', '勾选确认清单 cl-000a*', '协调 IT 账号/设备'],
    coach: ['完成 Brief 8 项', '勾选确认清单 cl-000b*', '制定个性化带教节奏'],
    learner: ['签署劳动合同/手册', '学习薪酬考勤制度', 'MBO 面谈'],
  },
  mentorship: {
    admin: ['监控阶段进度', '超 48h 待评分催办', '截止前 7/3/1 天提醒'],
    coach: ['逐项带教+评分(0-5)', '每阶段 ≥1 次 1v1 面谈', '填写阶段小结', '未达标需制定改进计划'],
    learner: ['完成考试/任务确认/现场带教', '提交验收项', '参与面谈'],
  },
  review: {
    admin: ['生成分析报告', '安排转正评估会议', '确认培训档案完整'],
    coach: ['撰写总评', '给出转正建议', '参与评估会议'],
    learner: ['提交转正申请', '准备答辩材料'],
  },
  completed: {
    admin: ['更新 HR 转正状态', '归档培训档案'],
    coach: ['交接独立上岗', '解除带教关系（可选）'],
    learner: ['进入独立上岗'],
  },
  archived: { admin: ['只读保留'], coach: [], learner: [] },
};

/** 阶段操作建议面板 */
export function StageActionPanel({ stage }: { stage: LifecycleStage }) {
  const actions = STAGE_ACTIONS[stage];
  const cfg = STAGE_CONFIG[stage];
  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="size-2.5 rounded-full" style={{ backgroundColor: cfg.color }} />
          <span className="text-sm font-semibold">{cfg.label} · 操作建议</span>
        </div>
      </div>
      <div className="space-y-3 px-4 py-3 text-sm">
        {actions.admin.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">👤 管理员</div>
            <ul className="space-y-1">
              {actions.admin.map((a) => (
                <li key={a} className="flex items-start gap-1.5 text-xs">
                  <span className="mt-1 size-1 shrink-0 rounded-full bg-primary" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}
        {actions.coach.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">👨‍🏫 导师</div>
            <ul className="space-y-1">
              {actions.coach.map((a) => (
                <li key={a} className="flex items-start gap-1.5 text-xs">
                  <span className="mt-1 size-1 shrink-0 rounded-full bg-emerald-500" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}
        {actions.learner.length > 0 && (
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">🎓 学员</div>
            <ul className="space-y-1">
              {actions.learner.map((a) => (
                <li key={a} className="flex items-start gap-1.5 text-xs">
                  <span className="mt-1 size-1 shrink-0 rounded-full bg-amber-500" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
