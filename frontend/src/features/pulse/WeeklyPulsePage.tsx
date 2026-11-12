import React, { useEffect, useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { PulseNote, ScenarioType } from '../../data/types';
import { pulseApi } from '../../data/mockApi';
import { PulseLine } from '../../pulseline/PulseLine';
import { PulseDivider } from '../../pulseline/PulseDivider';
import { ThemeCard } from './ThemeCard';
import { QuoteCard } from './QuoteCard';
import { ActionCard } from './ActionCard';
import { NoteChecksRail } from './NoteChecksRail';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Skeleton } from '../../components/Skeleton';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { Toast } from '../../components/Toast';
import { GoogleDocModal, getSavedDocUrl, isMockDocUrl } from '../../components/GoogleDocModal';
import {
  Copy,
  ExternalLink,
  Mail,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { formatRating, formatIndianNumber } from '../../lib/format';

export const WeeklyPulsePage: React.FC = () => {
  const { currentScenario } = useOutletContext<{ currentScenario: ScenarioType; selectedWeek: string }>();
  const navigate = useNavigate();

  const [note, setNote] = useState<PulseNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [docModalOpen, setDocModalOpen] = useState(false);

  const handleOpenGoogleDoc = () => {
    const url = getSavedDocUrl();
    if (isMockDocUrl(url)) {
      setDocModalOpen(true);
    } else {
      window.open(url, '_blank');
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await pulseApi.getPulse(undefined, currentScenario);
      setNote(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load weekly pulse data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentScenario]);

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollHeight - window.innerHeight;
      if (totalScroll > 0) {
        const currentProgress = Math.min(1, Math.max(0, window.scrollY / totalScroll));
        setScrollProgress(currentProgress);
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleCopyMarkdown = () => {
    if (!note) return;
    const md = `
# Groww Weekly Review Pulse
**Window:** ${note.windowStart} to ${note.windowEnd} | **Reviews Analyzed:** ${note.totalReviews} | **Avg Rating:** ${note.avgRating}★

## Pulse Score
${note.pulseScore} / 100 — ${note.moodLabel}

## Top 3 Themes
${note.topThemes.map((t, i) => `${i + 1}. **${t.label}** (${t.sharePct}% share, ${t.avgRating}★): ${t.summary}`).join('\n')}

## Voice of the Users (Verbatim Quotes)
${note.quotes.map(q => `- "${q.text}" (${q.rating}★)`).join('\n')}

## Operational Action Ideas
${note.actions.map((a, i) => `${i + 1}. [${a.owner}] ${a.text} (Target: ${a.successSignal})`).join('\n')}
    `.trim();

    navigator.clipboard.writeText(md).then(() => {
      setToastMessage('Weekly pulse note copied as Markdown to clipboard!');
      setTimeout(() => setToastMessage(null), 3500);
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-44 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8">
        <ErrorState
          title="Could not load Weekly Pulse"
          message={error}
          onRetry={loadData}
        />
      </div>
    );
  }

  if (!note || note.topThemes.length === 0) {
    return (
      <div className="py-8">
        <EmptyState
          title="No Weekly Pulse Available"
          description="There are no processed reviews or generated notes for this week yet. You can import new reviews or run the synthesis pipeline."
          actionLabel="Run Pulse Pipeline"
          onAction={() => navigate('/run')}
        />
      </div>
    );
  }

  const readRadius = 8;
  const readCircumference = 2 * Math.PI * readRadius;
  const readOffset = readCircumference - scrollProgress * readCircumference;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 1. Header with Title, Executive Memo Tag, 90-sec Read Chip */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">
              Weekly Review Pulse
            </h1>

            {/* 90-second read chip */}
            <div
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#162238] border border-[#2a3d5d] text-xs font-semibold text-text-secondary shadow-card"
              title="Estimated 90-second executive read"
            >
              <div className="relative w-4 h-4 flex items-center justify-center shrink-0">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 20 20">
                  <circle
                    cx="10"
                    cy="10"
                    r={readRadius}
                    fill="none"
                    stroke="#1e293b"
                    strokeWidth="2.5"
                  />
                  <circle
                    cx="10"
                    cy="10"
                    r={readRadius}
                    fill="none"
                    stroke="#00D09C"
                    strokeWidth="2.5"
                    strokeDasharray={readCircumference}
                    strokeDashoffset={readOffset}
                    strokeLinecap="round"
                    style={{ filter: 'drop-shadow(0 0 2px #00D09C)' }}
                  />
                </svg>
              </div>
              <span>90-second read</span>
            </div>

            {/* Executive Memo Pill Tag from dark design */}
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-primary-tint border border-primary-border text-[10px] font-mono font-bold text-primary">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              EXECUTIVE MEMO
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<Copy className="w-3.5 h-3.5" />}
              onClick={handleCopyMarkdown}
            >
              Copy Markdown
            </Button>
          </div>
        </div>

        {/* Subtitle */}
        <p className="text-xs text-text-secondary font-mono">
          Reviews from <strong className="text-white">{note.windowStart}</strong> to{' '}
          <strong className="text-white">{note.windowEnd}</strong> •{' '}
          <strong className="text-white">{formatIndianNumber(note.totalReviews)}</strong> reviews analyzed • Avg
          rating <strong className="text-white font-bold">{formatRating(note.avgRating)}</strong> • Source:{' '}
          <span className="font-semibold text-primary">Google Play</span>
        </p>
      </div>

      {/* 2. Composite Health & PulseLine Hero Strip */}
      <Card className="p-6 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
        <div className="flex flex-col lg:flex-row items-stretch gap-6">
          {/* Left score panel */}
          <div className="lg:w-60 shrink-0 flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-[#1e293b] pb-4 lg:pb-0 lg:pr-6">
            <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              COMPOSITE HEALTH
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-4xl sm:text-5xl font-extrabold font-display text-white tracking-tight">
                {note.pulseScore}
              </span>
              <span className="text-xs text-text-muted font-mono font-bold">/ 100</span>
            </div>
            <div className="mt-2.5 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-friction-tint text-friction-dark text-xs font-mono font-bold border border-friction-border shadow-glow-amber w-fit">
              <span className="w-2 h-2 rounded-full bg-friction animate-pulse" />
              {note.moodLabel}
            </div>
          </div>

          {/* Right SVG ECG Pulse Line */}
          <div className="flex-1 flex flex-col justify-center min-w-0">
            <div className="flex items-center justify-between text-xs text-text-muted mb-1 px-1">
              <span className="font-display font-semibold text-white flex items-center gap-2">
                12-Week Sentiment Rhythm
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#0e1726] border border-[#1e293b] text-friction-dark">
                  W4 & W5 KYC friction flagged
                </span>
              </span>
              <span className="text-[11px] font-mono text-text-muted">Threshold: 3.8★ (Amber)</span>
            </div>
            <PulseLine weeks={note.weeks} threshold={3.8} height={130} />
          </div>
        </div>
      </Card>

      {/* Main Grid: Content (Left) + Sticky Quality Gate Rail (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (8 cols): Top 3 Themes, Quotes, Actions */}
        <div className="lg:col-span-8 space-y-8">
          {/* Section 1: Top 3 Themes */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-4 rounded-full bg-primary" />
                <h2 className="text-base font-bold font-display text-white">Top 3 Themes</h2>
                <span className="text-xs text-text-muted font-mono">
                  Driving 62% of total review volume
                </span>
              </div>
              <button
                onClick={() => navigate('/themes')}
                className="text-xs font-semibold text-primary hover:underline font-mono"
              >
                View all themes &rarr;
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {note.topThemes.map((theme) => (
                <ThemeCard
                  key={theme.id}
                  theme={theme}
                  onExplore={(t) => navigate(`/themes?themeId=${t.id}`)}
                />
              ))}
            </div>
          </section>

          <PulseDivider />

          {/* Section 2: What Users Said (Voice of the users) */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-4 rounded-full bg-primary" />
                <h2 className="text-base font-bold font-display text-white">What Users Said</h2>
                <span className="text-xs text-text-muted font-normal">
                  Voice of the users
                </span>
              </div>
              <div className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                <ShieldCheck className="w-3 h-3" />
                PII scrubbed & anonymized
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {note.quotes.map((quote) => {
                const matchedTheme = note.allThemes.find((t) => t.id === quote.themeId);
                return (
                  <QuoteCard
                    key={quote.id}
                    quote={quote}
                    themeLabel={matchedTheme?.label}
                  />
                );
              })}
            </div>
          </section>

          <PulseDivider />

          {/* Section 3: Operational Action Ideas */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-4 rounded-full bg-primary" />
                <h2 className="text-base font-bold font-display text-white">Action Ideas</h2>
                <span className="text-xs text-text-muted font-normal">
                  Prioritized interventions for Sprint 46
                </span>
              </div>
              <span className="text-[11px] font-mono text-text-muted">
                3 Owners Assigned
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {note.actions.map((action, idx) => {
                const matchedTheme = note.allThemes.find((t) => t.id === action.themeId);
                return (
                  <ActionCard
                    key={action.id}
                    action={action}
                    index={idx}
                    themeLabel={matchedTheme?.label}
                  />
                );
              })}
            </div>
          </section>

          {/* Bottom Action Delivery Bar */}
          <Card className="p-4 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-xs font-mono text-text-secondary">
              <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
              <span className="text-white font-medium">Ready for senior management broadcast</span>
            </div>

            <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
              <Button
                variant="secondary"
                size="sm"
                icon={<Copy className="w-3.5 h-3.5" />}
                onClick={handleCopyMarkdown}
                className="flex-1 sm:flex-initial text-xs"
              >
                Copy note
              </Button>

              <Button
                variant="secondary"
                size="sm"
                icon={<ExternalLink className="w-3.5 h-3.5" />}
                onClick={handleOpenGoogleDoc}
                className="flex-1 sm:flex-initial text-xs"
              >
                Open Google Doc
              </Button>

              {/* View Gmail draft button (STRICTLY NO SEND BUTTON) */}
              <Button
                variant="primary"
                size="sm"
                icon={<Mail className="w-3.5 h-3.5 text-[#0b111e]" />}
                onClick={() => navigate('/run')}
                className="gap-2 w-full sm:w-auto justify-center text-xs"
              >
                <span>View Gmail draft</span>
                <span className="text-[10px] bg-[#0b111e]/20 text-[#0b111e] px-1.5 py-0.5 rounded font-mono font-bold">
                  Draft only
                </span>
              </Button>
            </div>
          </Card>
        </div>

        {/* Right Column (4 cols): Sticky Note Quality Gate Rail */}
        <div className="lg:col-span-4 lg:sticky lg:top-24 space-y-4">
          <NoteChecksRail
            wordCount={note.wordCount}
            checks={note.checks}
          />
        </div>
      </div>

      {/* Floating Toast Notification */}
      {toastMessage && (
        <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      )}

      {/* Google Doc Connect & View Modal */}
      <GoogleDocModal
        isOpen={docModalOpen}
        onClose={() => setDocModalOpen(false)}
        noteMarkdown={note ? `
# Groww Weekly Review Pulse
**Window:** ${note.windowStart} to ${note.windowEnd} | **Reviews Analyzed:** ${note.totalReviews} | **Avg Rating:** ${note.avgRating}★

## Pulse Score
${note.pulseScore} / 100 — ${note.moodLabel}

## Top 3 Themes
${note.topThemes.map((t, i) => `${i + 1}. **${t.label}** (${t.sharePct}% share, ${t.avgRating}★): ${t.summary}`).join('\n')}

## Voice of the Users (Verbatim Quotes)
${note.quotes.map(q => `- "${q.text}" (${q.rating}★)`).join('\n')}

## Operational Action Ideas
${note.actions.map((a, i) => `${i + 1}. [${a.owner}] ${a.text} (Target: ${a.successSignal})`).join('\n')}
        `.trim() : ''}
      />
    </div>
  );
};
