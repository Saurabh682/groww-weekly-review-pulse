import React from 'react';
import { Modal } from '../../components/Modal';
import { PipelineStage } from '../../data/types';
import { CheckCircle2, XCircle, Clock } from 'lucide-react';

interface RunLogsModalProps {
  isOpen: boolean;
  onClose: () => void;
  stages: PipelineStage[];
  error?: string;
}

export const RunLogsModal: React.FC<RunLogsModalProps> = ({
  isOpen,
  onClose,
  stages,
  error,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Pipeline Execution Logs"
      maxWidth="xl"
    >
      <div className="space-y-4">
        <div className="p-3 bg-text-primary text-slate-200 rounded-lg font-mono text-[11px] leading-relaxed overflow-x-auto">
          <div className="text-emerald-400 font-bold mb-1">
            [PIPELINE ORCHESTRATOR] Initializing Groww Weekly Review Pulse Engine...
          </div>
          <div>Target week: Week of 09 Nov 2026</div>
          <div>Review Source: Google Play Store (AppId: com.nextbillion.groww)</div>
          <div className="my-2 border-b border-slate-700" />

          {stages.map((stage, idx) => {
            const isDone = stage.status === 'done';
            const isFailed = stage.status === 'failed';
            const isSkipped = stage.status === 'skipped';

            return (
              <div key={stage.id} className="py-0.5 flex items-center justify-between">
                <span>
                  [{idx + 1}/7] {stage.label}...{' '}
                  <span
                    className={
                      isDone
                        ? 'text-emerald-400 font-bold'
                        : isFailed
                        ? 'text-rose-400 font-bold'
                        : isSkipped
                        ? 'text-slate-500'
                        : 'text-amber-400'
                    }
                  >
                    {stage.status.toUpperCase()}
                  </span>
                </span>
                <span className="text-slate-400 text-[10px]">
                  {stage.durationMs ? `${stage.durationMs}ms` : '-'}
                </span>
              </div>
            );
          })}

          {error && (
            <div className="mt-3 p-2 bg-rose-950/80 border border-rose-500/50 text-rose-200 rounded">
              <span className="font-bold text-rose-400">[FATAL ERROR] </span>
              {error}
            </div>
          )}

          <div className="mt-2 text-slate-400">
            {error
              ? 'Execution aborted at Stage 6 (Validate Gate). MCP delivery bypassed.'
              : 'Pipeline completed successfully. Google Doc published & Gmail draft staged.'}
          </div>
        </div>

        {/* Stage details breakdown */}
        <div className="space-y-2">
          <div className="text-xs font-bold uppercase tracking-wider text-text-muted">
            Stage Health Check
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {stages.map((s) => (
              <div
                key={s.id}
                className="p-2.5 rounded-lg border border-border bg-background flex items-center justify-between"
              >
                <div className="flex items-center gap-2 truncate">
                  {s.status === 'done' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0" />
                  ) : s.status === 'failed' ? (
                    <XCircle className="w-3.5 h-3.5 text-critical shrink-0" />
                  ) : (
                    <Clock className="w-3.5 h-3.5 text-text-muted shrink-0" />
                  )}
                  <span className="font-medium text-text-primary truncate">{s.label}</span>
                </div>
                <span className="text-[11px] font-mono text-text-muted shrink-0">
                  {s.durationMs ? `${s.durationMs}ms` : '0ms'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
};
