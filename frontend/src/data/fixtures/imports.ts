import { ImportSummary } from '../types';

export const FIXTURE_IMPORT_SUMMARY: ImportSummary = {
  imported: 662,
  duplicatesRemoved: 148,
  lowInfoExcluded: 412,
  piiRedacted: 19,
  coverageWeeks: 12,
  weeklyVolume: [
    { week: '24 Aug', count: 540 },
    { week: '31 Aug', count: 580 },
    { week: '07 Sep', count: 610 },
    { week: '14 Sep', count: 520 },
    { week: '21 Sep', count: 490 },
    { week: '28 Sep', count: 640 },
    { week: '05 Oct', count: 710 },
    { week: '12 Oct', count: 680 },
    { week: '19 Oct', count: 620 },
    { week: '26 Oct', count: 590 },
    { week: '02 Nov', count: 640 },
    { week: '09 Nov', count: 662 },
  ],
  history: [
    { fileName: 'playstore_groww_reviews_nov_w1.csv', date: '09 Nov 2026, 05:45 IST', rowsAdded: 662 },
    { fileName: 'playstore_groww_reviews_nov_w0.csv', date: '02 Nov 2026, 06:10 IST', rowsAdded: 640 },
    { fileName: 'playstore_groww_reviews_oct_w4.csv', date: '26 Oct 2026, 05:50 IST', rowsAdded: 590 },
    { fileName: 'playstore_groww_reviews_oct_w3.csv', date: '19 Oct 2026, 06:05 IST', rowsAdded: 620 },
    { fileName: 'playstore_groww_reviews_oct_w2.csv', date: '12 Oct 2026, 05:55 IST', rowsAdded: 680 },
  ],
};

export const LOW_COVERAGE_IMPORT_SUMMARY: ImportSummary = {
  imported: 124,
  duplicatesRemoved: 42,
  lowInfoExcluded: 88,
  piiRedacted: 4,
  coverageWeeks: 7,
  weeklyVolume: [
    { week: '24 Aug', count: 0 },
    { week: '31 Aug', count: 0 },
    { week: '07 Sep', count: 0 },
    { week: '14 Sep', count: 120 },
    { week: '21 Sep', count: 140 },
    { week: '28 Sep', count: 0 },
    { week: '05 Oct', count: 0 },
    { week: '12 Oct', count: 210 },
    { week: '19 Oct', count: 180 },
    { week: '26 Oct', count: 190 },
    { week: '02 Nov', count: 160 },
    { week: '09 Nov', count: 124 },
  ],
  history: [
    { fileName: 'playstore_groww_partial_batch.csv', date: '09 Nov 2026, 07:15 IST', rowsAdded: 124 },
  ],
};
