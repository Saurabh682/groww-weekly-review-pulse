import { AppRecord, Platform } from '../data/types';

export const STORE_NAMES: Record<Platform, string> = { play_store: 'Google Play', app_store: 'App Store' };

export const STORE_LISTINGS: Record<Platform, (app: AppRecord) => string | null> = {
  play_store: (app) => app.play_package_id,
  app_store: (app) => app.app_store_id,
};

export const PLATFORMS: Platform[] = ['play_store', 'app_store'];
