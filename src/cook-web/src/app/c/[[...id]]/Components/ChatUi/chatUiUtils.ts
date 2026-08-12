import {
  normalizeLegacyBlockCompatItem,
  normalizeLegacyBlockCompatList,
} from '@/c-utils/chatUiCompat';

const CUSTOM_BUTTON_AFTER_CONTENT_TAG = '<custom-button-after-content>';
const CUSTOM_BUTTON_AFTER_CONTENT_REGEX =
  /<custom-button-after-content>[\s\S]*?<\/custom-button-after-content>/g;

// mdflow 图片块兜底：图片 URL 为空（![alt]() 或 <img src="">）时渲染跳过/占位，
// 避免浏览器对空 src 的 <img> 报警告并产生 Uncaught (in promise) 加载失败。
const EMPTY_MD_IMAGE_REGEX = /!\[[^\]]*\]\(\s*\)/g;

// 静态资源（svg/png）导入形态兼容：webpack 下 next-image-loader 返回
// { src, height, width } 对象；turbopack（next dev --turbopack）下 svg 直接
// 返回 URL 字符串。统一解析成可用的 src 字符串，避免运行时取到 undefined/空。
export const resolveAssetSrc = (asset: unknown): string => {
  if (typeof asset === 'string') {
    return asset.trim();
  }
  if (asset && typeof asset === 'object' && 'src' in asset) {
    const src = (asset as { src?: unknown }).src;
    return typeof src === 'string' ? src.trim() : '';
  }
  return '';
};
const EMPTY_HTML_IMG_REGEX =
  /<img\b[^>]*\bsrc\s*=\s*["']\s*["'][^>]*>/gi;
const UNDEFINED_HTML_IMG_REGEX =
  /<img\b[^>]*\bsrc\s*=\s*["'](?:undefined|null)["'][^>]*>/gi;

export const sanitizeEmptyImageBlocks = (
  content?: string | null,
): string => {
  if (!content) {
    return content ?? '';
  }

  return content
    .replace(EMPTY_MD_IMAGE_REGEX, '')
    .replace(EMPTY_HTML_IMG_REGEX, '')
    .replace(UNDEFINED_HTML_IMG_REGEX, '');
};

export const appendCustomButtonAfterContent = (
  content: string | undefined,
  buttonMarkup: string,
): string => {
  const baseContent = content ?? '';

  if (!buttonMarkup) {
    return baseContent;
  }

  if (baseContent.includes(CUSTOM_BUTTON_AFTER_CONTENT_TAG)) {
    return baseContent;
  }

  const trimmedContent = baseContent.trimEnd();
  const endsWithCodeFence =
    trimmedContent.endsWith('```') || trimmedContent.endsWith('~~~');
  const needsLineBreak =
    endsWithCodeFence && !baseContent.endsWith('\n') ? '\n' : '';

  return baseContent + needsLineBreak + buttonMarkup;
};

export const hasCustomButtonAfterContent = (
  content?: string | null,
): boolean => {
  return Boolean(content?.includes(CUSTOM_BUTTON_AFTER_CONTENT_TAG));
};

export const stripCustomButtonAfterContent = (
  content?: string | null,
): string | null | undefined => {
  if (!content) {
    return content;
  }
  if (!hasCustomButtonAfterContent(content)) {
    return content;
  }
  // Remove ask button markup from listen mode content.
  return content.replace(CUSTOM_BUTTON_AFTER_CONTENT_REGEX, '').trimEnd();
};

export const syncCustomButtonAfterContent = ({
  content,
  buttonMarkup,
  shouldShowButton,
}: {
  content?: string | null;
  buttonMarkup: string;
  shouldShowButton: boolean;
}): string => {
  const baseContent = content ?? '';

  if (shouldShowButton) {
    return appendCustomButtonAfterContent(baseContent, buttonMarkup);
  }

  return stripCustomButtonAfterContent(baseContent) ?? '';
};

export const inheritCustomButtonAfterContent = ({
  nextContent,
  previousContent,
  buttonMarkup,
}: {
  nextContent?: string | null;
  previousContent?: string | null;
  buttonMarkup: string;
}): string => {
  const resolvedNextContent = nextContent ?? '';

  if (!hasCustomButtonAfterContent(previousContent)) {
    return resolvedNextContent;
  }

  return appendCustomButtonAfterContent(resolvedNextContent, buttonMarkup);
};

export { normalizeLegacyBlockCompatItem, normalizeLegacyBlockCompatList };
