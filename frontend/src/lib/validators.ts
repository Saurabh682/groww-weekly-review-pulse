import { PulseNote } from '../data/types';
import { countWords } from './countWords';
import { hasPii } from './piiGuard';

export interface InvariantResult {
  passed: boolean;
  failures: string[];
  checks: { id: string; label: string; passed: boolean; detail?: string }[];
}

export function assertPulseInvariants(note: PulseNote): InvariantResult {
  const failures: string[] = [];
  const checks: { id: string; label: string; passed: boolean; detail?: string }[] = [];

  // 1. Top Themes check (must be exactly 3)
  const topThemesCount = note.topThemes ? note.topThemes.length : 0;
  const themeCheckPassed = topThemesCount === 3;
  if (!themeCheckPassed) {
    failures.push(`Expected exactly 3 top themes, found ${topThemesCount}`);
  }
  checks.push({
    id: 'top-themes',
    label: 'Top 3 themes identified',
    passed: themeCheckPassed,
    detail: `${topThemesCount} / 3 themes`,
  });

  // 2. Quotes check (exactly 3, all verified verbatim)
  const quotesCount = note.quotes ? note.quotes.length : 0;
  const allVerbatim = note.quotes ? note.quotes.every(q => q.verifiedVerbatim) : false;
  const quoteCheckPassed = quotesCount === 3 && allVerbatim;
  if (quotesCount !== 3) {
    failures.push(`Expected exactly 3 quotes, found ${quotesCount}`);
  }
  if (!allVerbatim) {
    failures.push('All quotes must be verified verbatim from user reviews');
  }
  checks.push({
    id: 'quotes-verbatim',
    label: '3 verbatim quotes with review stars',
    passed: quoteCheckPassed,
    detail: `${quotesCount} / 3 verbatim`,
  });

  // 3. Action ideas check (exactly 3)
  const actionsCount = note.actions ? note.actions.length : 0;
  const actionCheckPassed = actionsCount === 3;
  if (!actionCheckPassed) {
    failures.push(`Expected exactly 3 action ideas, found ${actionsCount}`);
  }
  checks.push({
    id: 'actions',
    label: '3 operational action ideas',
    passed: actionCheckPassed,
    detail: `${actionsCount} / 3 actions`,
  });

  // 4. Word count check (<= 250 words)
  // Compile markdown note text if wordCount is not explicitly checked or check provided count
  const compiledText = [
    note.topThemes.map(t => `${t.label}: ${t.summary}`).join(' '),
    note.quotes.map(q => q.text).join(' '),
    note.actions.map(a => `${a.text} ${a.successSignal}`).join(' '),
  ].join(' ');
  const calculatedWords = countWords(compiledText);
  const wordCount = note.wordCount > 0 ? note.wordCount : calculatedWords;
  const wordCheckPassed = wordCount <= 250;
  if (!wordCheckPassed) {
    failures.push(`Total word count exceeds 250 words limit (${wordCount} words)`);
  }
  checks.push({
    id: 'word-count',
    label: 'Length is ≤ 250 words (90-sec read)',
    passed: wordCheckPassed,
    detail: `${wordCount} / 250 words`,
  });

  // 5. Zero PII check
  let piiDetected = false;
  for (const q of note.quotes) {
    if (hasPii(q.text)) piiDetected = true;
  }
  for (const t of note.topThemes) {
    if (hasPii(t.label) || hasPii(t.summary)) piiDetected = true;
  }
  for (const a of note.actions) {
    if (hasPii(a.text) || hasPii(a.successSignal)) piiDetected = true;
  }
  const piiCheckPassed = !piiDetected;
  if (!piiCheckPassed) {
    failures.push('PII or personal data detected in note content');
  }
  checks.push({
    id: 'zero-pii',
    label: 'Zero personal data / PII detected',
    passed: piiCheckPassed,
    detail: piiCheckPassed ? 'Clean' : 'PII detected',
  });

  return {
    passed: failures.length === 0,
    failures,
    checks,
  };
}
