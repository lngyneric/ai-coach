import { memo, useMemo, useEffect, useRef, useState } from 'react';
import { isEqual } from 'lodash';
import { IframeSandbox, type RenderSegment } from 'markdown-flow-ui/renderer';

interface ContentIframeProps {
  segments: RenderSegment[];
  mobileStyle: boolean;
  blockBid: string;
  confirmButtonText?: string;
  copyButtonText?: string;
  copiedButtonText?: string;
  sectionTitle?: string;
}

// ── Video source detection ──

declare let Aliplayer: any;

function isVideoSegment(segment: RenderSegment): boolean {
  if ((segment.type as string) === 'video') return true;
  try {
    const v = typeof segment.value === 'string' ? JSON.parse(segment.value) : segment.value;
    if (v?.source === 'direct' || v?.source === 'aliyunvod' || v?.source === 'bilibili' || v?.source === 'youtube') return true;
  } catch {}
  return false;
}

function parseVideoMeta(segment: RenderSegment): Record<string, any> {
  try {
    const v = typeof segment.value === 'string' ? JSON.parse(segment.value) : segment.value;
    return typeof v === 'object' && v ? v : {};
  } catch {
    return {};
  }
}

// ── Aliplayer SDK 动态加载器 ──

let aliplayerPromise: Promise<void> | null = null;

function loadAliplayerSDK(): Promise<void> {
  if (typeof Aliplayer !== 'undefined') return Promise.resolve();
  if (aliplayerPromise) return aliplayerPromise;

  aliplayerPromise = new Promise((resolve, reject) => {
    // 加载 CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '//g.alicdn.com/apsara-media-box/imp-web-player/2.35.4/skins/default/aliplayer-min.css';
    document.head.appendChild(link);

    // 加载 JS
    const script = document.createElement('script');
    script.src = '//g.alicdn.com/apsara-media-box/imp-web-player/2.35.4/aliplayer-min.js';
    script.onload = () => {
      // 等待 Aliplayer 全局变量就绪
      const check = setInterval(() => {
        if (typeof Aliplayer !== 'undefined') {
          clearInterval(check);
          resolve();
        }
      }, 100);
      setTimeout(() => clearInterval(check), 10000);
    };
    script.onerror = () => reject(new Error('Aliplayer SDK 加载失败'));
    document.head.appendChild(script);
  });

  return aliplayerPromise;
}

/** 阿里云 Aliplayer 播放器组件（动态加载 SDK） */
function AliplayerPlayer({ vid, playauth, cover, title }: {
  vid: string;
  playauth?: string;
  cover?: string;
  title?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);
  const [sdkReady, setSdkReady] = useState(false);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    loadAliplayerSDK()
      .then(() => setSdkReady(true))
      .catch(() => setLoadError(true));
  }, []);

  useEffect(() => {
    if (!sdkReady || !containerRef.current || playerRef.current) return;

    const player = new Aliplayer({
      id: containerRef.current.id,
      autoplay: true,
      width: '100%',
      height: '100%',
      vid: vid,
      playauth: playauth || '',
      cover: cover || '',
    }, function (player: any) {
      // 播放器就绪回调
    });

    playerRef.current = player;

    return () => {
      if (playerRef.current) {
        try { playerRef.current.dispose(); } catch {}
        playerRef.current = null;
      }
    };
  }, [sdkReady, vid, playauth, cover]);

  if (loadError) {
    // SDK 加载失败，回退到 iframe embed
    return (
      <iframe
        src={`//player.alicdn.com/video/player.html?vid=${vid}`}
        className="w-full h-full"
        allow="autoplay; fullscreen"
        allowFullScreen
        title={title || '阿里云 VOD'}
      />
    );
  }

  if (!sdkReady) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-muted rounded-lg">
        <span className="text-muted-foreground">加载播放器中...</span>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      id={`aliplayer-${vid}`}
      className="prism-player w-full h-full"
    />
  );
}

// ── 视频播放器调度 ──

function VideoPlayer({ meta }: { meta: Record<string, any> }) {
  switch (meta.source) {
    case 'direct':
      return (
        <video controls className="w-full max-w-3xl mx-auto rounded-lg shadow-lg" playsInline>
          <source src={meta.direct_url} type={meta.content_type || 'video/mp4'} />
          您的浏览器不支持视频播放
        </video>
      );

    case 'aliyunvod':
      return (
        <div className="w-full max-w-3xl mx-auto aspect-video rounded-lg overflow-hidden shadow-lg">
          <AliplayerPlayer
            vid={meta.video_id || meta.vid}
            playauth={meta.playauth}
            cover={meta.cover}
            title={meta.title}
          />
        </div>
      );

    case 'bilibili':
      return (
        <div className="w-full max-w-3xl mx-auto aspect-video rounded-lg overflow-hidden shadow-lg">
          <iframe
            src={`//player.bilibili.com/player.html?bvid=${meta.bvid}`}
            className="w-full h-full"
            allow="autoplay; fullscreen"
            allowFullScreen
            title={meta.title || 'Bilibili 视频'}
          />
        </div>
      );

    case 'youtube':
      return (
        <div className="w-full max-w-3xl mx-auto aspect-video rounded-lg overflow-hidden shadow-lg">
          <iframe
            src={`//www.youtube.com/embed/${meta.video_id}`}
            className="w-full h-full"
            allow="autoplay; fullscreen"
            allowFullScreen
            title={meta.title || 'YouTube 视频'}
          />
        </div>
      );

    default:
      return (
        <div className="w-full max-w-3xl mx-auto aspect-video rounded-lg overflow-hidden shadow-lg bg-muted flex items-center justify-center text-muted-foreground">
          不支持的视频源
        </div>
      );
  }
}

// ── 主组件 ──

const ContentIframe = memo(
  ({ segments, blockBid, sectionTitle }: ContentIframeProps) => {
    return (
      <>
        {segments.map((segment, index) => {
          if (segment.type === 'text') {
            return (
              <section key={'text' + index} data-element-bid={blockBid}>
                <div className='w-full h-full font-bold flex items-center justify-center text-primary'>
                  {sectionTitle}
                </div>
              </section>
            );
          }

          if (isVideoSegment(segment)) {
            const meta = parseVideoMeta(segment);
            return (
              <section key={'video' + index} data-element-bid={blockBid} className="my-4">
                <VideoPlayer meta={meta} />
              </section>
            );
          }

          const iframeNode = (
            <IframeSandbox
              key={'iframe' + index}
              type={segment.type}
              mode='blackboard'
              hideFullScreen
              content={segment.value}
            />
          );

          return (
            <section key={'sandbox' + index} data-element-bid={blockBid}>
              {segment.type === 'sandbox' ? (
                <div className='listen-sandbox-enter flex h-full w-full items-center justify-center'>
                  {iframeNode}
                </div>
              ) : (
                iframeNode
              )}
            </section>
          );
        })}
      </>
    );
  },
  (prevProps, nextProps) => {
    return (
      isEqual(prevProps.segments, nextProps.segments) &&
      prevProps.mobileStyle === nextProps.mobileStyle &&
      prevProps.blockBid === nextProps.blockBid &&
      prevProps.confirmButtonText === nextProps.confirmButtonText &&
      prevProps.copyButtonText === nextProps.copyButtonText &&
      prevProps.copiedButtonText === nextProps.copiedButtonText &&
      prevProps.sectionTitle === nextProps.sectionTitle
    );
  },
);

ContentIframe.displayName = 'ContentIframe';

export default ContentIframe;
