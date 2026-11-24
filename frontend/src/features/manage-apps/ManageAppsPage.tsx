import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { EmptyState } from '../../components/EmptyState';
import { Loaded } from '../../components/LoadStates';
import { Toast } from '../../components/Toast';
import { AppList, AppRecord, ListingBody, Registration, ShellContext } from '../../data/types';
import { AppAction, AppRows } from './AppRows';
import { ArchiveDialog } from './ArchiveDialog';
import { ListingDialog } from './ListingDialog';
import { RenameDialog } from './RenameDialog';
import { SignInCard } from './SignInCard';

const FULL_REASON = 'slots-full';
const DEFAULT_COUNTRY = 'in';

type OpenDialog = { kind: 'add' } | { kind: AppAction; app: AppRecord };

function appPath(app: AppRecord): string {
  return `/apps/${encodeURIComponent(app.app_key)}`;
}

interface HeadingProps {
  list: AppList;
  onAdd: (() => void) | null;
}

const Heading: React.FC<HeadingProps> = ({ list, onAdd }) => {
  const isFull = list.slots_used >= list.slots_total;
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">Manage apps</h1>
          <Badge variant={isFull ? 'amber' : 'gray'}>{`${list.slots_used} of ${list.slots_total} slots used`}</Badge>
        </div>
        {onAdd && (
          <Button
            size="sm"
            icon={<Plus className="w-3.5 h-3.5" />}
            disabled={isFull}
            aria-describedby={isFull ? FULL_REASON : undefined}
            onClick={onAdd}
          >
            Add app
          </Button>
        )}
      </div>
      {onAdd && isFull && (
        <p id={FULL_REASON} className="text-xs text-text-secondary font-mono">
          {`All ${list.slots_total} slots are used. Archive an app to add another.`}
        </p>
      )}
    </div>
  );
};

export const ManageAppsPage: React.FC = () => {
  const { apps, operator } = useOutletContext<ShellContext>();
  const [dialog, setDialog] = useState<OpenDialog | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const canChange = operator.session.status === 'signed_in';

  const close = () => setDialog(null);
  const finish = (message: string) => {
    close();
    setNotice(message);
    apps.retry();
  };
  const open = (next: OpenDialog) => {
    setNotice(null);
    setDialog(next);
  };

  return (
    <>
      <Loaded resource={apps} errorTitle="Could not load the apps" missing={null}>
        {(list) => {
          const live = list.apps.filter((app) => app.status !== 'archived');
          const archived = list.apps.filter((app) => app.status === 'archived');
          return (
            <div className="space-y-8 animate-fade-in">
              <Heading list={list} onAdd={canChange ? () => open({ kind: 'add' }) : null} />
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                <div className="lg:col-span-8 space-y-8 min-w-0">
                  {live.length > 0 ? (
                    <AppRows title="Live apps" apps={live} onAction={canChange ? (kind, app) => open({ kind, app }) : null} />
                  ) : (
                    <EmptyState title="No apps yet" description="Add an app to start collecting its reviews." />
                  )}
                  {archived.length > 0 && <AppRows title="Archived apps" apps={archived} onAction={null} />}
                </div>
                <div className="lg:col-span-4 lg:sticky lg:top-24">
                  <SignInCard operator={operator} />
                </div>
              </div>
            </div>
          );
        }}
      </Loaded>

      {dialog?.kind === 'add' && (
        <ListingDialog
          title="Add app"
          explanation="One listing per store, or none. Nothing is added before you confirm."
          confirmLabel="Add app"
          country={DEFAULT_COUNTRY}
          send={operator.send}
          register={(listing: ListingBody) => operator.send<Registration>('POST', '/apps', listing)}
          onRegistered={({ app, backfill_dispatch }) => finish(`${app.display_name} was added. ${backfill_dispatch.message}`)}
          onClose={close}
        />
      )}
      {dialog?.kind === 'replace' && (
        <ListingDialog
          title={`Replace ${dialog.app.display_name}`}
          explanation={`${dialog.app.display_name} is archived and a new app takes its slot. The history of ${dialog.app.display_name} stays readable and is not mixed with the new app.`}
          confirmLabel={`Replace ${dialog.app.display_name}`}
          country={dialog.app.country}
          send={operator.send}
          register={(listing: ListingBody) =>
            operator.send<Registration>('POST', `${appPath(dialog.app)}/replace`, listing)
          }
          onRegistered={({ app, backfill_dispatch }) =>
            finish(`${app.display_name} replaced ${dialog.app.display_name}. ${backfill_dispatch.message}`)
          }
          onClose={close}
        />
      )}
      {dialog?.kind === 'rename' && (
        <RenameDialog
          app={dialog.app}
          rename={(display_name) => operator.send<AppRecord>('PATCH', appPath(dialog.app), { display_name })}
          onRenamed={(app) => finish(`${dialog.app.display_name} is now called ${app.display_name}.`)}
          onClose={close}
        />
      )}
      {dialog?.kind === 'archive' && (
        <ArchiveDialog
          app={dialog.app}
          archive={() => operator.send<AppRecord>('DELETE', appPath(dialog.app))}
          onArchived={() => finish(`${dialog.app.display_name} was archived.`)}
          onClose={close}
        />
      )}
      {notice && <Toast message={notice} onClose={() => setNotice(null)} />}
    </>
  );
};
