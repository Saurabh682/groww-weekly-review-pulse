import React from 'react';

interface PulseDividerProps {
  className?: string;
  color?: string;
}

export const PulseDivider: React.FC<PulseDividerProps> = ({
  className = '',
  color = '#00D09C',
}) => {
  return (
    <div className={`w-full flex items-center justify-center my-6 select-none ${className}`} aria-hidden="true">
      <div className="w-full flex items-center">
        <div className="flex-1 h-[1px] bg-[#1e293b]" />
        <svg
          width="48"
          height="16"
          viewBox="0 0 48 16"
          fill="none"
          className="mx-2 text-primary"
        >
          <path
            d="M0 8 H14 L17 4 L21 14 L26 2 L30 11 L33 8 H48"
            stroke={color}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ filter: `drop-shadow(0 0 4px ${color})` }}
          />
        </svg>
        <div className="flex-1 h-[1px] bg-[#1e293b]" />
      </div>
    </div>
  );
};
