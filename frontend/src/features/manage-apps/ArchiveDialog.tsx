import React from 'react';
import { Button } from '../../components/Button';
import { ErrorState } from '../../components/ErrorState';
import { Modal } from '../../components/Modal';
import { AppRecord } from '../../data/types';
import { useRequest } from './useRequest';

interface ArchiveDialogProps {
  app: AppRecord;
  archive: () => Promise<AppRecord>;
  onArchived: () => void;
  onClose: () => void;
}

export const ArchiveDialog: React.FC<ArchiveDialogProps> = ({ app, archive, onArchived, onClose }) => {
  const save = useRequest();

  const close = () => {
    if (!save.busy) onClose();
  };

  return (
    <Modal
      isOpen
      onClose={close}
      title={`Archive ${app.display_name}?`}
      maxWidth="md"
      footer={
        <>
          <Button variant="ghost" size="sm" disabled={save.busy} onClick={close} autoFocus>
            Cancel
          </Button>
          <Button variant="danger" size="sm" loading={save.busy} onClick={() => save.run(archive, onArchived)}>
            Archive {app.display_name}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-xs text-text-secondary leading-relaxed">
          {app.display_name} stops collecting reviews and its slot is freed. Its history and Docs stay readable. An
          archived app cannot be made live again.
        </p>
        {save.problem && <ErrorState headingLevel={4} title="Not archived" message={save.problem} />}
      </div>
    </Modal>
  );
};
