import React from 'react';
import { Button } from '../../components/Button';
import { ErrorState } from '../../components/ErrorState';
import { Modal } from '../../components/Modal';
import { ListingBody, Registration } from '../../data/types';
import { STORE_NAMES } from '../../lib/stores';
import { TextField } from './TextField';
import { useRequest } from './useRequest';

const FORM = 'review-listing';
const NAME_LIMIT = 80;

interface DetailProps {
  label: string;
  value: string;
}

const Detail: React.FC<DetailProps> = ({ label, value }) => (
  <div className="flex justify-between gap-3">
    <dt className="text-text-muted">{label}</dt>
    <dd className="font-mono text-text-primary text-right break-all">{value}</dd>
  </div>
);

interface ReviewStepProps {
  title: string;
  explanation: string;
  confirmLabel: string;
  listing: ListingBody;
  onNameChange: (name: string) => void;
  register: (listing: ListingBody) => Promise<Registration>;
  onRegistered: (registration: Registration) => void;
  onBack: () => void;
  onClose: () => void;
}

export const ReviewStep: React.FC<ReviewStepProps> = ({
  title,
  explanation,
  confirmLabel,
  listing,
  onNameChange,
  register,
  onRegistered,
  onBack,
  onClose,
}) => {
  const save = useRequest();
  const name = listing.display_name.trim();

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    save.run(() => register({ ...listing, display_name: name }), onRegistered);
  };

  return (
    <Modal
      isOpen
      onClose={() => {
        if (!save.busy) onClose();
      }}
      title={title}
      footer={
        <>
          <Button variant="ghost" size="sm" disabled={save.busy} onClick={onBack}>
            Back
          </Button>
          <Button type="submit" form={FORM} size="sm" loading={save.busy} disabled={!name}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <form id={FORM} onSubmit={submit} className="space-y-4">
        <p className="text-xs text-text-secondary leading-relaxed">{explanation}</p>
        <TextField
          label="Display name"
          value={listing.display_name}
          maxLength={NAME_LIMIT}
          onChange={onNameChange}
          autoFocus
        />
        <dl className="text-xs space-y-2">
          <Detail label={STORE_NAMES.play_store} value={listing.play_package_id ?? 'Not on this store'} />
          <Detail label={STORE_NAMES.app_store} value={listing.app_store_id ?? 'Not on this store'} />
          <Detail label="Store country" value={listing.country} />
        </dl>
        {save.problem && <ErrorState title="Not saved" message={save.problem} />}
      </form>
    </Modal>
  );
};
