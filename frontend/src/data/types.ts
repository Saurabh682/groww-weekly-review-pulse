export type Sentiment = 'positive' | 'friction' | 'critical';

export interface WeekPoint {
  label: string;
  avgRating: number;
  isCurrent: boolean;
}

export interface Theme {
  id: string;
  label: string;
  summary: string;
  reviewCount: number;
  sharePct: number;
  avgRating: number;
  negShare: number;
  priorityScore: number;
  rank: number;
  sentiment: Sentiment;
  trendVsLastWeek: number; // pct points (+3.2, -1.5)
  inPulse: boolean;         // true for top 3
  ratingDistribution: [number, number, number, number, number]; // 1-star to 5-star counts
  weeklyTrend: number[];    // sparkline values (last 4-6 weeks)
}

export interface Quote {
  id: string;
  text: string;
  themeId: string;
  rating: number;
  verifiedVerbatim: boolean;
}

export interface ActionIdea {
  id: string;
  themeId: string;
  text: string;
  owner: 'Product' | 'Engineering' | 'Support' | 'Growth';
  successSignal: string;
}

export interface SampleReview {
  id: string;
  themeId: string;
  text: string;
  rating: number;
  quoteEligible: boolean;
  ineligibleReason?: string;
}

export interface PulseNote {
  weekStart: string;
  windowStart: string;
  windowEnd: string;
  totalReviews: number;
  avgRating: number;
  pulseScore: number;
  moodLabel: string;
  weeks: WeekPoint[];
  topThemes: Theme[];      // exactly 3
  allThemes: Theme[];      // at most 5
  quotes: Quote[];         // exactly 3
  actions: ActionIdea[];   // exactly 3
  wordCount: number;       // <= 250
  checks: { id: string; label: string; passed: boolean }[];
}

export type StageStatus = 'pending' | 'running' | 'done' | 'failed' | 'skipped';

export interface PipelineStage {
  id: string;
  label: string;
  status: StageStatus;
  durationMs?: number;
  counter?: string;
}

export interface RunState {
  stages: PipelineStage[];          // 7 stages
  validationPassed: boolean;
  validationRows: { id: string; label: string; passed: boolean; detail?: string }[];
  doc?: { title: string; url: string; status: 'Published' | 'Updated'; updatedAt: string };
  draft?: { to: string; subject: string; bodyPreview: string; status: 'Draft created, not sent' };
  mcp: { docs: 'connected' | 'disconnected'; gmail: 'connected' | 'disconnected' };
  error?: string;
}

export interface ImportSummary {
  imported: number;
  duplicatesRemoved: number;
  lowInfoExcluded: number;
  piiRedacted: number;
  weeklyVolume: { week: string; count: number }[];
  coverageWeeks: number;
  history: { fileName: string; date: string; rowsAdded: number }[];
}

export type ScenarioType = 'ok' | 'empty' | 'error' | 'validation-failed' | 'low-coverage';
