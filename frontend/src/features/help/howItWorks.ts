import { FaqItem, FeatureDetail } from './entries';
import { HELP_FACTS } from './liveApps';

export const NOTE_FACTS = {
  maxWords: 250,
  quotes: 3,
  actions: 3,
  quoteMinWords: 6,
  quoteMaxWords: 22,
  actionMaxWords: 30,
  minClusterSharePct: 3,
  groupOverWords: 8,
  shortCoverageWeeks: 8,
};

export const RANK_FORMULA = 'share × (0.6 + 0.4 × negative share)';

export const HOW_IT_WORKS_FEATURES: FeatureDetail[] = [
  {
    id: 'feat-note',
    title: 'The Weekly Note',
    category: 'note',
    badge: 'Weekly Note',
    badgeVariant: 'teal',
    summary: `A note of at most ${NOTE_FACTS.maxWords} words for each live app, written every Monday from the last ${HELP_FACTS.windowWeeks} weeks of reviews.`,
    keyCapabilities: [
      `Top themes: The ${HELP_FACTS.topThemes} themes ranked highest, each with its share of reviews and its average rating.`,
      `Quotes: ${NOTE_FACTS.quotes} sentences copied word for word from ${NOTE_FACTS.quotes} different reviews, each ${NOTE_FACTS.quoteMinWords} to ${NOTE_FACTS.quoteMaxWords} words long.`,
      `Actions: ${NOTE_FACTS.actions} suggested next steps, one for each top theme, each with a team that owns it.`,
      'Store coverage: Says which stores were read and whether either was only partly covered.',
      `Short history: The note says so when there are fewer than ${NOTE_FACTS.shortCoverageWeeks} weeks of reviews.`,
    ],
    workflow: [
      'Collect: New reviews are stored every day.',
      'Group: On Monday the reviews in the window are grouped into themes.',
      'Write: The note is built from the top themes, quotes and actions.',
      'Check: The note must pass every check before it is published.',
      'Publish: It goes to a Google Doc and a Gmail draft.',
    ],
    architecture:
      'Quotes are picked from the stored reviews, never written by a model. The suggested actions come from a fixed list for the kind of app, or from a general rule when no entry fits the theme.',
    safetyGuardrails: [
      `No note is written from fewer than ${HELP_FACTS.minReviews} usable reviews.`,
      'A note that fails a check is not published, and the last published note stays as it was.',
    ],
  },
  {
    id: 'feat-themes',
    title: 'Themes: How Reviews Are Grouped and Ranked',
    category: 'themes',
    badge: 'Themes',
    badgeVariant: 'blue',
    summary: `Reviews with similar meaning are grouped into at most ${HELP_FACTS.maxThemes} themes. The ${HELP_FACTS.topThemes} ranked highest go into the note.`,
    keyCapabilities: [
      `Small groups: A group with less than ${NOTE_FACTS.minClusterSharePct}% of the reviews is joined to the nearest larger one.`,
      'Names: A model names each theme. If that fails, a name is made from the most common words.',
      `Ranking: Each theme scores ${RANK_FORMULA}, so large themes with many low ratings come first.`,
      'Problems first: If the top themes are all praise, the highest-ranked problem theme takes the last place.',
    ],
    workflow: [
      'Read meaning: Each review is turned into numbers that describe its meaning.',
      'Group: Reviews close in meaning form one theme.',
      'Rank: Themes are scored and sorted.',
      'Show: The app page lists every theme and marks the top ones "In Pulse".',
    ],
    architecture:
      `Only English reviews of more than ${NOTE_FACTS.groupOverWords} words are grouped. Shorter or other-language reviews still count toward the totals on the app page.`,
    safetyGuardrails: [
      'Two top themes never share a name.',
      'Ties are broken the same way every time, so a rerun gives the same order.',
    ],
  },
  {
    id: 'feat-checks',
    title: 'Checks Before Publishing',
    category: 'checks',
    badge: 'Checks',
    badgeVariant: 'coral',
    summary: 'Every note is checked before it is published. If one check fails, nothing is published for that week.',
    keyCapabilities: [
      `Length: At most ${NOTE_FACTS.maxWords} words.`,
      `Themes: Exactly ${HELP_FACTS.topThemes} top themes, with different names.`,
      `Quotes: Exactly ${NOTE_FACTS.quotes}, each found word for word in its review, from ${NOTE_FACTS.quotes} different reviews.`,
      `Actions: Exactly ${NOTE_FACTS.actions}, each tied to a top theme and at most ${NOTE_FACTS.actionMaxWords} words.`,
      'Privacy: No phone number, email address, account number or similar detail anywhere in the note.',
    ],
    workflow: [
      'Build: The note is written for the week.',
      'Check: Every rule above is tested.',
      'Stop or publish: A failed check stops the run and records why.',
    ],
    architecture:
      'If the check itself fails with an error, the note counts as failed. The run history shows it, and the next Monday tries again.',
    safetyGuardrails: ['A failed note never replaces the last published one.'],
  },
  {
    id: 'feat-publishing',
    title: 'Google Doc and Gmail Draft',
    category: 'publishing',
    badge: 'Draft Only',
    badgeVariant: 'coral',
    summary: 'Each published note is written to a Google Doc for the app and saved as a Gmail draft. No email is ever sent.',
    keyCapabilities: [
      'Google Doc: One Doc per app and week. A rerun of the same week rewrites that Doc instead of making a second one.',
      'Gmail draft: One draft per app and week. A rerun updates that draft instead of making a second one.',
      'Links: "Open Google Doc" and "View Gmail draft" on the app page open what was written for that week.',
    ],
    workflow: [
      'Publish: After the checks pass, the note goes to Google Docs and Gmail.',
      'Review: A person opens the draft in Gmail and reads it.',
      'Send: Only that person can send it, from Gmail.',
    ],
    architecture:
      'Google Docs and Gmail are reached through Composio, using accounts connected once by the operator. The system can create and update Docs, and create and update drafts. It has no way to send an email.',
    safetyGuardrails: [
      'There is no send step anywhere in the system.',
      'A failed Doc or draft write marks the run as failed. It is not repeated on its own, so no second Doc or draft appears.',
    ],
  },
  {
    id: 'feat-cleaning',
    title: 'Cleaning and Privacy',
    category: 'cleaning',
    badge: 'Privacy',
    badgeVariant: 'teal',
    summary: 'Personal details are removed from every review before it is stored.',
    keyCapabilities: [
      'Removed: Phone numbers, email addresses, UPI IDs, PAN and Aadhaar numbers, account endings, links, handles and similar details.',
      'Reviewer names: Never stored.',
      'Duplicates: The same review read twice is stored once.',
      `Short reviews: Only reviews of more than ${NOTE_FACTS.groupOverWords} words are grouped into themes. Shorter ones still count in the totals.`,
      'Quotes: Only English reviews can be quoted.',
    ],
    workflow: [
      'Read: Reviews come from Google Play and the App Store.',
      'Clean: Personal details are replaced with [REDACTED].',
      'Store: The cleaned review is saved for its app.',
    ],
    architecture:
      'Cleaning happens before anything is saved, so the raw text with personal details is never stored. A quote that contains [REDACTED] is not used.',
    safetyGuardrails: ['The finished note is checked for personal details once more before it is published.'],
  },
  {
    id: 'feat-sample',
    title: 'Sample Pages',
    category: 'sample',
    badge: 'Sample Data',
    badgeVariant: 'amber',
    summary:
      'Weekly Pulse, Themes, Run & Publish and Data Import show fixed sample data. They are a preview of the design and do not read or change any live app.',
    keyCapabilities: [
      'Scenario selector: Shows the sample pages in different states, such as empty, error or a failed check.',
      'Data Import: Accepts a file to show the flow, but nothing is uploaded or stored.',
      'Run & Publish: Plays a sample run. Nothing is run, written or published.',
    ],
    workflow: [
      'Open a sample page: Use the "Sample data" items in the menu.',
      'Pick a scenario: Use the selector below the menu, or a "Launch" link on this page.',
      'Go back to live data: Choose an app in the top bar.',
    ],
    architecture: 'The sample figures are a fixed data set stored in the dashboard itself. They do not come from the server.',
    safetyGuardrails: ['Nothing on a sample page can change a live app.'],
  },
];

export const HOW_IT_WORKS_FAQS: FaqItem[] = [
  {
    id: 'faq-what',
    category: 'note',
    question: 'What is the Weekly Review Pulse?',
    answer: `It reads the public Google Play and App Store reviews of up to ${HELP_FACTS.slots} apps, groups them into themes, and every Monday writes a short note for each app: the top themes, quotes from real reviews and suggested actions. The note goes to a Google Doc and a Gmail draft.`,
    tag: 'Overview',
  },
  {
    id: 'faq-send',
    category: 'publishing',
    question: 'Can the system send emails?',
    answer:
      'No. It only creates and updates Gmail drafts. A person opens the draft in Gmail and decides whether to send it.',
    tag: 'Draft Only',
  },
  {
    id: 'faq-privacy',
    category: 'cleaning',
    question: 'How are names, phone numbers and other personal details handled?',
    answer:
      'Reviewer names are never stored. Phone numbers, email addresses, UPI IDs, PAN and Aadhaar numbers and similar details are replaced with [REDACTED] before a review is saved, and the finished note is checked again before it is published.',
    tag: 'Privacy',
  },
  {
    id: 'faq-not-published',
    category: 'checks',
    question: 'Why was a week not published?',
    answer: `Either the window held fewer than ${HELP_FACTS.minReviews} usable reviews, or the note failed a check. Collection health and the run history show which. The last published note stays as it was.`,
    tag: 'Checks',
  },
  {
    id: 'faq-ranking',
    category: 'themes',
    question: 'How are the top themes chosen?',
    answer: `Each theme scores ${RANK_FORMULA}. The ${HELP_FACTS.topThemes} highest go into the note, and at least one of them is a problem when the reviews have one.`,
    tag: 'Ranking',
  },
  {
    id: 'faq-sample',
    category: 'sample',
    question: 'Are the sample pages connected to my apps?',
    answer:
      'No. Weekly Pulse, Themes, Run & Publish and Data Import show fixed sample data. A file chosen on Data Import is not uploaded. Choose an app in the top bar to see live data.',
    tag: 'Sample Data',
  },
];

export const SAMPLE_SCENARIOS = [
  { scenario: 'ok', name: 'Normal', desc: 'A complete sample week.', color: 'text-emerald-400', link: '/sample?scenario=ok' },
  { scenario: 'empty', name: 'Empty', desc: 'A week with no reviews yet.', color: 'text-text-muted', link: '/sample?scenario=empty' },
  { scenario: 'error', name: 'Server Error', desc: 'The page when the server does not answer.', color: 'text-amber-400', link: '/sample?scenario=error' },
  { scenario: 'validation-failed', name: 'Failed Check', desc: 'A run whose note failed a check.', color: 'text-rose-400', link: '/run?scenario=validation-failed' },
  { scenario: 'low-coverage', name: 'Low Coverage', desc: 'Fewer weeks of reviews than the window.', color: 'text-amber-400', link: '/import?scenario=low-coverage' },
];
