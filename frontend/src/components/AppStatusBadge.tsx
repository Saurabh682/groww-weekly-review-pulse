import React from 'react';
import { AppStatus } from '../data/types';
import { Badge } from './Badge';

const STATUS_BADGES: Record<AppStatus, { text: string; variant: 'teal' | 'amber' | 'coral' | 'gray' }> = {
  active: { text: 'Active', variant: 'teal' },
  pending_backfill: { text: 'Waiting for first collection', variant: 'amber' },
  backfilling: { text: 'Collecting', variant: 'amber' },
  failed: { text: 'Failed', variant: 'coral' },
  archived: { text: 'Archived', variant: 'gray' },
};

interface AppStatusBadgeProps {
  status: AppStatus;
}

export const AppStatusBadge: React.FC<AppStatusBadgeProps> = ({ status }) => (
  <Badge variant={STATUS_BADGES[status].variant}>{STATUS_BADGES[status].text}</Badge>
);
