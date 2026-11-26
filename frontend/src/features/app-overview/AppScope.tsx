import React from 'react';
import { Link, useOutletContext, useParams } from 'react-router-dom';
import { Card } from '../../components/Card';
import { EmptyState } from '../../components/EmptyState';
import { AppRecord, ShellContext } from '../../data/types';
import { Loaded } from '../../components/LoadStates';

interface UnknownAppProps {
  appKey: string;
  apps: AppRecord[];
}

const UnknownApp: React.FC<UnknownAppProps> = ({ appKey, apps }) => (
  <div className="py-8 space-y-6">
    <EmptyState headingLevel={2} title="App not found" description={`There is no app called "${appKey}" here. Pick one of these apps.`} />
    <Card>
      <h2 className="text-base font-bold font-display text-white">Apps</h2>
      <ul className="mt-3 space-y-2">
        {apps
          .filter((app) => app.status !== 'archived')
          .map((app) => (
            <li key={app.app_key}>
              <Link to={`/apps/${app.app_key}`} className="text-xs font-semibold text-primary hover:underline">
                {app.display_name}
              </Link>
            </li>
          ))}
      </ul>
    </Card>
  </div>
);

interface AppScopeProps {
  children: (app: AppRecord) => React.ReactNode;
}

export const AppScope: React.FC<AppScopeProps> = ({ children }) => {
  const { appKey = '' } = useParams();
  const { apps } = useOutletContext<ShellContext>();
  return (
    <Loaded resource={apps} errorTitle="Could not load the apps" missing={<UnknownApp appKey={appKey} apps={[]} />}>
      {(list) => {
        const app = list.apps.find((candidate) => candidate.app_key === appKey);
        return app ? children(app) : <UnknownApp appKey={appKey} apps={list.apps} />;
      }}
    </Loaded>
  );
};
