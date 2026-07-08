'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useUserStore } from '@/store';
import request from '@/lib/request';

interface VideoSource {
  bid: string;
  title: string;
  sourceUrl: string;
}

export default function VideoCoursePage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params?.id as string;
  const isInitialized = useUserStore(s => s.isInitialized);
  const isGuest = useUserStore(s => s.isGuest);
  const [videos, setVideos] = useState<VideoSource[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showList, setShowList] = useState(false);

  useEffect(() => {
    if (isInitialized && isGuest) { router.push(`/login?redirect=/c/v/${courseId}`); return; }
    if (!isInitialized || isGuest || !courseId) return;
    loadVideo();
  }, [isInitialized, isGuest, courseId]);

  async function loadVideo() {
    setLoading(true);
    try {
      const shifu: any = await request.get(`/api/shifu/shifus/${courseId}/detail`);
      const tree: any = await request.get(`/api/learn/shifu/${courseId}/outline-item-tree?preview_mode=false`);
      const chapters: any[] = (tree?.outline_items || []);
      const found: VideoSource[] = [];
      for (const ch of chapters) {
        for (const lesson of (ch.children || [])) {
          if (!lesson.bid) continue;
          try {
            const md: any = await request.get(`/api/shifu/shifus/${courseId}/outlines/${lesson.bid}/mdflow`);
            const content = typeof md === 'string' ? md : md?.data || md?.content || '';
            // Support {{video}} format: first line with URL, skip AI entirely
            const videoTagMatch = content.match(/^\{\{video\}\}\s*\n\s*(https?:\/\/\S+)/im);
            const aliMatch = content.match(/source\s*=\s*"([^"]+)"/);
            const videoMatch = content.match(/\[video\]([^\[]+)\[\/video\]/);
            const src = videoTagMatch?.[1] || aliMatch?.[1] || videoMatch?.[1] || '';
            if (src) found.push({ bid: lesson.bid, title: lesson.name || '视频', sourceUrl: src });
          } catch { /* skip */ }
        }
      }
      setVideos(found);
    } catch (err: any) { setError(err?.message || err?.msg || '加载失败'); }
    finally { setLoading(false); }
  }

  if (!isInitialized) {
    return <div className="min-h-screen bg-black flex items-center justify-center"><div className="w-10 h-10 border-3 border-white/30 border-t-white rounded-full animate-spin" /></div>;
  }

  if (loading || error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        {loading ? (
          <div className="flex flex-col items-center gap-3"><div className="w-10 h-10 border-3 border-white/30 border-t-white rounded-full animate-spin" /><span className="text-white/60 text-sm">加载视频...</span></div>
        ) : (
          <div className="text-center px-6"><p className="text-white/80 text-lg mb-2">⚠️ {error}</p><button onClick={loadVideo} className="mt-4 px-4 py-2 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20">重试</button></div>
        )}
      </div>
    );
  }

  if (videos.length === 0) {
    return <div className="min-h-screen bg-black flex items-center justify-center"><p className="text-white/50 text-lg">暂无视频内容</p></div>;
  }

  const current = videos[currentIdx];

  return (
    <div className="min-h-screen bg-black">
      {/* Top bar */}
      <div className="fixed top-0 left-0 right-0 z-50" style={{ opacity: showList ? 1 : 0 }} onMouseEnter={() => setShowList(true)} onMouseLeave={() => setShowList(false)}>
        <div className="bg-gradient-to-b from-black/80 to-transparent px-4 py-3">
          <div className="flex items-center gap-3 max-w-7xl mx-auto">
            <button onClick={() => router.push('/courses')} className="text-white/70 hover:text-white transition-colors text-sm">← 返回</button>
            <span className="text-white/90 text-sm font-medium truncate">{current.title}</span>
          </div>
        </div>
      </div>

      {/* Video Player */}
      <div className="w-full h-full" style={{ minHeight: '100dvh' }}>
        <SimpleHlsPlayer src={current.sourceUrl} />
      </div>

      {/* Bottom right: lesson list */}
      <div className="fixed bottom-6 right-6 z-50">
        <button onClick={() => setShowList(!showList)} className="bg-white/10 backdrop-blur-md text-white px-3 py-2 rounded-full text-sm hover:bg-white/20 transition-all">
          {showList ? '✕ 收起' : `☰ ${currentIdx + 1}/${videos.length}`}
        </button>
        {showList && (
          <div className="absolute bottom-14 right-0 w-72 bg-black/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden shadow-2xl" onMouseEnter={() => setShowList(true)} onMouseLeave={() => setShowList(false)}>
            <div className="p-3 border-b border-white/10"><p className="text-white/70 text-xs font-medium">课程列表</p></div>
            <div className="max-h-80 overflow-y-auto">
              {videos.map((v, i) => (
                <button key={v.bid} onClick={() => { setCurrentIdx(i); setShowList(false); }}
                  className={`w-full text-left px-4 py-3 text-sm transition-colors flex items-center gap-3 ${i === currentIdx ? 'bg-white/15 text-white' : 'text-white/60 hover:bg-white/5 hover:text-white/80'}`}>
                  <span className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs shrink-0">{i + 1}</span>
                  <span className="truncate">{v.title}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Simple HLS Player ─────────────────────
function SimpleHlsPlayer({ src }: { src: string }) {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const [status, setStatus] = React.useState<'loading' | 'ready' | 'error'>('loading');
  const [errMsg, setErrMsg] = React.useState('');

  React.useEffect(() => {
    const v = videoRef.current;
    if (!v || !src) return;
    let hls: any = null;
    let destroyed = false;

    async function load() {
      // MP4: native play
      if (src.match(/\.(mp4|webm|ogg)$/i)) {
        v.src = src;
        v.addEventListener('loadedmetadata', () => { if (!destroyed) setStatus('ready'); });
        v.addEventListener('error', () => { if (!destroyed) { setStatus('error'); setErrMsg('视频加载失败'); }});
        return;
      }
      // HLS: try native (Safari) then hls.js
      if (v.canPlayType('application/vnd.apple.mpegurl')) {
        v.src = src;
        v.addEventListener('loadedmetadata', () => { if (!destroyed) setStatus('ready'); });
        return;
      }
      try {
        if (typeof (window as any).Hls === 'undefined') {
          await new Promise<void>((resolve, reject) => {
            const s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest/dist/hls.min.js';
            s.async = true;
            s.onload = () => resolve();
            s.onerror = () => reject(new Error('hls.js 加载失败'));
            document.body.appendChild(s);
          });
        }
        if (destroyed) return;
        const Hls = (window as any).Hls;
        if (Hls && Hls.isSupported()) {
          hls = new Hls();
          hls.loadSource(src);
          hls.attachMedia(v);
          hls.on(Hls.Events.MANIFEST_PARSED, () => { if (!destroyed) setStatus('ready'); });
          hls.on(Hls.Events.ERROR, (_e: any, d: any) => { if (d.fatal && !destroyed) { setStatus('error'); setErrMsg('播放错误'); }});
        } else {
          v.src = src;
          v.addEventListener('loadedmetadata', () => { if (!destroyed) setStatus('ready'); });
        }
      } catch (err: any) { if (!destroyed) { setStatus('error'); setErrMsg(err.message || '加载失败'); }}
    }
    load();
    return () => { destroyed = true; if (hls) hls.destroy(); };
  }, [src]);

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center" style={{ minHeight: '100dvh' }}>
      {status === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center bg-black z-10">
          <div className="flex flex-col items-center gap-3"><div className="w-10 h-10 border-3 border-white/30 border-t-white rounded-full animate-spin" /><span className="text-white/60 text-sm">加载视频...</span></div>
        </div>
      )}
      {status === 'error' && (
        <div className="absolute inset-0 flex items-center justify-center bg-black z-10">
          <div className="text-center px-6"><p className="text-white/80 text-lg mb-2">⚠️ {errMsg}</p>
            <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-white/10 text-white rounded-lg text-sm hover:bg-white/20">重试</button>
          </div>
        </div>
      )}
      <video ref={videoRef} className="w-full h-full object-contain" controls playsInline preload="metadata" style={{ maxHeight: '100dvh' }} />
    </div>
  );
}
