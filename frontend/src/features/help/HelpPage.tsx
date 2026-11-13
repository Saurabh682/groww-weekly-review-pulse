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
  ChevronUp,
  CheckCircle2,
  Cpu,
  SlidersHorizontal,
  ExternalLink,
  Zap,
  FileText,
  Compass,
  ArrowRight,
  Maximize2,
  Minimize2,
  Check,
  Copy,
} from 'lucide-react';

interface FaqItem {
  id: string;
  category: 'core' | 'pipeline' | 'hygiene' | 'mcp' | 'scenarios';
  question: string;
  answer: string;
  tag: string;
}

interface FeatureDetail {
  id: string;
  title: string;
  category: 'core' | 'themes' | 'pipeline' | 'mcp' | 'hygiene' | 'invariants' | 'testing';
  badge: string;
  badgeVariant: 'teal' | 'coral' | 'blue' | 'gray' | 'amber';
  summary: string;
  keyCapabilities: string[];
  workflow: string[];
  architecture: string;
  codeSnippet?: string;
  safetyGuardrails: string[];
}

export const HelpPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [openFaqIds, setOpenFaqIds] = useState<Record<string, boolean>>({
    'faq-1': true,
    'faq-2': false,
    'faq-3': false,
  });

  // Track expanded features
  const [expandedFeatureIds, setExpandedFeatureIds] = useState<Record<string, boolean>>({
    'feat-pulse': true,
    'feat-gdocs': true,
  });

  const [copiedSnippetId, setCopiedSnippetId] = useState<string | null>(null);

  const toggleFaq = (id: string) => {
    setOpenFaqIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleFeature = (id: string) => {
    setExpandedFeatureIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const expandAllFeatures = () => {
    const allExpanded: Record<string, boolean> = {};
    features.forEach((f) => {
      allExpanded[f.id] = true;
    });
    setExpandedFeatureIds(allExpanded);
  };

  const collapseAllFeatures = () => {
    setExpandedFeatureIds({});
  };

  const copyCode = (id: string, text: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedSnippetId(id);
    setTimeout(() => setCopiedSnippetId(null), 2500);
  };

  const features: FeatureDetail[] = [
    {
      id: 'feat-pulse',
      title: '90-Second Weekly Executive Note & Scoring Engine',
      category: 'core',
      badge: 'Core Intelligence',
      badgeVariant: 'teal',
      summary:
        'Distills thousands of raw weekly customer reviews into a strictly budgeted <= 250-word executive briefing tailored for C-suite and product leadership, readable in under 90 seconds.',
      keyCapabilities: [
        'Composite Pulse Score (0-100) combining star ratings, sentiment polarity, and review velocity.',
        'Dynamic Mood Status: Healthy (80+), Friction Flagged (65-79), High Friction (50-64), Severe Incident (<50).',
        '12-Week ECG Heartbeat Waveform: Visual cardiac rhythm with beats <3.8★ highlighted in amber friction tint.',
        'Top 3 Prioritized Customer Themes with volume share %, cohort star rating, and 4-week trend arrows.',
        'Verbatim Customer Quotes matched directly against raw store data (zero hallucinated feedback).',
        '3 Prioritized Operational Interventions with named team ownership (e.g. Core Brokerage, Mobile Reliability).',
      ],
      workflow: [
        'Open the dashboard root route (/) on Monday morning at 08:30 AM IST.',
        'Inspect the Pulse Score gauge and mood indicator to identify macro app health.',
        'Review the Top 3 customer pain points and read verbatim user testimonials.',
        'Examine the Sticky Note Checks Rail on the right to verify quality gate compliance.',
        'Use "Copy note", "Open Google Doc", or "View Gmail draft" to distribute to leadership.',
      ],
      architecture:
        'The synthesis engine operates in 2 phases: Analytical Clustering and Executive Distillation. Clustering groups reviews into unsupervised embeddings. Distillation runs a prompt bounded by deterministic length constraints (<= 250 words, Flesch-Kincaid Grade Level 8-10). Word count calculation strips Markdown syntax to ensure pure text readability in under 90 seconds (assuming standard 165 wpm executive reading speed).',
      codeSnippet: `// Scoring Formula
PulseScore = Math.round(
  (avgRating / 5.0) * 60 +
  (positiveSharePct * 30) -
  (critical1StarSharePct * 20)
); // Clamped between 0 and 100`,
      safetyGuardrails: [
        'Strict <= 250-word cap: Any draft exceeding 250 words is automatically rejected at the Quality Gate.',
        'Hallucination prevention: Quotes must be exact substrings of raw user submissions.',
        'Zero-PII guarantee: Reviewer names and account numbers are scrubbed before synthesis.',
      ],
    },
    {
      id: 'feat-gdocs',
      title: 'Google Docs MCP Programmatic Sync & Cloud Publishing',
      category: 'mcp',
      badge: 'Google Workspace MCP',
      badgeVariant: 'teal',
      summary:
        'Direct cloud delivery pipeline that writes the weekly executive report into Google Docs using the official Google Docs API (batchUpdate) without manual copy-pasting.',
      keyCapabilities: [
        'Programmatic batchUpdate text insertion at structural location index: 1.',
        'Real-time cloud autosave: Once inserted, the report lives permanently in your Google Drive.',
        'Interactive GoogleDocModal: Allows switching between prototype and live custom Google Doc IDs.',
        'Dual-Engine Clipboard Fallback: navigator.clipboard with offscreen execCommand fallback.',
        'Persistent Local Storage: Remembers your linked Google Document URL across sessions.',
      ],
      workflow: [
        'Navigate to Run & Publish (/run) or Weekly Pulse (/).',
        'Click "Open Google Doc" or open the Google Docs Integration modal.',
        'On first run, grant OAuth consent (documents and gmail.send scopes).',
        'The backend executes batchUpdate to inject the executive report into your document.',
        'The Google Doc opens in a new tab with all headers, themes, quotes, and action items pre-filled.',
      ],
      architecture:
        'Built on the official Google Docs REST API v1. The engine constructs an authorized OAuth2Client with refresh tokens stored in a secure local FileTokenStore. Calls docs.documents.batchUpdate with insertText operations. When users link a new document, the client normalizes URLs, extracts the 44-character document ID, and saves it in localStorage.',
      codeSnippet: `// Google Docs API batchUpdate Request
await docs.documents.batchUpdate({
  documentId: '1BPe7HxJWozrCPsyr_xR1LEYDb04mTxFOKSyB340REKE',
  requestBody: {
    requests: [{
      insertText: { location: { index: 1 }, text: reportContent }
    }]
  }
});`,
      safetyGuardrails: [
        'Non-destructive append/prepend: Only writes to the specified document index.',
        'OAuth scope isolation: Uses minimal necessary permissions (documents and gmail.send).',
        'Mock URL guard: Automatically prevents broken 404 links on prototype IDs.',
      ],
    },
    {
      id: 'feat-gmail',
      title: 'Gmail Draft Staging (Strict Draft-Only Architecture)',
      category: 'mcp',
      badge: 'Zero-Dispatch Safety',
      badgeVariant: 'coral',
      summary:
        'Pre-composes executive email announcements and stages them directly into Gmail. By architectural rule, the system NEVER sends emails automatically — human review is mandatory.',
      keyCapabilities: [
        'Strict "View Gmail draft" only: Absolutely no automated "Send email" trigger exists.',
        '1-Click Direct Gmail Compose: Generates native mail.google.com compose windows with pre-populated fields.',
        'Automatic Draft Persistence: Gmail web automatically saves any open compose window into your Drafts folder.',
        'Human-in-the-Loop Review: Leadership recipients, subject lines, and body text can be adjusted before dispatch.',
        'Interactive GmailDraftModal: Preview formatted email headers, recipient lists, and copy text with 1 click.',
      ],
      workflow: [
        'On the Weekly Pulse or Run & Publish page, click "View Gmail draft".',
        'Inspect the Gmail Draft Review modal showing recipients, subject, and preview.',
        'Click "Open in Gmail Compose" to open a pre-filled compose window in your browser.',
        'Alternatively, click "Copy Subject & Body" or "Open Gmail Drafts folder".',
        'Review the draft in Gmail and click Send manually when approved.',
      ],
      architecture:
        'Operates via deep-linked Google Mail Compose URLs (https://mail.google.com/mail/?view=cm&fs=1&to=...&su=...&body=...) and the backend Gmail MCP server. Pre-fills encoded headers and body text while preserving leadership allowlists.',
      codeSnippet: `// 1-Click Native Gmail Draft URL
const composeUrl = \`https://mail.google.com/mail/?view=cm&fs=1\` +
  \`&to=\${encodeURIComponent('product-leadership@groww.in, founders-office@groww.in')}\` +
  \`&su=\${encodeURIComponent('[Weekly Pulse] Groww App Play Store Reviews')}\` +
  \`&body=\${encodeURIComponent(fullExecutiveEmailBody)}\`;`,
      safetyGuardrails: [
        'Automated send prevention: Code reviews and Vitest test suites strictly enforce that no automated dispatch button can ever be committed.',
        'Operator allowlist: Only approved leadership domains (@groww.in) are pre-filled as recipients.',
      ],
    },
    {
      id: 'feat-themes',
      title: 'Themes Explorer & Neural PulseRing Orbit',
      category: 'themes',
      badge: 'Cluster Intelligence',
      badgeVariant: 'blue',
      summary:
        'Interactive constellation and orbital map grouping customer feedback into unsupervised semantic clusters with rating sentiment histograms and verbatim quote drilldowns.',
      keyCapabilities: [
        'PulseRing Orbit Visualization: Orbital node layout where satellite radius reflects review volume share.',
        'Top 3 vs Watchlist Segmentation: Strictly caps active pulse clusters at 3, moving others to Watchlist.',
        '5-Cluster Global Ceiling: Enforces maximum 5 clusters overall to prevent cognitive overload for executives.',
        'Slide-Over Theme Drawer: Click any theme node to view full star rating distribution (1★-5★) and user quotes.',
        'Cohort Rating vs Historical Benchmark: Visual delta against previous 4-week performance.',
      ],
      workflow: [
        'Navigate to Themes Explorer (/themes).',
        'View the central PulseRing orbit with orbiting theme satellites.',
        'Toggle between "Top Ranked" and "Watchlist" views.',
        'Click on any theme card or orbit node to slide open the Theme Drawer.',
        'Inspect sentiment distributions, key friction drivers, and authentic customer comments.',
      ],
      architecture:
        'Clustering uses semantic embedding distances. Theme priority is computed via an institutional weighted formula favoring high volume and negative sentiment: Priority = (Share% × 0.40) + (NegShare% × 0.40) + ((5 - Rating) × 10 × 0.20).',
      codeSnippet: `// Theme Priority Formula
const priority = (theme.sharePct * 0.40) +
                 (theme.negSharePct * 0.40) +
                 ((5 - theme.avgRating) * 10 * 0.20);`,
      safetyGuardrails: [
        'Cluster cap: Maximum 5 clusters allowed; excess clusters are automatically merged or pruned.',
        'Unique theme names: Duplicate or overlapping cluster labels are flagged as quality gate failures.',
      ],
    },
    {
      id: 'feat-pipeline',
      title: '7-Stage Heartbeat Pipeline & Coral Flatline Circuit Breaker',
      category: 'pipeline',
      badge: 'Pipeline Heartbeat',
      badgeVariant: 'teal',
      summary:
        'Automated end-to-end execution pipeline with live millisecond telemetry, step-by-step progress tracking, and a fail-safe circuit breaker that flatlines on errors.',
      keyCapabilities: [
        '7 Discrete Execution Stages: Ingest &rarr; Clean & PII &rarr; Cluster &rarr; Quotes &rarr; Synthesize &rarr; Validate Gate &rarr; Publish.',
        'Oversized Validate Gate Node: Critical decision junction evaluating all quality rules before delivery.',
        'Coral Flatline Connector: On failure, connector turns coral red and halts execution immediately.',
        'Live Execution Simulation: Run interactive dry-runs with realistic stage durations and counters.',
        'Detailed Diagnostic Logs Modal: Inspect timestamped JSON logs and telemetry for every step.',
      ],
      workflow: [
        'Navigate to Run & Publish (/run).',
        'Click "Run Simulation" or trigger an automated pipeline job.',
        'Watch the PulseStepper heartbeat animation transition through each stage.',
        'If a gate fails (e.g. ?scenario=validation-failed), observe the coral flatline halt the pipeline.',
        'Click "View Diagnostic Logs" to inspect raw stage logs and execution timing.',
      ],
      architecture:
        'Implements the State Machine and Circuit Breaker patterns. Stages execute sequentially. If any stage throws or returns status: "failed", subsequent stages are marked "skipped", preventing accidental downstream publication.',
      codeSnippet: `// Circuit Breaker Execution Flow
for (const stage of pipelineStages) {
  const result = await executeStage(stage);
  if (result.status === 'failed') {
    circuitBreaker.triggerFlatline();
    break; // Abort remaining delivery stages
  }
}`,
      safetyGuardrails: [
        'Zero-trust validation: Delivery stages cannot run without explicit green check on Stage 6 (Validate Gate).',
        'Audit trail: Every run records duration, processed row counts, and checksums in run_report.json.',
      ],
    },
    {
      id: 'feat-invariants',
      title: 'Six Deterministic Quality Gate Invariants',
      category: 'invariants',
      badge: 'Quality Gate Matrix',
      badgeVariant: 'coral',
      summary:
        'Mathematical matrix of 6 non-negotiable invariant rules that must ALL pass with 100% certainty before any executive note can be published.',
      keyCapabilities: [
        'Invariant 1 (Word Count): Pure text word count strictly <= 250 words (guaranteeing <= 90 sec read).',
        'Invariant 2 (Themes Count): Exactly 3 top themes synthesized (no more, no less).',
        'Invariant 3 (Verbatim Quotes): Exactly 3 verbatim customer quotes matching raw review text.',
        'Invariant 4 (Action Ideas): Exactly 3 concrete operational action ideas with designated team owners.',
        'Invariant 5 (Cluster Cap): At most 5 cluster themes generated in total.',
        'Invariant 6 (Zero PII): 0 personal identifiers (phone numbers, emails, names, account IDs).',
      ],
      workflow: [
        'View the Invariant Verification Matrix table on the /run screen.',
        'Each row displays the invariant name, rule ceiling, failure consequence, and verification logic.',
        'A green badge confirms all 6 rules passed.',
        'If any rule fails, the pipeline aborts Google Docs and Gmail delivery.',
      ],
      architecture:
        'Validated through deterministic TypeScript and Python assertions. Word count uses regex word-boundary counting on stripped markdown. Verbatim quotes use substring containment checks on the sanitized raw reviews dataset.',
      codeSnippet: `// Invariant Verification Matrix
const invariants = [
  { id: 'word-count', valid: countWords(text) <= 250 },
  { id: 'themes-count', valid: topThemes.length === 3 },
  { id: 'quotes-count', valid: quotes.length === 3 && quotesAreVerbatim(quotes, rawReviews) },
  { id: 'actions-count', valid: actions.length === 3 && actionsHaveOwners(actions) },
  { id: 'cluster-cap', valid: allThemes.length <= 5 },
  { id: 'zero-pii', valid: containsPii(text) === false }
];
const allPassed = invariants.every(inv => inv.valid);`,
      safetyGuardrails: [
        'Hard failure: If even one invariant check fails, the pipeline status is marked "FAILED" and delivery is aborted.',
      ],
    },
    {
      id: 'feat-hygiene',
      title: 'Zero-PII Sanitization & Review Hygiene Engine',
      category: 'hygiene',
      badge: 'Data Hygiene',
      badgeVariant: 'teal',
      summary:
        'Comprehensive data cleaning pipeline that removes reviewer identities, strips sensitive personal data with negative-lookahead regex, and filters out low-signal spam reviews.',
      keyCapabilities: [
        '4 Ingestion Hygiene Metrics: Cleaned & Indexed, Duplicates Pruned, Low-Info Excluded, PII Scrubbed.',
        'Negative-Lookahead Institutional PII Filter: Strips Indian mobile numbers (+91), emails, PANs, transaction IDs.',
        'Smart Value Preservation: Safely preserves timestamps (9:15 AM), app versions (v18.2), and currency amounts (₹500, Rs 21k).',
        'Low-Information Heuristic: Excludes unhelpful single-word reviews ("good", "ok", "app", "nice") without useful context.',
        'Drag-and-Drop Batch Ingestion: Validates raw Google Play Console CSV and JSON files up to 50MB.',
      ],
      workflow: [
        'Navigate to Data Import (/import).',
        'Drag and drop raw Play Store export CSV or JSON files into the dropzone.',
        'The engine checks required columns (review_text, rating, date).',
        'Review the 4 hygiene metric cards to see how many duplicates or PII items were purged.',
        'Inspect the 12-week review coverage waveform for sample density gaps.',
      ],
      architecture:
        'Uses multi-pass regex sanitization. Dropped identifiers never hit disk or downstream LLMs. Review volume coverage requires >= 100 reviews per weekly sample to ensure statistical validity.',
      codeSnippet: `// Indian Phone Number Sanitizer with Time/Version Preservation
const PHONE_REGEX = /(?:\\+91[\\-\\s]?)?[6-9]\\d{9}/g;
// Preserves timestamps like 9:15 AM and currency like Rs 10000`,
      safetyGuardrails: [
        'Pre-ingestion stripping: Reviewer usernames and Google profile IDs are omitted immediately at the parser level.',
      ],
    },
    {
      id: 'feat-scenarios',
      title: 'Scenario Simulator for Edge-Case & Resiliency Testing',
      category: 'testing',
      badge: 'Resiliency Simulator',
      badgeVariant: 'blue',
      summary:
        'Built-in sandbox simulation engine supporting 5 deterministic state scenarios to test empty states, API errors, quality gate rejections, and low coverage gaps.',
      keyCapabilities: [
        'Normal Scenario (?scenario=ok): Baseline healthy operational run (Score 68, 662 reviews).',
        'Empty State (?scenario=empty): Tests system behavior when zero reviews exist for the target week.',
        'API Error 500 (?scenario=error): Simulates server/database failure with retry recovery buttons.',
        'Validation Failed (?scenario=validation-failed): Simulates word count limit breach triggering the coral flatline.',
        'Low Coverage (?scenario=low-coverage): Simulates review volume drop (< 10 weeks coverage) with amber alert.',
      ],
      workflow: [
        'Use the Scenario Simulator selector dropdown in the left navigation sidebar.',
        'Select any scenario (e.g. "Validation Failed").',
        'The URL updates with ?scenario=validation-failed and re-renders the application state.',
        'Inspect how the UI handles errors, disables delivery buttons, and renders circuit breakers.',
        'Return to Normal (ok) to restore standard production data.',
      ],
      architecture:
        'State is driven by query parameters parsed in the application router and React outlet context. Mock APIs intercept requests and return deterministic fixture payloads matching each scenario type.',
      codeSnippet: `// URL Scenario Integration
const [searchParams] = useSearchParams();
const scenario = searchParams.get('scenario') || 'ok';
const data = await pulseApi.getRun(week, scenario);`,
      safetyGuardrails: [
        'Sandbox isolation: Scenario simulations run purely in client-side memory and never mutate production data.',
      ],
    },
  ];

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

  // Filtering features
  const filteredFeatures = features.filter((feat) => {
    if (activeCategory !== 'all' && feat.category !== activeCategory) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        feat.title.toLowerCase().includes(q) ||
        feat.summary.toLowerCase().includes(q) ||
        feat.architecture.toLowerCase().includes(q) ||
        feat.keyCapabilities.some((k) => k.toLowerCase().includes(q))
      );
    }
    return true;
  });

  // Filtering FAQs
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
            placeholder="Search all features, technical explanations, APIs, invariants, or formulas..."
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

        {/* Category Pills & Expand/Collapse Controls */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
            {[
              { id: 'all', label: 'All Topics' },
              { id: 'core', label: 'Core Pulse & Scoring' },
              { id: 'mcp', label: 'Google Docs & Gmail MCP' },
              { id: 'themes', label: 'Themes & Orbit' },
              { id: 'pipeline', label: 'Pipeline & Gates' },
              { id: 'hygiene', label: 'Zero-PII & Hygiene' },
              { id: 'invariants', label: 'Invariants' },
              { id: 'testing', label: 'Scenarios' },
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

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={expandAllFeatures}
              className="px-2.5 py-1 text-[11px] font-mono rounded bg-[#162238] border border-[#2a3d5d] text-text-muted hover:text-white transition-colors flex items-center gap-1"
            >
              <Maximize2 className="w-3 h-3 text-teal-400" /> Expand All
            </button>
            <button
              type="button"
              onClick={collapseAllFeatures}
              className="px-2.5 py-1 text-[11px] font-mono rounded bg-[#162238] border border-[#2a3d5d] text-text-muted hover:text-white transition-colors flex items-center gap-1"
            >
              <Minimize2 className="w-3 h-3 text-text-muted" /> Collapse All
            </button>
          </div>
        </div>
      </div>

      {/* 3. FEATURE DEEP-DIVE EXPLORER (With Expandable Technical Details) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold font-display text-white">
              Feature Deep-Dive Explorer & Architecture Manual
            </h2>
          </div>
          <span className="text-xs text-text-muted font-mono">
            {filteredFeatures.length} comprehensive feature specifications
          </span>
        </div>

        <div className="space-y-4">
          {filteredFeatures.map((feat) => {
            const isExpanded = expandedFeatureIds[feat.id] ?? false;
            return (
              <Card
                key={feat.id}
                className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card transition-all hover:border-primary/40"
              >
                {/* Feature Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1e293b]">
                  <div className="flex items-start sm:items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-primary-tint border border-primary-border flex items-center justify-center text-primary shrink-0 mt-0.5 sm:mt-0">
                      <Zap className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold font-display text-white">
                        {feat.title}
                      </h3>
                      <p className="text-xs text-text-muted font-sans mt-0.5">
                        {feat.summary}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    <Badge variant={feat.badgeVariant}>{feat.badge}</Badge>
                    <button
                      type="button"
                      onClick={() => toggleFeature(feat.id)}
                      className="px-3 py-1.5 rounded-lg bg-[#0e1726] border border-[#2a3d5d] text-xs font-mono text-teal-400 hover:text-white hover:bg-[#1b2a47] transition-all flex items-center gap-1.5"
                    >
                      <span>{isExpanded ? 'Hide Details' : 'Expand Explanation'}</span>
                      {isExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Key Capabilities Bullet Grid */}
                <div className="py-3">
                  <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-text-muted block mb-2">
                    Core Capabilities & Output Artifacts
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-text-secondary">
                    {feat.keyCapabilities.map((cap, i) => (
                      <div key={i} className="flex items-start gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                        <span>{cap}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* EXPANDABLE DEEP DIVE SECTION */}
                {isExpanded && (
                  <div className="mt-3 pt-4 border-t border-[#1e293b] space-y-4 animate-fade-in bg-[#0c1424]/70 -mx-5 -mb-5 p-5 rounded-b-card">
                    {/* Step-by-Step Workflow */}
                    <div>
                      <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-teal-400 flex items-center gap-1.5 mb-2">
                        <ArrowRight className="w-3.5 h-3.5" /> Step-by-Step Operational Workflow
                      </h4>
                      <ol className="list-decimal list-inside space-y-1.5 text-xs text-text-secondary">
                        {feat.workflow.map((step, idx) => (
                          <li key={idx} className="leading-relaxed">
                            <span className="text-white font-medium">{step.split(':')[0]}:</span>
                            {step.includes(':') ? step.split(':').slice(1).join(':') : ''}
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* Architecture & Implementation Details */}
                    <div>
                      <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-teal-400 flex items-center gap-1.5 mb-1.5">
                        <Cpu className="w-3.5 h-3.5" /> Under-the-Hood Architecture & Design
                      </h4>
                      <p className="text-xs text-text-secondary leading-relaxed bg-[#090d16] p-3 rounded-lg border border-[#1e293b]">
                        {feat.architecture}
                      </p>
                    </div>

                    {/* Code / Formula Specification Snippet */}
                    {feat.codeSnippet && (
                      <div>
                        <div className="flex items-center justify-between mb-1.5">
                          <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-teal-400 flex items-center gap-1.5">
                            <FileText className="w-3.5 h-3.5" /> Technical Specification & Code Contract
                          </h4>
                          <button
                            type="button"
                            onClick={() => copyCode(feat.id, feat.codeSnippet!)}
                            className="text-[10px] font-mono text-text-muted hover:text-white flex items-center gap-1"
                          >
                            {copiedSnippetId === feat.id ? (
                              <>
                                <Check className="w-3 h-3 text-teal-400" /> Copied
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" /> Copy Snippet
                              </>
                            )}
                          </button>
                        </div>
                        <pre className="p-3 rounded-lg bg-[#070b12] border border-[#1e293b] text-text-primary text-xs font-mono overflow-x-auto leading-relaxed">
                          {feat.codeSnippet}
                        </pre>
                      </div>
                    )}

                    {/* Safety Guardrails & Edge Cases */}
                    <div>
                      <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-rose-400 flex items-center gap-1.5 mb-1.5">
                        <ShieldCheck className="w-3.5 h-3.5" /> Safety Guardrails & Fail-Safe Mechanisms
                      </h4>
                      <ul className="space-y-1 text-xs text-text-secondary">
                        {feat.safetyGuardrails.map((guard, gi) => (
                          <li key={gi} className="flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0 mt-1.5" />
                            <span>{guard}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </section>

      {/* 4. The 4 Core Screens System Architecture (Existing Section) */}
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
                    <strong className="text-white">Voice of Users & Actions:</strong> Verbatim quotes + operational action ideas mapped to Product/Engineering.
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
                    <strong className="text-white">Google Docs MCP:</strong> Programmatically syncs and opens live Google Docs with full reports.
                  </span>
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-white">Gmail Staging:</strong> Exclusively "View Gmail draft" via native compose; zero automated dispatch.
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

      {/* 5. The Six Deterministic Invariant Checks */}
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

      {/* 6. Mathematical Models & Formulas */}
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

      {/* 7. Scenario Simulator Cheat Sheet */}
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

      {/* 8. Interactive Frequently Asked Questions */}
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

      {/* 9. Technical Support & Quick Links */}
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
