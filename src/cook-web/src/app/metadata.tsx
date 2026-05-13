import { Metadata, Viewport } from 'next';

const brandName = process.env.NEXT_PUBLIC_BRAND_NAME || 'AI-Shifu';

export const metadata: Metadata = {
  title: brandName,
  description: '',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};