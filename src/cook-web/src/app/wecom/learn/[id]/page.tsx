'use client';

import { use, useCallback, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  getLessonIdFromQuery,
} from '@/c-utils/urlUtils';
import Loading from '@/components/loading';
import { useUserStore } from '@/store';
import type { AuthResult } from '@/lib/api';

const ShifuRoot = dynamic(() => import('@/components/shifu-root'), {
  ssr: false,
  loading: () => (
    <div className='h-screen w-full flex items-center justify-center'>
      <Loading />
    </div>
  ),
});

type WeComLearnPageParams = { id: string };

export default function Page({ params }: { params: Promise<WeComLearnPageParams> }) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setUser = useUserStore(state => state.setUserInfo);

  const code = searchParams.get('code');
  const state = searchParams.get('state');

  const handleAuthCallback = useCallback(async (authCode: string) => {
    try {
      const callbackUrl = `/api/user/oauth/wecom/callback?code=${encodeURIComponent(authCode)}`;
      if (state) {
        // eslint-disable-next-line @typescript-eslint/restrict-template-expressions
        const resp = await fetch(`${callbackUrl}&state=${encodeURIComponent(state)}`);
      } else {
        const resp = await fetch(callbackUrl);
      }

      // After OAuth callback, the backend sets the token cookie.
      // Refresh to load the page cleanly with the token.
      // Strip code/state from URL to keep it clean.
      const cleanUrl = window.location.pathname + window.location.hash;
      window.history.replaceState({}, '', cleanUrl);
      setAuthReady(true);
    } catch (err) {
      setError('Authentication failed. Please try again.');
    }
  }, [state]);

  const redirectToOAuth = useCallback(() => {
    // Redirect to WeCom OAuth authorize page
    const redirectUri = window.location.origin + `/wecom/learn/${id}`;
    const oauthUrl = `/api/user/oauth/wecom?redirect_uri=${encodeURIComponent(redirectUri)}`;
    fetch(oauthUrl)
      .then(res => res.json())
      .then(data => {
        if (data.data?.authorize_url) {
          window.location.href = data.data.authorize_url;
        } else {
          setError('Failed to initiate WeCom authentication.');
        }
      })
      .catch(() => {
        setError('Failed to connect to authentication server.');
      });
  }, [id]);

  useEffect(() => {
    if (code) {
      handleAuthCallback(code);
    } else {
      // No code — need to initiate OAuth flow
      redirectToOAuth();
    }
  }, [code, handleAuthCallback, redirectToOAuth]);

  if (error) {
    return (
      <div className='h-screen w-full flex items-center justify-center'>
        <div className='text-center'>
          <p className='text-red-500 mb-4'>{error}</p>
          <button
            onClick={() => redirectToOAuth()}
            className='px-4 py-2 bg-blue-500 text-white rounded'
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!authReady) {
    return (
      <div className='h-screen w-full flex items-center justify-center'>
        <Loading />
      </div>
    );
  }

  const initialLessonId = getLessonIdFromQuery(searchParams);

  return (
    <div className='h-screen w-full'>
      <ShifuRoot id={id} initialLessonId={initialLessonId} />
    </div>
  );
}
