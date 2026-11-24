export function appPath(appKey: string, rest: string): string {
  return `/apps/${encodeURIComponent(appKey)}/${rest}`;
}
