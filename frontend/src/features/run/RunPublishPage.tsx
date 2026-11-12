import React, { useEffect, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { RunState, PipelineStage, ScenarioType } from '../../data/types';
import { pulseApi } from '../../data/mockApi';
import { PulseStepper } from '../../pulseline/PulseStepper';
import { RunLogsModal } from './RunLogsModal';
import { Card } from '../../components/Card';
import { Chip } from '../../components/Chip';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Skeleton } from '../../components/Skeleton';
import {
  Play,
  RotateCcw,
  ExternalLink,
  Mail,
  FileText,
  ShieldAlert,
  ShieldCheck,
  Check,
  X,
  Terminal,
  Activity,
} from 'lucide-react';

export const RunPublishPage: React.FC = () => {
  const { currentScenario } = useOutletContext<{ currentScenario: ScenarioType }>();
  const [searchParams] = useSearchParams();

  const [runState, setRunState] = useState<RunState | null>(null);
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRunningSim, setIsRunningSim] = useState(false);
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [selectedStage, setSelectedStage] = useState<PipelineStage | null>(null);

  const loadRun = async () => {
    setLoading(true);
    try {
      const data = await pulseApi.getRun(undefined, currentScenario);
      setRunState(data);
      setStages(data.stages);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRun();
  }, [currentScenario]);

  useEffect(() => {
    if (searchParams.get('trigger') === 'true' && !loading && !isRunningSim) {
      handleTriggerRun();
    }
  }, [searchParams, loading]);

  const handleTriggerRun = async () => {
    if (isRunningSim) return;
    setIsRunningSim(true);

    const initial = stages.map((s) => ({
      ...s,
      status: 'pending' as const,
      durationMs: undefined,
    }));
    setStages(initial);

    const isFailScenario = currentScenario === 'validation-failed';

    for (let i = 0; i < initial.length; i++) {
      setStages((prev) =>
        prev.map((s, idx) => (idx === i ? { ...s, status: 'running' } : s))
      );

      await new Promise((r) => setTimeout(r, 450));

      if (isFailScenario && initial[i].id === 'validate') {
        setStages((prev) =>
          prev.map((s, idx) => {
            if (idx === i) return { ...s, status: 'failed', durationMs: 420 };
            if (idx > i) return { ...s, status: 'skipped' };
            return s;
          })
        );
        setIsRunningSim(false);
        return;
      }

      setStages((prev) =>
        prev.map((s, idx) =>
          idx === i ? { ...s, status: 'done', durationMs: Math.round(300 + Math.random() * 800) } : s
        )
      );
    }

    setIsRunningSim(false);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-56" />
          <Skeleton className="h-56" />
        </div>
      </div>
    );
  }

  const isFailed = currentScenario === 'validation-failed' || stages.some((s) => s.status === 'failed');

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 1. Page Header with Run Metadata & Primary Action */}
      <Card className="p-5 sm:p-6 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold font-display tracking-tight text-white">
                Run & Publish Pipeline
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#1e293b] border border-[#2a3d5d] text-[10px] font-mono text-text-secondary">
                #PL-2026W45-09
              </span>
            </div>
            <p className="text-xs text-text-secondary mt-1 font-mono">
              Automated end-to-end ingestion, clustering, quote extraction, and leadership dispatch.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold border ${
                isFailed
                  ? 'bg-failure-tint text-failure-dark border-failure-border'
                  : 'bg-primary-tint text-primary border-primary-border shadow-glow-teal-sm'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isFailed ? 'bg-failure' : 'bg-primary animate-pulse'
                }`}
              />
              {isFailed ? 'Pipeline Halted' : 'All Systems Nominal'}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#1e293b]">
          <div className="text-xs font-mono text-text-muted flex items-center gap-2">
            <span>Last executed: Today, 08:29 AM IST</span>
            <span>•</span>
            <span>7 Stages</span>
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <Button
              variant="secondary"
              size="sm"
              icon={<Terminal className="w-3.5 h-3.5" />}
              onClick={() => setIsLogsOpen(true)}
              className="flex-1 sm:flex-initial text-xs"
            >
              View Run Logs
            </Button>

            <Button
              variant="primary"
              size="sm"
              loading={isRunningSim}
              icon={<Play className="w-3.5 h-3.5 text-[#0b111e]" />}
              onClick={handleTriggerRun}
              className="flex-1 sm:flex-initial text-xs"
            >
              {isRunningSim ? 'Running Pipeline...' : 'Run Pipeline Now'}
            </Button>
          </div>
        </div>
      </Card>

      {/* 2. Pipeline Stage Heartbeat / Pulse Trace */}
      <Card className="p-5 sm:p-6 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Pipeline Stage Heartbeat
            </h2>
          </div>
          <span className="text-[11px] font-mono text-text-muted">
            {stages.filter((s) => s.status === 'done').length} / {stages.length} Stages Complete
          </span>
        </div>

        {/* Desktop Horizontal Stepper Track */}
        <div className="hidden md:block">
          <PulseStepper
            stages={stages}
            activeStageId={selectedStage?.id}
            onSelectStage={(stage) => {
              setSelectedStage(stage);
              setIsLogsOpen(true);
            }}
          />
        </div>

        {/* Mobile Vertical Stepper Timeline (Stitch Mobile Pattern) */}
        <div className="md:hidden flex flex-col relative pl-2 py-1">
          {/* Continuous vertical progress line */}
          <div className="absolute left-[23px] top-4 bottom-4 w-0.5 bg-primary/30" />

          {stages.map((stage, idx) => {
            const isDone = stage.status === 'done';
            const isRunning = stage.status === 'running';
            const isStageFailed = stage.status === 'failed';
            const isGate = stage.id === 'validate';

            const stageDescriptions: Record<string, string> = {
              ingest: 'Google Play API · 1,240 reviews',
              clean: 'Zero-mask rule · 14 scrubbed',
              cluster: 'Semantic vector · 5 clusters',
              quotes: 'Sentiment verified · 3 verbatim',
              generate: 'Claude 3.5 Sonnet · 231 words',
              validate: 'Guardrails · 6/6 passed',
              publish: 'Docs + Gmail · Synced',
            };

            return (
              <div
                key={stage.id}
                onClick={() => {
                  setSelectedStage(stage);
                  setIsLogsOpen(true);
                }}
                className="flex items-start gap-3 relative py-2.5 cursor-pointer group"
              >
                {/* Node Indicator */}
                <div
                  className={`z-10 w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold font-mono transition-transform group-active:scale-95 ${
                    isStageFailed
                      ? 'bg-failure text-white shadow-glow-coral'
                      : isRunning
                      ? 'bg-primary text-[#0b111e] animate-pulse-glow'
                      : isDone
                      ? 'bg-primary-tint text-primary border border-primary-border shadow-glow-teal-sm'
                      : 'bg-[#0e1726] border border-[#2a3d5d] text-text-muted'
                  }`}
                >
                  {isStageFailed ? (
                    <X className="w-4 h-4 stroke-[3]" />
                  ) : isDone ? (
                    <Check className="w-4 h-4 stroke-[3]" />
                  ) : isRunning ? (
                    <span className="w-2.5 h-2.5 rounded-full bg-[#0b111e] animate-ping" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>

                {/* Stage Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-xs font-display font-bold ${
                        isStageFailed
                          ? 'text-failure'
                          : isRunning || isDone
                          ? 'text-white'
                          : 'text-text-muted'
                      }`}
                    >
                      {idx + 1}. {stage.label}
                      {isGate && (
                        <span className="ml-1.5 px-1.5 py-0.2 rounded text-[9px] bg-primary-tint text-primary font-mono border border-primary-border">
                          Gate
                        </span>
                      )}
                    </span>
                    <span className="text-[10px] font-mono text-text-muted">
                      {stage.durationMs ? `${(stage.durationMs / 1000).toFixed(1)}s` : isRunning ? 'Running' : 'Pending'}
                    </span>
                  </div>
                  <p className="text-[11px] text-text-secondary truncate mt-0.5 font-mono">
                    {stageDescriptions[stage.id] || stage.counter || 'Deterministic pipeline phase'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Validation Incident Guard Advisory */}
      <div className="p-4 rounded-xl bg-[#162238] border border-[#2a3d5d] flex items-start gap-3 shadow-card">
        <div className="w-7 h-7 rounded-full bg-failure/20 text-failure border border-failure/40 flex items-center justify-center shrink-0 mt-0.5">
          <ShieldAlert className="w-4 h-4" />
        </div>
        <div className="min-w-0">
          <div className="text-xs font-bold font-display text-white">Validation Incident Guard</div>
          <p className="text-[11px] text-text-secondary leading-relaxed mt-0.5">
            Zero-trust fail-safe is armed. Pipeline will automatically flatline dispatches to Google Docs and leadership email distribution if any deterministic constraint fails.
          </p>
        </div>
      </div>

      {/* 3. Incident Banner if Validation Gate Failed */}
      {isFailed && (
        <div
          role="alert"
          className="p-5 rounded-card bg-failure-tint border border-failure-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 animate-fade-in shadow-glow-coral"
        >
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-lg bg-failure/20 text-failure shrink-0 border border-failure/40">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold font-display text-white">
                  Validation Gate Failed — Publishing Aborted
                </h3>
                <Badge variant="coral">Pipeline Halted</Badge>
              </div>
              <p className="text-xs text-[#fca5a5] mt-1 max-w-2xl leading-relaxed">
                The synthesized note exceeded the strict 250-word ceiling (284 words generated). Invariant check failed to prevent executive note bloat. MCP delivery to Google Docs and Gmail draft was automatically skipped.
              </p>
            </div>
          </div>

          <Button
            variant="danger"
            size="sm"
            icon={<RotateCcw className="w-3.5 h-3.5" />}
            onClick={handleTriggerRun}
            loading={isRunningSim}
          >
            Retry Validation
          </Button>
        </div>
      )}

      {/* 4. Delivery Artifacts (Google Docs + Gmail Draft Preview) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Artifact 1: Google Doc */}
        <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-text-muted">
                    Google Docs Delivery
                  </span>
                  <h3 className="text-sm font-bold font-display text-white leading-tight">
                    Executive Pulse Document
                  </h3>
                </div>
              </div>

              <Chip
                size="sm"
                variant={isFailed ? 'outline' : 'positive'}
                label={isFailed ? 'Skipped' : 'Published'}
                icon={isFailed ? <X className="w-3 h-3" /> : <Check className="w-3 h-3 stroke-[2.5]" />}
              />
            </div>

            <p className="text-xs text-text-secondary leading-relaxed mb-4">
              Formatted one-page note synced directly to Google Drive via official Google Docs MCP server.
            </p>

            <div className="p-3 rounded-lg bg-[#0e1726] border border-[#1e293b] text-xs space-y-1.5 mb-4">
              <div className="flex justify-between">
                <span className="text-text-muted">Title:</span>
                <span className="font-semibold text-white">Groww Weekly Review Pulse - Week of 09 Nov 2026</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Updated:</span>
                <span className="font-mono text-[11px] text-text-secondary">09 Nov 2026, 06:30 IST</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">MCP Connection:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1 font-mono text-[11px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Docs MCP Connected
                </span>
              </div>
            </div>
          </div>

          <Button
            variant="secondary"
            size="sm"
            disabled={isFailed}
            icon={<ExternalLink className="w-3.5 h-3.5" />}
            onClick={() =>
              window.open(
                'https://docs.google.com/document/d/mock-groww-weekly-pulse-2026-11-09',
                '_blank'
              )
            }
            className="w-full justify-center"
          >
            Open Google Doc
          </Button>
        </Card>

        {/* Artifact 2: Gmail Draft Preview (STRICTLY NO SEND BUTTON) */}
        <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-text-muted">
                    Gmail Staging
                  </span>
                  <h3 className="text-sm font-bold font-display text-white leading-tight">
                    Executive Email Draft
                  </h3>
                </div>
              </div>

              <Chip
                size="sm"
                variant={isFailed ? 'outline' : 'neutral'}
                label={isFailed ? 'Skipped' : 'Draft created, not sent'}
              />
            </div>

            <p className="text-xs text-text-secondary leading-relaxed mb-4">
              Pre-composed email draft staged in Gmail for leadership distribution. Never sent automatically.
            </p>

            <div className="p-3 rounded-lg bg-[#0e1726] border border-[#1e293b] text-xs space-y-1.5 mb-4">
              <div className="flex justify-between">
                <span className="text-text-muted">To:</span>
                <span className="font-semibold text-white truncate max-w-[240px]">
                  product-leadership@groww.in, founders-office@groww.in
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Subject:</span>
                <span className="font-semibold text-white truncate max-w-[240px]">
                  [Weekly Pulse] Groww App Play Store Reviews — Week of 09 Nov 2026
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">MCP Connection:</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1 font-mono text-[11px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Gmail MCP Connected
                </span>
              </div>
            </div>
          </div>

          {/* User requirement: STRICTLY 'View Gmail draft', NEVER 'Send email' */}
          <Button
            variant="secondary"
            size="sm"
            disabled={isFailed}
            icon={<Mail className="w-3.5 h-3.5" />}
            onClick={() => {
              alert('Gmail Draft Preview: Created and staged in your Gmail drafts folder. Review before manual dispatch.');
            }}
            className="w-full justify-center"
          >
            View Gmail draft
          </Button>
        </Card>
      </div>

      {/* 5. Invariants Quality Gate Matrix Table */}
      <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-bold font-display text-white">
              Quality Gate Invariant Verification Matrix
            </h3>
          </div>
          <span className="text-[11px] font-mono text-primary flex items-center gap-1 font-semibold">
            {runState?.validationRows?.filter((r) => r.passed).length} / {runState?.validationRows?.length} Passed
          </span>
        </div>

        {/* Mobile View: Checklist rows (Stitch Mobile Pattern) */}
        <div className="md:hidden flex flex-col gap-2">
          {runState?.validationRows?.map((row) => (
            <div
              key={`mob-${row.id}`}
              className="flex items-center justify-between py-2 px-3 bg-[#0e1726] border border-[#1e293b] rounded-lg"
            >
              <div className="flex items-center gap-2 min-w-0">
                {row.passed ? (
                  <Check className="w-4 h-4 text-primary shrink-0 stroke-[2.5]" />
                ) : (
                  <X className="w-4 h-4 text-failure shrink-0 stroke-[2.5]" />
                )}
                <span className="text-xs text-white truncate font-medium">{row.label}</span>
              </div>
              <span
                className={`text-[11px] font-mono font-bold shrink-0 ml-2 ${
                  row.passed ? 'text-primary' : 'text-failure'
                }`}
              >
                {row.detail || (row.passed ? 'Passed' : 'Failed')}
              </span>
            </div>
          ))}
        </div>

        {/* Desktop View: Full Matrix Table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#1e293b] bg-[#0e1726]/90 text-[11px] font-mono font-bold text-text-muted uppercase tracking-wider">
                <th className="py-2.5 px-3">Invariant Check</th>
                <th className="py-2.5 px-3">Enforced Rule</th>
                <th className="py-2.5 px-3">Evaluation Detail</th>
                <th className="py-2.5 px-3 text-right">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]">
              {runState?.validationRows?.map((row) => (
                <tr key={row.id} className="hover:bg-[#1b2a47]/60 transition-colors">
                  <td className="py-3 px-3 font-semibold text-white">
                    {row.label}
                  </td>
                  <td className="py-3 px-3 text-text-secondary">
                    {row.id === 'top-themes'
                      ? 'Exactly 3 themes from clusters'
                      : row.id === 'quotes-verbatim'
                      ? 'Exactly 3 verbatim user quotes with stars'
                      : row.id === 'actions'
                      ? 'Exactly 3 operational action ideas'
                      : row.id === 'word-count'
                      ? 'Word count strictly ≤ 250 words'
                      : row.id === 'zero-pii'
                      ? 'Zero phone, email, order IDs, account numbers'
                      : 'Coverage threshold met'}
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-text-muted">
                    {row.detail || '-'}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                        row.passed
                          ? 'bg-primary-tint text-primary border border-primary-border'
                          : 'bg-failure-tint text-failure-dark border border-failure-border'
                      }`}
                    >
                      {row.passed ? (
                        <>
                          <Check className="w-3 h-3 stroke-[3]" /> Passed
                        </>
                      ) : (
                        <>
                          <X className="w-3 h-3 stroke-[3]" /> Failed
                        </>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Execution Logs Modal */}
      <RunLogsModal
        isOpen={isLogsOpen}
        onClose={() => setIsLogsOpen(false)}
        stages={stages}
        error={runState?.error}
      />
    </div>
  );
};
