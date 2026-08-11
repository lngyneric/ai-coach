/**
 * Coaching / report domain types（coach-lab 迁移）。
 *
 * 来源：coach-lab/src/lib/api/types.ts，按 cook-web 真实后端契约适配：
 *  - 字段命名沿用 coach-lab camelCase 域模型（组件契约），后端 snake_case
 *    由 `src/lib/coach-api/index.ts` 适配器在边界处映射。
 *  - 已确认 cook-web 无重复类型定义 → 以本文件为唯一域类型来源。
 *
 * 后端表（ai-shifu-dev flaskr/service/learning_portal/models.py）：
 *  - coach_phases（MentorshipPhase）: phase_bid/name/code/duration_days/
 *    passing_score/theory_weight/practice_weight/review_weight/mentor_weight
 *  - learner_coaching（LearnerMentorship）: record_bid/learner_bid/phase_bid/
 *    status/theory_score/practice_score/peer_review_score/coach_score/
 *    total_score/started_at/completed_at
 *  - learner_checklist_items（LearnerChecklistItem）: record_bid/item_bid/score/
 *    comment/status/submitted_at/scored_at
 *  - coach_checklist（MentorshipChecklist）: item_bid/phase_bid/name/category/
 *    max_score/is_required
 *  - coach_sessions（CoachSession）: session_bid/learner_bid/mentor_bid/
 *    phase_bid/session_type/session_date/duration_minutes/topic/mentor_notes/
 *    learner_notes/action_items/status/coach_rating/ai_summary/next_action
 */

// ── Phase metadata (coach_phases) ──────────────────────────────────
export type ChecklistCategory = 'exam' | 'review' | 'practice';

export interface PhaseMeta {
  phaseBid: string;
  name: string;
  code: string;
  sortOrder: number;
  durationDays: number;
  passingScore: number;
  theoryWeight: number;
  practiceWeight: number;
  reviewWeight: number;
  mentorWeight: number;
}

// ── Coach students list（/api/portal/mentor/students）──────────────
export interface CoachStudent {
  learnerBid: string;
  userBid: string;
  name: string;
  employeeNo: string;
  department: string;
  positionName: string;
  onboardingDate: string | null;
  status: string;
  currentPhaseStatus: string | null;
  currentPhaseBid?: string | null;
  /** 当前阶段 learner_coaching.record_bid（面谈/任务闭环关联，TRAINING-LOOP） */
  currentPhaseRecordBid?: string | null;
  pendingTaskCount: number;
  pendingScoreCount: number;
}

// ── Pending score item（/api/portal/mentor/pending-scores）─────────
export interface PendingScore {
  recordBid: string;
  learnerBid: string;
  itemBid: string;
  comment: string;
  submittedAt: string | null;
}

// ── Phase detail per learner（learner_coaching ⋈ coach_phases）─────
export interface PhaseDetail {
  recordBid: string;
  phaseBid: string;
  phaseName: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | string;
  // dimension scores（后端列：theory/practice/peer_review/coach）
  theoryScore: number;
  practiceScore: number;
  reviewScore: number;
  mentorScore: number;
  totalScore: number;
  durationDays: number;
  passingScore: number;
  checklistProgress: string;
  checklistPct: number;
  startedAt: string;
  completedAt: string;
  // summary trio — 后端 learner_coaching 无这三列（dev 缺列，v1 为空）
  coachSummary: string;
  learnerFeedback: string;
  improvementPlan: string;
}

// ── Checklist item（提交明细）──────────────────────────────────────
export interface ChecklistItem {
  recordBid: string;
  itemBid: string;
  phaseBid: string;
  name: string;
  category: ChecklistCategory;
  maxScore: number;
  isRequired: boolean;
  status: 'pending' | 'submitted' | 'scored';
  score: number | null;
  comment: string;
  submittedAt: string | null;
  scoredAt: string | null;
}

// ── 1v1 coaching session（coach_sessions）──────────────────────────
export type SessionType = 'kickoff' | 'regular' | 'review';
export type SessionStatus = 'planned' | 'done' | 'summarized';

export interface CoachSession {
  sessionBid: string;
  learnerBid: string;
  phaseBid: string | null;
  sessionType: SessionType | string;
  sessionDate: string;
  duration: number | null; // minutes
  topic: string;
  // 课前准备（后端 coach_sessions 无 goal/pre_course_bids 列 → 常为空）
  preCourseBids: string[];
  goal: string;
  // 面谈交互
  coachNotes: string;
  actionItems: string;
  // 课后总结
  aiSummary: string;
  nextAction: string;
  coachRating: number | null; // 1-100
  status: SessionStatus | string;
}

// ── Analysis report ────────────────────────────────────────────────
export interface ReportPhase {
  phaseBid: string;
  name: string;
  status: string;
  totalScore: number;
  passingScore: number;
  theoryScore: number;
  practiceScore: number;
  reviewScore: number;
  mentorScore: number;
  coachSummary: string;
  startedAt: string;
  completedAt: string;
}

export interface CoachReport {
  learnerName: string;
  learnerBid: string;
  totalPhases: number;
  completedPhases: number;
  inProgressPhases: number;
  checklistTotal: number;
  checklistScored: number;
  checklistPassed: number;
  checklistPassRate: number;
  sessionCount: number;
  phases: ReportPhase[];
  generatedAt: string;
}

// ── Data-source contract（coachApi 适配器实现）─────────────────────
export interface CoachApi {
  listStudents(): Promise<CoachStudent[]>;
  listPendingScores(): Promise<PendingScore[]>;
  listPhaseDetails(learnerBid: string): Promise<PhaseDetail[]>;
  listChecklistItems(learnerBid: string, phaseBid?: string): Promise<ChecklistItem[]>;
  listSessions(learnerBid: string): Promise<CoachSession[]>;
  getReport(learnerBid: string): Promise<CoachReport>;
  scoreItem(input: { recordBid: string; score: number; comment: string }): Promise<void>;
  submitPhaseSummary(input: {
    recordBid: string;
    coachSummary?: string;
    learnerFeedback?: string;
    improvementPlan?: string;
    complete?: boolean;
  }): Promise<void>;
  createSession(input: {
    learnerBid: string;
    phaseBid: string | null;
    sessionType: SessionType;
    sessionDate: string;
    topic: string;
    preCourseBids?: string[];
    goal?: string;
    /** 培训闭环（TRAINING-LOOP-DESIGN §改造2）：可选关联当前阶段
     *  learner_coaching.record_bid → POST /api/coach/sessions phase_record_bid */
    phaseRecordBid?: string | null;
  }): Promise<CoachSession>;
  saveSessionNotes(input: {
    sessionBid: string;
    coachNotes: string;
    actionItems: string;
    duration?: number;
  }): Promise<void>;
  summarizeSession(input: {
    sessionBid: string;
    aiSummary: string;
    nextAction: string;
    coachRating?: number;
  }): Promise<void>;
}
