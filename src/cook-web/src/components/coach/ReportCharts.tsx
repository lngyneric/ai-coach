'use client';

import ReactECharts from 'echarts-for-react';
import type { CoachReport } from '@/lib/coach-api/types';
import { useEffect, useState } from 'react';

function useIsDark() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const el = document.documentElement;
    const update = () => setDark(el.classList.contains('dark'));
    update();
    const obs = new MutationObserver(update);
    obs.observe(el, { attributes: true, attributeFilter: ['class'] });
    return () => obs.disconnect();
  }, []);
  return dark;
}

const statusLabel: Record<string, string> = {
  completed: '已完成',
  in_progress: '进行中',
  not_started: '未开始',
  failed: '未通过',
};

/** Multi-phase total-score trend — the "能力曲线" the design doc promised. */
export function ScoreTrendChart({ report }: { report: CoachReport }) {
  const dark = useIsDark();
  const started = report.phases.filter((p) => p.status !== 'not_started' && p.passingScore > 0);
  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: dark ? '#9ca3af' : '#6b7280' },
    grid: { left: 40, right: 24, top: 32, bottom: 32 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: started.map((p) => p.name.replace(/ · .*/, '')),
      axisLine: { lineStyle: { color: dark ? '#1f2937' : '#e5e7eb' } },
    },
    yAxis: {
      type: 'value',
      max: 100,
      splitLine: { lineStyle: { color: dark ? '#1f2937' : '#e5e7eb' } },
    },
    series: [
      {
        name: '阶段总分',
        type: 'line',
        smooth: true,
        symbolSize: 8,
        data: started.map((p) => p.totalScore),
        lineStyle: { width: 3, color: '#0f63ee' },
        itemStyle: { color: '#0f63ee' },
        areaStyle: { color: 'rgba(15,99,238,0.08)' },
        markLine: started.length > 0 ? {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#f59e0b' },
          data: [{ yAxis: started[0]?.passingScore ?? 60, label: { formatter: '及格线' } }],
        } : undefined,
      },
    ],
  };
  return <ReactECharts option={option} style={{ height: 260 }} notMerge />;
}

/** Per-dimension breakdown across started phases (理论/实操/导师评价). */
export function DimensionChart({ report }: { report: CoachReport }) {
  const dark = useIsDark();
  const started = report.phases.filter((p) => p.status !== 'not_started' && p.passingScore > 0);
  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: dark ? '#9ca3af' : '#6b7280' },
    legend: { bottom: 0, textStyle: { color: dark ? '#9ca3af' : '#6b7280' } },
    grid: { left: 40, right: 24, top: 24, bottom: 48 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: started.map((p) => p.name.replace(/ · .*/, '')),
      axisLine: { lineStyle: { color: dark ? '#1f2937' : '#e5e7eb' } },
    },
    yAxis: {
      type: 'value',
      max: 100,
      splitLine: { lineStyle: { color: dark ? '#1f2937' : '#e5e7eb' } },
    },
    series: [
      { name: '理论', type: 'bar', data: started.map((p) => p.theoryScore), itemStyle: { color: '#0f63ee' } },
      { name: '实操', type: 'bar', data: started.map((p) => p.practiceScore), itemStyle: { color: '#2a9d90' } },
      { name: '导师评价', type: 'bar', data: started.map((p) => p.mentorScore), itemStyle: { color: '#e8c468' } },
    ],
  };
  return <ReactECharts option={option} style={{ height: 260 }} notMerge />;
}

export function ReportCharts({ report }: { report: CoachReport }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-xl border border-border bg-card p-4">
        <h3 className="mb-1 text-sm font-medium">阶段成绩趋势</h3>
        <p className="mb-2 text-xs text-muted-foreground">各阶段总分变化（虚线为及格线）</p>
        <ScoreTrendChart report={report} />
      </div>
      <div className="rounded-xl border border-border bg-card p-4">
        <h3 className="mb-1 text-sm font-medium">能力维度构成</h3>
        <p className="mb-2 text-xs text-muted-foreground">理论 / 实操 / 导师评价对比</p>
        <DimensionChart report={report} />
      </div>
    </div>
  );
}

export { statusLabel };
