import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ImportSummary, ScenarioType } from '../../data/types';
import { pulseApi } from '../../data/mockApi';
import { PulseWaveMini } from '../../pulseline/PulseWaveMini';
import { Dropzone } from './Dropzone';
import { Card } from '../../components/Card';
import { Stat } from '../../components/Stat';
import { Badge } from '../../components/Badge';
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
      {/* 1. Header */}
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
          Review pipeline hygiene gates: Deduplication, $\le 8$ words & non-English filtering, and PII masking.
        </p>
      </div>

      {/* 2. Scenario Switcher Tabs (Stitch Mobile Pattern) */}
      <div className="flex items-center justify-between bg-[#162238] p-1 rounded-xl border border-[#2a3d5d] text-xs font-mono">
        <button
          onClick={() => {
            const params = new URLSearchParams(window.location.search);
            params.delete('scenario');
            window.history.pushState({}, '', `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`);
            window.location.reload();
          }}
          className={`flex-1 py-1.5 px-2 rounded-lg text-center font-semibold transition-all ${
            currentScenario === 'ok'
              ? 'bg-primary text-[#0b111e] shadow-glow-teal-sm'
              : 'text-text-muted hover:text-white'
          }`}
        >
          Active
        </button>
        <button
          onClick={() => {
            const params = new URLSearchParams(window.location.search);
            params.set('scenario', 'empty');
            window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            window.location.reload();
          }}
          className={`flex-1 py-1.5 px-2 rounded-lg text-center font-semibold transition-all ${
            currentScenario === 'empty'
              ? 'bg-primary text-[#0b111e] shadow-glow-teal-sm'
              : 'text-text-muted hover:text-white'
          }`}
        >
          Empty State
        </button>
        <button
          onClick={() => {
            const params = new URLSearchParams(window.location.search);
            params.set('scenario', 'error');
            window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            window.location.reload();
          }}
          className={`flex-1 py-1.5 px-2 rounded-lg text-center font-semibold transition-all ${
            currentScenario === 'error'
              ? 'bg-primary text-[#0b111e] shadow-glow-teal-sm'
              : 'text-text-muted hover:text-white'
          }`}
        >
          Schema Error
        </button>
        <button
          onClick={() => {
            const params = new URLSearchParams(window.location.search);
            params.set('scenario', 'low-coverage');
            window.history.pushState({}, '', `${window.location.pathname}?${params.toString()}`);
            window.location.reload();
          }}
          className={`flex-1 py-1.5 px-2 rounded-lg text-center font-semibold transition-all ${
            currentScenario === 'low-coverage'
              ? 'bg-primary text-[#0b111e] shadow-glow-teal-sm'
              : 'text-text-muted hover:text-white'
          }`}
        >
          Low Coverage
        </button>
      </div>

      {/* 3. Four Health Metrics Stat Cards (2x2 on mobile, 4-col on desktop) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card className="p-3.5 sm:p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
          <Stat
            label="Reviews Cleaned & Indexed"
            value={formatIndianNumber(summary?.imported || 0)}
            subtext="Phase 1 & 2 verified"
            icon={<Database className="w-4 h-4 text-primary" />}
          />
        </Card>

        <Card className="p-3.5 sm:p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
          <Stat
            label="Duplicates Pruned"
            value={formatIndianNumber(summary?.duplicatesRemoved || 0)}
            subtext="Exact text & hash matches"
            icon={<FilterX className="w-4 h-4 text-text-muted" />}
          />
        </Card>

        <Card className="p-3.5 sm:p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
          <Stat
            label="Low-Info Excluded"
            value={formatIndianNumber(summary?.lowInfoExcluded || 0)}
            subtext="≤ 8 words or non-English"
            icon={<AlertTriangle className="w-4 h-4 text-friction-dark" />}
          />
        </Card>

        <Card className="p-3.5 sm:p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
          <Stat
            label="PII Entities Redacted"
            value={formatIndianNumber(summary?.piiRedacted || 0)}
            subtext="Phones, emails, ref IDs"
            icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
          />
        </Card>
      </div>

      {/* Zero-PII Active Banner */}
      <div className="p-3.5 rounded-xl bg-[#162238] border border-[#2a3d5d] flex items-start gap-2.5 text-xs text-text-secondary">
        <ShieldCheck className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-white font-medium">Zero-PII Active:</strong> Reviewer names and IDs ignored automatically at parser layer. Phone, PAN & Aadhaar masks enforced.
        </p>
      </div>

      {/* 4. Dropzone for CSV / JSON Upload */}
      <Dropzone
        onFileUploaded={handleFileUpload}
        isUploading={isUploading}
      />

      {/* 4. PulseWaveMini Weekly Coverage Strip */}
      <Card className="p-6 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold font-display text-white">
                12-Week Ingestion Volume Waveform
              </h3>
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

        {/* Low Coverage Warning Banner */}
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

      {/* 5. Ingestion History Table & Mobile Cards */}
      <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-bold font-display text-white">
              Recent Batch Ingestion History
            </h3>
          </div>
          <span className="text-[11px] font-mono text-text-muted">
            {summary?.history?.length} Batches Synced
          </span>
        </div>

        {/* Mobile View: Batch Cards (Stitch Mobile Pattern) */}
        <div className="md:hidden flex flex-col gap-2.5">
          {summary?.history?.map((item, idx) => (
            <div
              key={`mob-batch-${idx}`}
              className="p-3 bg-[#0e1726] border border-[#1e293b] rounded-xl flex flex-col gap-2"
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
                    <div className="text-[10px] font-mono text-text-muted">
                      {item.date} • +{formatIndianNumber(item.rowsAdded)} rows
                    </div>
                  </div>
                </div>

                <span className="px-2 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-[10px] font-mono font-semibold text-emerald-400 shrink-0">
                  Ready for Pulse
                </span>
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-[#1e293b]/60 text-[10px] font-mono text-text-muted">
                <span className="flex items-center gap-1 text-primary">
                  <CheckCircle2 className="w-3 h-3" />
                  Sanitization Passed
                </span>
                <button
                  onClick={() => alert(`Audit log for ${item.fileName}:\n• Deduplication: Clean\n• Zero-PII: Passed\n• Rows indexed: ${item.rowsAdded}`)}
                  className="px-2 py-0.5 rounded bg-[#162238] border border-[#2a3d5d] text-white hover:text-primary font-semibold transition-colors"
                >
                  View Audit
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Desktop View: Data Table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#1e293b] bg-[#0e1726]/90 text-[11px] font-mono font-bold text-text-muted uppercase tracking-wider">
                <th className="py-2.5 px-3">Batch File Name</th>
                <th className="py-2.5 px-3">Timestamp (IST)</th>
                <th className="py-2.5 px-3 text-right">Reviews Added</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]">
              {summary?.history?.map((item, idx) => (
                <tr key={idx} className="hover:bg-[#1b2a47]/60 transition-colors">
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
                    <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      Cleaned & Stored
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Floating Toast Notification */}
      {toastMessage && (
        <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      )}
    </div>
  );
};
