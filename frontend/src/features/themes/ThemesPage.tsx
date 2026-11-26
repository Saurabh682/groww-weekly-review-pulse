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
import { SearchField } from '../../components/SearchField';
import { SectionTitle } from '../../components/SectionTitle';
import { Skeleton } from '../../components/Skeleton';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import {
  ChevronRight,
  TrendingUp,
  TrendingDown,
  ArrowUpDown,
  Filter,
  SlidersHorizontal,
  Lightbulb,
  Star,
  RefreshCw,
} from 'lucide-react';
import { formatRating, formatShare, formatTrend } from '../../lib/format';

const SENTIMENT_FILTERS: (Sentiment | 'all')[] = ['all', 'critical', 'friction', 'positive'];

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
        <ErrorState headingLevel={2}
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
        <EmptyState headingLevel={2}
          title="No Themes Discovered"
          description="Theme clustering has not run yet or no reviews were found for this cycle."
        />
      </div>
    );
  }

  const inPulseCount = themes.filter((t) => t.inPulse).length;
  const watchlistCount = themes.filter((t) => !t.inPulse).length;

  return (
    <div className="space-y-8 animate-fade-in">
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

        <Chip
          variant="positive"
          size="sm"
          label="5/5 theme cap"
          icon={<span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />}
          className="sm:hidden"
        />
      </div>

      <div className="flex items-center gap-2">
        <SearchField
          label="Search themes"
          placeholder="Search clusters, phrases, or tags..."
          value={searchQuery}
          onChange={setSearchQuery}
          className="flex-1"
        />

        <Button
          variant="secondary"
          aria-label="Change sentiment filter"
          className="relative shrink-0"
          onClick={() => setFilterSentiment(SENTIMENT_FILTERS[(SENTIMENT_FILTERS.indexOf(filterSentiment) + 1) % SENTIMENT_FILTERS.length])}
        >
          <SlidersHorizontal className="w-4 h-4" />
          {filterSentiment !== 'all' && (
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-primary shadow-glow-teal-sm" />
          )}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        <Card padding="roomy" className="lg:col-span-5 flex flex-col items-center justify-center relative overflow-hidden">
          <div className="w-full flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted">
              Cluster Orbit Map
            </span>
            <span className="text-3xs font-mono text-primary flex items-center gap-1">
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

          <div className="w-full flex items-center justify-between pt-3 border-t border-border text-2xs font-mono text-text-muted">
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
            <Button variant="ghost" size="sm" icon={<RefreshCw className="w-3 h-3" />} onClick={loadThemes}>
              Re-cluster
            </Button>
          </div>
        </Card>

        <div className="lg:col-span-7 space-y-3">
          <SectionTitle>Cluster Priority Leaderboard</SectionTitle>

          {themes.slice(0, 3).map((theme) => (
            <Card
              key={theme.id}
              variant="interactive"
              onClick={() => handleOpenTheme(theme)} padding="tight" className="flex items-center justify-between gap-4"
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
                  <div className="text-3xs text-text-muted font-mono">{theme.reviewCount} revs</div>
                </div>
                <ChevronRight className="w-4 h-4 text-text-muted" />
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div className="w-full flex items-center gap-1" role="group" aria-label="Theme list">
        {[
          { id: 'all' as const, label: 'All Clusters', count: themes.length },
          { id: 'inPulse' as const, label: 'Top Ranked (In Pulse)', count: inPulseCount },
          { id: 'watchlist' as const, label: 'Watchlist', count: watchlistCount },
        ].map((tab) => (
          <Button
            key={tab.id}
            size="sm"
            variant={mobileTab === tab.id ? 'primary' : 'ghost'}
            aria-pressed={mobileTab === tab.id}
            onClick={() => setMobileTab(tab.id)}
            className="flex-1"
          >
            {tab.label} ({tab.count})
          </Button>
        ))}
      </div>

      <div className="md:hidden space-y-3">
        {sortedThemes.map((theme) => {
          const isCritical = theme.sentiment === 'critical';
          const isFriction = theme.sentiment === 'friction';
          const badgeVariant = isCritical ? 'coral' : isFriction ? 'amber' : 'teal';

          return (
            <Card
              key={`mob-${theme.id}`}
              variant="interactive"
              onClick={() => handleOpenTheme(theme)} padding="tight" className="flex flex-col gap-3 active:scale-[0.99]"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-border border border-border-subtle text-primary flex items-center justify-center font-mono text-xs font-bold">
                    #{theme.rank}
                  </div>
                  <div>
                    <h3 className="font-bold font-display text-sm text-white leading-tight">
                      {theme.label}
                    </h3>
                    <p className="text-2xs text-text-secondary mt-0.5 line-clamp-1">
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

              <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-sidebar border border-border">
                <div className="flex flex-col">
                  <span className="text-3xs font-mono text-text-muted">Share</span>
                  <span className="font-mono text-sm font-bold text-white">{formatShare(theme.sharePct)}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-3xs font-mono text-text-muted">Reviews</span>
                  <span className="font-mono text-sm font-bold text-white">{theme.reviewCount}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-3xs font-mono text-text-muted">Rating</span>
                  <div className="flex items-center gap-1 font-mono text-sm font-bold text-friction-dark">
                    <span>{formatRating(theme.avgRating)}</span>
                    <Star className="w-3 h-3 fill-friction-dark" />
                  </div>
                </div>
              </div>

              {(() => {
                const negPct = theme.negShare > 1 ? theme.negShare : theme.negShare * 100;
                const posPct = Math.max(5, Math.min(95, Math.round(100 - negPct)));
                return (
                  <>
                    <div className="w-full bg-sidebar h-1.5 rounded-full overflow-hidden flex border border-border">
                      <div
                        className="bg-primary h-full"
                        style={{ width: `${posPct}%` }}
                      />
                      <div
                        className="bg-critical h-full"
                        style={{ width: `${100 - posPct}%` }}
                      />
                    </div>

                    <div className="flex justify-between items-center text-2xs font-mono text-text-muted">
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

      <div className="hidden md:block">
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 mb-4 border-t border-border">
          <div className="flex items-center gap-2" role="group" aria-label="Sentiment filter">
            <Filter className="w-3.5 h-3.5 text-text-muted mr-1" />
            {SENTIMENT_FILTERS.map((sent) => (
              <Button
                key={sent}
                size="sm"
                variant={filterSentiment === sent ? 'primary' : 'secondary'}
                aria-pressed={filterSentiment === sent}
                onClick={() => setFilterSentiment(sent)}
              >
                {sent.charAt(0).toUpperCase() + sent.slice(1)}
              </Button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-xs text-text-secondary font-mono">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              aria-label="Sort themes"
              className="text-xs bg-surface border border-border-subtle rounded-lg px-2.5 py-1 text-white font-mono focus:outline-none focus:border-primary cursor-pointer"
            >
              <option value="priority">Priority Score (Highest)</option>
              <option value="share">Review Share (Highest)</option>
              <option value="rating">Avg Rating (Lowest friction first)</option>
            </select>
          </div>
        </div>

        <Card padding="none" className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-sidebar/90 text-2xs font-mono font-bold text-text-muted uppercase tracking-wider">
                  <th className="py-3 px-4">Rank</th>
                  <th className="py-3 px-4">Cluster Theme & Summary</th>
                  <th className="py-3 px-4">Sentiment</th>
                  <th className="py-3 px-4 text-right">Review Share</th>
                  <th className="py-3 px-4 text-center">Avg Rating</th>
                  <th className="py-3 px-4 text-center">Trend (4w)</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {sortedThemes.map((theme) => {
                  return (
                    <tr
                      key={theme.id}
                      onClick={() => handleOpenTheme(theme)}
                      className="hover:bg-surface-elevated hover:border-l-2 hover:border-l-primary transition-all cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 font-mono font-bold text-white">
                        #{theme.rank}
                      </td>

                      <td className="py-3.5 px-4 max-w-sm">
                        <div className="flex items-center gap-2">
                          <span className="font-bold font-display text-white text-xs group-hover:text-primary transition-colors">
                            {theme.label}
                          </span>
                          {theme.inPulse && (
                            <Badge variant="teal">In Pulse</Badge>
                          )}
                        </div>
                        <p className="text-2xs text-text-secondary truncate mt-0.5">
                          {theme.summary}
                        </p>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <Chip
                          size="sm"
                          variant={theme.sentiment}
                          label={theme.sentiment}
                        />
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono">
                        <div className="font-bold text-white">{formatShare(theme.sharePct)}</div>
                        <div className="text-3xs text-text-muted">{theme.reviewCount} revs</div>
                      </td>

                      <td className="py-3.5 px-4 text-center font-mono font-bold text-friction-dark whitespace-nowrap">
                        {formatRating(theme.avgRating)}
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <div className="flex items-center justify-center gap-1 font-mono">
                          {theme.trendVsLastWeek > 0 ? (
                            <TrendingUp className="w-3.5 h-3.5 text-critical" />
                          ) : (
                            <TrendingDown className="w-3.5 h-3.5 text-primary" />
                          )}
                          <span className="text-2xs font-bold">
                            {formatTrend(theme.trendVsLastWeek)}
                          </span>
                        </div>
                      </td>

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

      <Card padding="tight" className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-full bg-primary-tint border border-primary-border text-primary flex items-center justify-center shrink-0">
            <Lightbulb className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-bold font-display text-white">Auto-Cluster Recommendation</p>
            <p className="text-2xs text-text-secondary truncate font-mono">
              DigiLocker friction contributes to 44% of week-over-week 1-star drops.
            </p>
          </div>
        </div>
        <Button
          variant="secondary"
          size="sm"
          className="shrink-0"
          onClick={() => {
            const digi = themes.find((t) => t.id.includes('kyc') || t.label.includes('DigiLocker') || t.rank === 2);
            if (digi) handleOpenTheme(digi);
          }}
        >
          Review
        </Button>
      </Card>

      <ThemeDrawer
        theme={selectedTheme}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
};
