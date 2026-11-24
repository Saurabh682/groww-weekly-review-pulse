import React from 'react';
import { Link } from 'react-router-dom';
import { AppStatusBadge } from '../../components/AppStatusBadge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { SectionTitle } from '../../components/SectionTitle';
import { AppRecord } from '../../data/types';
import { PLATFORMS, STORE_LISTINGS, STORE_NAMES } from '../../lib/stores';

export type AppAction = 'rename' | 'replace' | 'archive';

const ACTIONS: { action: AppAction; label: string }[] = [
  { action: 'rename', label: 'Rename' },
  { action: 'replace', label: 'Replace' },
  { action: 'archive', label: 'Archive' },
];

interface AppRowsProps {
  title: string;
  apps: AppRecord[];
  onAction: ((action: AppAction, app: AppRecord) => void) | null;
}

export const AppRows: React.FC<AppRowsProps> = ({ title, apps, onAction }) => (
  <section aria-label={title}>
    <SectionTitle>{title}</SectionTitle>
    <Card>
      <ul className="divide-y divide-border">
        {apps.map((app) => (
          <li
            key={app.app_key}
            className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 py-4 first:pt-0 last:pb-0"
          >
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <Link to={`/apps/${app.app_key}`} className="text-sm font-bold font-display text-white hover:text-primary">
                  {app.display_name}
                </Link>
                <AppStatusBadge status={app.status} />
              </div>
              <dl className="text-[11px] font-mono space-y-1">
                {PLATFORMS.map((platform) => (
                  <div key={platform} className="flex gap-2">
                    <dt className="text-text-muted whitespace-nowrap">{STORE_NAMES[platform]}</dt>
                    <dd className="text-text-secondary break-all">{STORE_LISTINGS[platform](app) ?? 'Not on this store'}</dd>
                  </div>
                ))}
              </dl>
            </div>
            {onAction && (
              <div className="flex flex-wrap gap-2 shrink-0">
                {ACTIONS.map(({ action, label }) => (
                  <Button
                    key={action}
                    variant="secondary"
                    size="sm"
                    aria-label={`${label} ${app.display_name}`}
                    onClick={() => onAction(action, app)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </Card>
  </section>
);
