import React from 'react';

interface SectionTitleProps {
  children: React.ReactNode;
}

export const SectionTitle: React.FC<SectionTitleProps> = ({ children }) => (
  <div className="flex items-center gap-2 mb-4">
    <span className="w-1.5 h-4 rounded-full bg-primary" />
    <h2 className="text-base font-bold font-display text-white">{children}</h2>
  </div>
);
