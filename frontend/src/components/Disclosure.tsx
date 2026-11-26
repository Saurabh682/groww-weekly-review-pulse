import React from 'react';
import { ChevronDown } from 'lucide-react';
import { Card } from './Card';

interface DisclosureProps {
  id: string;
  isOpen: boolean;
  onToggle: () => void;
  summary: React.ReactNode;
  children: React.ReactNode;
}

export const Disclosure: React.FC<DisclosureProps> = ({ id, isOpen, onToggle, summary, children }) => {
  const panelId = `${id}-panel`;
  return (
    <Card padding="none" className="overflow-hidden">
      <button
        type="button"
        aria-expanded={isOpen}
        aria-controls={panelId}
        onClick={onToggle}
        className="w-full text-left p-4 flex items-center justify-between gap-3 hover:bg-surface-elevated/60 transition-colors"
      >
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5 min-w-0">{summary}</div>
        <ChevronDown
          aria-hidden="true"
          className={`w-4 h-4 text-text-muted shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180 text-primary' : ''}`}
        />
      </button>
      {isOpen && (
        <div
          id={panelId}
          className="px-4 pb-4 pt-3 text-xs text-text-secondary leading-relaxed font-sans border-t border-border/60 bg-sidebar/40"
        >
          {children}
        </div>
      )}
    </Card>
  );
};
