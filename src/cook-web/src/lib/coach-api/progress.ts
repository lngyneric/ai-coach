/**
 * progress.ts —— 学员带教进度详表聚合器（/admin/coach/students/[learner_bid]/progress）。
 *
 * 数据源全部来自现有接口（coachApi 适配器）：
 *  - GET /api/portal/mentor/students       → 学员信息
 *  - GET /api/coach/sessions               → 面谈记录
 *  - GET /api/coach/checklist/<record_bid> → 三态合规（需 phase record_bid）
 *  - GET /api/shifu/coach/phase-detail     → 每学员阶段明细（v1 dev 未注册 → 空态）
 *  - course_enrollments 课程分配 → coach 无 manage_users，明细接口不可达 → 占位
 *
 * 任务完成百分比：优先用现有状态字段聚合计算（不新增列 / 不迁移）——
 *  - 阶段完成度   = completed phases / total phases（learner_coaching.status）
 *  - 面谈闭环率   = summarized sessions / total sessions（coach_sessions.status）
 *  - 验收完成度   = scored items / total checklist（learner_checklist_items.status）
 *  - 课程完成度   = completed enrollments / total enrollments（course_enrollments，待接通）
 * 无数据时显示 0% / 占位（placeholder=true），不虚构数据。
 *
 * 三大重点模块（入职 / 三个明白 / 小灶培训）为占位卡片，规则后续加入。
 */

import { coachApi } from './index';
import type {
  ChecklistItem,
  CoachSession,
  CoachStudent,
  PhaseDetail,
} from './types';

// ── 任务完成百分比 ────────────────────────────────────────────────
export interface TaskCompletion {
  key: string;
  label: string;
  /** 已完成数 */
  done: number;
  /** 总数 */
  total: number;
  /** 0-100（四舍五入） */
  pct: number;
  /** 数据来源字段说明 */
  source: string;
  /** total === 0 或数据源未接通 → 占位（页面显示 0% + 提示） */
  placeholder: boolean;
  /** 占位提示文案 */
  placeholderNote?: string;
}

export function pct(done: number, total: number): number {
  if (!total || total <= 0) return 0;
  return Math.round((done / total) * 100);
}

/** 从现有状态字段聚合各任务完成百分比（纯函数，可单测）。 */
export function computeTaskCompletions(input: {
  phases: PhaseDetail[];
  sessions: CoachSession[];
  checklist: ChecklistItem[];
}): TaskCompletion[] {
  const phases = input.phases || [];
  const sessions = input.sessions || [];
  const checklist = input.checklist || [];

  const completedPhases = phases.filter(p => p.status === 'completed').length;
  const summarizedSessions = sessions.filter(s => s.status === 'summarized').length;
  const scoredItems = checklist.filter(c => c.status === 'scored').length;

  return [
    {
      key: 'phase',
      label: '阶段完成度',
      done: completedPhases,
      total: phases.length,
      pct: pct(completedPhases, phases.length),
      source: 'learner_coaching.status=completed',
      placeholder: phases.length === 0,
      placeholderNote:
        phases.length === 0 ? '每学员阶段明细端点未接通（v1 缺口），阶段完成度暂为 0%' : undefined,
    },
    {
      key: 'session',
      label: '面谈闭环率',
      done: summarizedSessions,
      total: sessions.length,
      pct: pct(summarizedSessions, sessions.length),
      source: 'coach_sessions.status=summarized',
      placeholder: sessions.length === 0,
      placeholderNote:
        sessions.length === 0 ? '暂无面谈记录，面谈闭环率暂为 0%' : undefined,
    },
    {
      key: 'checklist',
      label: '验收完成度',
      done: scoredItems,
      total: checklist.length,
      pct: pct(scoredItems, checklist.length),
      source: 'learner_checklist_items.status=scored',
      // coachApi.listChecklistItems 当前仅派生 submitted 项（pending-scores 源），
      // scored 全量需 checklist 全量端点（v1 缺口）→ 有提交但无 scored 时也标占位。
      placeholder: checklist.length === 0 || scoredItems === 0,
      placeholderNote:
        checklist.length === 0
          ? '暂无验收项提交，验收完成度暂为 0%'
          : scoredItems === 0
            ? `已提交 ${checklist.length} 项，但当前接口仅暴露 submitted 状态，` +
              'scored 全量需 checklist 全量端点（v1 缺口），验收完成度暂为 0%'
            : undefined,
    },
    {
      key: 'course',
      label: '课程完成度',
      done: 0,
      total: 0,
      pct: 0,
      source: 'course_enrollments.status=completed',
      placeholder: true,
      placeholderNote: '课程分配完成度接口待接通（需 manage_users 数据域）',
    },
  ];
}

// ── 三大重点模块占位 ──────────────────────────────────────────────
export interface FocusModulePlaceholder {
  key: string;
  name: string;
  subtitle: string;
  /** 占位状态：规则后续加入 */
  placeholder: true;
  placeholderNote: string;
  /** 完成度占位（0%） */
  pct: 0;
}

/**
 * 三大重点模块占位（结构先建，规则后续加入）：
 *  - 入职（onboarding）
 *  - 三个明白（带教体系：血球/尿液/凝血产品三个明白考试）
 *  - 小灶培训（intensive 小灶教学）
 * 完成度统一占位 0%，不虚构数据；接入规则后替换为真实计算。
 */
export const FOCUS_MODULES: FocusModulePlaceholder[] = [
  {
    key: 'onboarding',
    name: '入职',
    subtitle: '新员工入职（onboarding）',
    placeholder: true,
    placeholderNote: '入职流程与验收规则待加入',
    pct: 0,
  },
  {
    key: 'three-clarity',
    name: '三个明白',
    subtitle: '带教体系：血球 / 尿液 / 凝血产品三个明白考试',
    placeholder: true,
    placeholderNote: '三个明白考试与带教规则待加入',
    pct: 0,
  },
  {
    key: 'intensive',
    name: '小灶培训',
    subtitle: '小灶教学（intensive 小灶培训）',
    placeholder: true,
    placeholderNote: '小灶培训规则待加入',
    pct: 0,
  },
];

// ── 时间线（跨数据源统一排序）─────────────────────────────────────
export interface TimelineEvent {
  at: string;
  type:
    | 'phase_started'
    | 'phase_completed'
    | 'item_submitted'
    | 'session_created'
    | 'session_done'
    | 'session_summarized';
  ref: string;
  note: string;
}

/** 由阶段 + 面谈 + 验收项派生时间线（按时间倒序）。 */
export function buildTimeline(input: {
  phases: PhaseDetail[];
  sessions: CoachSession[];
  checklist: ChecklistItem[];
}): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  for (const p of input.phases || []) {
    if (p.startedAt) {
      events.push({
        at: p.startedAt,
        type: 'phase_started',
        ref: p.phaseBid,
        note: `阶段「${p.phaseName}」开始`,
      });
    }
    if (p.status === 'completed' && p.completedAt) {
      events.push({
        at: p.completedAt,
        type: 'phase_completed',
        ref: p.phaseBid,
        note: `阶段「${p.phaseName}」完成`,
      });
    }
  }
  for (const c of input.checklist || []) {
    if (c.submittedAt && c.status === 'submitted') {
      events.push({
        at: c.submittedAt,
        type: 'item_submitted',
        ref: c.recordBid,
        note: `验收项「${c.name}」提交`,
      });
    }
  }
  for (const s of input.sessions || []) {
    if (!s.sessionDate) continue;
    const base = { ref: s.sessionBid, note: `面谈「${s.topic || s.sessionType}」` };
    if (s.status === 'summarized') {
      events.push({ at: s.sessionDate, type: 'session_summarized', ...base });
    } else if (s.status === 'done') {
      events.push({ at: s.sessionDate, type: 'session_done', ...base });
    } else {
      events.push({ at: s.sessionDate, type: 'session_created', ...base });
    }
  }
  return events.sort(
    (a, b) =>
      (new Date(b.at).getTime() || 0) - (new Date(a.at).getTime() || 0),
  );
}

// ── 详表聚合（页面数据源）─────────────────────────────────────────
export interface ProgressTable {
  learner: CoachStudent | null;
  phases: PhaseDetail[];
  checklist: ChecklistItem[];
  sessions: CoachSession[];
  summary: {
    totalPhases: number;
    completedPhases: number;
    inProgressPhases: number;
    sessionCount: number;
    checklistTotal: number;
    checklistScored: number;
    /** 报告 context 的课程分配计数（coach 无 manage_users，只有计数） */
    enrollmentCount: number;
  };
  completion: TaskCompletion[];
  timeline: TimelineEvent[];
}

/**
 * 聚合某学员的带教进度详表（页面在 mount 时调用）。
 * 任一接口失败都不阻塞整表：coachApi 各方法已做空态/降级。
 */
export async function collectProgressTable(
  learnerBid: string,
): Promise<ProgressTable> {
  const [students, phases, checklist, sessions] = await Promise.all([
    coachApi.listStudents().catch(() => []),
    coachApi.listPhaseDetails(learnerBid).catch(() => []),
    coachApi.listChecklistItems(learnerBid).catch(() => []),
    coachApi.listSessions(learnerBid).catch(() => []),
  ]);

  const learner =
    (students as CoachStudent[]).find(s => s.learnerBid === learnerBid) ?? null;

  const completion = computeTaskCompletions({ phases, sessions, checklist });

  return {
    learner,
    phases,
    checklist,
    sessions,
    summary: {
      totalPhases: phases.length,
      completedPhases: phases.filter(p => p.status === 'completed').length,
      inProgressPhases: phases.filter(p => p.status === 'in_progress').length,
      sessionCount: sessions.length,
      checklistTotal: checklist.length,
      checklistScored: checklist.filter(c => c.status === 'scored').length,
      // coach 无 manage_users，课程分配明细接口不可达 → 占位 0（见 completion.course）
      enrollmentCount: 0,
    },
    completion,
    timeline: buildTimeline({ phases, sessions, checklist }),
  };
}

export default collectProgressTable;
