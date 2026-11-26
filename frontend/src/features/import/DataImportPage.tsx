import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ImportSummary, ScenarioType } from '../../data/types';
import { pulseApi } from '../../data/mockApi';
import { PulseWaveMini } from '../../pulseline/PulseWaveMini';
import { Dropzone } from './Dropzone';
import { Card } from '../../components/Card';
import { Stat } from '../../components/Stat';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Chip } from '../../components/Chip';
import { Skeleton } from '../../components/Skeleton';
import { Toast } from '../../components/Toast';
import {
  FileText,
  FilterX,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Database,
  History,
} from 'lucide-react';
import { formatIndianNumber } from '../../lib/format';

const SCENARIOS = [
  { id: 'ok', label: 'Active' },
  { id: 'empty', label: 'Empty State' },
  { id: 'error', label: 'Schema Error' },
  { id: 'low-coverage', label: 'Low Coverage' },
] as const;

const openScenario = (id: (typeof SCENARIOS)[number]['id']) => {
  const params = new URLSearchParams(window.location.search);
  if (id === 'ok') params.delete('scenario');
  else params.set('scenario', id);
  const query = params.toString();
  window.history.pushState({}, '', `${window.location.pathname}${query ? `?${query}` : ''}`);
  window.location.reload();
};

export const DataImportPage: React.FC = () => {
  const { currentScenario } = useOutletContext<{ currentScenario: ScenarioType }>();

  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const data = await pulseApi.getImportSummary(currentScenario);
      setSummary(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [currentScenario]);

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const res = await pulseApi.uploadReviews(file);
      setToastMessage(res.message);
      if (summary) {
        setSummary({
          ...summary,
          imported: summary.imported + res.rowsAdded,
          history: [
            {
              fileName: file.name,
              date: 'Just now',
              rowsAdded: res.rowsAdded,
            },
            ...summary.history,
          ],
        });
      }
    } finally {
      setIsUploading(false);
      setTimeout(() => setToastMessage(null), 4000);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-1/3" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const isLowCoverage = summary ? summary.coverageWeeks < 10 : false;

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">
            Data Ingestion & Hygiene
          </h1>
          <Badge variant="teal" className="py-1">
            Google Play Store Ingestion
          </Badge>
        </div>
        <p className="text-xs text-text-secondary mt-1 font-mono">
          Review pipeline hygiene gates: Deduplication, ≤ 8 words & non-English filtering, and PII masking.
        </p>
      </div>

      <div className="flex items-center gap-1" role="group" aria-label="Sample scenario">
        {SCENARIOS.map((scenario) => (
          <Button
            key={scenario.id}
            size="sm"
            variant={currentScenario === scenario.id ? 'primary' : 'ghost'}
            aria-pressed={currentScenario === scenario.id}
            onClick={() => openScenario(scenario.id)}
            className="flex-1"
          >
            {scenario.label}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card padding="tight">
          <Stat
            label="Reviews Cleaned & Indexed"
            value={formatIndianNumber(summary?.imported || 0)}
            subtext="Phase 1 & 2 verified"
            icon={<Database className="w-4 h-4 text-primary" />}
          />
        </Card>

        <Card padding="tight">
          <Stat
            label="Duplicates Pruned"
            value={formatIndianNumber(summary?.duplicatesRemoved || 0)}
            subtext="Exact text & hash matches"
            icon={<FilterX className="w-4 h-4 text-text-muted" />}
          />
        </Card>

        <Card padding="tight">
          <Stat
            label="Low-Info Excluded"
            value={formatIndianNumber(summary?.lowInfoExcluded || 0)}
            subtext="≤ 8 words or non-English"
            icon={<AlertTriangle className="w-4 h-4 text-friction-dark" />}
          />
        </Card>

        <Card padding="tight">
          <Stat
            label="PII Entities Redacted"
            value={formatIndianNumber(summary?.piiRedacted || 0)}
            subtext="Phones, emails, ref IDs"
            icon={<ShieldCheck className="w-4 h-4 text-primary" />}
          />
        </Card>
      </div>

      <Card padding="tight" className="flex items-start gap-2.5 text-xs text-text-secondary">
        <ShieldCheck className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-white font-medium">Zero-PII Active:</strong> Reviewer names and IDs ignored automatically at parser layer. Phone, PAN & Aadhaar masks enforced.
        </p>
      </Card>

      <Dropzone
        onFileUploaded={handleFileUpload}
        isUploading={isUploading}
      />

      <Card padding="roomy">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold font-display text-white">
                12-Week Ingestion Volume Waveform
              </h2>
              <Badge variant={isLowCoverage ? 'amber' : 'teal'}>
                {summary?.coverageWeeks} / 12 Weeks Covered
              </Badge>
            </div>
            <p className="text-xs text-text-secondary mt-0.5 font-mono">
              Visualizes weekly review sample density. Gaps indicate ingestion outages.
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-text-muted">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-primary" />
              Healthy volume
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-friction" />
              Missing data gap
            </span>
          </div>
        </div>

        {isLowCoverage && (
          <div className="mb-4 p-3 rounded-lg bg-friction-tint border border-friction-border text-friction-dark text-xs flex items-center gap-2 shadow-glow-amber">
            <AlertTriangle className="w-4 h-4 text-friction shrink-0" />
            <span>
              <strong>Low coverage alert:</strong> Only {summary?.coverageWeeks} of 12 weeks have review data. Pulse score trend may exhibit historical gaps.
            </span>
          </div>
        )}

        <div className="pt-2">
          <PulseWaveMini data={summary?.weeklyVolume || []} height={70} />
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-bold font-display text-white">
              Recent Batch Ingestion History
            </h2>
          </div>
          <span className="text-2xs font-mono text-text-muted">
            {summary?.history?.length} Batches Synced
          </span>
        </div>

        <div className="md:hidden flex flex-col gap-2.5">
          {summary?.history?.map((item, idx) => (
            <div
              key={`mob-batch-${idx}`}
              className="p-3 bg-sidebar border border-border rounded-xl flex flex-col gap-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 rounded-lg bg-primary-tint border border-primary-border text-primary flex items-center justify-center shrink-0">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-mono text-xs font-semibold text-white truncate">
                      {item.fileName}
                    </div>
                    <div className="text-3xs font-mono text-text-muted">
                      {item.date} • +{formatIndianNumber(item.rowsAdded)} rows
                    </div>
                  </div>
                </div>

                <Chip variant="positive" size="sm" label="Ready for Pulse" className="shrink-0" />
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-border/60 text-3xs font-mono text-text-muted">
                <span className="flex items-center gap-1 text-primary">
                  <CheckCircle2 className="w-3 h-3" />
                  Sanitization Passed
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => alert(`Audit log for ${item.fileName}:\n• Deduplication: Clean\n• Zero-PII: Passed\n• Rows indexed: ${item.rowsAdded}`)}
                >
                  View Audit
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border bg-sidebar/90 text-2xs font-mono font-bold text-text-muted uppercase tracking-wider">
                <th className="py-2.5 px-3">Batch File Name</th>
                <th className="py-2.5 px-3">Timestamp (IST)</th>
                <th className="py-2.5 px-3 text-right">Reviews Added</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {summary?.history?.map((item, idx) => (
                <tr key={idx} className="hover:bg-surface-elevated/60 transition-colors">
                  <td className="py-3 px-3 font-mono font-medium text-white flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-text-muted" />
                    {item.fileName}
                  </td>
                  <td className="py-3 px-3 text-text-secondary font-mono">
                    {item.date}
                  </td>
                  <td className="py-3 px-3 text-right font-mono font-bold text-primary">
                    +{formatIndianNumber(item.rowsAdded)}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <Chip variant="positive" size="sm" icon={<CheckCircle2 className="w-3 h-3" />} label="Cleaned & Stored" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {toastMessage && (
        <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      )}
    </div>
  );
};
