import React, { useState } from 'react';
import { NavLink, Outlet, useLocation, useMatch, useNavigate } from 'react-router-dom';
import {
  Activity,
  Calendar,
  Download,
  HelpCircle,
  Layers,
  LineChart,
  ListChecks,
  PlayCircle,
  SlidersHorizontal,
  UploadCloud,
} from 'lucide-react';
import { Badge } from '../components/Badge';
import { Button } from '../components/Button';
import { Menu, MenuItem } from '../components/Menu';
import { AppList, COLLECTING, ScenarioType, ShellContext } from '../data/types';
import { useApi } from '../data/useApi';
import { useOperator } from '../data/useOperator';
import { AppSwitcher } from './AppSwitcher';

const APPS_PATH = '/apps?include_archived=true';
const SAMPLE_WEEKS = ['Week of 9 Nov 2026', 'Week of 2 Nov 2026', 'Week of 26 Oct 2026', 'Week of 19 Oct 2026'];
const LIST_OPTIONS = {
  slowMeansWaking: true,
  refreshWhile: ({ apps }: AppList) => apps.some((app) => COLLECTING.includes(app.status)),
};
const ICON = 'w-4 h-4';

const SAMPLE_ITEMS = [
  { to: '/sample', label: 'Weekly Pulse', icon: <Activity className={ICON} /> },
  { to: '/themes', label: 'Themes', icon: <Layers className={ICON} /> },
  { to: '/run', label: 'Run & Publish', icon: <PlayCircle className={ICON} /> },
  { to: '/import', label: 'Data Import', icon: <UploadCloud className={ICON} /> },
];

const sideLink = (isActive: boolean) =>
  `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs transition-all duration-150 ${
    isActive
      ? 'bg-primary-tint text-primary font-bold border border-primary-border shadow-glow-teal-sm'
      : 'text-text-secondary hover:text-white hover:bg-surface/60'
  }`;

const MANAGE_ITEM = { to: '/manage', label: 'Manage Apps', icon: <ListChecks className={ICON} /> };

const bottomLink = (isActive: boolean) =>
  `flex flex-col items-center justify-center min-w-[56px] h-12 py-1 px-2 text-[10px] font-medium transition-all ${
    isActive ? 'text-primary font-bold scale-105' : 'text-text-muted hover:text-white'
  }`;

export const Shell: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const appKey = useMatch('/apps/:appKey/*')?.params.appKey;
  const apps = useApi<AppList>(APPS_PATH, LIST_OPTIONS);
  const operator = useOperator();
  const [selectedWeek, setSelectedWeek] = useState(SAMPLE_WEEKS[0]);

  const queryParams = new URLSearchParams(location.search);
  const currentScenario = (queryParams.get('scenario') as ScenarioType) || 'ok';
  const isSample = SAMPLE_ITEMS.some((item) => item.to === location.pathname);

  const handleScenarioChange = (scenario: ScenarioType) => {
    const params = new URLSearchParams(location.search);
    if (scenario === 'ok') {
      params.delete('scenario');
    } else {
      params.set('scenario', scenario);
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    navigate(`${location.pathname}${query}`);
  };

  const samplePath = (path: string, extra: Record<string, string> = {}) => {
    const params = new URLSearchParams(currentScenario === 'ok' ? extra : { ...extra, scenario: currentScenario });
    const query = params.toString();
    return query ? `${path}?${query}` : path;
  };

  const overviewItem = {
    to: appKey ? `/apps/${appKey}` : '/',
    label: 'App Overview',
    icon: <LineChart className={ICON} />,
  };

  const context: ShellContext = { currentScenario, selectedWeek, apps, operator };

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row text-text-primary antialiased selection:bg-primary selection:text-primary-on">
      <aside className="hidden md:flex flex-col w-60 bg-surface-dim border-r border-border shrink-0 select-none">
        <div className="h-16 flex items-center px-5 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-on shadow-glow-teal-sm">
              <Activity className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <div className="font-bold font-display text-sm leading-tight tracking-tight text-white">Review Pulse</div>
              <div className="text-[10px] font-mono text-text-secondary tracking-wider">Weekly Review Intel</div>
            </div>
          </div>
        </div>

        <nav className="p-3 space-y-1.5 flex-1" aria-label="Main">
          <NavLink to={overviewItem.to} end={overviewItem.to === '/'} className={({ isActive }) => sideLink(isActive)}>
            {overviewItem.icon}
            <span className="font-medium">{overviewItem.label}</span>
          </NavLink>
          <NavLink to={MANAGE_ITEM.to} className={({ isActive }) => sideLink(isActive)}>
            {MANAGE_ITEM.icon}
            <span className="font-medium">{MANAGE_ITEM.label}</span>
          </NavLink>
          <NavLink to="/help" className={({ isActive }) => sideLink(isActive)}>
            <HelpCircle className={ICON} />
            <span className="font-medium">Help</span>
          </NavLink>

          <div className="pt-4 pb-1 px-3.5 text-[10px] font-mono uppercase tracking-wider text-text-muted">
            Sample data
          </div>
          {SAMPLE_ITEMS.map((item) => (
            <NavLink key={item.to} to={samplePath(item.to)} className={({ isActive }) => sideLink(isActive)}>
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {isSample && (
          <div className="p-3.5 border-t border-border bg-canvas-subtle/60">
            <label
              htmlFor="scenario"
              className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2"
            >
              <SlidersHorizontal className="w-3 h-3 text-primary" />
              Scenario Simulator
            </label>
            <select
              id="scenario"
              value={currentScenario}
              onChange={(e) => handleScenarioChange(e.target.value as ScenarioType)}
              className="w-full text-xs bg-surface border border-border-subtle rounded-lg px-2.5 py-1.5 text-text-primary font-medium focus:outline-none focus:border-primary cursor-pointer"
            >
              <option value="ok">Normal (ok)</option>
              <option value="empty">Empty State</option>
              <option value="error">API Error (500)</option>
              <option value="validation-failed">Validation Failed (Flatline)</option>
              <option value="low-coverage">Low Coverage Wave</option>
            </select>
          </div>
        )}
      </aside>

      <div className="flex-1 flex flex-col min-w-0 pb-20 md:pb-0">
        <header className="bg-surface-dim/95 border-b border-border px-4 sm:px-6 shrink-0 sticky top-0 z-30 backdrop-blur-md">
          <div className="flex items-center justify-between gap-2.5 h-16">
            <div className="flex items-center gap-2.5 min-w-0">
              <AppSwitcher state={apps.state} appKey={appKey} />
              {isSample && (
                <div className="hidden lg:block">
                  <Menu
                    label="Choose sample week"
                    text={selectedWeek}
                    icon={<Calendar className="w-3.5 h-3.5 text-primary shrink-0" />}
                  >
                    {(close) =>
                      SAMPLE_WEEKS.map((week) => (
                        <MenuItem
                          key={week}
                          selected={selectedWeek === week}
                          onSelect={() => {
                            setSelectedWeek(week);
                            close();
                          }}
                        >
                          {week}
                        </MenuItem>
                      ))
                    }
                  </Menu>
                </div>
              )}
              {isSample && <Badge variant="amber">Sample data</Badge>}
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              <Button
                variant="secondary"
                size="sm"
                icon={<HelpCircle className="w-3.5 h-3.5 text-primary" />}
                onClick={() => navigate('/help')}
              >
                Help
              </Button>
              {isSample && (
                <>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Download className="w-3.5 h-3.5" />}
                    onClick={() => alert('PDF report generation triggered via MCP.')}
                    className="hidden xl:inline-flex"
                  >
                    Export PDF
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={<PlayCircle className="w-3.5 h-3.5" />}
                    onClick={() => navigate(samplePath('/run', { trigger: 'true' }))}
                    className="hidden sm:inline-flex"
                  >
                    Run pulse
                  </Button>
                </>
              )}
            </div>
          </div>
        </header>

        <main className="flex-1 w-full max-w-[1280px] mx-auto p-4 sm:p-6 lg:p-8">
          <Outlet context={context} />
        </main>
      </div>

      <nav
        aria-label="Mobile"
        className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-surface-dim/95 backdrop-blur-xl border-t border-border flex items-center justify-around z-40 px-1 pb-safe"
      >
        {[overviewItem, MANAGE_ITEM, ...SAMPLE_ITEMS].map((item) => (
          <NavLink key={item.label} to={item.to} end={item.to === '/'} className={({ isActive }) => bottomLink(isActive)}>
            <div className="text-current mb-0.5">{item.icon}</div>
            <span className="font-mono tracking-tight leading-none text-center">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};
