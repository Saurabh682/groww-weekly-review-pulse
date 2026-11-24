import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar } from 'lucide-react';
import { AppStatusBadge } from '../../components/AppStatusBadge';
import { Badge } from '../../components/Badge';
import { Menu, MenuItem } from '../../components/Menu';
import { AppRecord, PulseWeek } from '../../data/types';
import { formatMoment, weekLabel } from '../../lib/dates';

interface AppHeadingProps {
  app: AppRecord;
  pulses: PulseWeek[];
  week: string | null;
}

export const AppHeading: React.FC<AppHeadingProps> = ({ app, pulses, week }) => {
  const navigate = useNavigate();
  const home = `/apps/${app.app_key}`;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">{app.display_name}</h1>
          <AppStatusBadge status={app.status} />
        </div>
        {week && pulses.length > 0 && (
          <Menu
            label="Choose week"
            text={weekLabel(week)}
            icon={<Calendar className="w-3.5 h-3.5 text-primary shrink-0" />}
          >
            {(close) =>
              pulses.map((pulse, index) => (
                <MenuItem
                  key={pulse.week_start}
                  selected={pulse.week_start === week}
                  onSelect={() => {
                    close();
                    navigate(index === 0 ? home : `${home}/weeks/${pulse.week_start}`);
                  }}
                >
                  <span>{weekLabel(pulse.week_start)}</span>
                  {index === 0 && <Badge variant="teal">Latest</Badge>}
                </MenuItem>
              ))
            }
          </Menu>
        )}
      </div>
      {app.archived_at && (
        <p className="text-xs text-text-secondary font-mono">
          Archived on {formatMoment(app.archived_at)}. This page is read-only and collects no new reviews.
        </p>
      )}
    </div>
  );
};
