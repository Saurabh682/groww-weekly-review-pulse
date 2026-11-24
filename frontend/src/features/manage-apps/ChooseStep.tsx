import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Button } from '../../components/Button';
import { ErrorState } from '../../components/ErrorState';
import { Modal } from '../../components/Modal';
import { StoreSearchResult } from '../../data/types';
import { PLATFORMS } from '../../lib/stores';
import { Choices, isDecided, isOnNoStore } from './choices';
import { StoreChoice } from './StoreChoice';
import { TextField } from './TextField';
import { RequestState } from './useRequest';

const TERM_LIMIT = 100;

interface ChooseStepProps {
  title: string;
  explanation: string;
  term: string;
  country: string;
  found: StoreSearchResult | null;
  choices: Choices;
  search: RequestState;
  onSearch: (term: string, country: string) => void;
  onSearchAgain: () => void;
  onChoose: (choices: Choices) => void;
  onReview: () => void;
  onClose: () => void;
}

export const ChooseStep: React.FC<ChooseStepProps> = ({
  title,
  explanation,
  term,
  country: firstCountry,
  found,
  choices,
  search,
  onSearch,
  onSearchAgain,
  onChoose,
  onReview,
  onClose,
}) => {
  const [name, setName] = useState(term);
  const [country, setCountry] = useState(firstCountry);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    onSearch(name.trim(), country.trim().toLowerCase());
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      title={title}
      maxWidth="2xl"
      footer={
        <>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            size="sm"
            disabled={!found || search.busy || !isDecided(choices) || isOnNoStore(choices)}
            onClick={onReview}
          >
            Review
          </Button>
        </>
      }
    >
      <div className="space-y-6">
        <p className="text-xs text-text-secondary leading-relaxed">{explanation}</p>
        <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-end">
          <div className="sm:col-span-6">
            <TextField label="App name" value={name} maxLength={TERM_LIMIT} onChange={setName} autoFocus />
          </div>
          <div className="sm:col-span-3">
            <TextField label="Store country" value={country} maxLength={2} onChange={setCountry} />
          </div>
          <div className="sm:col-span-3">
            <Button
              type="submit"
              variant="secondary"
              size="sm"
              icon={<Search className="w-3.5 h-3.5 text-primary" />}
              loading={search.busy}
              disabled={!name.trim() || !country.trim()}
            >
              Search stores
            </Button>
          </div>
        </form>
        {search.problem && <ErrorState title="Search failed" message={search.problem} />}
        {found && (
          <>
            {found.no_matches && (
              <p role="status" className="text-xs text-text-secondary">
                No matches on either store. Check the spelling, or enter the IDs yourself.
              </p>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {PLATFORMS.map((platform) => (
                <StoreChoice
                  key={platform}
                  search={found.stores[platform]}
                  choice={choices[platform]}
                  searching={search.busy}
                  onChoose={(choice) => onChoose({ ...choices, [platform]: choice })}
                  onSearchAgain={onSearchAgain}
                />
              ))}
            </div>
            {isOnNoStore(choices) && (
              <p role="status" className="text-xs text-friction-dark">
                Choose a listing on at least one store.
              </p>
            )}
          </>
        )}
      </div>
    </Modal>
  );
};
