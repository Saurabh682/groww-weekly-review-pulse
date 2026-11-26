import React from 'react';
import { Theme } from '../../data/types';
import { Card } from '../../components/Card';
import { Badge } from '../../components/Badge';
import { formatRating, formatTrend, formatShare } from '../../lib/format';
import { TrendingUp, TrendingDown, Star } from 'lucide-react';

interface ThemeCardProps {
  theme: Theme;
  onExplore?: (theme: Theme) => void;
}

export const ThemeCard: React.FC<ThemeCardProps> = ({ theme, onExplore }) => {
  const isCritical = theme.sentiment === 'critical';
  const isFriction = theme.sentiment === 'friction';

  const badgeVariant = isCritical ? 'coral' : isFriction ? 'amber' : 'teal';

  const progressColor = isCritical
    ? 'bg-critical shadow-glow-coral'
    : isFriction
    ? 'bg-friction shadow-glow-amber'
    : 'bg-primary shadow-glow-teal-sm';

  return (
    <Card
      variant="interactive"
      onClick={() => onExplore && onExplore(theme)}
      tone={theme.sentiment}
      className="relative flex flex-col justify-between"
    >
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <Badge variant={badgeVariant} className="px-2.5 py-0.5 text-2xs font-bold">
              THEME 0{theme.rank}
            </Badge>
          </div>

          <span
            className={`inline-flex items-center text-2xs font-mono font-bold px-2 py-0.5 rounded ${
              theme.trendVsLastWeek > 0
                ? isCritical || isFriction
                  ? 'bg-critical-tint text-critical-dark border border-critical-border'
                  : 'bg-primary-tint text-primary border border-primary-border'
                : 'bg-surface-elevated text-text-muted border border-border-subtle'
            }`}
          >
            {theme.trendVsLastWeek > 0 ? (
              <TrendingUp className="w-3 h-3 mr-1" />
            ) : (
              <TrendingDown className="w-3 h-3 mr-1" />
            )}
            {formatTrend(theme.trendVsLastWeek)} vs lw
          </span>
        </div>

        <h3 className="text-sm font-bold font-display text-white leading-tight mb-2">
          {theme.label}
        </h3>

        <p className="text-xs text-text-secondary leading-relaxed mb-4 line-clamp-3">
          {theme.summary}
        </p>
      </div>

      <div className="pt-3 border-t border-border space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-2xs font-medium text-text-muted">Review Volume Share</span>
          <span className="font-mono font-bold text-white">{formatShare(theme.sharePct)}</span>
        </div>

        <div className="w-full h-1.5 bg-sidebar rounded-full overflow-hidden border border-border">
          <div
            className={`h-full rounded-full ${progressColor}`}
            style={{ width: `${Math.min(100, theme.sharePct * 2.2)}%` }}
          />
        </div>

        <div className="flex items-center justify-between text-xs pt-1">
          <span className="text-2xs text-text-muted">Cohort Rating</span>
          <div className="flex items-center gap-1 font-mono font-bold text-friction-dark">
            <Star className="w-3 h-3 fill-friction-dark" />
            <span>{formatRating(theme.avgRating)}</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
