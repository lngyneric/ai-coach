'use client';

import React, { useCallback, useEffect, useState } from 'react';
import api from '@/api';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';

/**
 * AI 学习报告展示（W2 遗留 3：/api/coach/report 真实接入）。
 *
 * 消费 GET /api/coach/report/<learner_bid>?source=auto|rule|llm
 *  - view_any_report（admin/hr/dept/coach）→ 任意学员
 *  - view_own_report（learner）→ 仅本人
 */

type ReportData = {
  learner_bid: string;
  generated_by: string;
  markdown: string;
  report: Record<string, unknown>;
  context: {
    session_count: number;
    mentorship_count: number;
    enrollment_count: number;
  };
};

export default function LearnerReportView({
  learnerBid,
}: {
  learnerBid: string;
}) {
  const { toast } = useToast();
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<'auto' | 'rule' | 'llm'>('auto');

  const load = useCallback(
    (src: 'auto' | 'rule' | 'llm') => {
      setLoading(true);
      setError(null);
      api
        .getCoachReport({ learner_bid: learnerBid, source: src })
        .then((res: any) => {
          setData(res as ReportData);
        })
        .catch(e => {
          console.error('[report] failed', e);
          setError(e?.message || '报告生成失败（可能无查看权限）');
        })
        .finally(() => setLoading(false));
    },
    [learnerBid],
  );

  useEffect(() => {
    load('auto');
  }, [load]);

  const handleReload = (src: 'auto' | 'rule' | 'llm') => {
    setSource(src);
    load(src);
    toast({ title: `重新生成（source=${src}）` });
  };

  return (
    <div className='space-y-4'>
      <div className='flex flex-wrap items-center justify-between gap-2'>
        <div>
          <h1 className='text-xl font-semibold text-gray-900'>AI 学习报告</h1>
          <p className='mt-1 text-sm text-gray-500'>
            learner_bid：{learnerBid} · 当前 source：{source}
            {data ? ` · generated_by=${data.generated_by}` : ''}
          </p>
        </div>
        <div className='flex gap-2'>
          <Button
            size='sm'
            variant='outline'
            onClick={() => handleReload('auto')}
          >
            auto
          </Button>
          <Button
            size='sm'
            variant='outline'
            onClick={() => handleReload('rule')}
          >
            rule
          </Button>
          <Button
            size='sm'
            variant='outline'
            onClick={() => handleReload('llm')}
          >
            llm
          </Button>
        </div>
      </div>

      {error && (
        <Card className='border-red-200 bg-red-50'>
          <CardContent className='p-4 text-sm text-red-700'>
            {error}
          </CardContent>
        </Card>
      )}

      {data && (
        <div className='grid grid-cols-3 gap-3'>
          <Card className='border-slate-200'>
            <CardContent className='p-3 text-center'>
              <p className='text-xs text-slate-500'>面谈记录</p>
              <p className='text-xl font-semibold'>
                {data.context.session_count}
              </p>
            </CardContent>
          </Card>
          <Card className='border-slate-200'>
            <CardContent className='p-3 text-center'>
              <p className='text-xs text-slate-500'>带教记录</p>
              <p className='text-xl font-semibold'>
                {data.context.mentorship_count}
              </p>
            </CardContent>
          </Card>
          <Card className='border-slate-200'>
            <CardContent className='p-3 text-center'>
              <p className='text-xs text-slate-500'>课程进度</p>
              <p className='text-xl font-semibold'>
                {data.context.enrollment_count}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className='border-slate-200'>
        <CardContent className='p-4'>
          {loading ? (
            <p className='py-8 text-center text-sm text-slate-400'>
              AI 报告生成中…
            </p>
          ) : data?.markdown ? (
            <div className='prose prose-sm max-w-none whitespace-pre-wrap text-sm leading-relaxed text-slate-700'>
              {data.markdown}
            </div>
          ) : (
            <p className='py-8 text-center text-sm text-slate-400'>
              暂无报告内容
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
