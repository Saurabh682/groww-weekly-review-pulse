import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Smartphone } from 'lucide-react';
import { Badge } from '../components/Badge';
import { Menu, MenuItem } from '../components/Menu';
import { ApiState, AppList } from '../data/types';

interface AppSwitcherProps {
  state: ApiState<AppList>;
  appKey: string | undefined;
}

const WAITING_TEXT = {
  loading: 'Loading apps',
  waking: 'Waking backend',
  missing: 'Apps unavailable',
  error: 'Apps unavailable',
};

export const AppSwitcher: React.FC<AppSwitcherProps> = ({ state, appKey }) => {
  const navigate = useNavigate();
  const [showArchived, setShowArchived] = useState(false);

  if (state.status !== 'ready') {
    return (
      <span className="flex items-center gap-2 px-3 py-1.5 text-xs text-text-muted" role="status">
        <Smartphone className="w-3.5 h-3.5" />
        {WAITING_TEXT[state.status]}
      </span>
    );
  }

  const { apps, slots_used, slots_total } = state.data;
  const selected = apps.find((app) => app.app_key === appKey);
  const listed = apps.filter((app) => showArchived || app.status !== 'archived');

  return (
    <Menu
      label="Choose app"
      text={selected?.display_name ?? 'Choose an app'}
      icon={<Smartphone className="w-3.5 h-3.5 text-primary shrink-0" />}
    >
      {(close) => (
        <>
          <div className="px-3 py-1.5 text-3xs font-mono uppercase tracking-wider text-text-muted">
            {slots_used} of {slots_total} app slots used
          </div>
          {listed.map((app) => (
            <MenuItem
              key={app.app_key}
              selected={app.app_key === appKey}
              onSelect={() => {
                close();
                navigate(`/apps/${app.app_key}`);
              }}
            >
              <span className="truncate">{app.display_name}</span>
              {app.status === 'archived' && <Badge variant="gray">Archived</Badge>}
            </MenuItem>
          ))}
          <label className="flex items-center gap-2 mt-1 px-3 py-2 border-t border-border text-xs text-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
              className="accent-primary"
            />
            Show archived apps
          </label>
          <Link
            to="/manage"
            onClick={close}
            className="block px-3 py-2 border-t border-border text-xs font-semibold text-primary hover:bg-surface-elevated transition-colors"
          >
            Manage apps
          </Link>
        </>
      )}
    </Menu>
  );
};
