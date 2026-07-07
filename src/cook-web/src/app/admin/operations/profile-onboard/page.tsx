'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUserStore } from '@/store';
import request from '@/lib/request';

export default function ProfileOnboardPage() {
  const router = useRouter();
  const isInitialized = useUserStore(s => s.isInitialized);
  const isGuest = useUserStore(s => s.isGuest);
  const [onboarding, setOnboarding] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isInitialized && isGuest) {
      router.push('/login?redirect=/admin/operations/profile-onboard');
      return;
    }
    if (!isInitialized || isGuest) return;
    loadOnboarding();
  }, [isInitialized, isGuest]);

  async function loadOnboarding() {
    setLoading(true);
    try {
      const resp: any = await request.get('/api/shifu/profile-onboarding');
      setOnboarding(resp);
    } catch {
      setOnboarding({ error: '加载失败' });
    } finally {
      setLoading(false);
    }
  }

  async function completeOnboarding() {
    try {
      await request.post('/api/shifu/profile-onboarding/complete', {});
      setOnboarding({ ...onboarding, completed: true });
    } catch {
      // ignore
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-4">创作者入职引导</h1>
      {loading ? (
        <div className="animate-pulse space-y-3">
          <div className="h-8 bg-slate-200 rounded w-1/3" />
          <div className="h-20 bg-slate-200 rounded" />
        </div>
      ) : onboarding?.error ? (
        <p className="text-red-500 text-sm">{onboarding.error}</p>
      ) : onboarding?.completed ? (
        <div className="bg-green-50 p-4 rounded-xl">
          <p className="text-green-700">✅ 入职引导已完成</p>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border p-6">
            <h2 className="font-semibold mb-2">欢迎成为创作者</h2>
            <p className="text-sm text-slate-600 mb-4">
              完成以下步骤即可开始创建课程
            </p>
            <button
              onClick={completeOnboarding}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              完成引导
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
