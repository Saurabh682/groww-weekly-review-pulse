import React, { useEffect, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { Theme, Sentiment, ScenarioType } from '../../data/types';
import { pulseApi } from '../../data/mockApi';
import { PulseRing } from '../../pulseline/PulseRing';
import { PulseNode } from '../../pulseline/PulseNode';
import { ThemeDrawer } from './ThemeDrawer';
import { Card } from '../../components/Card';
import { Chip } from '../../components/Chip';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Skeleton } from '../../components/Skeleton';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import {
  ChevronRight,
  TrendingUp,
  TrendingDown,
  ArrowUpDown,
  Filter,
  Search,
  SlidersHorizontal,
  Lightbulb,
  Star,
  RefreshCw,
} from 'lucide-react';
import { formatRating, formatShare, formatTrend } from '../../lib/format';

export const ThemesPage: React.FC = () => {
  const { currentScenario } = useOutletContext<{ currentScenario: ScenarioType }>();
  const [searchParams] = useSearchParams();

  const [themes, setThemes] = useState<Theme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterSentiment, setFilterSentiment] = useState<Sentiment | 'all'>('all');
  const [sortBy, setSortBy] = useState<'priority' | 'share' | 'rating'>('priority');
  const [mobileTab, setMobileTab] = useState<'all' | 'inPulse' | 'watchlist'>('all');
  const [selectedTheme, setSelectedTheme] = useState<Theme | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const loadThemes = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await pulseApi.getThemes(undefined, currentScenario);
      setThemes(data);

      const themeIdFromUrl = searchParams.get('themeId');
      if (themeIdFromUrl) {
        const matched = data.find((t) => t.id === themeIdFromUrl);
        if (matched) {
          setSelectedTheme(matched);
          setIsDrawerOpen(true);
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch theme clusters');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadThemes();
  }, [currentScenario]);

  const filteredThemes = themes.filter((theme) => {
    if (filterSentiment !== 'all' && theme.sentiment !== filterSentiment) {
      return false;
    }
    if (mobileTab === 'inPulse' && !theme.inPulse) {
      return false;
    }
    if (mobileTab === 'watchlist' && theme.inPulse) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchLabel = theme.label.toLowerCase().includes(q);
      const matchSummary = theme.summary.toLowerCase().includes(q);
      if (!matchLabel && !matchSummary) return false;
    }
    return true;
  });

  const sortedThemes = [...filteredThemes].sort((a, b) => {
    if (sortBy === 'priority') return b.priorityScore - a.priorityScore;
    if (sortBy === 'share') return b.sharePct - a.sharePct;
    if (sortBy === 'rating') return a.avgRating - b.avgRating;
    return 0;
  });

  const handleOpenTheme = (theme: Theme) => {
    setSelectedTheme(theme);
    setIsDrawerOpen(true);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8">
        <ErrorState
          title="Theme Explorer Error"
          message={error}
          onRetry={loadThemes}
        />
      </div>
    );
  }

  if (themes.length === 0) {
    return (
      <div className="py-8">
        <EmptyState
          title="No Themes Discovered"
          description="Theme clustering has not run yet or no reviews were found for this cycle."
        />
      </div>
    );
  }

  const inPulseCount = themes.filter((t) => t.inPulse).length;
  const watchlistCount = themes.filter((t) => !t.inPulse).length;

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* 1. Header with Title and Cluster Badge */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">
              Themes Explorer
            </h1>
            <Badge variant="teal" className="py-1">
              {themes.length} of 5 clusters active
            </Badge>
          </div>
          <p className="text-xs text-text-secondary mt-1 font-mono">
            Unsupervised review clustering mapped by sentiment share and operational priority score.
          </p>
        </div>

        {/* Mobile 5/5 theme cap pill */}
        <div className="inline-flex sm:hidden items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary-tint border border-primary-border text-[11px] font-mono font-semibold text-primary">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          <span>5/5 theme cap</span>
        </div>
      </div>

      {/* 2. Mobile Quick Search & Filter Bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 flex items-center gap-2 px-3 py-2 bg-[#162238] border border-[#2a3d5d] rounded-xl shadow-sm focus-within:border-primary/60 transition-colors">
          <Search className="w-4 h-4 text-text-muted shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search clusters, phrases, or tags..."
            className="w-full bg-transparent text-xs text-white placeholder:text-text-muted focus:outline-none font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="text-xs text-text-muted hover:text-white font-mono px-1"
            >
              ✕
            </button>
          )}
        </div>

        <button
          onClick={() => {
            // cycle sentiment filter
            const modes: (Sentiment | 'all')[] = ['all', 'critical', 'friction', 'positive'];
            const nextIdx = (modes.indexOf(filterSentiment) + 1) % modes.length;
            setFilterSentiment(modes[nextIdx]);
          }}
          className="w-10 h-10 rounded-xl bg-[#162238] border border-[#2a3d5d] flex items-center justify-center text-text-muted hover:text-white transition-colors relative shrink-0 active:scale-95"
          title="Toggle sentiment filter"
        >
          <SlidersHorizontal className="w-4 h-4" />
          {filterSentiment !== 'all' && (
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary shadow-glow-teal-sm" />
          )}
        </button>
      </div>

      {/* 3. Radial Pulse Ring & Leaderboard Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Orbital Pulse Ring (5 cols) */}
        <Card className="lg:col-span-5 flex flex-col items-center justify-center p-4 sm:p-6 bg-[#162238]/90 border border-[#2a3d5d] shadow-card relative overflow-hidden">
          <div className="w-full flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted">
              Cluster Orbit Map
            </span>
            <span className="text-[10px] font-mono text-primary flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              Live Dynamics
            </span>
          </div>

          <div className="w-full flex justify-center py-1">
            <PulseRing
              themes={themes}
              selectedThemeId={selectedTheme?.id}
              onSelectTheme={handleOpenTheme}
            />
          </div>

          {/* Orbit legend & micro controls */}
          <div className="w-full flex items-center justify-between pt-3 border-t border-[#1e293b] text-[11px] font-mono text-text-muted">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-primary" />
                Growth
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-friction" />
                Friction
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-critical" />
                Risk
              </span>
            </div>
            <button
              onClick={loadThemes}
              className="inline-flex items-center gap-1 text-primary hover:underline font-semibold"
            >
              <span>Re-cluster</span>
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>
        </Card>

        {/* Top Priority Leaderboard (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted">
            Cluster Priority Leaderboard
          </div>

          {themes.slice(0, 3).map((theme) => (
            <Card
              key={theme.id}
              variant="interactive"
              onClick={() => handleOpenTheme(theme)}
              className="p-4 flex items-center justify-between gap-4 bg-[#162238]/90 border border-[#2a3d5d] hover:border-primary/50 hover:bg-[#1b2a47]"
            >
              <div className="flex items-center gap-3 min-w-0">
                <PulseNode sharePct={theme.sharePct} sentiment={theme.sentiment} rank={theme.rank} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold font-display text-sm text-white truncate">
                      {theme.label}
                    </span>
                    {theme.inPulse && <Badge variant="teal">Top 3 Pulse</Badge>}
                  </div>
                  <div className="text-xs text-text-secondary truncate mt-0.5">
                    {theme.summary}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0">
                <div className="text-right">
                  <div className="text-xs font-mono font-bold text-white">{formatShare(theme.sharePct)}</div>
                  <div className="text-[10px] text-text-muted font-mono">{theme.reviewCount} revs</div>
                </div>
                <ChevronRight className="w-4 h-4 text-text-muted" />
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* 4. Segmented Control / Tabs (Stitch Mobile Pattern) */}
      <div className="w-full bg-[#162238] p-1 rounded-xl flex items-center gap-1 border border-[#2a3d5d]">
        <button
          onClick={() => setMobileTab('all')}
          className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-mono font-semibold transition-all text-center flex items-center justify-center gap-1.5 ${
            mobileTab === 'all'
              ? 'bg-primary text-[#0b111e] shadow-glow-teal-sm'
              : 'text-text-muted hover:text-white'
          }`}
        >
          <span>All Clusters</span>
          <span className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-bold ${
            mobileTab === 'all' ? 'bg-[#0b111e]/20 text-[#0b111e]' : 'bg-[#1e293b] text-text-muted'
          }`}>
            {themes.length}
          </span>
        </button>

        <button
          onClick={() => setMobileTab('inPulse')}
          className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-mono font-semibold transition-all text-center flex items-center justify-center gap-1.5 ${
            mobileTab === 'inPulse'
              ? 'bg-primary text-[#0b111e] shadow-glow-teal-sm'
              : 'text-text-muted hover:text-white'
          }`}
        >
          <span>Top Ranked (In Pulse)</span>
          <span className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-bold ${
            mobileTab === 'inPulse' ? 'bg-[#0b111e]/20 text-[#0b111e]' : 'bg-[#1e293b] text-text-muted'
          }`}>
            {inPulseCount}
          </span>
        </button>

        <button
          onClick={() => setMobileTab('watchlist')}
          className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-mono font-semibold transition-all text-center flex items-center justify-center gap-1.5 ${
            mobileTab === 'watchlist'
              ? 'bg-primary text-[#0b111e] shadow-glow-teal-sm'
              : 'text-text-muted hover:text-white'
          }`}
        >
          <span>Watchlist</span>
          <span className={`w-4 h-4 rounded-full text-[10px] flex items-center justify-center font-bold ${
            mobileTab === 'watchlist' ? 'bg-[#0b111e]/20 text-[#0b111e]' : 'bg-[#1e293b] text-text-muted'
          }`}>
            {watchlistCount}
          </span>
        </button>
      </div>

      {/* 5. Mobile Theme Cards List (< md screens) */}
      <div className="md:hidden space-y-3">
        {sortedThemes.map((theme) => {
          const isCritical = theme.sentiment === 'critical';
          const isFriction = theme.sentiment === 'friction';
          const badgeVariant = isCritical ? 'coral' : isFriction ? 'amber' : 'teal';

          return (
            <Card
              key={`mob-${theme.id}`}
              variant="interactive"
              onClick={() => handleOpenTheme(theme)}
              className="p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col gap-3 active:scale-[0.99] transition-transform"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-[#1e293b] border border-[#2a3d5d] text-primary flex items-center justify-center font-mono text-xs font-bold">
                    #{theme.rank}
                  </div>
                  <div>
                    <h2 className="font-bold font-display text-sm text-white leading-tight">
                      {theme.label}
                    </h2>
                    <p className="text-[11px] text-text-secondary mt-0.5 line-clamp-1">
                      {theme.summary}
                    </p>
                  </div>
                </div>
                {theme.inPulse ? (
                  <Badge variant={badgeVariant}>In Pulse</Badge>
                ) : (
                  <Badge variant="gray">Watchlist</Badge>
                )}
              </div>

              {/* 3-Col Key Metrics */}
              <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-[#0e1726] border border-[#1e293b]">
                <div className="flex flex-col">
                  <span className="text-[10px] font-mono text-text-muted">Share</span>
                  <span className="font-mono text-sm font-bold text-white">{formatShare(theme.sharePct)}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] font-mono text-text-muted">Reviews</span>
                  <span className="font-mono text-sm font-bold text-white">{theme.reviewCount}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[10px] font-mono text-text-muted">Rating</span>
                  <div className="flex items-center gap-1 font-mono text-sm font-bold text-amber-400">
                    <span>{formatRating(theme.avgRating)}</span>
                    <Star className="w-3 h-3 fill-amber-400" />
                  </div>
                </div>
              </div>

              {/* Volume & Sentiment Pill Bar */}
              {(() => {
                const negPct = theme.negShare > 1 ? theme.negShare : theme.negShare * 100;
                const posPct = Math.max(5, Math.min(95, Math.round(100 - negPct)));
                return (
                  <>
                    <div className="w-full bg-[#0e1726] h-1.5 rounded-full overflow-hidden flex border border-[#1e293b]">
                      <div
                        className="bg-primary h-full"
                        style={{ width: `${posPct}%` }}
                      />
                      <div
                        className="bg-critical h-full"
                        style={{ width: `${100 - posPct}%` }}
                      />
                    </div>

                    <div className="flex justify-between items-center text-[11px] font-mono text-text-muted">
                      <span className="text-primary font-semibold">
                        {posPct}% Positive Feedback
                      </span>
                      <span className="text-text-secondary flex items-center gap-0.5">
                        Tap to view reviews &rarr;
                      </span>
                    </div>
                  </>
                );
              })()}
            </Card>
          );
        })}
      </div>

      {/* 6. Desktop Themes Data Table (md:block) */}
      <div className="hidden md:block">
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 mb-4 border-t border-[#1e293b]">
          {/* Filter Chips */}
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-text-muted mr-1" />
            {(['all', 'critical', 'friction', 'positive'] as const).map((sent) => (
              <button
                key={sent}
                onClick={() => setFilterSentiment(sent)}
                className={`px-3 py-1 rounded-full text-xs font-mono transition-colors ${
                  filterSentiment === sent
                    ? 'bg-primary text-[#0b111e] font-bold shadow-glow-teal-sm'
                    : 'bg-[#162238] border border-[#2a3d5d] text-text-secondary hover:text-white hover:bg-[#1b2a47]'
                }`}
              >
                {sent.charAt(0).toUpperCase() + sent.slice(1)}
              </button>
            ))}
          </div>

          {/* Sort selector */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-xs text-text-secondary font-mono">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="text-xs bg-[#162238] border border-[#2a3d5d] rounded-lg px-2.5 py-1 text-white font-mono focus:outline-none focus:border-primary cursor-pointer"
            >
              <option value="priority">Priority Score (Highest)</option>
              <option value="share">Review Share (Highest)</option>
              <option value="rating">Avg Rating (Lowest friction first)</option>
            </select>
          </div>
        </div>

        <Card className="p-0 overflow-hidden bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1e293b] bg-[#0e1726]/90 text-[11px] font-mono font-bold text-text-muted uppercase tracking-wider">
                  <th className="py-3 px-4">Rank</th>
                  <th className="py-3 px-4">Cluster Theme & Summary</th>
                  <th className="py-3 px-4">Sentiment</th>
                  <th className="py-3 px-4 text-right">Review Share</th>
                  <th className="py-3 px-4 text-center">Avg Rating</th>
                  <th className="py-3 px-4 text-center">Trend (4w)</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e293b]">
                {sortedThemes.map((theme) => {
                  return (
                    <tr
                      key={theme.id}
                      onClick={() => handleOpenTheme(theme)}
                      className="hover:bg-[#1b2a47] hover:border-l-2 hover:border-l-primary transition-all cursor-pointer group"
                    >
                      {/* Rank */}
                      <td className="py-3.5 px-4 font-mono font-bold text-white">
                        #{theme.rank}
                      </td>

                      {/* Theme Label & Summary */}
                      <td className="py-3.5 px-4 max-w-sm">
                        <div className="flex items-center gap-2">
                          <span className="font-bold font-display text-white text-xs group-hover:text-primary transition-colors">
                            {theme.label}
                          </span>
                          {theme.inPulse && (
                            <Badge variant="teal">In Pulse</Badge>
                          )}
                        </div>
                        <p className="text-[11px] text-text-secondary truncate mt-0.5">
                          {theme.summary}
                        </p>
                      </td>

                      {/* Sentiment */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <Chip
                          size="sm"
                          variant={theme.sentiment}
                          label={theme.sentiment}
                        />
                      </td>

                      {/* Review Share % */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono">
                        <div className="font-bold text-white">{formatShare(theme.sharePct)}</div>
                        <div className="text-[10px] text-text-muted">{theme.reviewCount} revs</div>
                      </td>

                      {/* Avg Rating */}
                      <td className="py-3.5 px-4 text-center font-mono font-bold text-amber-400 whitespace-nowrap">
                        {formatRating(theme.avgRating)}
                      </td>

                      {/* 4-week trend sparkline */}
                      <td className="py-3.5 px-4 text-center">
                        <div className="flex items-center justify-center gap-1 font-mono">
                          {theme.trendVsLastWeek > 0 ? (
                            <TrendingUp className="w-3.5 h-3.5 text-critical" />
                          ) : (
                            <TrendingDown className="w-3.5 h-3.5 text-primary" />
                          )}
                          <span className="text-[11px] font-bold">
                            {formatTrend(theme.trendVsLastWeek)}
                          </span>
                        </div>
                      </td>

                      {/* Action */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenTheme(theme);
                          }}
                        >
                          Sample reviews
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* 7. Bottom Floating Auto-Cluster Recommendation (Stitch Mobile Pattern) */}
      <div className="p-4 rounded-xl bg-[#162238] border border-[#2a3d5d] flex items-center justify-between gap-3 shadow-card">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-full bg-primary-tint border border-primary-border text-primary flex items-center justify-center shrink-0">
            <Lightbulb className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-bold font-display text-white">Auto-Cluster Recommendation</p>
            <p className="text-[11px] text-text-secondary truncate font-mono">
              DigiLocker friction contributes to 44% of week-over-week 1-star drops.
            </p>
          </div>
        </div>
        <button
          onClick={() => {
            const digi = themes.find((t) => t.id.includes('kyc') || t.label.includes('DigiLocker') || t.rank === 2);
            if (digi) handleOpenTheme(digi);
          }}
          className="px-3 py-1.5 rounded-lg bg-[#0e1726] border border-[#1e293b] text-white hover:text-primary font-mono text-xs font-semibold shrink-0 transition-colors"
        >
          Review
        </button>
      </div>

      {/* Slide-over Theme Sample Reviews Drawer */}
      <ThemeDrawer
        theme={selectedTheme}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
};
