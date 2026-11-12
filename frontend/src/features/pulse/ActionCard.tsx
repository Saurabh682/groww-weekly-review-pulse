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
    <Card className="flex flex-col justify-between bg-[#162238]/85 border border-[#2a3d5d] hover:border-primary/40 transition-all duration-150">
      <div>
        {/* Header: Action Number + Owner Badge */}
        <div className="flex items-center justify-between mb-2.5 pb-2.5 border-b border-[#1e293b]">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-text-muted">
              ACTION 0{index + 1}
            </span>
            <Badge variant={ownerVariants[action.owner] || 'blue'}>
              {action.owner}
            </Badge>
          </div>

          {themeLabel && (
            <div className="text-[10px] font-mono text-text-muted truncate max-w-[140px]">
              • {themeLabel}
            </div>
          )}
        </div>

        {/* Action description text */}
        <p className="text-xs font-medium text-white leading-relaxed mb-4">
          {sanitizePii(action.text)}
        </p>
      </div>

      {/* Target signal & arrow button */}
      <div className="pt-3 border-t border-[#1e293b] flex items-center justify-between gap-3">
        <div className="text-[11px] leading-tight">
          <span className="font-mono text-primary font-bold">Target: </span>
          <span className="text-[#dde2f5] font-medium">
            {sanitizePii(action.successSignal)}
          </span>
        </div>

        <button
          className="w-7 h-7 rounded-lg bg-[#0e1726] border border-[#2a3d5d] text-text-muted hover:text-primary hover:border-primary/50 flex items-center justify-center shrink-0 transition-colors"
          title="Sprint backlog task"
        >
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </Card>
  );
};
