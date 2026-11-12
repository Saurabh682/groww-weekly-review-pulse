import React, { useState, useEffect } from 'react';
import { ExternalLink, Copy, Check, FileText, Plus, Link2 } from 'lucide-react';
import { Modal } from './Modal';
import { Button } from './Button';

interface GoogleDocModalProps {
  isOpen: boolean;
  onClose: () => void;
  noteMarkdown?: string;
}

export const STORAGE_KEY_DOC_URL = 'groww_pulse_google_doc_url';
export const DEFAULT_MOCK_DOC_URL = 'https://docs.google.com/document/d/1BPe7HxJWozrCPsyr_xR1LEYDb04mTxFOKSyB340REKE/edit';

export function getSavedDocUrl(): string {
  try {
    return localStorage.getItem(STORAGE_KEY_DOC_URL) || DEFAULT_MOCK_DOC_URL;
  } catch {
    return DEFAULT_MOCK_DOC_URL;
  }
}

export function isMockDocUrl(url: string): boolean {
  return url.includes('mock-groww-weekly-pulse');
}

export const GoogleDocModal: React.FC<GoogleDocModalProps> = ({
  isOpen,
  onClose,
  noteMarkdown = '',
}) => {
  const [docUrl, setDocUrl] = useState<string>('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setDocUrl(getSavedDocUrl());
    }
  }, [isOpen]);

  const handleCreateNewDoc = () => {
    if (noteMarkdown) {
      navigator.clipboard.writeText(noteMarkdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
    window.open('https://docs.new', '_blank');
  };

  const handleSaveAndOpen = () => {
    let finalUrl = docUrl.trim();
    if (!finalUrl) {
      finalUrl = DEFAULT_MOCK_DOC_URL;
    }
    // If user just entered an ID like 1abc... convert to full Google Doc URL
    if (!finalUrl.startsWith('http://') && !finalUrl.startsWith('https://')) {
      finalUrl = `https://docs.google.com/document/d/${finalUrl}/edit`;
    }

    try {
      localStorage.setItem(STORAGE_KEY_DOC_URL, finalUrl);
      setDocUrl(finalUrl);
    } catch {
      // ignore localStorage error
    }

    window.open(finalUrl, '_blank');
    onClose();
  };

  const handleResetToDefault = () => {
    localStorage.removeItem(STORAGE_KEY_DOC_URL);
    setDocUrl(DEFAULT_MOCK_DOC_URL);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Google Docs Integration"
      maxWidth="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <button
            type="button"
            onClick={handleResetToDefault}
            className="text-xs text-text-muted hover:text-text-primary transition-colors underline"
          >
            Reset to prototype default
          </button>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<ExternalLink className="w-3.5 h-3.5" />}
              onClick={handleSaveAndOpen}
            >
              Save & Open Doc
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-5 text-sm">
        {/* Notice Banner */}
        <div className="p-3.5 rounded-card bg-[#0b111e]/80 border border-amber-500/30 text-amber-200 text-xs leading-relaxed flex items-start gap-2.5">
          <FileText className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <strong>Why did you see "Page not found"?</strong>
            <p className="text-text-muted mt-1">
              The dashboard defaults to a synthetic prototype ID (<code className="text-amber-300">mock-groww-weekly-pulse-2026-11-09</code>) that doesn't exist on Google's live servers. To view a real document, link your own Google Doc below or create a new one.
            </p>
          </div>
        </div>

        {/* Action 1: Create New Doc with Note Pre-copied */}
        <div className="p-4 rounded-card bg-[#0b111e]/50 border border-border-subtle space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-text-primary flex items-center gap-2">
              <Plus className="w-4 h-4 text-teal-400" /> Option A: Create New Google Doc
            </span>
            {copied && (
              <span className="text-xs text-teal-400 flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Note copied to clipboard!
              </span>
            )}
          </div>
          <p className="text-xs text-text-muted">
            Launches Google Docs in a new tab (<code className="text-text-secondary">docs.new</code>) and automatically copies the 231-word weekly executive note to your clipboard so you can immediately paste (<kbd className="px-1 py-0.5 rounded bg-surface-elevated border border-border text-[10px]">Ctrl+V</kbd>) into it.
          </p>
          <Button
            variant="secondary"
            size="sm"
            icon={<Copy className="w-3.5 h-3.5" />}
            onClick={handleCreateNewDoc}
            className="w-full justify-center"
          >
            Create New Doc & Copy Note
          </Button>
        </div>

        {/* Action 2: Link Live Doc URL */}
        <div className="p-4 rounded-card bg-[#0b111e]/50 border border-border-subtle space-y-2.5">
          <span className="font-semibold text-text-primary flex items-center gap-2">
            <Link2 className="w-4 h-4 text-primary" /> Option B: Link Existing Google Doc
          </span>
          <p className="text-xs text-text-muted">
            Paste your Google Doc URL or document ID. The dashboard buttons will open your live document:
          </p>
          <input
            type="text"
            value={docUrl}
            onChange={(e) => setDocUrl(e.target.value)}
            placeholder="https://docs.google.com/document/d/YOUR_DOC_ID/edit"
            className="w-full px-3 py-2 rounded-lg bg-[#0e1726] border border-[#2a3d5d] text-text-primary text-xs font-mono focus:outline-none focus:border-teal-400 transition-colors"
          />
        </div>
      </div>
    </Modal>
  );
};
