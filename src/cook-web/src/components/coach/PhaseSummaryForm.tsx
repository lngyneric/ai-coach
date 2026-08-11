'use client';

import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Loader2, X } from 'lucide-react';
import { api } from '@/lib/coach-api';
import type { PhaseDetail } from '@/lib/coach-api/types';

export function PhaseSummaryForm({
  phase,
  onClose,
  onSaved,
}: {
  phase: PhaseDetail;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [coachSummary, setCoachSummary] = useState(phase.coachSummary);
  const [learnerFeedback, setLearnerFeedback] = useState(phase.learnerFeedback);
  const [improvementPlan, setImprovementPlan] = useState(phase.improvementPlan);
  const [complete, setComplete] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 合规控制点 3：验收不通过需制定改进计划
  const failedAcceptance = phase.totalScore > 0 && phase.totalScore < phase.passingScore;
  const needImprovement = failedAcceptance && !improvementPlan.trim();

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.submitPhaseSummary({
        recordBid: phase.recordBid,
        coachSummary,
        learnerFeedback,
        improvementPlan,
        complete,
      });
      onSaved();
    } catch (e) {
      setError(String(e));
      setSaving(false);
    }
  };

  return (
    <Dialog.Root open onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[85vh] w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-xl border border-border bg-card p-5 shadow-lg focus:outline-none">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-lg font-semibold">阶段小结</Dialog.Title>
              <Dialog.Description className="mt-0.5 text-sm text-muted-foreground">
                {phase.phaseName}
              </Dialog.Description>
            </div>
            <Dialog.Close className="rounded-md p-1 text-muted-foreground hover:bg-accent">
              <X className="size-4" />
            </Dialog.Close>
          </div>

          <div className="mt-4 space-y-4">
            {failedAcceptance && (
              <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm">
                <b>本阶段总分 {phase.totalScore} 未达及格线 {phase.passingScore}</b>
                <p className="mt-0.5 text-muted-foreground">
                  按合规控制点，验收不通过需制定改进计划后方可继续。
                </p>
              </div>
            )}
            {(
              [
                ['导师小结', coachSummary, setCoachSummary, '本阶段整体表现、亮点与不足…', false],
                ['学员反馈', learnerFeedback, setLearnerFeedback, '学员对阶段安排的反馈…', false],
                ['改进计划', improvementPlan, setImprovementPlan, '下一阶段的具体改进安排…', needImprovement],
              ] as const
            ).map(([label, value, setter, placeholder, required]) => (
              <div key={label}>
                <label className="mb-1.5 block text-sm font-medium">
                  {label}
                  {required && <span className="ml-1 text-destructive">*</span>}
                </label>
                <textarea
                  value={value}
                  onChange={(e) => setter(e.target.value)}
                  rows={3}
                  placeholder={placeholder}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:border-ring focus:outline-none"
                />
              </div>
            ))}

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={complete}
                onChange={(e) => setComplete(e.target.checked)}
                className="size-4 rounded border-input accent-[#0f63ee]"
              />
              标记本阶段为已完成
            </label>
          </div>

          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}

          <div className="mt-5 flex justify-end gap-2">
            <Dialog.Close className="rounded-lg border border-border px-4 py-2 text-sm hover:bg-accent">
              取消
            </Dialog.Close>
            <button
              type="button"
              disabled={saving || needImprovement}
              onClick={submit}
              className="inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-lighter disabled:opacity-50"
            >
              {saving && <Loader2 className="mr-1.5 size-4 animate-spin" />}
              保存小结
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
