/**
 * Indian numbering system formatting and metric display helpers.
 */

export function formatIndianNumber(num: number): string {
  if (isNaN(num)) return '0';
  return num.toLocaleString('en-IN');
}

export function formatRating(rating: number): string {
  return `${rating.toFixed(1)}★`;
}

export function formatTrend(pct: number): string {
  const prefix = pct > 0 ? '+' : '';
  return `${prefix}${pct.toFixed(1)}%`;
}

export function formatShare(pct: number): string {
  return `${pct.toFixed(1)}%`;
}
