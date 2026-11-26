import React from 'react';
import { ExternalLink, Mail } from 'lucide-react';
import { Badge } from '../../components/Badge';
import { ExternalButtonLink } from '../../components/Button';
import { Card } from '../../components/Card';
import { Stat } from '../../components/Stat';
import { PulseWeek } from '../../data/types';
import { formatDay, formatMoment, weekLabel } from '../../lib/dates';
import { formatIndianNumber, formatRating } from '../../lib/format';

const GMAIL_DRAFTS_URL = 'https://mail.google.com/mail/#drafts';
interface PulseSummaryProps {
  pulse: PulseWeek;
}

export const PulseSummary: React.FC<PulseSummaryProps> = ({ pulse }) => {
  const isPublished = pulse.status === 'published';
  return (
    <Card padding="roomy" className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-bold font-display text-white">{weekLabel(pulse.week_start)}</h2>
            <Badge variant={isPublished ? 'teal' : 'amber'}>{isPublished ? 'Published' : 'Not published'}</Badge>
          </div>
          <p className="text-xs text-text-secondary font-mono mt-1">
            Reviews from {formatDay(pulse.window_start)} to {formatDay(pulse.window_end)}
            {pulse.published_at && ` • Published ${formatMoment(pulse.published_at)}`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {pulse.doc_url && (
            <ExternalButtonLink href={pulse.doc_url} icon={<ExternalLink className="w-3.5 h-3.5" />}>
              Open Google Doc
            </ExternalButtonLink>
          )}
          {pulse.draft_created && (
            <ExternalButtonLink href={GMAIL_DRAFTS_URL} icon={<Mail className="w-3.5 h-3.5" />}>
              View Gmail draft
            </ExternalButtonLink>
          )}
        </div>
      </div>

      {pulse.short_coverage && (
        <p className="text-xs text-friction-dark bg-friction-tint border border-friction-border rounded-lg px-3 py-2">
          Short coverage: these reviews span {pulse.coverage_weeks.toFixed(1)} weeks, and a full pulse needs at least 8.
        </p>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        <Stat label="Usable reviews" value={formatIndianNumber(pulse.total_reviews)} subtext="very short ones left out" />
        <Stat label="Grouped" value={formatIndianNumber(pulse.analyzed_reviews)} subtext="longer English reviews" />
        <Stat label="Average rating" value={formatRating(pulse.avg_rating)} subtext="of the grouped reviews" />
        <Stat label="Weeks covered" value={pulse.coverage_weeks.toFixed(1)} subtext="of up to 12" />
      </div>
    </Card>
  );
};
