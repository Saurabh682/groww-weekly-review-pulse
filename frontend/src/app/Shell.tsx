import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Activity,
  Layers,
  PlayCircle,
  UploadCloud,
  HelpCircle,
  Calendar,
  ChevronDown,
  Download,
  CheckCircle2,
  SlidersHorizontal,
} from 'lucide-react';
import { Badge } from '../components/Badge';
import { Button } from '../components/Button';
import { ScenarioType } from '../data/types';

export const Shell: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Read scenario from query param
  const queryParams = new URLSearchParams(location.search);
  const currentScenario = (queryParams.get('scenario') as ScenarioType) || 'ok';

  const [selectedWeek, setSelectedWeek] = useState('Week of 9 Nov 2026');
  const [isWeekDropdownOpen, setIsWeekDropdownOpen] = useState(false);

  const availableWeeks = [
    'Week of 9 Nov 2026',
    'Week of 2 Nov 2026',
    'Week of 26 Oct 2026',
    'Week of 19 Oct 2026',
  ];

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

  const navItems = [
    { to: '/', label: 'Weekly Pulse', icon: <Activity className="w-4 h-4" /> },
    { to: '/themes', label: 'Themes', icon: <Layers className="w-4 h-4" /> },
    { to: '/run', label: 'Run & Publish', icon: <PlayCircle className="w-4 h-4" /> },
    { to: '/import', label: 'Data Import', icon: <UploadCloud className="w-4 h-4" /> },
    { to: '/help', label: 'Help', icon: <HelpCircle className="w-4 h-4" /> },
  ];

  const getNavPath = (path: string) => {
    return currentScenario !== 'ok' ? `${path}?scenario=${currentScenario}` : path;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row text-text-primary antialiased selection:bg-primary selection:text-[#0b111e]">
      {/* Desktop Left Sidebar (240px) */}
      <aside className="hidden md:flex flex-col w-60 bg-[#0d1320] border-r border-[#1e293b] shrink-0 select-none">
        {/* Brand / Logo */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-[#1e293b]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-[#0b111e] shadow-glow-teal-sm">
              <Activity className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <div className="font-bold font-display text-sm leading-tight tracking-tight text-white">
                Groww Pulse
              </div>
              <div className="text-[10px] font-mono text-text-secondary tracking-wider">
                Weekly Review Intel
              </div>
            </div>
          </div>
        </div>

        {/* Internal Intel Pill */}
        <div className="px-5 pt-4 pb-2">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#162238] border border-[#2a3d5d] text-[10px] font-mono font-semibold text-text-secondary">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            <span>INTERNAL INTEL • V2.4</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1.5 flex-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={getNavPath(item.to)}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs transition-all duration-150 ${
                  isActive
                    ? 'bg-primary-tint text-primary font-bold border border-primary-border shadow-glow-teal-sm'
                    : 'text-text-secondary hover:text-white hover:bg-[#162238]/60'
                }`
              }
            >
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Scenario Simulator */}
        <div className="p-3.5 border-t border-[#1e293b] bg-[#080e1b]/60">
          <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-text-muted mb-2">
            <SlidersHorizontal className="w-3 h-3 text-primary" />
            <span>Scenario Simulator</span>
          </div>
          <select
            value={currentScenario}
            onChange={(e) => handleScenarioChange(e.target.value as ScenarioType)}
            className="w-full text-xs bg-[#162238] border border-[#2a3d5d] rounded-lg px-2.5 py-1.5 text-text-primary font-medium focus:outline-none focus:border-primary cursor-pointer"
          >
            <option value="ok">Normal (ok)</option>
            <option value="empty">Empty State</option>
            <option value="error">API Error (500)</option>
            <option value="validation-failed">Validation Failed (Flatline)</option>
            <option value="low-coverage">Low Coverage Wave</option>
          </select>
        </div>

        {/* Footer info matching dark design */}
        <div className="p-3.5 border-t border-[#1e293b] text-[10px] font-mono text-text-muted space-y-1">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Play Store Sync:
            </span>
            <span className="text-white">Live (12m ago)</span>
          </div>
          <div className="flex items-center justify-between text-text-muted/70">
            <span>Docs & Schema</span>
            <span>v2.4.1</span>
          </div>
        </div>
      </aside>

      {/* Main Body Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-20 md:pb-0">
        {/* Top Header Bar */}
        <header className="bg-[#0d1320] border-b border-[#1e293b] px-4 sm:px-6 shrink-0 sticky top-0 z-30 backdrop-blur-md bg-[#0d1320]/95">
          {/* Mobile Top Row */}
          <div className="flex md:hidden items-center justify-between h-14 border-b border-[#1e293b]/60">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center text-[#0b111e] shadow-glow-teal-sm">
                <Activity className="w-4 h-4 stroke-[2.5]" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold font-display text-sm text-white">
                  Groww <span className="text-primary">Pulse</span>
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#162238] border border-[#2a3d5d] text-[10px] font-mono text-text-secondary">
                  <span className="w-1 h-1 rounded-full bg-primary" />
                  Google Play only
                </span>
              </div>
            </div>

            {/* Quick Run Action & Help Button */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => navigate(getNavPath('/help'))}
                className="px-2 py-1 rounded-lg bg-[#162238] border border-[#2a3d5d] text-xs font-mono text-teal-400 hover:text-white flex items-center gap-1 transition-colors"
                title="Help & Guide"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Help</span>
              </button>
              <Button
                variant="primary"
                size="sm"
                icon={<PlayCircle className="w-3.5 h-3.5 text-[#0b111e]" />}
                onClick={() => navigate(getNavPath('/run?trigger=true'))}
                className="py-1 px-2.5 text-xs"
              >
                Run pulse
              </Button>
            </div>
          </div>

          {/* Mobile Sub Row: Week Selector & Active Page Indicator */}
          <div className="flex md:hidden items-center justify-between h-11">
            <div className="relative">
              <button
                onClick={() => setIsWeekDropdownOpen(!isWeekDropdownOpen)}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#162238] border border-[#2a3d5d] text-xs font-mono font-medium text-white active:bg-[#1b2a47]"
                aria-expanded={isWeekDropdownOpen}
              >
                <Calendar className="w-3 h-3 text-primary" />
                <span>{selectedWeek}</span>
                <ChevronDown className="w-3 h-3 text-text-muted" />
              </button>

              {isWeekDropdownOpen && (
                <div className="absolute left-0 mt-1 w-52 bg-[#162238] border border-[#2a3d5d] rounded-lg shadow-drawer py-1 z-50 animate-fade-in">
                  {availableWeeks.map((week) => (
                    <button
                      key={week}
                      onClick={() => {
                        setSelectedWeek(week);
                        setIsWeekDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                        selectedWeek === week
                          ? 'bg-primary-tint text-primary font-bold'
                          : 'text-text-primary hover:bg-[#1b2a47]'
                      }`}
                    >
                      {week}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Active Route Pill */}
            <span className="text-[11px] font-mono uppercase tracking-wider text-text-muted px-2 py-0.5 rounded bg-[#0e1726] border border-[#1e293b]">
              {location.pathname === '/'
                ? 'Weekly Pulse'
                : location.pathname.startsWith('/themes')
                ? 'Themes'
                : location.pathname.startsWith('/run')
                ? 'Run & Publish'
                : location.pathname.startsWith('/import')
                ? 'Data Import'
                : location.pathname.startsWith('/help')
                ? 'Help'
                : 'Groww Pulse'}
            </span>
          </div>

          {/* Desktop Single Row */}
          <div className="hidden md:flex items-center justify-between h-16">
            {/* Left section: Week selector + Dark filters */}
            <div className="flex items-center gap-2.5">
              {/* Week Selector Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setIsWeekDropdownOpen(!isWeekDropdownOpen)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-[#162238] border border-[#2a3d5d] rounded-lg text-xs font-semibold text-white hover:border-primary/50 transition-colors"
                  aria-expanded={isWeekDropdownOpen}
                >
                  <Calendar className="w-3.5 h-3.5 text-primary" />
                  <span>{selectedWeek}</span>
                  <ChevronDown className="w-3 h-3 text-text-muted" />
                </button>

                {isWeekDropdownOpen && (
                  <div className="absolute left-0 mt-1 w-52 bg-[#162238] border border-[#2a3d5d] rounded-lg shadow-drawer py-1 z-40 animate-fade-in">
                    {availableWeeks.map((week) => (
                      <button
                        key={week}
                        onClick={() => {
                          setSelectedWeek(week);
                          setIsWeekDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 text-xs transition-colors ${
                          selectedWeek === week
                            ? 'bg-primary-tint text-primary font-bold'
                            : 'text-text-primary hover:bg-[#1b2a47]'
                        }`}
                      >
                        {week}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Google Play only Badge */}
              <Badge variant="teal" className="gap-1.5 py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-primary" />
                Google Play only
              </Badge>

              {/* All Products Badge */}
              <Badge variant="gray" className="hidden lg:inline-flex py-1">
                All Products (Stocks, MF, F&O)
              </Badge>

              {/* Generated Today Badge */}
              <div className="hidden xl:inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#162238] border border-[#2a3d5d] text-[11px] font-mono text-text-muted">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Generated Today, 08:30 AM</span>
              </div>
            </div>

            {/* Right section: Help, Export PDF & Run pulse button */}
            <div className="flex items-center gap-2.5">
              <Button
                variant="secondary"
                size="sm"
                icon={<HelpCircle className="w-3.5 h-3.5 text-teal-400" />}
                onClick={() => navigate(getNavPath('/help'))}
                className="text-xs"
              >
                Help
              </Button>

              <Button
                variant="secondary"
                size="sm"
                icon={<Download className="w-3.5 h-3.5" />}
                onClick={() => alert('PDF report generation triggered via MCP.')}
                className="hidden sm:inline-flex text-xs"
              >
                Export PDF
              </Button>

              <Button
                variant="primary"
                size="sm"
                icon={<PlayCircle className="w-3.5 h-3.5 text-[#0b111e]" />}
                onClick={() => navigate(getNavPath('/run?trigger=true'))}
              >
                Run pulse
              </Button>
            </div>
          </div>
        </header>

        {/* Page Content Container (max 1280px) */}
        <main className="flex-1 w-full max-w-[1280px] mx-auto p-4 sm:p-6 lg:p-8">
          <Outlet context={{ currentScenario, selectedWeek }} />
        </main>
      </div>

      {/* Mobile Bottom Navigation (< 768px) with Stitch Design */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-[#0d1320]/95 backdrop-blur-xl border-t border-[#1e293b] flex items-center justify-around z-40 px-1 pb-safe shadow-[0_-2px_12px_rgba(0,0,0,0.5)]">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={getNavPath(item.to)}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center min-w-[64px] h-12 py-1 px-2 text-[10px] font-medium transition-all ${
                isActive
                  ? 'text-primary font-bold scale-105'
                  : 'text-text-muted hover:text-white'
              }`
            }
          >
            <div className="text-current mb-0.5">
              {item.icon}
            </div>
            <span className="font-mono tracking-tight leading-none">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};
