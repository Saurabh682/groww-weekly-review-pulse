import React from 'react';
import { Search } from 'lucide-react';
import { Button } from '../../components/Button';
import { Platform, StoreCandidate, StoreSearch } from '../../data/types';
import { formatIndianNumber, formatRating } from '../../lib/format';
import { STORE_NAMES } from '../../lib/stores';
import { Choice } from './choices';
import { TextField } from './TextField';

const ENTER_ID: Record<Platform, { option: string; field: string }> = {
  play_store: { option: 'Enter a package name', field: 'Package name' },
  app_store: { option: 'Enter an App Store ID', field: 'App Store ID' },
};

interface OptionProps {
  store: string;
  checked: boolean;
  onSelect: () => void;
  children: React.ReactNode;
}

const Option: React.FC<OptionProps> = ({ store, checked, onSelect, children }) => (
  <label
    className={`flex items-center gap-3 px-3 py-2 rounded-lg border text-xs cursor-pointer transition-colors ${
      checked ? 'bg-primary-tint border-primary-border' : 'border-border-subtle hover:bg-surface-elevated'
    }`}
  >
    <input type="radio" name={store} checked={checked} onChange={onSelect} className="accent-primary shrink-0" />
    {children}
  </label>
);

function ratingText({ rating, rating_count }: StoreCandidate): string {
  if (rating === null) return 'No rating';
  return rating_count === null ? formatRating(rating) : `${formatRating(rating)} • ${formatIndianNumber(rating_count)} ratings`;
}

interface CandidateProps {
  candidate: StoreCandidate;
}

const Candidate: React.FC<CandidateProps> = ({ candidate }) => (
  <>
    {candidate.icon_url && (
      <img src={candidate.icon_url} alt="" referrerPolicy="no-referrer" className="w-8 h-8 rounded-lg shrink-0" />
    )}
    <span className="min-w-0">
      <span className="block font-bold text-text-primary break-words">{candidate.title}</span>
      {candidate.developer && <span className="block text-text-secondary break-words">{candidate.developer}</span>}
      <span className="block text-2xs font-mono text-text-muted">{ratingText(candidate)}</span>
    </span>
  </>
);

interface StoreChoiceProps {
  search: StoreSearch;
  choice: Choice | null;
  searching: boolean;
  onChoose: (choice: Choice) => void;
  onSearchAgain: () => void;
}

export const StoreChoice: React.FC<StoreChoiceProps> = ({ search, choice, searching, onChoose, onSearchAgain }) => {
  const enterId = ENTER_ID[search.platform];
  return (
    <fieldset className="min-w-0 space-y-2">
      <legend className="mb-2 text-xs font-bold font-display text-white">{STORE_NAMES[search.platform]}</legend>
      {search.message && <p className="text-xs text-text-secondary">{search.message}</p>}
      {search.status === 'error' && (
        <Button
          variant="secondary"
          size="sm"
          icon={<Search className="w-3.5 h-3.5" />}
          loading={searching}
          onClick={onSearchAgain}
        >
          Search again
        </Button>
      )}
      {search.candidates.map((candidate) => (
        <Option
          key={candidate.listing_id}
          store={search.platform}
          checked={choice?.kind === 'found' && choice.id === candidate.listing_id}
          onSelect={() => onChoose({ kind: 'found', id: candidate.listing_id })}
        >
          <Candidate candidate={candidate} />
        </Option>
      ))}
      <Option
        store={search.platform}
        checked={choice?.kind === 'entered'}
        onSelect={() => onChoose({ kind: 'entered', id: '' })}
      >
        {enterId.option}
      </Option>
      {choice?.kind === 'entered' && (
        <TextField
          label={enterId.field}
          value={choice.id}
          maxLength={search.platform === 'play_store' ? 200 : 20}
          onChange={(id) => onChoose({ kind: 'entered', id })}
        />
      )}
      <Option store={search.platform} checked={choice?.kind === 'absent'} onSelect={() => onChoose({ kind: 'absent' })}>
        Not on this store
      </Option>
    </fieldset>
  );
};
