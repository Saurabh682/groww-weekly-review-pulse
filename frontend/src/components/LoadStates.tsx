import React from 'react';
import { Loader2 } from 'lucide-react';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { Skeleton } from './Skeleton';
import { ApiResource } from '../data/types';

export const LoadingPanels: React.FC = () => (
  <div className="space-y-6" role="status" aria-label="Loading">
    <Skeleton className="h-10 w-2/3" />
    <Skeleton className="h-44 w-full" />
    <Skeleton className="h-64 w-full" />
  </div>
);

export const WakingBackend: React.FC = () => (
  <div className="py-8" role="status">
    <EmptyState
      title="Waking backend"
      description="The data service sleeps when nobody uses it. It can take a minute to start, and this page loads by itself when it is ready."
      icon={<Loader2 className="w-6 h-6 animate-spin" />}
    />
  </div>
);

interface LoadedProps<T> {
  resource: ApiResource<T>;
  errorTitle: string;
  missing: React.ReactNode;
  children: (data: T) => React.ReactNode;
}

export function Loaded<T>({ resource, errorTitle, missing, children }: LoadedProps<T>): React.ReactElement {
  const { state, retry } = resource;
  switch (state.status) {
    case 'loading':
      return <LoadingPanels />;
    case 'waking':
      return <WakingBackend />;
    case 'missing':
      return <>{missing}</>;
    case 'error':
      return (
        <div className="py-8">
          <ErrorState title={errorTitle} message={state.message} onRetry={retry} />
        </div>
      );
    case 'ready':
      return <>{children(state.data)}</>;
  }
}
