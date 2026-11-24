import React, { useEffect, useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface MenuProps {
  label: string;
  text: string;
  icon: React.ReactNode;
  children: (close: () => void) => React.ReactNode;
}

export const Menu: React.FC<MenuProps> = ({ label, text, icon, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return undefined;
    const closeOnOutsidePress = (event: MouseEvent) => {
      if (!container.current?.contains(event.target as Node)) setIsOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('mousedown', closeOnOutsidePress);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('mousedown', closeOnOutsidePress);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [isOpen]);

  return (
    <div className="relative min-w-0" ref={container}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 max-w-full bg-surface border border-border-subtle rounded-lg text-xs font-semibold text-white hover:border-primary/50 transition-colors"
        aria-expanded={isOpen}
        aria-label={`${label}: ${text}`}
      >
        {icon}
        <span className="truncate">{text}</span>
        <ChevronDown className="w-3 h-3 text-text-muted shrink-0" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-1 w-60 bg-surface border border-border-subtle rounded-lg shadow-drawer py-1 z-50 animate-fade-in">
          {children(() => setIsOpen(false))}
        </div>
      )}
    </div>
  );
};

interface MenuItemProps {
  selected: boolean;
  onSelect: () => void;
  children: React.ReactNode;
}

export const MenuItem: React.FC<MenuItemProps> = ({ selected, onSelect, children }) => (
  <button
    type="button"
    onClick={onSelect}
    aria-current={selected ? 'true' : undefined}
    className={`w-full flex items-center justify-between gap-2 text-left px-3 py-2 text-xs transition-colors ${
      selected ? 'bg-primary-tint text-primary font-bold' : 'text-text-primary hover:bg-surface-elevated'
    }`}
  >
    {children}
  </button>
);
