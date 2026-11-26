import React, { useEffect, useState } from 'react';
import { Link, useOutletContext, useNavigate } from 'react-router-dom';
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
import { Badge } from '../../components/Badge';
import { Chip } from '../../components/Chip';
import { SectionTitle } from '../../components/SectionTitle';
import { Skeleton } from '../../components/Skeleton';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { Toast } from '../../components/Toast';
import { GoogleDocModal, getSavedDocUrl, isMockDocUrl } from '../../components/GoogleDocModal';
import { GmailDraftModal } from '../../components/GmailDraftModal';
import {
  Copy,
  ExternalLink,
  Mail,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { formatRating, formatIndianNumber } from '../../lib/format';
import { CSS_COLOUR } from '../../styles/cssColours';

export const WeeklyPulsePage: React.FC = () => {
  const { currentScenario } = useOutletContext<{ currentScenario: ScenarioType; selectedWeek: string }>();
  const navigate = useNavigate();

  const [note, setNote] = useState<PulseNote | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [gmailModalOpen, setGmailModalOpen] = useState(false);

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
        <ErrorState headingLevel={2}
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
        <EmptyState headingLevel={2}
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
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">
              Weekly Review Pulse
            </h1>

            <Chip
              variant="neutral"
              label="90-second read"
              icon={<div className="relative w-4 h-4 flex items-center justify-center shrink-0">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 20 20">
                  <circle
                    cx="10"
                    cy="10"
                    r={readRadius}
                    fill="none"
                    stroke={CSS_COLOUR.border}
                    strokeWidth="2.5"
                  />
                  <circle
                    cx="10"
                    cy="10"
                    r={readRadius}
                    fill="none"
                    stroke={CSS_COLOUR.primary}
                    strokeWidth="2.5"
                    strokeDasharray={readCircumference}
                    strokeDashoffset={readOffset}
                    strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 2px ${CSS_COLOUR.primary})` }}
                  />
                </svg>
              </div>}
            />

            <Chip
              variant="positive"
              size="sm"
              label="EXECUTIVE MEMO"
              icon={<span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />}
            />
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

        <p className="text-xs text-text-secondary font-mono">
          Reviews from <strong className="text-white">{note.windowStart}</strong> to{' '}
          <strong className="text-white">{note.windowEnd}</strong> •{' '}
          <strong className="text-white">{formatIndianNumber(note.totalReviews)}</strong> reviews analyzed • Avg
          rating <strong className="text-white font-bold">{formatRating(note.avgRating)}</strong> • Source:{' '}
          <span className="font-semibold text-primary">Google Play</span>
        </p>
      </div>

      <Card padding="roomy">
        <div className="flex flex-col lg:flex-row items-stretch gap-6">
          <div className="lg:w-60 shrink-0 flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-border pb-4 lg:pb-0 lg:pr-6">
            <div className="text-2xs font-mono font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              COMPOSITE HEALTH
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-4xl sm:text-5xl font-extrabold font-display text-white tracking-tight">
                {note.pulseScore}
              </span>
              <span className="text-xs text-text-muted font-mono font-bold">/ 100</span>
            </div>
            <Chip
              variant="friction"
              label={note.moodLabel}
              icon={<span className="w-2 h-2 rounded-full bg-friction animate-pulse" />}
              className="mt-2.5 w-fit font-mono font-bold"
            />
          </div>

          <div className="flex-1 flex flex-col justify-center min-w-0">
            <div className="flex items-center justify-between text-xs text-text-muted mb-1 px-1">
              <span className="font-display font-semibold text-white flex items-center gap-2">
                12-Week Sentiment Rhythm
                <Badge variant="amber">W4 & W5 KYC friction flagged</Badge>
              </span>
              <span className="text-2xs font-mono text-text-muted">Threshold: 3.8★ (Amber)</span>
            </div>
            <PulseLine weeks={note.weeks} threshold={3.8} height={130} />
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-8 space-y-8">
          <section>
            <SectionTitle
              note="Driving 62% of total review volume"
              aside={
                <Link to="/themes" className="text-xs font-semibold text-primary hover:underline font-mono">
                  View all themes &rarr;
                </Link>
              }
            >
              Top 3 Themes
            </SectionTitle>

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

          <section>
            <SectionTitle
              note="Voice of the users"
              aside={<Chip variant="positive" size="sm" icon={<ShieldCheck className="w-3 h-3" />} label="PII scrubbed & anonymized" />}
            >
              What Users Said
            </SectionTitle>

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

          <section>
            <SectionTitle
              note="Prioritized interventions for Sprint 46"
              aside={<span className="text-2xs font-mono text-text-muted">3 Owners Assigned</span>}
            >
              Action Ideas
            </SectionTitle>

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

          <Card padding="tight" className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
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

              <Button
                variant="primary"
                size="sm"
                icon={<Mail className="w-3.5 h-3.5 text-primary-on" />}
                onClick={() => setGmailModalOpen(true)}
                className="gap-2 w-full sm:w-auto justify-center text-xs"
              >
                <span>View Gmail draft</span>
                <span className="text-3xs bg-background/20 text-primary-on px-1.5 py-0.5 rounded font-mono font-bold">
                  Draft only
                </span>
              </Button>
            </div>
          </Card>
        </div>

        <div className="lg:col-span-4 lg:sticky lg:top-24 space-y-4">
          <NoteChecksRail
            wordCount={note.wordCount}
            checks={note.checks}
          />
        </div>
      </div>

      {toastMessage && (
        <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      )}

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

      <GmailDraftModal
        isOpen={gmailModalOpen}
        onClose={() => setGmailModalOpen(false)}
      />
    </div>
  );
};
