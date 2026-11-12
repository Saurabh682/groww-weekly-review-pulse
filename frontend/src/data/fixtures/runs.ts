import { RunState, PipelineStage } from '../types';

export const INITIAL_PIPELINE_STAGES: PipelineStage[] = [
  { id: 'ingest', label: 'Play Store Ingestion', status: 'done', durationMs: 1420, counter: '662 reviews' },
  { id: 'clean', label: 'Hygiene & Anonymization', status: 'done', durationMs: 840, counter: '662 clean / 0 PII' },
  { id: 'cluster', label: 'Theme Clustering', status: 'done', durationMs: 2310, counter: '5 clusters' },
  { id: 'quotes', label: 'Quote Selection', status: 'done', durationMs: 620, counter: '3 quotes selected' },
  { id: 'synthesize', label: 'Pulse Note Synthesis', status: 'done', durationMs: 1890, counter: '125 words' },
  { id: 'validate', label: 'Validate Invariants (Gate)', status: 'done', durationMs: 410, counter: '5 / 5 passed' },
  { id: 'publish', label: 'Docs & Gmail MCP Delivery', status: 'done', durationMs: 980, counter: 'Published' },
];

export const FIXTURE_RUN_STATE: RunState = {
  stages: INITIAL_PIPELINE_STAGES,
  validationPassed: true,
  validationRows: [
    { id: 'top-themes', label: 'Top 3 themes identified', passed: true, detail: '3 / 3 themes with >8% share' },
    { id: 'quotes-verbatim', label: '3 verbatim quotes with review stars', passed: true, detail: '3 / 3 verified verbatim against clean DB' },
    { id: 'actions', label: '3 operational action ideas', passed: true, detail: 'Assigned to Product & Engineering owners' },
    { id: 'word-count', label: 'Length is ≤ 250 words (90-sec read)', passed: true, detail: '125 words (1.1 min read)' },
    { id: 'zero-pii', label: 'Zero personal data / PII detected', passed: true, detail: 'Negative lookahead regex passed on all blocks' },
    { id: 'coverage', label: 'Weekly volume coverage check', passed: true, detail: '662 reviews (Threshold: ≥100)' },
  ],
  doc: {
    title: 'Groww Weekly Review Pulse - Week of 09 Nov 2026',
    url: 'https://docs.google.com/document/d/mock-groww-weekly-pulse-2026-11-09',
    status: 'Published',
    updatedAt: '09 Nov 2026, 06:30 IST',
  },
  draft: {
    to: 'product-leadership@groww.in, founders-office@groww.in',
    subject: '[Weekly Pulse] Groww App Play Store Reviews — Week of 09 Nov 2026',
    bodyPreview: '662 reviews analyzed (Avg: 3.7★). Top friction: KYC & Onboarding (34.2%), UPI & Autopay Reconciliation (27.5%), Market-Open Screen Freezes (18.1%). Full Google Doc published with 3 operational action ideas.',
    status: 'Draft created, not sent',
  },
  mcp: {
    docs: 'connected',
    gmail: 'connected',
  },
};

export const FAILED_RUN_STATE: RunState = {
  stages: [
    { id: 'ingest', label: 'Play Store Ingestion', status: 'done', durationMs: 1420, counter: '662 reviews' },
    { id: 'clean', label: 'Hygiene & Anonymization', status: 'done', durationMs: 840, counter: '662 clean / 0 PII' },
    { id: 'cluster', label: 'Theme Clustering', status: 'done', durationMs: 2310, counter: '5 clusters' },
    { id: 'quotes', label: 'Quote Selection', status: 'done', durationMs: 620, counter: '3 quotes selected' },
    { id: 'synthesize', label: 'Pulse Note Synthesis', status: 'done', durationMs: 1890, counter: '284 words' },
    { id: 'validate', label: 'Validate Invariants (Gate)', status: 'failed', durationMs: 410, counter: 'Failed' },
    { id: 'publish', label: 'Docs & Gmail MCP Delivery', status: 'skipped', counter: 'Skipped' },
  ],
  validationPassed: false,
  validationRows: [
    { id: 'top-themes', label: 'Top 3 themes identified', passed: true, detail: '3 / 3 themes' },
    { id: 'quotes-verbatim', label: '3 verbatim quotes with review stars', passed: true, detail: '3 / 3 verified verbatim' },
    { id: 'actions', label: '3 operational action ideas', passed: true, detail: '3 / 3 actions' },
    { id: 'word-count', label: 'Length is ≤ 250 words (90-sec read)', passed: false, detail: '284 words exceeds 250 word limit' },
    { id: 'zero-pii', label: 'Zero personal data / PII detected', passed: true, detail: 'Clean' },
  ],
  mcp: {
    docs: 'connected',
    gmail: 'connected',
  },
  error: 'Validation gate rejected synthesized note: word count (284 words) exceeded strict 250-word ceiling. Delivery halted to prevent executive note bloat.',
};
