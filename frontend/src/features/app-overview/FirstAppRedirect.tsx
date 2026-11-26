import React from 'react';
import { Navigate, useNavigate, useOutletContext } from 'react-router-dom';
import { EmptyState } from '../../components/EmptyState';
import { ShellContext } from '../../data/types';
import { Loaded } from '../../components/LoadStates';

const NoApps: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="py-8">
      <EmptyState headingLevel={2}
        title="No apps yet"
        description="Register an app to start collecting its reviews."
        actionLabel="Manage apps"
        onAction={() => navigate('/manage')}
      />
    </div>
  );
};

export const FirstAppRedirect: React.FC = () => {
  const { apps } = useOutletContext<ShellContext>();
  return (
    <Loaded resource={apps} errorTitle="Could not load the apps" missing={<NoApps />}>
      {(list) => {
        const first = list.apps.find((app) => app.status === 'active') ?? list.apps.find((app) => app.status !== 'archived');
        return first ? <Navigate to={`/apps/${first.app_key}`} replace /> : <NoApps />;
      }}
    </Loaded>
  );
};
