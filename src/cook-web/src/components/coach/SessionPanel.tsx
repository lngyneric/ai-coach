'use client';

import { useState } from 'react';
import {
  BadgeCheck,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardEdit,
  Loader2,
  MessageSquare,
  Plus,
  Sparkles,
  Star,
} from 'lucide-react';
import { api } from '@/lib/coach-api';
import { useStreamingASR, StreamingTranscript } from '@/components/coach/StreamingASR';
import type { CoachSession, PhaseDetail, SessionType } from '@/lib/coach-api/types';
import { cn } from '@/lib/utils';

const typeLabel: Record<string, string> = {
  kickoff: '启动',
  regular: '常规',
  review: '复盘',
};

const statusStep: Record<string, number> = { planned: 0, done: 1, summarized: 2 };

/** 1v1 三环进度：课前准备 → 面谈交互 → 课后总结 */
function ThreeRingSteps({ session }: { session: CoachSession }) {
  const step = statusStep[session.status] ?? 0;
  const rings = [
    { label: '课前准备', icon: BookOpen },
    { label: '面谈交互', icon: MessageSquare },
    { label: '课后总结', icon: Sparkles },
  ];
  return (
    <div className="flex items-center gap-1">
      {rings.map((ring, i) => {
        const active = i <= step;
        const Icon = ring.icon;
        return (
          <div key={ring.label} className="flex items-center">
            {i > 0 && <span className={cn('mx-1 h-px w-4', i <= step ? 'bg-primary' : 'bg-border')} />}
            <span
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px]',
                active ? 'bg-primary/10 text-primary' : 'bg-secondary text-muted-foreground'
              )}
            >
              <Icon className="size-3" />
              {ring.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function SessionCard({
  session,
  onEditNotes,
  onSummarize,
}: {
  session: CoachSession;
  onEditNotes: (s: CoachSession) => void;
  onSummarize: (s: CoachSession) => void;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 font-medium">
          <MessageSquare className="size-4 shrink-0 text-primary" />
          <span className="min-w-0">{session.topic}</span>
        </div>
        <span className="shrink-0 rounded bg-secondary px-1.5 py-0.5 text-[11px]">
          {typeLabel[session.sessionType] ?? session.sessionType}
        </span>
      </div>

      <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <CalendarDays className="size-3.5" />
          {session.sessionDate.slice(0, 10)}
        </span>
        {session.duration && <span>{session.duration} 分钟</span>}
      </div>

      <div className="mt-2.5">
        <ThreeRingSteps session={session} />
      </div>

      {/* 课前准备 */}
      {(session.goal || session.preCourseBids.length > 0) && (
        <div className="mt-2.5 border-t border-border pt-2 text-xs">
          {session.goal && (
            <p>
              <b>目标：</b>
              {session.goal}
            </p>
          )}
          {session.preCourseBids.length > 0 && (
            <p className="mt-0.5 text-muted-foreground">
              课前课件：{session.preCourseBids.join('、')}
            </p>
          )}
        </div>
      )}

      {/* 面谈交互 */}
      {session.coachNotes && (
        <p className="mt-2 border-t border-border pt-2 text-muted-foreground">{session.coachNotes}</p>
      )}
      {session.actionItems && (
        <p className="mt-1 text-xs">
          <Star className="mr-1 inline size-3.5 text-amber-500" />
          {session.actionItems}
        </p>
      )}

      {/* 课后总结 */}
      {session.aiSummary && (
        <div className="mt-2 rounded-lg border border-primary/20 bg-primary/5 p-2.5 text-xs">
          <div className="mb-0.5 flex items-center gap-1 font-medium text-primary">
            <Sparkles className="size-3.5" />
            AI 汇总
            {session.coachRating !== null && (
              <span className="ml-auto rounded bg-primary/10 px-1.5 tabular-nums">
                {session.coachRating} 分
              </span>
            )}
          </div>
          <p className="text-muted-foreground">{session.aiSummary}</p>
          {session.nextAction && (
            <p className="mt-1">
              <b>下一步：</b>
              {session.nextAction}
            </p>
          )}
        </div>
      )}

      <div className="mt-3 flex justify-end gap-2 border-t border-border pt-2.5">
        {session.status !== 'summarized' && (
          <button
            type="button"
            onClick={() => onEditNotes(session)}
            className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs hover:bg-accent"
          >
            <ClipboardEdit className="size-3.5" />
            {session.status === 'planned' ? '记录面谈' : '编辑记录'}
          </button>
        )}
        {session.status === 'done' && (
          <button
            type="button"
            onClick={() => onSummarize(session)}
            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary-lighter"
          >
            <Sparkles className="size-3.5" />
            课后总结
          </button>
        )}
        {session.status === 'summarized' && (
          <span className="inline-flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="size-3.5" />
            闭环完成
          </span>
        )}
      </div>
    </div>
  );
}

export function SessionPanel({
  learnerId,
  phases,
  sessions,
  onChanged,
}: {
  learnerId: string;
  phases: PhaseDetail[];
  sessions: CoachSession[];
  onChanged: () => void;
}) {
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<CoachSession | null>(null);
  const [summarizing, setSummarizing] = useState<CoachSession | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // create form state
  const [sessionType, setSessionType] = useState<SessionType>('regular');
  const [phaseBid, setPhaseBid] = useState<string>('');
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [topic, setTopic] = useState('');
  const [goal, setGoal] = useState('');
  const [preCourses, setPreCourses] = useState('');

  // notes form state
  const [notes, setNotes] = useState('');
  const [actions, setActions] = useState('');
  const [duration, setDuration] = useState('');

  // summarize form state
  const [aiSummary, setAiSummary] = useState('');
  const [nextAction, setNextAction] = useState('');
  const [rating, setRating] = useState('');

  const asr = useStreamingASR();

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setErr(null);
    try {
      await fn();
      setShowCreate(false);
      setEditing(null);
      setSummarizing(null);
      setTopic('');
      setGoal('');
      setPreCourses('');
      onChanged();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">1v1 面谈（三环闭环）</h2>
        <button
          type="button"
          onClick={() => setShowCreate((v) => !v)}
          className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary-lighter"
        >
          <Plus className="size-3.5" />
          发起面谈
        </button>
      </div>

      {err && <p className="rounded-lg border border-destructive/30 bg-destructive/5 p-2 text-xs text-destructive">{err}</p>}

      {showCreate && (
        <div className="space-y-2.5 rounded-xl border border-primary/30 bg-primary/5 p-3.5 text-sm">
          <div className="text-xs font-medium text-primary">课前准备</div>
          <div className="grid grid-cols-2 gap-2">
            <select
              value={sessionType}
              onChange={(e) => setSessionType(e.target.value as SessionType)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="kickoff">启动面谈</option>
              <option value="regular">常规面谈</option>
              <option value="review">复盘面谈</option>
            </select>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            />
          </div>
          <select
            value={phaseBid}
            onChange={(e) => setPhaseBid(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            <option value="">关联阶段（可选）</option>
            {phases.map((p) => (
              <option key={p.phaseBid} value={p.phaseBid}>
                {p.phaseName}
              </option>
            ))}
          </select>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="面谈主题 *"
            className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          />
          <input
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="目标设定"
            className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          />
          <input
            value={preCourses}
            onChange={(e) => setPreCourses(e.target.value)}
            placeholder="课前推荐课件（逗号分隔）"
            className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          />
          <button
            type="button"
            disabled={!topic || busy}
            onClick={() =>
              run(async () => {
                await api.createSession({
                  learnerBid: learnerId,
                  phaseBid: phaseBid || null,
                  sessionType,
                  sessionDate: date,
                  topic,
                  goal,
                  preCourseBids: preCourses.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
                });
              })
            }
            className="inline-flex items-center rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
          >
            {busy && <Loader2 className="mr-1 size-3.5 animate-spin" />}
            创建面谈
          </button>
        </div>
      )}

      {sessions.length === 0 && !showCreate && (
        <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
          暂无面谈记录，点击「发起面谈」开始 1v1 闭环
        </p>
      )}

      {sessions.map((s) => (
        <div key={s.sessionBid}>
          <SessionCard session={s} onEditNotes={setEditing} onSummarize={setSummarizing} />

          {editing?.sessionBid === s.sessionBid && (
            <div className="mt-2 space-y-2 rounded-xl border border-border bg-muted/30 p-3.5 text-sm">
              <div className="text-xs font-medium">面谈交互记录</div>
              <StreamingTranscript
                transcript={asr.state.transcript}
                partial={asr.state.partial}
                recording={asr.state.recording}
                onStart={asr.start}
                onStop={() => { asr.stop(); setNotes((prev:string) => prev + (prev ? " " : "") + asr.state.transcript); }}
              />
              <textarea
                value={notes || s.coachNotes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="面谈笔记…"
                className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
              <input
                value={actions || s.actionItems}
                onChange={(e) => setActions(e.target.value)}
                placeholder="行动项"
                className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
              <input
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="时长（分钟）"
                type="number"
                className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setEditing(null)} className="rounded-md px-2.5 py-1 text-xs hover:bg-accent">
                  取消
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      await api.saveSessionNotes({
                        sessionBid: s.sessionBid,
                        coachNotes: notes || s.coachNotes,
                        actionItems: actions || s.actionItems,
                        duration: duration ? Number(duration) : undefined,
                      });
                    })
                  }
                  className="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground disabled:opacity-50"
                >
                  保存记录
                </button>
              </div>
            </div>
          )}

          {summarizing?.sessionBid === s.sessionBid && (
            <div className="mt-2 space-y-2 rounded-xl border border-primary/30 bg-primary/5 p-3.5 text-sm">
              <div className="flex items-center gap-1 text-xs font-medium text-primary">
                <Sparkles className="size-3.5" />
                课后总结（AI 汇总为占位，正式环境接 LLM）
              </div>
              <textarea
                value={aiSummary}
                onChange={(e) => setAiSummary(e.target.value)}
                rows={3}
                placeholder="AI 汇总本场要点…"
                className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
              <input
                value={nextAction}
                onChange={(e) => setNextAction(e.target.value)}
                placeholder="后续行动建议"
                className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
              <input
                value={rating}
                onChange={(e) => setRating(e.target.value)}
                placeholder="本场评分 1-100"
                type="number"
                min={1}
                max={100}
                className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setSummarizing(null)} className="rounded-md px-2.5 py-1 text-xs hover:bg-accent">
                  取消
                </button>
                <button
                  type="button"
                  disabled={!aiSummary || busy}
                  onClick={() =>
                    run(async () => {
                      await api.summarizeSession({
                        sessionBid: s.sessionBid,
                        aiSummary,
                        nextAction,
                        coachRating: rating ? Number(rating) : undefined,
                      });
                    })
                  }
                  className="inline-flex items-center rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground disabled:opacity-50"
                >
                  {busy && <Loader2 className="mr-1 size-3.5 animate-spin" />}
                  完成闭环
                </button>
              </div>
            </div>
          )}
        </div>
      ))}

      {sessions.some((s) => s.status === 'summarized') && (
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <BadgeCheck className="size-3.5 text-emerald-500" />
          已完成总结的面谈进入学员培训档案
        </p>
      )}
    </div>
  );
}
