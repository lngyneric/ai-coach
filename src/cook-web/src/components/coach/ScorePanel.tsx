'use client';

import { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Loader2, X } from 'lucide-react';
import { api } from '@/lib/coach-api';
import type { ChecklistItem } from '@/lib/coach-api/types';
import { cn } from '@/lib/utils';

/**
 * Redesigned scoring interaction.
 *
 * Fixes vs. the legacy docker/coach.html:
 * 1. record_bid is always submitted (legacy code drops it from the body).
 * 2. The coach sees the learner's submission (name/category/comment/time)
 *    inside the panel instead of scoring blind.
 * 3. Keyboard friendly: 0-5 keys pick the score, Cmd/Ctrl+Enter submits.
 */
export function ScorePanel({
  item,
  onClose,
  onScored,
}: {
  item: ChecklistItem;
  onClose: () => void;
  onScored: () => void;
}) {
  const [score, setScore] = useState<number | null>(null);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = score !== null && !submitting;

  const submit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      // recordBid explicitly included — the legacy UI's bug.
      await api.scoreItem({ recordBid: item.recordBid, score, comment });
      onScored();
    } catch (e) {
      setError(String(e));
      setSubmitting(false);
    }
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        submit();
      }
      const n = Number(e.key);
      if (!e.metaKey && !e.ctrlKey && n >= 0 && n <= 5 && document.activeElement?.tagName !== 'TEXTAREA') {
        setScore(n);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [score, comment, submitting]);

  return (
    <Dialog.Root open onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=open]:fade-in" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-5 shadow-lg focus:outline-none">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-lg font-semibold">验收评分</Dialog.Title>
              <Dialog.Description className="mt-0.5 text-sm text-muted-foreground">
                {item.name}
              </Dialog.Description>
            </div>
            <Dialog.Close className="rounded-md p-1 text-muted-foreground hover:bg-accent">
              <X className="size-4" />
            </Dialog.Close>
          </div>

          {/* Learner submission — previously invisible to the coach */}
          <div className="mt-4 rounded-lg border border-border bg-muted/40 p-3 text-sm">
            <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
              {item.category && (
                <span className="rounded bg-secondary px-1.5 py-0.5">{item.category}</span>
              )}
              {item.submittedAt && (
                <span>提交于 {new Date(item.submittedAt).toLocaleString('zh-CN')}</span>
              )}
            </div>
            <p>{item.comment || '（学员未填写备注）'}</p>
          </div>

          <div className="mt-4">
            <div className="mb-2 text-sm font-medium">评分（0–5）</div>
            <div className="flex gap-2">
              {[0, 1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setScore(n)}
                  className={cn(
                    'flex size-10 items-center justify-center rounded-lg border text-sm font-semibold tabular-nums transition-colors',
                    score === n
                      ? n >= 3
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-destructive bg-destructive text-destructive-foreground'
                      : 'border-border hover:bg-accent'
                  )}
                >
                  {n}
                </button>
              ))}
              <span className="ml-1 self-center text-xs text-muted-foreground">≥3 为通过</span>
            </div>
          </div>

          <div className="mt-4">
            <label className="mb-1.5 block text-sm font-medium" htmlFor="score-comment">
              评语（可选）
            </label>
            <textarea
              id="score-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              placeholder="给学员的反馈…"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:border-ring focus:outline-none"
            />
          </div>

          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}

          <div className="mt-5 flex items-center justify-between">
            <span className="text-xs text-muted-foreground">⌘/Ctrl + Enter 提交</span>
            <div className="flex gap-2">
              <Dialog.Close className="rounded-lg border border-border px-4 py-2 text-sm hover:bg-accent">
                取消
              </Dialog.Close>
              <button
                type="button"
                disabled={!canSubmit}
                onClick={submit}
                className="inline-flex items-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-lighter disabled:opacity-50"
              >
                {submitting && <Loader2 className="mr-1.5 size-4 animate-spin" />}
                提交评分
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
