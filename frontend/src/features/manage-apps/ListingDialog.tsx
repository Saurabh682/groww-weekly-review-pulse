import React, { useState } from 'react';
import { ListingBody, Operator, Registration, StoreSearchResult } from '../../data/types';
import { ChooseStep } from './ChooseStep';
import { Choices, keepListed, listingId, NO_CHOICES } from './choices';
import { ReviewStep } from './ReviewStep';
import { useRequest } from './useRequest';

interface ListingDialogProps {
  title: string;
  explanation: string;
  confirmLabel: string;
  country: string;
  send: Operator['send'];
  register: (listing: ListingBody) => Promise<Registration>;
  onRegistered: (registration: Registration) => void;
  onClose: () => void;
}

export const ListingDialog: React.FC<ListingDialogProps> = ({
  title,
  explanation,
  confirmLabel,
  country,
  send,
  register,
  onRegistered,
  onClose,
}) => {
  const [found, setFound] = useState<StoreSearchResult | null>(null);
  const [choices, setChoices] = useState<Choices>(NO_CHOICES);
  const [reviewing, setReviewing] = useState(false);
  const search = useRequest();
  const [displayName, setDisplayName] = useState('');

  const searchStores = (name: string, place: string, onFound: (result: StoreSearchResult) => void) =>
    search.run(
      () => send<StoreSearchResult>('POST', '/search', { name, country: place }),
      (result) => {
        setFound(result);
        onFound(result);
      },
    );

  const startOver = (result: StoreSearchResult) => {
    setChoices(NO_CHOICES);
    setDisplayName(result.term);
  };

  const searchAgain = ({ term, country: place }: StoreSearchResult) =>
    searchStores(term, place, (result) => setChoices((current) => keepListed(current, result)));

  if (found && reviewing) {
    return (
      <ReviewStep
        title={title}
        explanation={explanation}
        confirmLabel={confirmLabel}
        listing={{
          display_name: displayName,
          play_package_id: listingId(choices.play_store),
          app_store_id: listingId(choices.app_store),
          country: found.country,
          lang: 'en',
        }}
        onNameChange={setDisplayName}
        register={register}
        onRegistered={onRegistered}
        onBack={() => setReviewing(false)}
        onClose={onClose}
      />
    );
  }

  return (
    <ChooseStep
      title={title}
      explanation={explanation}
      term={found?.term ?? ''}
      country={found?.country ?? country}
      found={found}
      choices={choices}
      search={search}
      onSearch={(name, place) => searchStores(name, place, startOver)}
      onSearchAgain={() => found && searchAgain(found)}
      onChoose={setChoices}
      onReview={() => setReviewing(true)}
      onClose={onClose}
    />
  );
};
