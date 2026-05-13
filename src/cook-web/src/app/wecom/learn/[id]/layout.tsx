import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Learning',
  description: 'Enterprise learning platform',
  viewport: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no',
};

export default function WeComLearnLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className='min-h-screen bg-background'>
      {children}
    </div>
  );
}
