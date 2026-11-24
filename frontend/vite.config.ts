/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { requirePublishableKey } from './publishableKey';

export default defineConfig(({ mode }) => {
  requirePublishableKey(loadEnv(mode, __dirname).VITE_SUPABASE_PUBLISHABLE_KEY);
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./tests/setup.ts'],
    },
  };
});
