import { PulseNote, Theme, Quote, ActionIdea, WeekPoint } from '../types';
import { countWords } from '../../lib/countWords';

export const FIXTURE_WEEKS: WeekPoint[] = [
  { label: '24 Aug', avgRating: 4.1, isCurrent: false },
  { label: '31 Aug', avgRating: 4.0, isCurrent: false },
  { label: '07 Sep', avgRating: 3.9, isCurrent: false },
  { label: '14 Sep', avgRating: 3.7, isCurrent: false }, // below 3.8 -> amber
  { label: '21 Sep', avgRating: 3.6, isCurrent: false }, // amber
  { label: '28 Sep', avgRating: 3.9, isCurrent: false },
  { label: '05 Oct', avgRating: 4.0, isCurrent: false },
  { label: '12 Oct', avgRating: 4.2, isCurrent: false },
  { label: '19 Oct', avgRating: 3.8, isCurrent: false },
  { label: '26 Oct', avgRating: 3.6, isCurrent: false }, // amber
  { label: '02 Nov', avgRating: 3.5, isCurrent: false }, // amber
  { label: '09 Nov', avgRating: 3.7, isCurrent: true },  // current beat
];

export const FIXTURE_THEMES: Theme[] = [
  {
    id: 'theme-kyc',
    label: 'KYC & Onboarding Bottlenecks',
    summary: 'Users experience multiday verification stalls and Digilocker timeouts during initial account setup.',
    reviewCount: 226,
    sharePct: 34.2,
    avgRating: 1.8,
    negShare: 82.5,
    priorityScore: 89,
    rank: 1,
    sentiment: 'critical',
    trendVsLastWeek: 4.8,
    inPulse: true,
    ratingDistribution: [142, 48, 20, 10, 6],
    weeklyTrend: [180, 195, 210, 226],
  },
  {
    id: 'theme-upi',
    label: 'UPI & Autopay Reconciliation Lag',
    summary: 'SIP autopay debits without instant balance reflection cause user anxiety and duplicate orders.',
    reviewCount: 182,
    sharePct: 27.5,
    avgRating: 2.2,
    negShare: 71.0,
    priorityScore: 78,
    rank: 2,
    sentiment: 'friction',
    trendVsLastWeek: -2.1,
    inPulse: true,
    ratingDistribution: [95, 52, 22, 9, 4],
    weeklyTrend: [195, 190, 186, 182],
  },
  {
    id: 'theme-crashes',
    label: 'Market-Open Auth & Screen Freezes',
    summary: 'Spikes in 9:15 AM login volume trigger biometric authentication failures and watchlist freezes.',
    reviewCount: 120,
    sharePct: 18.1,
    avgRating: 2.1,
    negShare: 74.3,
    priorityScore: 72,
    rank: 3,
    sentiment: 'critical',
    trendVsLastWeek: 3.5,
    inPulse: true,
    ratingDistribution: [68, 32, 12, 5, 3],
    weeklyTrend: [95, 102, 110, 120],
  },
  {
    id: 'theme-withdrawal',
    label: 'Withdrawal & Settlement Delays',
    summary: 'Confusion around T+1 trading balance locks and multiday payout processing timelines.',
    reviewCount: 75,
    sharePct: 11.4,
    avgRating: 2.4,
    negShare: 64.0,
    priorityScore: 54,
    rank: 4,
    sentiment: 'friction',
    trendVsLastWeek: -1.2,
    inPulse: false,
    ratingDistribution: [35, 22, 10, 5, 3],
    weeklyTrend: [82, 79, 77, 75],
  },
  {
    id: 'theme-ease-of-use',
    label: 'Mutual Fund & Direct SIP UX',
    summary: 'Strong positive reception for zero-commission mutual fund tracking and clean portfolio UI.',
    reviewCount: 59,
    sharePct: 8.8,
    avgRating: 4.8,
    negShare: 4.2,
    priorityScore: 18,
    rank: 5,
    sentiment: 'positive',
    trendVsLastWeek: 1.1,
    inPulse: false,
    ratingDistribution: [1, 2, 3, 11, 42],
    weeklyTrend: [52, 55, 57, 59],
  },
];

export const FIXTURE_QUOTES: Quote[] = [
  {
    id: 'quote-1',
    themeId: 'theme-kyc',
    text: 'KYC verification has been pending for over 5 days with zero status updates. Documents submitted twice already.',
    rating: 1,
    verifiedVerbatim: true,
  },
  {
    id: 'quote-2',
    themeId: 'theme-upi',
    text: 'UPI autopay for SIP got debited twice from bank account but orders still show as pending in Groww.',
    rating: 1,
    verifiedVerbatim: true,
  },
  {
    id: 'quote-3',
    themeId: 'theme-crashes',
    text: 'App crashes continuously at 9:15 AM right at market open. Unable to exit options positions.',
    rating: 1,
    verifiedVerbatim: true,
  },
];

export const FIXTURE_ACTIONS: ActionIdea[] = [
  {
    id: 'action-1',
    themeId: 'theme-kyc',
    text: 'Ship instant OCR document validation and real-time push alerts for Digilocker status transitions.',
    owner: 'Product',
    successSignal: 'Reduce KYC drop-off rate from 18% to <8%',
  },
  {
    id: 'action-2',
    themeId: 'theme-upi',
    text: 'Implement automated dual-switch bank polling before presenting transaction failure to users.',
    owner: 'Engineering',
    successSignal: 'Zero double-debit false negatives within 60s',
  },
  {
    id: 'action-3',
    themeId: 'theme-crashes',
    text: 'Scale market-open auth session cache cluster and enable instant fallback PIN without full restart.',
    owner: 'Engineering',
    successSignal: 'Maintain 9:15-9:30 AM crash-free sessions above 99.8%',
  },
];

// Helper to compute note markdown word count
const NOTE_MARKDOWN_BODY = `
Weekly Review Pulse - Groww Play Store Reviews
Window: 02 Nov 2026 to 08 Nov 2026

Top 3 Themes:
1. KYC & Onboarding Bottlenecks: Users experience multiday verification stalls and Digilocker timeouts during initial account setup.
2. UPI & Autopay Reconciliation Lag: SIP autopay debits without instant balance reflection cause user anxiety and duplicate orders.
3. Market-Open Auth & Screen Freezes: Spikes in 9:15 AM login volume trigger biometric authentication failures and watchlist freezes.

Voice of the Users:
- "KYC verification has been pending for over 5 days with zero status updates. Documents submitted twice already." (1★)
- "UPI autopay for SIP got debited twice from bank account but orders still show as pending in Groww." (1★)
- "App crashes continuously at 9:15 AM right at market open. Unable to exit options positions." (1★)

Operational Action Ideas:
1. Product: Ship instant OCR document validation and real-time push alerts for Digilocker status transitions. Target: Reduce KYC drop-off rate from 18% to <8%.
2. Engineering: Implement automated dual-switch bank polling before presenting transaction failure to users. Target: Zero double-debit false negatives within 60s.
3. Engineering: Scale market-open auth session cache cluster and enable instant fallback PIN without full restart. Target: Maintain 9:15-9:30 AM crash-free sessions above 99.8%.
`.trim();

export const FIXTURE_PULSE_NOTE: PulseNote = {
  weekStart: '09 Nov 2026',
  windowStart: '02 Nov 2026',
  windowEnd: '08 Nov 2026',
  totalReviews: 662,
  avgRating: 3.7,
  pulseScore: 68,
  moodLabel: 'High Friction',
  weeks: FIXTURE_WEEKS,
  topThemes: FIXTURE_THEMES.filter(t => t.inPulse),
  allThemes: FIXTURE_THEMES,
  quotes: FIXTURE_QUOTES,
  actions: FIXTURE_ACTIONS,
  wordCount: countWords(NOTE_MARKDOWN_BODY),
  checks: [
    { id: 'top-themes', label: 'Top 3 themes identified', passed: true },
    { id: 'quotes-verbatim', label: '3 verbatim quotes with review stars', passed: true },
    { id: 'actions', label: '3 operational action ideas', passed: true },
    { id: 'word-count', label: 'Length is ≤ 250 words (90-sec read)', passed: true },
    { id: 'zero-pii', label: 'Zero personal data / PII detected', passed: true },
  ],
};
