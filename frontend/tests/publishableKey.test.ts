import { expect, it } from 'vitest';
import { requirePublishableKey } from '../publishableKey';

it.each(['sb_publishable_abc', '', undefined])('builds with %s', (key) => {
  expect(() => requirePublishableKey(key)).not.toThrow();
});

it.each(['sb_secret_abc', 'eyJhbGciOiJIUzI1NiJ9.service.role', 'anything'])('refuses to build %s into the page', (key) => {
  expect(() => requirePublishableKey(key)).toThrow('VITE_SUPABASE_PUBLISHABLE_KEY');
  expect(() => requirePublishableKey(key)).not.toThrow(key);
});
