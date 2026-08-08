'use client';
import { use } from 'react';
import dynamic from 'next/dynamic';
import Loading from '@/components/loading';
import MobileUnsupportedDialog from '@/components/MobileUnsupportedDialog';
import { getLessonIdFromQuery } from '@/c-utils/urlUtils';

const ShifuRoot = dynamic(() => import('@/components/shifu-root'), {
  ssr: false,
  loading: () => (
    <div className='h-screen w-full flex items-center justify-center'>
      <Loading />
    </div>
  ),
});

type ShifuPageParams = { id: string };

// useSearchParams() 需要 Suspense 边界，且与 use() 混用会抛错；
// 本页面纯客户端渲染，直接用 window.location.search 解析更可靠。
function getInitialLessonId(): string {
  if (typeof window === 'undefined') return '';
  return getLessonIdFromQuery(new URLSearchParams(window.location.search));
}

export default function Page({ params }: { params: Promise<ShifuPageParams> }) {
  const { id } = use(params);
  const initialLessonId = getInitialLessonId();

  return (
    <>
      <MobileUnsupportedDialog />
      <div className='h-screen w-full'>
        <ShifuRoot
          id={id}
          initialLessonId={initialLessonId}
        />
      </div>
    </>
  );
}

