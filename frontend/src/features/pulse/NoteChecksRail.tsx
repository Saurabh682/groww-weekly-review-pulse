import React from 'react';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Check, X, ShieldCheck, Info, Sliders, TrendingUp } from 'lucide-react';

interface NoteCheckItem {
  id: string;
  label: string;
  passed: boolean;
}

interface NoteChecksRailProps {
  wordCount: number;
  checks: NoteCheckItem[];
  className?: string;
}

export const NoteChecksRail: React.FC<NoteChecksRailProps> = ({
  wordCount,
  checks,
  className = '',
}) => {
  const maxWords = 250;
  const isNearLimit = wordCount >= 240 && wordCount <= maxWords;
  const isOverLimit = wordCount > maxWords;

  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const progressRatio = Math.min(1, wordCount / maxWords);
  const strokeDashoffset = circumference - progressRatio * circumference;

  let strokeColor = '#00D09C';
  let statusTextColor = 'text-primary';
  if (isOverLimit) {
    strokeColor = '#F43F5E';
    statusTextColor = 'text-critical font-bold';
  } else if (isNearLimit) {
    strokeColor = '#F59E0B';
    statusTextColor = 'text-friction-dark font-bold';
  }

  const checkSubtitles: Record<string, string> = {
    'top-themes': 'Balanced: 1 positive, 2 friction',
    'quotes-verbatim': 'Authenticated via Google Play IDs',
    'actions': 'Sprint 46 assigned owners',
    'word-count': 'Optimal 90s executive digest range',
    'zero-pii': 'Zero PAN, phone, or name tokens',
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 1. Quality Gate Card */}
      <Card className="p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#1e293b]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-primary" />
            <h3 className="text-xs font-bold font-display uppercase tracking-wider text-white">
              Note checks
            </h3>
          </div>
          <Info className="w-3.5 h-3.5 text-text-muted hover:text-white cursor-pointer" />
        </div>

        {/* Circular Word Counter */}
        <div className="flex items-center gap-4 mb-5 p-3 rounded-xl bg-[#0e1726] border border-[#1e293b]">
          <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
              <circle
                cx="32"
                cy="32"
                r={radius}
                fill="none"
                stroke="#1e293b"
                strokeWidth="4"
              />
              <circle
                cx="32"
                cy="32"
                r={radius}
                fill="none"
                stroke={strokeColor}
                strokeWidth="4"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                style={{ filter: `drop-shadow(0 0 4px ${strokeColor})` }}
                className="transition-all duration-300"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className={`text-xs font-mono font-bold ${statusTextColor}`}>
                {wordCount}
              </span>
            </div>
          </div>

          <div>
            <div className="text-xs font-mono font-bold text-white">
              {wordCount} / {maxWords} words
            </div>
            <div className="text-[11px] text-text-muted mt-0.5">
              {isOverLimit ? (
                <span className="text-critical font-bold">Exceeds 250-word cap!</span>
              ) : isNearLimit ? (
                <span className="text-friction-dark font-bold">Approaching limit</span>
              ) : (
                'Optimal 90s executive digest range'
              )}
            </div>
          </div>
        </div>

        {/* Checklist items */}
        <div className="space-y-3 mb-4">
          {checks.map((check) => (
            <div
              key={check.id}
              className="flex items-start justify-between text-xs gap-2"
            >
              <div>
                <div
                  className={`font-medium ${
                    check.passed ? 'text-white' : 'text-critical font-semibold'
                  }`}
                >
                  {check.label}
                </div>
                <div className="text-[10px] font-mono text-text-muted mt-0.5">
                  {checkSubtitles[check.id] || 'Verified against database invariants'}
                </div>
              </div>

              <div
                className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                  check.passed
                    ? 'bg-primary-tint text-primary border border-primary-border'
                    : 'bg-failure-tint text-failure border border-failure-border'
                }`}
              >
                {check.passed ? (
                  <Check className="w-2.5 h-2.5 stroke-[3]" />
                ) : (
                  <X className="w-2.5 h-2.5 stroke-[3]" />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Digest Metadata */}
        <div className="pt-3 border-t border-[#1e293b] space-y-1.5 text-[10px] font-mono text-text-muted">
          <div className="flex justify-between">
            <span>Model Run</span>
            <span className="text-[#dde2f5]">Pulse-v2.4 (Claude 3.5 Sonnet)</span>
          </div>
          <div className="flex justify-between">
            <span>Timestamp</span>
            <span className="text-[#dde2f5]">08:30 IST Today</span>
          </div>
          <div className="flex justify-between">
            <span>Review Sample</span>
            <span className="text-[#dde2f5]">N=662 (100% indexed)</span>
          </div>
        </div>

        {/* Button: Configure digest rules */}
        <div className="mt-4 pt-3 border-t border-[#1e293b]">
          <Button
            variant="secondary"
            size="sm"
            icon={<Sliders className="w-3.5 h-3.5" />}
            onClick={() => alert('Digest configuration rules editor opened.')}
            className="w-full text-xs justify-center"
          >
            Configure digest rules
          </Button>
        </div>
      </Card>

      {/* 2. Pulse Score Trend Card */}
      <Card className="p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-primary-tint border border-primary-border text-primary font-mono font-bold text-xs shrink-0 flex items-center gap-0.5 shadow-glow-teal-sm">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+4pt</span>
          </div>
          <div className="text-xs leading-relaxed">
            <div className="font-bold text-white font-display mb-0.5">Pulse Score Trend</div>
            <p className="text-text-secondary text-[11px]">
              Up from 74/100 last week thanks to UPI AutoPay rollout & resolution of login friction.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
