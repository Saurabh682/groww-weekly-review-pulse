import { STATUS_BADGES } from '../../components/AppStatusBadge';
import { AppStatus } from '../../data/types';
import { TREND_WEEKS } from '../../lib/themeTrend';
import { FaqItem, FeatureDetail } from './entries';

export const HELP_FACTS = {
  slots: 5,
  minReviews: 30,
  windowWeeks: 12,
  maxThemes: 5,
  topThemes: 3,
  trendWeeks: TREND_WEEKS,
};

export const SCHEDULE = {
  daily: { cron: '30 20 * * *', text: 'every day at 02:00 India time' },
  pulse: { cron: '30 3 * * 1', text: 'every Monday at 09:00 India time' },
  monthly: { cron: '30 21 1 * *', text: 'on the 2nd of each month at 03:00 India time' },
};

const BADGE = { badge: 'Your Apps', badgeVariant: 'teal' } as const;

const STATUS_MEANING: Record<AppStatus, string> = {
  pending_backfill: 'The app was added and its first collection has not started.',
  backfilling: 'The first collection is running. It can take up to an hour.',
  active: 'Reviews are collected every day and a pulse is written every Monday.',
  failed: 'The last collection did not work. Collection health shows the reason, and the daily run tries again.',
  archived: 'The app no longer collects reviews. Its page and Docs stay readable.',
};

const STATUS_ORDER: AppStatus[] = ['pending_backfill', 'backfilling', 'active', 'failed', 'archived'];

export const LIVE_APP_FEATURES: FeatureDetail[] = [
  {
    id: 'feat-app-overview',
    title: 'App Overview: One App, Its Latest Pulse',
    category: 'apps',
    ...BADGE,
    summary:
      'The latest weekly pulse of the app you picked, with its themes, theme trend, collection health and links to the Google Doc and the Gmail draft.',
    keyCapabilities: [
      'App picker: The button in the top bar switches apps. Tick "Show archived apps" to list those too.',
      'Usable reviews: The reviews in the window, with very short ones left out.',
      'Grouped: The longer English reviews that the themes are made from.',
      `Themes: At most ${HELP_FACTS.maxThemes} per week. The ${HELP_FACTS.topThemes} marked "In Pulse" are in the note.`,
      `Theme trend: Each theme's share over the last ${HELP_FACTS.trendWeeks} weeks, once there are two weekly pulses.`,
      'Week picker: Opens one of the last 12 weekly pulses on its own page.',
    ],
    workflow: [
      'Pick an app: Use the button in the top bar.',
      'Read the pulse: Start with the numbers, then the theme table.',
      'Check the reviews behind it: Collection health says what each store delivered.',
      'Open the note: "Open Google Doc" and "View Gmail draft" lead to what was written for that week.',
    ],
    architecture:
      'Every figure comes from the stored weekly run. The address holds the app and the week, so a copied link opens the same page for anyone.',
    safetyGuardrails: [
      'Reading the page changes nothing.',
      'The system writes a Gmail draft and never sends an email.',
      'Reviews of one app are never mixed with those of another.',
    ],
  },
  {
    id: 'feat-manage-apps',
    title: 'Manage Apps: Add, Rename, Replace, Archive',
    category: 'apps',
    ...BADGE,
    summary: `Choose which apps get a weekly pulse. There are ${HELP_FACTS.slots} slots, and every live app uses one.`,
    keyCapabilities: [
      'Add app: Search both stores by name, then choose one listing per store or "Not on this store".',
      'Rename: Changes the display name only. Stores, history, Docs and drafts stay as they are.',
      'Replace: Archives an app and gives its slot to a new one. The two histories are not mixed.',
      'Archive: Stops collection and frees the slot. An archived app cannot be made live again.',
    ],
    workflow: [
      'Sign in: Use the sign-in card on Manage Apps.',
      'Add app: Search by name and pick the matching listing in each store.',
      'Review: Check the display name and both listings.',
      'Confirm: Nothing is added before this step.',
    ],
    architecture:
      'Each change is sent once and is never repeated automatically. If no answer comes back, the page says the change may have been saved, so check the list before trying again.',
    safetyGuardrails: [
      'Only a signed-in operator can change anything. Anyone can read the page.',
      'A listing that does not exist in the store is refused.',
      'Archiving asks first and names the app.',
    ],
  },
  {
    id: 'feat-app-status',
    title: 'App Status: What Each Label Means',
    category: 'apps',
    ...BADGE,
    summary: 'The label next to an app name says where the app is between being added and its weekly pulse.',
    keyCapabilities: [
      ...STATUS_ORDER.map((status) => `${STATUS_BADGES[status].text}: ${STATUS_MEANING[status]}`),
      `Not enough reviews yet: The app is active, but its last ${HELP_FACTS.windowWeeks} weeks hold fewer than ${HELP_FACTS.minReviews} reviews with enough text.`,
    ],
    workflow: [
      'Right after adding: The app waits for its first collection.',
      'First collection: It reads the recent reviews of each chosen store.',
      'First pulse: It follows the first collection when there are enough reviews.',
      'Every week: A new pulse is written on Monday.',
    ],
    architecture:
      'An open page checks for news every minute while an app waits for its first result, and whenever you return to the tab. You do not need to reload it.',
    safetyGuardrails: [
      `No pulse is written from fewer than ${HELP_FACTS.minReviews} reviews, because themes from a handful of reviews would mislead.`,
      'A failed collection never removes the last pulse.',
    ],
  },
  {
    id: 'feat-collection',
    title: 'Collection Health & Schedule',
    category: 'apps',
    ...BADGE,
    summary: 'Shows when each store was last read, which days were covered and how many reviews were new.',
    keyCapabilities: [
      `Daily: New reviews are collected ${SCHEDULE.daily.text}.`,
      `Weekly: Pulses are written ${SCHEDULE.pulse.text}, from the last ${HELP_FACTS.windowWeeks} weeks of reviews.`,
      `Monthly check: Last month's reviews are read again ${SCHEDULE.monthly.text}, to fill what was missed.`,
      'New reviews: "7 of 73 read" means 73 were read and 7 were new and inside the window.',
      'Partial: The store did not deliver the start of the window, or its feed had gaps.',
      'Store limit reached: The store gave as many reviews as it allows, so older ones can be missing.',
    ],
    workflow: [
      'Look at the badge: OK, Running, Failed or Turned off, for each store.',
      'Check "Covered": These are the days the last run reached.',
      'Open "Run history": It lists the last 10 runs.',
    ],
    architecture:
      'The schedule runs on GitHub, which can start a run some hours late. Each app runs on its own, so one failed app does not stop the others.',
    safetyGuardrails: [
      'Personal details are removed before a review is stored.',
      'A pulse says when a store was only partly covered.',
    ],
  },
  {
    id: 'feat-sign-in',
    title: 'Operator Sign-in by Email Link',
    category: 'apps',
    ...BADGE,
    summary: 'Operators sign in with a link sent to their email. There is no password.',
    keyCapabilities: [
      'One use: A link works once and for an hour.',
      'Same browser: A link works only in the browser that asked for it.',
      'Existing accounts only: A link goes out only to an address that already has an account.',
    ],
    workflow: [
      'Ask for a link: Enter your email on Manage Apps.',
      'Open the email: Use the same browser, on the same device.',
      'Make changes: The buttons appear next to each app.',
      'Sign out: Use the button in the same card.',
    ],
    architecture:
      'The answer to a link request is the same for every address, so it does not reveal who is an operator. The email service limits how many links go out per hour.',
    safetyGuardrails: [
      'Signing in never creates an account.',
      'The server checks the operator list again on every change.',
    ],
  },
];

export const LIVE_APP_FAQS: FaqItem[] = [
  {
    id: 'faq-no-pulse',
    category: 'apps',
    question: 'Why does an app have no pulse yet?',
    answer: `Its first collection has not finished, it failed, or the last ${HELP_FACTS.windowWeeks} weeks hold fewer than ${HELP_FACTS.minReviews} reviews with enough text. The app page says which. A small app can stay without a pulse for a long time; its reviews are still collected, and the count is checked again every Monday.`,
    tag: 'App Status',
  },
  {
    id: 'faq-first-result',
    category: 'apps',
    question: 'How long until a new app shows something?',
    answer: `If this dashboard is connected to GitHub, the first collection is requested when you add the app. If it is not, the app waits for the daily run, ${SCHEDULE.daily.text}. GitHub can start a run some hours late, and the collection itself can take up to an hour. The message after adding says which applies.`,
    tag: 'First Collection',
  },
  {
    id: 'faq-sign-in-link',
    category: 'apps',
    question: 'Why did my sign-in link not work?',
    answer:
      'It was opened in a different browser, was used before, or is more than an hour old. Ask for a new one and open it in the same browser. If the page says the email limit was reached, wait an hour before asking again.',
    tag: 'Sign-in',
  },
  {
    id: 'faq-slots-full',
    category: 'apps',
    question: `All ${HELP_FACTS.slots} slots are used. How do I add another app?`,
    answer:
      'Use Replace to archive an app and put the new one in its slot, or Archive to free the slot first. The old app stays readable, but it cannot be made live again.',
    tag: 'Manage Apps',
  },
  {
    id: 'faq-app-store-count',
    category: 'apps',
    question: 'Why are there fewer App Store reviews than Google Play reviews?',
    answer:
      "Apple's public feed holds only about the 500 newest reviews for a country. For a busy app that can be less than the whole window, and the pulse then says the App Store is only partly covered.",
    tag: 'Store Limits',
  },
];
