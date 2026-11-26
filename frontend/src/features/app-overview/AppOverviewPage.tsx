import React from 'react';
import { Loader2 } from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { AppHealth, AppRecord, AppStatus, COLLECTING, PulseAttempt, PulseHistory } from '../../data/types';
import { useApi } from '../../data/useApi';
import { formatDay } from '../../lib/dates';
import { AppHeading } from './AppHeading';
import { AppScope } from './AppScope';
import { HealthCard } from './HealthCard';
import { Loaded } from '../../components/LoadStates';
import { PulseSummary } from './PulseSummary';
import { ThemeTable } from './ThemeTable';
import { ThemeTrendPanel } from './ThemeTrendPanel';
import { appPath } from './paths';

interface AppProps {
  app: AppRecord;
}

function awaitsFirstPulse(app: AppRecord, { pulses, latest_run }: PulseHistory): boolean {
  const unanswered = (latest_run?.status ?? 'running') === 'running';
  return pulses.length === 0 && (COLLECTING.includes(app.status) || (app.status === 'active' && unanswered));
}

interface HealthRailProps extends AppProps {
  waiting: boolean;
}

const HealthRail: React.FC<HealthRailProps> = ({ app, waiting }) => {
  const health = useApi<AppHealth>(appPath(app.app_key, 'health'), { refreshWhile: () => waiting });
  return (
    <Loaded resource={health} errorTitle="Could not load collection health" missing={null}>
      {(data) => <HealthCard health={data} />}
    </Loaded>
  );
};

const NO_PULSE_YET: Record<Exclude<AppStatus, 'pending_backfill' | 'backfilling'>, string> = {
  active: "Pulses are written every Monday. This app's first one appears here after the next run.",
  failed: 'The first pulse is written after a collection works. The daily run tries again.',
  archived: 'This app was archived before its first pulse was written.',
};

interface NoPulseProps extends AppProps {
  latestRun: PulseAttempt | null;
}

const NoPulse: React.FC<NoPulseProps> = ({ app, latestRun }) => {
  if (app.status === 'pending_backfill' || app.status === 'backfilling') {
    return (
      <div role="status">
        <EmptyState headingLevel={2}
          title={`Collecting reviews for ${app.display_name}`}
          description="The first collection can take up to an hour. The first pulse follows it, and this page fills in then."
          icon={<Loader2 className="w-6 h-6 animate-spin" />}
        />
      </div>
    );
  }
  if (app.status === 'active' && latestRun?.status === 'low_volume') {
    const { min_reviews, usable_reviews, window_start, window_end } = latestRun;
    return (
      <EmptyState headingLevel={2}
        title="Not enough reviews yet"
        description={`A pulse needs ${min_reviews} reviews with enough text. ${app.display_name} has ${usable_reviews} from ${formatDay(window_start)} to ${formatDay(window_end)}. New reviews are collected every day, and the count is checked again every Monday.`}
      />
    );
  }
  return <EmptyState headingLevel={2} title="No pulse" description={NO_PULSE_YET[app.status]} />;
};

const Overview: React.FC<AppProps> = ({ app }) => {
  const history = useApi<PulseHistory>(appPath(app.app_key, 'pulses?limit=12'), {
    refreshWhile: (data) => awaitsFirstPulse(app, data),
  });
  return (
    <Loaded resource={history} errorTitle={`Could not load ${app.display_name}`} missing={null}>
      {(data) => {
        const { pulses, latest_run } = data;
        const latest = pulses.length > 0 ? pulses[0] : null;
        return (
          <div className="space-y-8 animate-fade-in">
            <AppHeading app={app} pulses={pulses} week={latest?.week_start ?? null} />
            {app.status === 'failed' && (
              <ErrorState headingLevel={2}
                title="The last collection failed"
                message="Collection health shows what went wrong. The daily run tries again."
              />
            )}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              <div className="lg:col-span-8 space-y-8 min-w-0">
                {latest ? (
                  <>
                    <PulseSummary pulse={latest} />
                    <ThemeTable themes={latest.themes} />
                    <ThemeTrendPanel pulses={pulses} />
                  </>
                ) : (
                  <NoPulse app={app} latestRun={latest_run} />
                )}
              </div>
              <div className="lg:col-span-4 lg:sticky lg:top-24">
                <HealthRail app={app} waiting={awaitsFirstPulse(app, data)} />
              </div>
            </div>
          </div>
        );
      }}
    </Loaded>
  );
};

export const AppOverviewPage: React.FC = () => <AppScope>{(app) => <Overview app={app} />}</AppScope>;
