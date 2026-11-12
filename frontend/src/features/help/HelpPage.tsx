import React, { useState } from 'react';
import { Card } from '../../components/Card';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import {
  HelpCircle,
  BookOpen,
  ShieldCheck,
  Activity,
  Layers,
  PlayCircle,
  UploadCloud,
  Search,
  ChevronDown,
  CheckCircle2,
  Cpu,
  SlidersHorizontal,
  ExternalLink,
  Zap,
} from 'lucide-react';

interface FaqItem {
  id: string;
  category: 'core' | 'pipeline' | 'hygiene' | 'mcp' | 'scenarios';
  question: string;
  answer: string;
  tag: string;
}

export const HelpPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [openFaqIds, setOpenFaqIds] = useState<Record<string, boolean>>({
    'faq-1': true,
    'faq-2': false,
    'faq-3': false,
  });

  const toggleFaq = (id: string) => {
    setOpenFaqIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const faqs: FaqItem[] = [
    {
      id: 'faq-1',
      category: 'core',
      question: 'What is the Groww Weekly Review Pulse?',
      answer:
        'Groww Weekly Review Pulse is an executive intelligence system that continuously analyzes thousands of public Google Play reviews of the Groww Android app. Every Monday at 08:30 AM IST, it distills customer feedback into a strictly budgeted <= 250-word executive note with exactly 3 synthesized themes, 3 verbatim quotes, and 3 prioritized operational interventions.',
      tag: 'Executive Overview',
    },
    {
      id: 'faq-2',
      category: 'mcp',
      question: 'Can the system automatically broadcast emails to leadership?',
      answer:
        'No. By architectural principle and user safety rules, the system NEVER includes an automated "Send email" trigger. The delivery pipeline strictly stages drafts in your connected Gmail Drafts folder using the official Gmail MCP server. Leadership drafts must always be manually inspected and dispatched by a human operator.',
      tag: 'Safety Guardrail',
    },
    {
      id: 'faq-3',
      category: 'hygiene',
      question: 'How are reviewer names, phone numbers, and PII handled?',
      answer:
        'Zero PII is strictly guaranteed. Reviewer usernames, profile pictures, and Play Store identifiers are dropped at the parser ingestion level. In addition, an institutional negative-lookahead regex sanitizer strips 10-digit Indian phone numbers (+91), emails, PANs, Aadhaar numbers, and transaction IDs while preserving critical timestamps (e.g. 9:15 AM), app versions (v18.2.1), and currency amounts (Rs 500, ₹10,000).',
      tag: 'Zero-PII Architecture',
    },
    {
      id: 'faq-4',
      category: 'core',
      question: 'How is the Composite Health Score (0-100) computed?',
      answer:
        'The Composite Pulse Score maps weekly review star ratings and sentiment volumes to an institutional index: 80-100 is "Healthy", 65-79 indicates "Friction Flagged" (e.g. KYC or DigiLocker stalls), 50-64 indicates "High Friction", and < 50 denotes severe technical incidents or market-open auth freezes.',
      tag: 'Scoring Formula',
    },
    {
      id: 'faq-5',
      category: 'pipeline',
      question: 'What causes the Pipeline to Flatline in coral on the Run screen?',
      answer:
        'The pipeline is gated by deterministic invariant checks (Stage 6: Quality Gate). If synthesized content exceeds 250 words, fails to extract exactly 3 themes, includes non-verbatim quotes, or exposes PII, the Quality Gate triggers a coral flatline, immediately aborting Google Docs and Gmail dispatch.',
      tag: 'Fail-Safe Circuit Breaker',
    },
    {
      id: 'faq-6',
      category: 'scenarios',
      question: 'How do I test edge cases like validation errors or low coverage?',
      answer:
        'You can test scenarios anytime via URL query parameters: ?scenario=ok (normal), ?scenario=empty (no data), ?scenario=error (500 API failure), ?scenario=validation-failed (word count overflow triggering flatline), and ?scenario=low-coverage (historical coverage gap < 10 weeks). You can also use the Scenario Simulator dropdown in the left sidebar.',
      tag: 'Scenario Simulator',
    },
    {
      id: 'faq-7',
      category: 'hygiene',
      question: 'What batch file formats can I upload on the Data Import page?',
      answer:
        'The ingestion engine accepts raw Play Console CSV and JSON files up to 50MB. Required columns include review text (content/review_text), star rating (score/rating), and timestamp (at/date). Files missing required columns will trigger client-side schema validation alerts.',
      tag: 'Batch Ingestion',
    },
  ];

  const filteredFaqs = faqs.filter((faq) => {
    if (activeCategory !== 'all' && faq.category !== activeCategory) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        faq.question.toLowerCase().includes(q) ||
        faq.answer.toLowerCase().includes(q) ||
        faq.tag.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* 1. Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary-tint border border-primary-border flex items-center justify-center text-primary shadow-glow-teal-sm">
              <HelpCircle className="w-5 h-5" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">
              App Guide & Knowledge Base
            </h1>
          </div>
          <p className="text-xs text-text-secondary mt-1 font-mono">
            Exhaustive operational manual, architecture specifications, deterministic guardrails, and data contracts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="teal" className="py-1">
            Groww Pulse v2.4
          </Badge>
          <Badge variant="gray" className="py-1 hidden sm:inline-flex">
            Institutional Edition
          </Badge>
        </div>
      </div>

      {/* 2. Interactive Search & Category Filter */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 px-3.5 py-2.5 bg-[#162238] border border-[#2a3d5d] rounded-xl shadow-card focus-within:border-primary/60 transition-colors">
          <Search className="w-4 h-4 text-text-muted shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search help topics (e.g., PII masking, 250 words, Gmail draft, PulseLine, formulas)..."
            className="w-full bg-transparent text-xs text-white placeholder:text-text-muted focus:outline-none font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="text-xs text-text-muted hover:text-white font-mono px-1"
            >
              ✕
            </button>
          )}
        </div>

        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          {[
            { id: 'all', label: 'All Topics' },
            { id: 'core', label: 'Core Pulse & Scoring' },
            { id: 'pipeline', label: 'Pipeline & Quality Gate' },
            { id: 'hygiene', label: 'Zero-PII & Hygiene' },
            { id: 'mcp', label: 'MCP Delivery' },
            { id: 'scenarios', label: 'Scenarios' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-3 py-1 rounded-full transition-all ${
                activeCategory === cat.id
                  ? 'bg-primary text-[#0b111e] font-bold shadow-glow-teal-sm'
                  : 'bg-[#162238] border border-[#2a3d5d] text-text-muted hover:text-white hover:bg-[#1b2a47]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. The 4 Core Screens System Architecture */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-4 rounded-full bg-primary" />
          <h2 className="text-lg font-bold font-display text-white">
            The 4 Core Dashboard Screens
          </h2>
          <span className="text-xs text-text-muted font-mono">
            Navigation Map & Workflows
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Card 1: Weekly Pulse */}
          <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center">
                    <Activity className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold font-display text-white">
                      1. Weekly Pulse (/)
                    </h3>
                    <span className="text-[10px] font-mono text-text-muted">
                      90-Second Executive Read Note
                    </span>
                  </div>
                </div>
                <Badge variant="teal">Screen 1</Badge>
              </div>

              <p className="text-xs text-text-secondary leading-relaxed mb-3">
                The central command view presenting the synthesized one-page executive memo for Groww leadership.
              </p>

              <ul className="text-xs text-text-secondary space-y-1.5 font-sans mb-4">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Pulse Score (0-100) & Mood:</strong> Real-time sentiment index with dynamic mood label (Healthy, Friction Flagged, Severe Drop).
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">12-Week ECG PulseLine:</strong> Beat amplitude mapped to star ratings (1-5★). Beats under 3.8★ tint amber.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Top 3 Themes:</strong> Driving 62%+ of volume with volume share bar, cohort rating, and 4w trend.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Voice of Users & Actions:</strong> Verbatim verbatim quotes + operational action ideas mapped to Product/Engineering.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Sticky Note Checks Rail:</strong> Circular word count gauge (&lt;= 250w) and quality gate invariants.
                  </span>
                </li>
              </ul>
            </div>

            <div className="pt-3 border-t border-[#1e293b] flex items-center justify-between text-[11px] font-mono text-text-muted">
              <span>Path: /</span>
              <span className="text-primary font-semibold">Leadership Digest</span>
            </div>
          </Card>

          {/* Card 2: Themes Explorer */}
          <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center">
                    <Layers className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold font-display text-white">
                      2. Themes Explorer (/themes)
                    </h3>
                    <span className="text-[10px] font-mono text-text-muted">
                      Neural Cluster Orbit & Leaderboard
                    </span>
                  </div>
                </div>
                <Badge variant="teal">Screen 2</Badge>
              </div>

              <p className="text-xs text-text-secondary leading-relaxed mb-3">
                Explores unsupervised clustering of reviews with radial visualization and deep sample review drill-downs.
              </p>

              <ul className="text-xs text-text-secondary space-y-1.5 font-sans mb-4">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">PulseRing Orbit Map:</strong> Central Core Pulse Net hub with satellite nodes sized by review volume share (12-32px).
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">5-Cluster Cap:</strong> Strictly at most 5 clusters total; top 3 are included in the Pulse note, remainder in Watchlist.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Slide-Over Theme Drawer:</strong> Tap any theme to view 1★-5★ rating histogram and authentic verbatim quotes.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Mobile Constellation:</strong> Compact search bar, segmented control tabs (Top Ranked / Watchlist), and auto-cluster recommendations.
                  </span>
                </li>
              </ul>
            </div>

            <div className="pt-3 border-t border-[#1e293b] flex items-center justify-between text-[11px] font-mono text-text-muted">
              <span>Path: /themes</span>
              <span className="text-primary font-semibold">Cluster Intelligence</span>
            </div>
          </Card>

          {/* Card 3: Run & Publish */}
          <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center">
                    <PlayCircle className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold font-display text-white">
                      3. Run & Publish (/run)
                    </h3>
                    <span className="text-[10px] font-mono text-text-muted">
                      7-Stage Stepper & Delivery Gates
                    </span>
                  </div>
                </div>
                <Badge variant="teal">Screen 3</Badge>
              </div>

              <p className="text-xs text-text-secondary leading-relaxed mb-3">
                Controls the automated pipeline execution, validates quality invariants, and stages MCP deliverables.
              </p>

              <ul className="text-xs text-text-secondary space-y-1.5 font-sans mb-4">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">7-Stage Heartbeat Stepper:</strong> Ingest &rarr; Clean & PII &rarr; Cluster &rarr; Quotes &rarr; Generate &rarr; Validate &rarr; Publish.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Fail-Safe Coral Flatline:</strong> Oversized Validate Gate node halts dispatches if any invariant check is breached.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Google Docs MCP:</strong> One-click open link to live synced Google Doc format.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Gmail Staging:</strong> Exclusively "View Gmail draft"; zero direct automated dispatch.
                  </span>
                </li>
              </ul>
            </div>

            <div className="pt-3 border-t border-[#1e293b] flex items-center justify-between text-[11px] font-mono text-text-muted">
              <span>Path: /run</span>
              <span className="text-primary font-semibold">Pipeline Heartbeat</span>
            </div>
          </Card>

          {/* Card 4: Data Import */}
          <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center">
                    <UploadCloud className="w-4 h-4 stroke-[2.5]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold font-display text-white">
                      4. Data Import (/import)
                    </h3>
                    <span className="text-[10px] font-mono text-text-muted">
                      Play Store Ingestion & Hygiene
                    </span>
                  </div>
                </div>
                <Badge variant="teal">Screen 4</Badge>
              </div>

              <p className="text-xs text-text-secondary leading-relaxed mb-3">
                Manages batch review uploads, automated sanitization filters, and weekly sample coverage rhythm.
              </p>

              <ul className="text-xs text-text-secondary space-y-1.5 font-sans mb-4">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">4 Hygiene Metrics:</strong> Cleaned & Indexed, Duplicates Pruned, Low-Info Excluded, and PII Scrubbed.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">CSV & JSON Dropzone:</strong> Client-side column validation ensuring review_text and ratings are present.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">PulseWaveMini Waveform:</strong> 12-week sample density graph with amber gap markers for ingestion outages.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Audit Trail:</strong> Ingestion history with timestamped rows added and sanitization status.
                  </span>
                </li>
              </ul>
            </div>

            <div className="pt-3 border-t border-[#1e293b] flex items-center justify-between text-[11px] font-mono text-text-muted">
              <span>Path: /import</span>
              <span className="text-primary font-semibold">Hygiene Gate</span>
            </div>
          </Card>
        </div>
      </section>

      {/* 4. The Six Deterministic Quality Gate Invariants */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold font-display text-white">
            The Six Deterministic Invariant Checks
          </h2>
          <span className="text-xs text-text-muted font-mono">
            Zero-Trust Quality Gate Matrix
          </span>
        </div>

        <Card className="p-0 overflow-hidden bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#1e293b] bg-[#0e1726]/90 text-[11px] font-mono font-bold text-text-muted uppercase tracking-wider">
                  <th className="py-3 px-4">Gate Invariant</th>
                  <th className="py-3 px-4">Enforced Ceiling / Rule</th>
                  <th className="py-3 px-4">Failure Consequence</th>
                  <th className="py-3 px-4 text-right">Verification Logic</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e293b]">
                <tr className="hover:bg-[#1b2a47]/50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    1. Word Count Limit
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-mono font-bold">
                    Strictly &le; 250 words
                  </td>
                  <td className="py-3 px-4 text-critical font-mono">
                    Pipeline Flatlines; Docs/Gmail sync aborted
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-text-secondary">
                    Markdown syntax stripped; words &le; 250
                  </td>
                </tr>
                <tr className="hover:bg-[#1b2a47]/50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    2. Synthesized Themes
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-mono font-bold">
                    Exactly 3 themes
                  </td>
                  <td className="py-3 px-4 text-critical font-mono">
                    Quality Gate rejection
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-text-secondary">
                    topThemes.length === 3
                  </td>
                </tr>
                <tr className="hover:bg-[#1b2a47]/50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    3. Verbatim User Quotes
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-mono font-bold">
                    Exactly 3 quotes (verbatim)
                  </td>
                  <td className="py-3 px-4 text-critical font-mono">
                    Hallucination flag triggered
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-text-secondary">
                    Raw review text substring match verified
                  </td>
                </tr>
                <tr className="hover:bg-[#1b2a47]/50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    4. Operational Action Ideas
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-mono font-bold">
                    Exactly 3 action ideas
                  </td>
                  <td className="py-3 px-4 text-critical font-mono">
                    Strategy gap flagged
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-text-secondary">
                    Discrete owner assigned + success metric
                  </td>
                </tr>
                <tr className="hover:bg-[#1b2a47]/50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    5. Cluster Category Cap
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-mono font-bold">
                    At most 5 clusters total
                  </td>
                  <td className="py-3 px-4 text-critical font-mono">
                    Re-cluster threshold activated
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-text-secondary">
                    allThemes.length &le; 5
                  </td>
                </tr>
                <tr className="hover:bg-[#1b2a47]/50 transition-colors">
                  <td className="py-3 px-4 font-semibold text-white">
                    6. Zero PII Exposure
                  </td>
                  <td className="py-3 px-4 text-emerald-400 font-mono font-bold">
                    0 usernames, emails, phones, IDs
                  </td>
                  <td className="py-3 px-4 text-critical font-mono">
                    Severe Privacy Incident Block
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-text-secondary">
                    containsPii(text) === false
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </section>

      {/* 5. Mathematical Models & Formulas */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold font-display text-white">
            Mathematical Models & Formulas
          </h2>
          <span className="text-xs text-text-muted font-mono">
            Analytical Engines
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-bold font-display text-white">
                Cluster Priority Score Formula
              </h3>
            </div>
            <p className="text-xs text-text-secondary mb-3">
              Determines which themes enter the Top 3 Pulse vs remain in Watchlist:
            </p>
            <div className="p-3 rounded-lg bg-[#0e1726] border border-[#1e293b] font-mono text-xs text-primary leading-relaxed mb-3">
              Priority = (Share% × 0.40) + (NegShare% × 0.40) + ((5 - Rating) × 10 × 0.20)
            </div>
            <p className="text-[11px] text-text-muted leading-relaxed font-sans">
              Weighted towards high review volume and elevated negative sentiment to guarantee leadership focus on customer friction.
            </p>
          </Card>

          <Card className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-bold font-display text-white">
                ECG PulseLine Beat Amplitude
              </h3>
            </div>
            <p className="text-xs text-text-secondary mb-3">
              Maps average weekly rating to visual ECG heartbeat pulse height:
            </p>
            <div className="p-3 rounded-lg bg-[#0e1726] border border-[#1e293b] font-mono text-xs text-primary leading-relaxed mb-3">
              Y_peak = BaselineY - ((AvgRating - 1.0) / 4.0) × MaxBeatHeight
            </div>
            <p className="text-[11px] text-text-muted leading-relaxed font-sans">
              Ratings below 3.8★ automatically tint the heartbeat segment amber with friction annotations.
            </p>
          </Card>
        </div>
      </section>

      {/* 6. Scenario Simulator Cheat Sheet */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold font-display text-white">
            Scenario Simulator Guide
          </h2>
          <span className="text-xs text-text-muted font-mono">
            Interactive Test Scenarios
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            {
              scenario: 'ok',
              name: 'Normal (ok)',
              desc: 'Standard healthy weekly run with 68/100 score and 1,240 reviews.',
              color: 'text-emerald-400',
              link: '/?scenario=ok',
            },
            {
              scenario: 'empty',
              name: 'Empty State',
              desc: 'Awaiting ingestion. Displays clean zero-data recovery cards.',
              color: 'text-text-muted',
              link: '/?scenario=empty',
            },
            {
              scenario: 'error',
              name: 'API Error (500)',
              desc: 'Simulates network or repository backend failure with retry trigger.',
              color: 'text-amber-400',
              link: '/?scenario=error',
            },
            {
              scenario: 'validation-failed',
              name: 'Validation Failed',
              desc: 'Simulates word-count limit breach triggering coral flatline circuit breaker.',
              color: 'text-rose-400',
              link: '/run?scenario=validation-failed',
            },
            {
              scenario: 'low-coverage',
              name: 'Low Coverage',
              desc: 'Simulates missing weekly ingestion data (< 10 weeks) with amber alert.',
              color: 'text-amber-400',
              link: '/import?scenario=low-coverage',
            },
          ].map((sc) => (
            <Card
              key={sc.scenario}
              className="p-3.5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between"
            >
              <div>
                <div className={`font-mono text-xs font-bold ${sc.color} mb-1`}>
                  {sc.name}
                </div>
                <p className="text-[11px] text-text-secondary leading-relaxed mb-3">
                  {sc.desc}
                </p>
              </div>
              <a
                href={sc.link}
                className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold text-primary hover:underline"
              >
                <span>Launch &rarr;</span>
              </a>
            </Card>
          ))}
        </div>
      </section>

      {/* 7. Interactive Frequently Asked Questions */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold font-display text-white">
              Frequently Asked Questions
            </h2>
          </div>
          <span className="text-xs font-mono text-text-muted">
            {filteredFaqs.length} answers available
          </span>
        </div>

        <div className="space-y-2.5">
          {filteredFaqs.map((faq) => {
            const isOpen = openFaqIds[faq.id] ?? false;
            return (
              <div
                key={faq.id}
                className="bg-[#162238]/90 border border-[#2a3d5d] rounded-xl overflow-hidden shadow-card transition-colors"
              >
                <button
                  onClick={() => toggleFaq(faq.id)}
                  className="w-full text-left p-4 flex items-center justify-between gap-3 text-xs font-semibold text-white hover:bg-[#1b2a47]/60 transition-colors"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="px-2 py-0.5 rounded-full bg-[#0e1726] border border-[#1e293b] text-[10px] font-mono text-primary shrink-0">
                      {faq.tag}
                    </span>
                    <span className="font-display font-bold text-sm text-white truncate">
                      {faq.question}
                    </span>
                  </div>
                  <ChevronDown
                    className={`w-4 h-4 text-text-muted shrink-0 transition-transform duration-200 ${
                      isOpen ? 'rotate-180 text-primary' : ''
                    }`}
                  />
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 pt-1 text-xs text-text-secondary leading-relaxed font-sans border-t border-[#1e293b]/60 bg-[#0e1726]/40">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* 8. Technical Support & Quick Links */}
      <div className="p-5 rounded-xl bg-gradient-to-r from-[#162238] to-[#0e1726] border border-[#2a3d5d] shadow-card flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold font-display text-white">
            Need additional integrations or custom LLM rules?
          </h3>
          <p className="text-xs text-text-secondary mt-0.5 font-mono">
            Connect via internal Slack <strong className="text-white">#groww-review-pulse-dev</strong> or founders-office engineering desk.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => alert('Diagnostic export triggered. All local metrics and stage logs saved.')}
            className="text-xs font-mono"
          >
            Export Diagnostic
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => window.open('https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_IN', '_blank')}
            icon={<ExternalLink className="w-3.5 h-3.5 text-[#0b111e]" />}
            className="text-xs"
          >
            Play Store Page
          </Button>
        </div>
      </div>
    </div>
  );
};
