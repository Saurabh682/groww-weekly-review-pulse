import React from 'react';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';
import { AppHealth, CollectionRun } from '../../data/types';
import { formatDay, formatMoment } from '../../lib/dates';
import { formatIndianNumber } from '../../lib/format';
import { PLATFORMS, STORE_LISTINGS, STORE_NAMES } from './stores';

const RUN_STATUS: Record<CollectionRun['status'], { text: string; variant: 'teal' | 'amber' | 'coral' | 'gray' }> = {
  ok: { text: 'OK', variant: 'teal' },
  running: { text: 'Running', variant: 'amber' },
  failed: { text: 'Failed', variant: 'coral' },
  skipped_disabled: { text: 'Turned off', variant: 'gray' },
};

const RUN_MODES: Record<CollectionRun['mode'], string> = {
  backfill: 'First collection',
  daily: 'Daily',
  reconcile: 'Monthly check',
  csv_import: 'File import',
};

interface DetailProps {
  label: string;
  children: React.ReactNode;
}

const Detail: React.FC<DetailProps> = ({ label, children }) => (
  <div className="flex justify-between gap-3">
    <dt className="text-text-muted whitespace-nowrap">{label}</dt>
    <dd className="text-text-primary text-right">{children}</dd>
  </div>
);

function covered(run: CollectionRun): string {
  return run.covered_start
    ? `${formatDay(run.covered_start)} to ${formatDay(run.window_end)}`
    : `Nothing between ${formatDay(run.window_start)} and ${formatDay(run.window_end)}`;
}

interface StoreHealthProps {
  name: string;
  run: CollectionRun | null;
  isListed: boolean;
  reviews: number | null;
  caveat: string | null;
}

const StoreHealth: React.FC<StoreHealthProps> = ({ name, run, isListed, reviews, caveat }) => (
  <div className="py-4 first:pt-0">
    <div className="flex items-center justify-between gap-2 mb-2">
      <h3 className="text-xs font-bold font-display text-white">{name}</h3>
      {run ? (
        <Badge variant={RUN_STATUS[run.status].variant}>{RUN_STATUS[run.status].text}</Badge>
      ) : (
        <Badge variant="gray">{isListed ? 'No run yet' : 'Not on this store'}</Badge>
      )}
    </div>
    <dl className="text-[11px] font-mono space-y-1">
      {reviews !== null && <Detail label="In pulse window">{formatIndianNumber(reviews)}</Detail>}
      {run && (
        <>
          <Detail label="Last run">{formatMoment(run.finished_at ?? run.started_at)}</Detail>
          <Detail label="Covered">{covered(run)}</Detail>
          <Detail label="New reviews">
            {formatIndianNumber(run.inserted)} of {formatIndianNumber(run.fetched)} read
          </Detail>
        </>
      )}
    </dl>
    <div className="flex flex-wrap gap-1.5 mt-2 empty:hidden">
      {caveat && <Badge variant="amber">{`Pulse: ${caveat}`}</Badge>}
      {run?.source_limit_hit && <Badge variant="amber">Store limit reached</Badge>}
      {run && run.feed_gaps > 0 && <Badge variant="amber">{`Feed gaps: ${run.feed_gaps}`}</Badge>}
    </div>
    {run?.error && <p className="text-xs text-failure-dark mt-2 break-words">{run.error}</p>}
  </div>
);

interface HealthCardProps {
  health: AppHealth;
}

export const HealthCard: React.FC<HealthCardProps> = ({ health }) => (
  <Card>
    <h2 className="text-base font-bold font-display text-white mb-4">Collection health</h2>
    <div className="divide-y divide-border">
      {PLATFORMS.map((platform) => {
        const coverage = health.stores.find((store) => store.platform === platform);
        return (
          <StoreHealth
            key={platform}
            name={STORE_NAMES[platform]}
            run={health.collections[platform]}
            isListed={STORE_LISTINGS[platform](health.app) !== null}
            reviews={coverage?.reviews ?? null}
            caveat={coverage?.caveat ?? null}
          />
        );
      })}
    </div>
    <details className="border-t border-border pt-4 text-xs text-text-secondary">
      <summary className="cursor-pointer font-semibold hover:text-white">Run history</summary>
      {health.runs.length === 0 ? (
        <p className="mt-2">No runs yet.</p>
      ) : (
        <ul className="mt-2 divide-y divide-border">
          {health.runs.map((run) => (
            <li key={`${run.platform}-${run.started_at}`} className="flex items-center justify-between gap-2 py-2">
              <div>
                <div className="text-text-primary">
                  {RUN_MODES[run.mode]} • {STORE_NAMES[run.platform]}
                </div>
                <div className="text-[10px] font-mono text-text-muted">
                  {formatMoment(run.started_at)} • {formatIndianNumber(run.inserted)} new
                </div>
              </div>
              <Badge variant={RUN_STATUS[run.status].variant}>{RUN_STATUS[run.status].text}</Badge>
            </li>
          ))}
        </ul>
      )}
    </details>
  </Card>
);
