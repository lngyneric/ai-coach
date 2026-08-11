/**
 * coachApi —— coach-lab 域类型 → cook-web 真实后端 的适配器。
 *
 * 消费 cook-web `@/api`（src/api/api.ts + src/lib/request.ts 自动解包
 * make_common_response 的 data，业务 code!==0 时抛错）。
 *
 * 后端契约来源（ai-shifu-dev）：
 *  - GET  /api/portal/mentor/students        → CoachStudent[]
 *  - GET  /api/portal/mentor/pending-scores  → PendingScore[]
 *  - POST /api/portal/mentorship/items/<record_bid>/score
 *  - GET  /api/coach/sessions  / POST /api/coach/sessions
 *  - PUT  /api/coach/sessions/<session_bid>  （编辑字段白名单，含 status/
 *    mentor_notes/action_items/duration_minutes/coach_rating；有笔记时自动
 *    LLM 生成 ai_summary）
 *  - POST /api/coach/sessions/<session_bid>/summarize（显式重新生成）
 *  - GET  /api/coach/report/<learner_bid>?source=rule
 *    （report-align 升级后响应含 phases/total_phases/completed_phases/
 *    checklist_pass_rate/session_count/learner_name/generated_at，getReport
 *    直接映射，不再依赖 404 的 /api/shifu/coach/phase-detail 端点）
 *  - GET  /api/shifu/coach/phase-detail/<learner_bid>（v1 dev 未注册 → 空态降级）
 *  - POST /api/shifu/coach/phase-summary（v1 dev 未注册 → 错误上抛）
 *
 * 命名冲突说明：cook-web 已有 `src/lib/api.ts`（请求工厂），故本模块命名
 * `@/lib/coach-api`，迁移组件 import 均指向此处。
 */

import requestApi from '@/api';
import type {
  ChecklistItem,
  CoachApi,
  CoachReport,
  CoachSession,
  CoachStudent,
  PendingScore,
  PhaseDetail,
} from './types';

/* eslint-disable @typescript-eslint/no-explicit-any -- 原始 API 载荷在边界映射 */
const num = (v: any): number => (v == null ? 0 : Number(v));

const mapStudent = (s: any): CoachStudent => ({
  learnerBid: s.learner_bid,
  userBid: s.user_bid ?? '',
  name: s.name ?? s.employee_no ?? s.learner_bid,
  employeeNo: s.employee_no ?? '',
  department: s.department ?? '',
  positionName: s.position_name ?? '',
  onboardingDate: s.onboarding_date ?? null,
  status: s.status ?? '',
  currentPhaseStatus: s.current_phase_status ?? null,
  currentPhaseBid: s.current_phase_bid ?? null,
  pendingTaskCount: num(s.pending_task_count),
  pendingScoreCount: num(s.pending_score_count),
});

const mapPending = (p: any): PendingScore => ({
  recordBid: p.record_bid,
  learnerBid: p.learner_bid,
  itemBid: p.item_bid,
  comment: p.comment ?? '',
  submittedAt: p.submitted_at ?? null,
});

const mapPhase = (p: any): PhaseDetail => ({
  recordBid: p.record_bid ?? p.phase_bid,
  phaseBid: p.phase_bid,
  phaseName: p.phase_name ?? p.name ?? '',
  status: p.status ?? '',
  theoryScore: num(p.theory_score),
  practiceScore: num(p.practice_score),
  reviewScore: num(p.peer_review_score ?? p.review_score),
  mentorScore: num(p.coach_score ?? p.mentor_score),
  totalScore: num(p.total_score),
  durationDays: num(p.duration_days ?? 60),
  passingScore: num(p.passing_score ?? 60),
  checklistProgress: p.checklist_progress ?? '0/0',
  checklistPct: num(p.checklist_pct),
  startedAt: p.started_at ?? '',
  completedAt: p.completed_at ?? '',
  coachSummary: p.coach_summary ?? '',
  learnerFeedback: p.learner_feedback ?? '',
  improvementPlan: p.improvement_plan ?? '',
});

const mapSession = (s: any): CoachSession => ({
  sessionBid: s.session_bid,
  learnerBid: s.learner_bid ?? '',
  phaseBid: s.phase_bid ?? null,
  sessionType: s.session_type ?? 'regular',
  sessionDate: s.session_date ?? '',
  duration: s.duration_minutes ?? s.duration ?? null,
  topic: s.topic ?? '',
  preCourseBids: s.pre_course_bids
    ? String(s.pre_course_bids).split(',').filter(Boolean)
    : [],
  goal: s.goal ?? '',
  coachNotes: s.mentor_notes ?? s.coach_notes ?? '',
  actionItems: s.action_items ?? '',
  aiSummary: s.ai_summary ?? '',
  nextAction: s.next_action ?? '',
  coachRating: s.coach_rating ?? null,
  status: s.status ?? 'done',
});

/** 每学员阶段明细：v1 dev 后端无 live 端点 → 尝试请求，失败返回空态。 */
async function listPhaseDetails(learnerBid: string): Promise<PhaseDetail[]> {
  try {
    const rows: any[] = await requestApi.getShifuCoachPhaseDetail({ learner_bid: learnerBid });
    if (!Array.isArray(rows)) return [];
    return rows.map(mapPhase);
  } catch {
    // dev 后端 /api/shifu/coach/phase-detail 未注册（404）→ 空态降级；
    // 后端补齐后此适配器自动生效（无需改动组件）。
    return [];
  }
}

/** 报告 phases[]（后端 report-align 契约）→ ReportPhase[]（camelCase）。 */
const mapReportPhase = (p: any) => ({
  phaseBid: p.phase_bid ?? '',
  name: p.name ?? '',
  status: p.status ?? '',
  totalScore: num(p.total_score),
  passingScore: num(p.passing_score ?? 60),
  theoryScore: num(p.theory_score),
  practiceScore: num(p.practice_score),
  reviewScore: num(p.review_score ?? p.peer_review_score),
  mentorScore: num(p.mentor_score ?? p.coach_score),
  coachSummary: p.coach_summary ?? '',
  startedAt: p.started_at ?? '',
  completedAt: p.completed_at ?? '',
});

export const coachApi: CoachApi = {
  async listStudents() {
    const rows: any[] = await requestApi.getPortalMentorStudents({});
    return (Array.isArray(rows) ? rows : []).map(mapStudent);
  },

  async listPendingScores() {
    const rows: any[] = await requestApi.getPortalMentorPendingScores({});
    return (Array.isArray(rows) ? rows : []).map(mapPending);
  },

  listPhaseDetails,

  async listChecklistItems(learnerBid) {
    // 无独立 checklist 端点（API 缺口）：由 pending-scores 派生 submitted 项，
    // 与 coach-lab httpAdapter 行为一致。item 名/分类需 coach_checklist 联表，
    // 当前以 itemBid 兜底展示。
    const pending = await this.listPendingScores();
    return pending
      .filter(p => p.learnerBid === learnerBid)
      .map(
        (p): ChecklistItem => ({
          recordBid: p.recordBid,
          itemBid: p.itemBid,
          phaseBid: '',
          name: p.itemBid,
          category: 'exam',
          maxScore: 5,
          isRequired: true,
          status: 'submitted',
          score: null,
          comment: p.comment,
          submittedAt: p.submittedAt,
          scoredAt: null,
        }),
      );
  },

  async listSessions(learnerBid) {
    const data = (await requestApi.getCoachSessions({
      page: 1,
      size: 100,
    })) as { items?: any[]; total?: number };
    return (data?.items ?? [])
      .filter(s => s.learner_bid === learnerBid)
      .map(mapSession);
  },

  async getReport(learnerBid) {
    // report-align：后端 GET /api/coach/report 已返回 phases + 全部统计字段，
    // 直接映射（snake_case → camelCase），不再依赖 404 的 phase-detail 端点。
    // 旧后端（无这些字段）时各字段回退默认/空，行为与现状降级一致。
    const reportData = await requestApi
      .getCoachReport({ learner_bid: learnerBid, source: 'rule' })
      .catch(() => null);
    const ctx = (reportData as any)?.context ?? {};
    const rawPhases = (reportData as any)?.phases ?? [];
    const phases = (Array.isArray(rawPhases) ? rawPhases : []).map(mapReportPhase);
    return {
      learnerName: (reportData as any)?.learner_name ?? '',
      learnerBid,
      totalPhases: num((reportData as any)?.total_phases) || phases.length,
      completedPhases: num((reportData as any)?.completed_phases),
      inProgressPhases: num((reportData as any)?.in_progress_phases),
      checklistTotal: num((reportData as any)?.checklist_total),
      checklistScored: num((reportData as any)?.checklist_scored),
      checklistPassed: num((reportData as any)?.checklist_passed),
      checklistPassRate: num((reportData as any)?.checklist_pass_rate),
      sessionCount:
        num((reportData as any)?.session_count) || num(ctx.session_count),
      phases,
      generatedAt: (reportData as any)?.generated_at ?? '',
    } as CoachReport;
  },

  async scoreItem({ recordBid, score, comment }) {
    await requestApi.scorePortalMentorshipItem({
      record_bid: recordBid,
      score,
      comment: comment ?? '',
    });
  },

  async submitPhaseSummary(input) {
    // dev 后端 /api/shifu/coach/phase-summary 未注册 → 404 上抛，
    // PhaseSummaryForm 会展示错误提示（v1 阶段数据空态下不可达）。
    await requestApi.submitShifuCoachPhaseSummary({
      record_bid: input.recordBid,
      coach_summary: input.coachSummary,
      learner_feedback: input.learnerFeedback,
      improvement_plan: input.improvementPlan,
      complete: input.complete,
    });
  },

  async createSession(input) {
    const created = (await requestApi.createCoachSession({
      learner_bid: input.learnerBid,
      phase_bid: input.phaseBid || null,
      session_type: input.sessionType,
      session_date: input.sessionDate,
      topic: input.topic,
      status: 'planned',
    })) as any;
    return mapSession(created);
  },

  async saveSessionNotes({ sessionBid, coachNotes, actionItems, duration }) {
    await requestApi.updateCoachSession({
      session_bid: sessionBid,
      mentor_notes: coachNotes,
      action_items: actionItems,
      duration_minutes: duration,
      status: 'done',
    });
  },

  async summarizeSession({ sessionBid, coachRating }) {
    // 1) 显式触发 LLM 重新生成 ai_summary（后端返回真实总结，覆盖手工占位文本）
    await requestApi.summarizeCoachSession({ session_bid: sessionBid });
    // 2) 置为 summarized + 落评分（后端 status/coach_rating 均在可编辑白名单）
    await requestApi.updateCoachSession({
      session_bid: sessionBid,
      status: 'summarized',
      coach_rating: coachRating,
    });
  },
};

export default coachApi;

// coach-lab 组件以具名 `api` 引用适配器（`import { api } from '@/lib/coach-api'`）
export const api = coachApi;
