import React from 'react';
import { PipelineStage } from '../data/types';
import { Check, X, ShieldAlert, ShieldCheck, Loader2 } from 'lucide-react';

interface PulseStepperProps {
  stages: PipelineStage[];
  onSelectStage?: (stage: PipelineStage) => void;
  activeStageId?: string;
}

export const PulseStepper: React.FC<PulseStepperProps> = ({
  stages,
  onSelectStage,
  activeStageId,
}) => {
  if (!stages || stages.length === 0) return null;

  const failedStageIndex = stages.findIndex((s) => s.status === 'failed');
  const hasFailed = failedStageIndex !== -1;

  return (
    <div className="w-full py-4 select-none">
      <div className="relative flex items-center justify-between">
        {/* Background track line */}
        <div className="absolute left-6 right-6 top-5 -translate-y-1/2 h-[3px] bg-[#1e293b] z-0" />

        {/* Dynamic coloured segment lines between nodes */}
        {stages.map((stage, idx) => {
          if (idx === stages.length - 1) return null;
          const nextStage = stages[idx + 1];

          let segmentColor = 'bg-[#1e293b]';
          if (hasFailed && idx >= failedStageIndex) {
            segmentColor = 'bg-critical shadow-glow-coral';
          } else if (stage.status === 'done' && (nextStage.status === 'done' || nextStage.status === 'running')) {
            segmentColor = 'bg-primary shadow-glow-teal-sm';
          } else if (stage.status === 'running') {
            segmentColor = 'bg-primary/40';
          }

          const stepPercent = 100 / (stages.length - 1);
          const leftPercent = idx * stepPercent;

          return (
            <div
              key={`segment-${idx}`}
              className={`absolute top-5 -translate-y-1/2 h-[3px] z-0 transition-colors duration-300 ${segmentColor}`}
              style={{
                left: `${leftPercent}%`,
                width: `${stepPercent}%`,
              }}
            />
          );
        })}

        {/* 7 Stage Nodes */}
        {stages.map((stage, idx) => {
          const isGate = stage.id === 'validate';
          const isSelected = activeStageId === stage.id;
          const isFailed = stage.status === 'failed';
          const isDone = stage.status === 'done';
          const isRunning = stage.status === 'running';
          const isSkipped = stage.status === 'skipped';

          const size = isGate ? 'w-11 h-11' : 'w-9 h-9';

          let nodeClasses = 'border-2 bg-[#0e1726] text-text-muted border-[#2a3d5d]';
          if (isDone) {
            nodeClasses = 'bg-primary border-primary text-[#0b111e] font-bold shadow-glow-teal';
          } else if (isRunning) {
            nodeClasses = 'bg-primary-tint border-primary text-primary animate-pulse shadow-glow-teal-sm';
          } else if (isFailed) {
            nodeClasses = 'bg-critical-tint border-critical text-critical shadow-glow-coral';
          } else if (isSkipped) {
            nodeClasses = 'bg-[#080e1b] border-dashed border-[#1e293b] text-text-muted/40';
          }

          return (
            <div
              key={stage.id}
              className="relative z-10 flex flex-col items-center cursor-pointer group"
              onClick={() => onSelectStage && onSelectStage(stage)}
              role="button"
              tabIndex={0}
              aria-label={`Stage ${idx + 1}: ${stage.label}. Status: ${stage.status}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectStage && onSelectStage(stage);
                }
              }}
            >
              {/* Outer pulsing ring for running */}
              {isRunning && (
                <div className="absolute inset-0 rounded-full border-2 border-primary animate-pulse-glow -m-1" />
              )}

              {/* Node Circle */}
              <div
                className={`rounded-full flex items-center justify-center transition-all duration-200 ${size} ${nodeClasses} ${
                  isSelected ? 'ring-2 ring-primary ring-offset-2 ring-offset-[#0b111e]' : ''
                } group-hover:scale-105`}
              >
                {isGate ? (
                  isFailed ? (
                    <ShieldAlert className="w-5 h-5 text-critical" />
                  ) : isDone ? (
                    <ShieldCheck className="w-5 h-5 text-[#0b111e] stroke-[2.5]" />
                  ) : isRunning ? (
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                  ) : (
                    <span className="text-xs font-bold font-mono">GATE</span>
                  )
                ) : isDone ? (
                  <Check className="w-4 h-4 stroke-[3]" />
                ) : isFailed ? (
                  <X className="w-4 h-4 stroke-[3]" />
                ) : isRunning ? (
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                ) : (
                  <span className="text-xs font-mono font-medium">{idx + 1}</span>
                )}
              </div>

              {/* Stage label below */}
              <div className="mt-2 text-center max-w-[100px]">
                <div
                  className={`text-xs font-semibold leading-tight line-clamp-2 ${
                    isDone
                      ? 'text-white'
                      : isFailed
                      ? 'text-critical-dark font-bold'
                      : isRunning
                      ? 'text-primary font-bold'
                      : 'text-text-secondary'
                  }`}
                >
                  {stage.label}
                </div>
                {stage.counter && (
                  <div className="text-[10px] font-mono text-text-muted mt-0.5 whitespace-nowrap">
                    {stage.counter}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
