export function requirePublishableKey(key: string | undefined): void {
  if (key && !key.startsWith('sb_publishable_')) {
    throw new Error('VITE_SUPABASE_PUBLISHABLE_KEY must start with sb_publishable_. Every visitor can read it, so a secret key is banned here.');
  }
}
