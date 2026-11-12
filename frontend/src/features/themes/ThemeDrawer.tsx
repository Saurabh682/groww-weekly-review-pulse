import React, { useEffect, useState } from 'react';
import { Theme, SampleReview } from '../../data/types';
import { Drawer } from '../../components/Drawer';
import { Chip } from '../../components/Chip';
import { Badge } from '../../components/Badge';
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
      {/* 1. Theme Header Overview Card */}
      <div className="p-4 rounded-xl bg-[#162238] border border-[#2a3d5d] shadow-card space-y-3">
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
      </div>

      {/* 2. Rating Distribution Histogram */}
      <div>
        <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted mb-2.5">
          Rating Breakdown
        </h4>
        <div className="space-y-2 p-3.5 rounded-xl bg-[#162238] border border-[#2a3d5d]">
          {[5, 4, 3, 2, 1].map((stars) => {
            const count = theme.ratingDistribution[stars - 1] || 0;
            const pct = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
            return (
              <div key={stars} className="flex items-center gap-2.5 text-xs">
                <span className="w-7 font-mono font-bold text-text-secondary flex items-center">
                  {stars}<Star className="w-3 h-3 text-amber-400 fill-amber-400 ml-0.5" />
                </span>
                <div className="flex-1 h-2 bg-[#0e1726] rounded-full overflow-hidden border border-[#1e293b]">
                  <div
                    className={`h-full rounded-full ${
                      stars <= 2 ? 'bg-critical shadow-glow-coral' : stars === 3 ? 'bg-friction shadow-glow-amber' : 'bg-primary shadow-glow-teal-sm'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="w-14 text-right text-[11px] font-mono text-text-muted">
                  {count} ({pct.toFixed(0)}%)
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Sample Customer Reviews */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted">
            Representative Play Store Reviews ({samples.length})
          </h4>
          <span className="text-[11px] font-mono text-text-muted">Anonymized customer reviews</span>
        </div>

        {loading ? (
          <div className="space-y-3">
            <div className="h-20 bg-surface-elevated/40 animate-pulse rounded-lg" />
            <div className="h-20 bg-surface-elevated/40 animate-pulse rounded-lg" />
          </div>
        ) : samples.length === 0 ? (
          <div className="p-6 text-center text-xs text-text-muted border border-dashed border-[#2a3d5d] rounded-lg">
            No sample reviews available for this cluster.
          </div>
        ) : (
          <div className="space-y-3">
            {samples.map((sample) => (
              <div
                key={sample.id}
                className="p-3.5 rounded-xl bg-[#162238] border border-[#2a3d5d] hover:border-primary/40 transition-colors space-y-2"
              >
                {/* Header: Stars + Eligible Chip */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-3.5 h-3.5 ${
                          star <= sample.rating
                            ? 'text-amber-400 fill-amber-400'
                            : 'text-[#1e293b] fill-[#1e293b]'
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

                {/* Sanitized Text */}
                <p className="text-xs text-[#dde2f5] leading-relaxed">
                  {sanitizePii(sample.text)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </Drawer>
  );
};
