import React, { useEffect, useState } from 'react';
import { Theme, SampleReview } from '../../data/types';
import { Drawer } from '../../components/Drawer';
import { Chip } from '../../components/Chip';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/Skeleton';
import { PulseNode } from '../../pulseline/PulseNode';
import { pulseApi } from '../../data/mockApi';
import { sanitizePii } from '../../lib/piiGuard';
import { formatRating, formatShare } from '../../lib/format';
import { Star, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ThemeDrawerProps {
  theme: Theme | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ThemeDrawer: React.FC<ThemeDrawerProps> = ({
  theme,
  isOpen,
  onClose,
}) => {
  const [samples, setSamples] = useState<SampleReview[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (theme && isOpen) {
      setLoading(true);
      pulseApi
        .getThemeSamples(theme.id)
        .then((data) => setSamples(data))
        .finally(() => setLoading(false));
    }
  }, [theme, isOpen]);

  if (!theme) return null;

  const totalReviews = theme.ratingDistribution.reduce((a, b) => a + b, 0);

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={theme.label}
      subtitle={`Rank #${theme.rank} • Priority Score: ${theme.priorityScore} / 100 • ${theme.reviewCount} Reviews`}
    >
      <Card padding="tight" className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PulseNode sharePct={theme.sharePct} sentiment={theme.sentiment} rank={theme.rank} />
            <Chip
              label={theme.sentiment.toUpperCase()}
              variant={theme.sentiment}
              size="sm"
            />
            {theme.inPulse && (
              <Badge variant="teal">In Pulse Top 3</Badge>
            )}
          </div>
          <div className="text-sm font-mono font-bold text-white">
            {formatRating(theme.avgRating)} ({formatShare(theme.sharePct)} share)
          </div>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          {theme.summary}
        </p>
      </Card>

      <div>
        <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted mb-2.5">
          Rating Breakdown
        </h3>
        <Card padding="tight" className="space-y-2">
          {[5, 4, 3, 2, 1].map((stars) => {
            const count = theme.ratingDistribution[stars - 1] || 0;
            const pct = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
            return (
              <div key={stars} className="flex items-center gap-2.5 text-xs">
                <span className="w-7 font-mono font-bold text-text-secondary flex items-center">
                  {stars}<Star className="w-3 h-3 text-friction-dark fill-friction-dark ml-0.5" />
                </span>
                <div className="flex-1 h-2 bg-sidebar rounded-full overflow-hidden border border-border">
                  <div
                    className={`h-full rounded-full ${
                      stars <= 2 ? 'bg-critical shadow-glow-coral' : stars === 3 ? 'bg-friction shadow-glow-amber' : 'bg-primary shadow-glow-teal-sm'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="w-14 text-right text-2xs font-mono text-text-muted">
                  {count} ({pct.toFixed(0)}%)
                </span>
              </div>
            );
          })}
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted">
            Representative Play Store Reviews ({samples.length})
          </h3>
          <span className="text-2xs font-mono text-text-muted">Anonymized customer reviews</span>
        </div>

        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
        ) : samples.length === 0 ? (
          <EmptyState headingLevel={4} compact title="No sample reviews" description="No sample reviews available for this cluster." />
        ) : (
          <div className="space-y-3">
            {samples.map((sample) => (
              <Card key={sample.id} padding="tight" className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-3.5 h-3.5 ${
                          star <= sample.rating
                            ? 'text-friction-dark fill-friction-dark'
                            : 'text-border fill-border'
                        }`}
                      />
                    ))}
                  </div>

                  {sample.quoteEligible ? (
                    <Chip
                      size="sm"
                      variant="positive"
                      label="Quote eligible"
                      icon={<CheckCircle2 className="w-3 h-3 text-primary" />}
                    />
                  ) : (
                    <Chip
                      size="sm"
                      variant="failure"
                      label={sample.ineligibleReason || 'Ineligible (PII)'}
                      icon={<AlertCircle className="w-3 h-3 text-failure" />}
                    />
                  )}
                </div>

                <p className="text-xs text-text-primary leading-relaxed">
                  {sanitizePii(sample.text)}
                </p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Drawer>
  );
};
