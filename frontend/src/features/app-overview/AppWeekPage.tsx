import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';
import { EmptyState } from '../../components/EmptyState';
import { AppRecord, PulseHistory, PulseWeekDetail, StoreCoverage } from '../../data/types';
import { useApi } from '../../data/useApi';
import { formatIndianNumber } from '../../lib/format';
import { AppHeading } from './AppHeading';
import { AppScope } from './AppScope';
import { Loaded } from './LoadStates';
import { PulseSummary } from './PulseSummary';
import { ThemeTable } from './ThemeTable';
import { STORE_NAMES } from './stores';
import { appPath } from './paths';

interface StoreCountsProps {
  stores: StoreCoverage[];
}

const StoreCounts: React.FC<StoreCountsProps> = ({ stores }) => (
  <Card>
    <h2 className="text-base font-bold font-display text-white mb-4">Reviews per store</h2>
    <ul className="divide-y divide-border">
      {stores.map((store) => (
        <li key={store.platform} className="py-3 first:pt-0 last:pb-0">
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="text-text-secondary">{STORE_NAMES[store.platform]}</span>
            <span className="font-mono font-bold text-white">{formatIndianNumber(store.reviews)}</span>
          </div>
          {store.caveat && (
            <div className="mt-1.5">
              <Badge variant="amber">{store.caveat}</Badge>
            </div>
          )}
        </li>
      ))}
    </ul>
  </Card>
);

interface WeekProps {
  app: AppRecord;
  week: string;
}

const MissingWeek: React.FC<WeekProps> = ({ app, week }) => {
  const navigate = useNavigate();
  return (
    <div className="py-8">
      <EmptyState
        title="Week not found"
        description={`${app.display_name} has no pulse for "${week}".`}
        actionLabel="See the latest pulse"
        onAction={() => navigate(`/apps/${app.app_key}`)}
      />
    </div>
  );
};

const Week: React.FC<WeekProps> = ({ app, week }) => {
  const detail = useApi<PulseWeekDetail>(appPath(app.app_key, `pulses/${encodeURIComponent(week)}`));
  const history = useApi<PulseHistory>(appPath(app.app_key, 'pulses?limit=12'));
  const pulses = history.state.status === 'ready' ? history.state.data.pulses : [];

  return (
    <Loaded
      resource={detail}
      errorTitle={`Could not load ${app.display_name}`}
      missing={<MissingWeek app={app} week={week} />}
    >
      {(pulse) => (
        <div className="space-y-8 animate-fade-in">
          <AppHeading app={app} pulses={pulses} week={pulse.week_start} />
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-8 space-y-8 min-w-0">
              <PulseSummary pulse={pulse} />
              <ThemeTable themes={pulse.themes} />
            </div>
            <div className="lg:col-span-4 lg:sticky lg:top-24">
              <StoreCounts stores={pulse.stores} />
            </div>
          </div>
        </div>
      )}
    </Loaded>
  );
};

export const AppWeekPage: React.FC = () => {
  const { week = '' } = useParams();
  return <AppScope>{(app) => <Week app={app} week={week} />}</AppScope>;
};
