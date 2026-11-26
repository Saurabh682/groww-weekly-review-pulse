import React from 'react';

interface SectionTitleProps {
  children: React.ReactNode;
  note?: string;
  aside?: React.ReactNode;
}

export const SectionTitle: React.FC<SectionTitleProps> = ({ children, note, aside }) => (
  <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 mb-4">
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 min-w-0">
      <span className="w-1.5 h-4 rounded-full bg-primary" aria-hidden="true" />
      <h2 className="text-base font-bold font-display text-white">{children}</h2>
      {note && <span className="text-xs text-text-muted font-mono">{note}</span>}
    </div>
    {aside}
  </div>
);
