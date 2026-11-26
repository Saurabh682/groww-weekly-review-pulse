import React from 'react';
import { ActionIdea } from '../../data/types';
import { Card } from '../../components/Card';
import { Badge } from '../../components/Badge';
import { ArrowRight } from 'lucide-react';
import { sanitizePii } from '../../lib/piiGuard';

interface ActionCardProps {
  action: ActionIdea;
  index: number;
  themeLabel?: string;
}

export const ActionCard: React.FC<ActionCardProps> = ({
  action,
  index,
  themeLabel,
}) => {
  const ownerVariants: Record<string, 'teal' | 'amber' | 'coral' | 'blue' | 'gray'> = {
    Product: 'teal',
    Engineering: 'blue',
    Support: 'coral',
    Growth: 'amber',
  };

  return (
    <Card className="flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2.5 pb-2.5 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-text-muted">
              ACTION 0{index + 1}
            </span>
            <Badge variant={ownerVariants[action.owner] || 'blue'}>
              {action.owner}
            </Badge>
          </div>

          {themeLabel && (
            <div className="text-3xs font-mono text-text-muted truncate max-w-[140px]">
              • {themeLabel}
            </div>
          )}
        </div>

        <p className="text-xs font-medium text-white leading-relaxed mb-4">
          {sanitizePii(action.text)}
        </p>
      </div>

      <div className="pt-3 border-t border-border flex items-center justify-between gap-3">
        <div className="text-2xs leading-tight">
          <span className="font-mono text-primary font-bold">Target: </span>
          <span className="text-text-primary font-medium">
            {sanitizePii(action.successSignal)}
          </span>
        </div>

        <ArrowRight className="w-3.5 h-3.5 text-text-muted shrink-0" aria-hidden="true" />
      </div>
    </Card>
  );
};
