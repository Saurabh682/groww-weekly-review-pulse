import { Platform, StoreSearch, StoreSearchResult } from '../../data/types';
import { PLATFORMS } from '../../lib/stores';

export type Choice = { kind: 'found'; id: string } | { kind: 'entered'; id: string } | { kind: 'absent' };
export type Choices = Record<Platform, Choice | null>;

export const NO_CHOICES: Choices = { play_store: null, app_store: null };

export function listingId(choice: Choice | null): string | null {
  return choice && choice.kind !== 'absent' ? choice.id.trim() : null;
}

function listed(choice: Choice | null, { candidates }: StoreSearch): Choice | null {
  const isGone = choice?.kind === 'found' && !candidates.some((candidate) => candidate.listing_id === choice.id);
  return isGone ? null : choice;
}

export function keepListed(choices: Choices, { stores }: StoreSearchResult): Choices {
  return {
    play_store: listed(choices.play_store, stores.play_store),
    app_store: listed(choices.app_store, stores.app_store),
  };
}

export function isDecided(choices: Choices): boolean {
  return PLATFORMS.every((platform) => choices[platform]?.kind === 'absent' || Boolean(listingId(choices[platform])));
}

export function isOnNoStore(choices: Choices): boolean {
  return PLATFORMS.every((platform) => choices[platform]?.kind === 'absent');
}
