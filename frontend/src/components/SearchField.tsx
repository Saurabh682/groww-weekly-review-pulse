import React from 'react';
import { Search, X } from 'lucide-react';
import { Button } from './Button';

interface SearchFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export const SearchField: React.FC<SearchFieldProps> = ({ label, value, onChange, placeholder = label, className = '' }) => (
  <div
    className={`flex items-center gap-2 px-3.5 py-1.5 bg-surface border border-border-subtle rounded-card shadow-card focus-within:border-primary/60 transition-colors ${className}`}
  >
    <Search className="w-4 h-4 text-text-muted shrink-0" aria-hidden="true" />
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      aria-label={label}
      className="w-full bg-transparent py-1 text-xs text-white placeholder:text-text-muted focus:outline-none font-sans"
    />
    {value && (
      <Button variant="ghost" size="sm" aria-label="Clear search" onClick={() => onChange('')}>
        <X className="w-3.5 h-3.5" />
      </Button>
    )}
  </div>
);
