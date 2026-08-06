'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import LearnerReportView from '@/components/LearnerReportView';

export default function HrReportPage() {
  const params = useParams<{ learner_bid: string }>();
  return (
    <div className='space-y-4'>
      <LearnerReportView learnerBid={params?.learner_bid || ''} />
    </div>
  );
}
