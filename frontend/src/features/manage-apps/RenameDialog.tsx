import React, { useState } from 'react';
import { Button } from '../../components/Button';
import { ErrorState } from '../../components/ErrorState';
import { Modal } from '../../components/Modal';
import { AppRecord } from '../../data/types';
import { TextField } from './TextField';
import { useRequest } from './useRequest';

const FORM = 'rename-app';
const NAME_LIMIT = 80;

interface RenameDialogProps {
  app: AppRecord;
  rename: (displayName: string) => Promise<AppRecord>;
  onRenamed: (app: AppRecord) => void;
  onClose: () => void;
}

export const RenameDialog: React.FC<RenameDialogProps> = ({ app, rename, onRenamed, onClose }) => {
  const [name, setName] = useState(app.display_name);
  const save = useRequest();
  const canSave = name.trim() !== '' && name.trim() !== app.display_name;

  const close = () => {
    if (!save.busy) onClose();
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (canSave && !save.busy) save.run(() => rename(name.trim()), onRenamed);
  };

  return (
    <Modal
      isOpen
      onClose={close}
      title={`Rename ${app.display_name}`}
      maxWidth="md"
      footer={
        <>
          <Button variant="ghost" size="sm" disabled={save.busy} onClick={close}>
            Cancel
          </Button>
          <Button type="submit" form={FORM} size="sm" loading={save.busy} disabled={!canSave}>
            Save name
          </Button>
        </>
      }
    >
      <form id={FORM} onSubmit={submit} className="space-y-4">
        <p className="text-xs text-text-secondary leading-relaxed">
          Only the name changes. Its stores, history, Docs and drafts stay as they are.
        </p>
        <TextField label="Display name" value={name} maxLength={NAME_LIMIT} onChange={setName} autoFocus />
        {save.problem && <ErrorState title="Not saved" message={save.problem} />}
      </form>
    </Modal>
  );
};
