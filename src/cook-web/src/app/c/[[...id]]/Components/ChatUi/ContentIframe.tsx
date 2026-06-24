import { memo, useMemo } from 'react';
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

/** Detect if a segment value is a video source object from MDFlow */
function isVideoSegment(segment: RenderSegment): boolean {
  if (segment.type === 'video') return true;
  try {
    const v = typeof segment.value === 'string' ? JSON.parse(segment.value) : segment.value;
    if (v?.source === 'direct' || v?.source === 'aliyunvod' || v?.source === 'bilibili' || v?.source === 'youtube') return true;
  } catch {}
  return false;
}

/** Parse video metadata from segment value */
function parseVideoMeta(segment: RenderSegment): Record<string, any> {
  try {
    const v = typeof segment.value === 'string' ? JSON.parse(segment.value) : segment.value;
    return typeof v === 'object' && v ? v : {};
  } catch {
    return {};
  }
}

/** Render video player based on source type */
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
          <iframe
            src={meta.embed_url}
            className="w-full h-full"
            allow="autoplay; fullscreen"
            allowFullScreen
            title={meta.title || '阿里云 VOD 视频'}
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

          // Check if this segment is a video
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