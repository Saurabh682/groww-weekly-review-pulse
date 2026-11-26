import React from 'react';
import { Quote } from '../../data/types';
import { Card } from '../../components/Card';
import { Chip } from '../../components/Chip';
import { Badge } from '../../components/Badge';
import { Check, Star } from 'lucide-react';
import { sanitizePii } from '../../lib/piiGuard';
import { formatRating } from '../../lib/format';

interface QuoteCardProps {
  quote: Quote;
  themeLabel?: string;
  versionTag?: string;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({
  quote,
  themeLabel,
  versionTag = 'Nov 8, 2026 Android v18.2.1',
}) => {
  return (
    <Card className="flex flex-col justify-between">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2.5 border-b border-border">
          <div className="flex items-center gap-1.5">
            {quote.verifiedVerbatim && (
              <Chip
                size="sm"
                variant="positive"
                label="Verified verbatim"
                icon={<Check className="w-3 h-3 stroke-[2.5]" />}
              />
            )}
            {themeLabel && (
              <Badge variant="gray" className="truncate max-w-[130px]">
                {themeLabel}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-1 font-mono text-xs font-bold text-friction-dark">
            <Star className="w-3 h-3 fill-friction-dark" />
            <span>({formatRating(quote.rating)})</span>
          </div>
        </div>

        <blockquote className="text-xs font-normal text-text-primary leading-relaxed italic relative pl-3 border-l-2 border-primary/50 mb-4">
          &ldquo;{sanitizePii(quote.text)}&rdquo;
        </blockquote>
      </div>

      <div className="pt-2 border-t border-border flex items-center justify-between text-3xs font-mono text-text-muted">
        <span>Google Play Store</span>
        <span>{versionTag}</span>
      </div>
    </Card>
  );
};
