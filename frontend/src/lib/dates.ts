const DAY_MS = 86_400_000;
const DAYS_PER_WEEK = 7;

function midnight(isoDay: string): Date {
  return new Date(`${isoDay}T00:00:00Z`);
}

export function formatDay(isoDay: string): string {
  return midnight(isoDay).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

export function formatShortDay(isoDay: string): string {
  return midnight(isoDay).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
}

export function formatMoment(isoMoment: string): string {
  return new Date(isoMoment).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' });
}

export function weekLabel(weekStart: string): string {
  return `Week of ${formatDay(weekStart)}`;
}

export function addWeeks(weekStart: string, weeks: number): string {
  const moved = midnight(weekStart).getTime() + weeks * DAYS_PER_WEEK * DAY_MS;
  return new Date(moved).toISOString().slice(0, weekStart.length);
}
