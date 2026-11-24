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

export type AppStatus = 'pending_backfill' | 'backfilling' | 'active' | 'failed' | 'archived';
export type Platform = 'play_store' | 'app_store';

export interface AppRecord {
  app_key: string;
  display_name: string;
  status: AppStatus;
  play_package_id: string | null;
  app_store_id: string | null;
  country: string;
  lang: string;
  category: string | null;
  created_at: string;
  archived_at: string | null;
}

export interface AppList {
  slots_used: number;
  slots_total: number;
  apps: AppRecord[];
}

export interface PulseTheme {
  label: string;
  review_count: number;
  share_pct: number;
  avg_rating: number;
  is_top3: boolean;
}

export interface PulseWeek {
  week_start: string;
  status: string;
  window_start: string;
  window_end: string;
  total_reviews: number;
  analyzed_reviews: number;
  avg_rating: number;
  coverage_weeks: number;
  short_coverage: boolean;
  doc_url: string | null;
  draft_created: boolean;
  published_at: string | null;
  themes: PulseTheme[];
}

export interface PulseHistory {
  app_key: string;
  pulses: PulseWeek[];
}

export interface StoreCoverage {
  platform: Platform;
  reviews: number;
  caveat: string | null;
}

export interface PulseWeekDetail extends PulseWeek {
  app_key: string;
  stores: StoreCoverage[];
  note_markdown: string | null;
}

export interface CollectionRun {
  platform: Platform;
  mode: 'backfill' | 'daily' | 'reconcile' | 'csv_import';
  status: 'running' | 'ok' | 'failed' | 'skipped_disabled';
  window_start: string;
  window_end: string;
  covered_start: string | null;
  fetched: number;
  inserted: number;
  source_limit_hit: boolean;
  feed_gaps: number;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface AppHealth {
  app: AppRecord;
  collections: Record<Platform, CollectionRun | null>;
  runs: CollectionRun[];
  stores: StoreCoverage[];
}

export type ApiState<T> =
  | { status: 'loading' }
  | { status: 'waking' }
  | { status: 'ready'; data: T }
  | { status: 'missing'; message: string }
  | { status: 'error'; message: string };

export interface ApiResource<T> {
  state: ApiState<T>;
  retry: () => void;
}

export interface ShellContext {
  currentScenario: ScenarioType;
  selectedWeek: string;
  apps: ApiResource<AppList>;
}
