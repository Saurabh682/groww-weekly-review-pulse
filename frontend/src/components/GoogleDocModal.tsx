import React, { useState, useEffect } from 'react';
import { ExternalLink, Copy, Check, FileText, Plus, Link2, Eye } from 'lucide-react';
import { Modal } from './Modal';
import { Button } from './Button';

interface GoogleDocModalProps {
  isOpen: boolean;
  onClose: () => void;
  noteMarkdown?: string;
}

export const STORAGE_KEY_DOC_URL = 'groww_pulse_google_doc_url';
export const DEFAULT_REAL_DOC_URL = 'https://docs.google.com/document/d/1BPe7HxJWozrCPsyr_xR1LEYDb04mTxFOKSyB340REKE/edit';

export const DEFAULT_NOTE_TEXT = `Groww Weekly Review Pulse: Week of 09 Nov 2026
Google Play reviews (2026-08-17 to 2026-11-09) • Total: 1,435 • Analyzed: 662 • Avg Rating: 2.7★

Top Themes:
1. Charges & Pricing (31.0% share, 2.6★)
Users report unexpected charges and request transparent fee breakdowns on equity and DP deductions.

2. App Performance & Bugs (28.8% share, 2.4★)
Frequent app lag and freezing reported during peak trading hours, impacting order execution.

3. Positive UX & Simplicity (26.1% share, 3.6★)
Users praise intuitive navigation, clean interface design, and straightforward mutual fund investing.

Customer Voice (Verbatim Quotes):
• "Withdrawal request placed on Monday, still pending on Friday" (1★ review, Charges & Pricing)
• "added USD 216 (21k rupees), 8 days ago and it was never added to my account" (1★ review, App Performance & Bugs)
• "Hi team your nifty terminal lagging in the desktop and everything 20 to 25 minutes auto frezze please resolve this issue" (5★ review, Positive UX & Simplicity)

Recommended Operational Actions:
1. [Charges & Pricing] Deploy in-app fee breakdown calculator and display itemized DP charges on order confirmation screens. (Owner: Core Brokerage Team)
2. [App Performance & Bugs] Conduct load testing on morning market-open websocket channels and patch chart rendering memory leaks. (Owner: Mobile Reliability Team)
3. [Positive UX & Simplicity] Maintain current simplified mutual fund dashboard layout while streamlining advanced equity analytics. (Owner: Product Design Team)
`;

export function isMockDocUrl(url: string): boolean {
  return !url || url.includes('mock-groww-weekly-pulse');
}

export function getSavedDocUrl(): string {
  try {
    const saved = localStorage.getItem(STORAGE_KEY_DOC_URL);
    if (!saved || isMockDocUrl(saved)) {
      return DEFAULT_REAL_DOC_URL;
    }
    return saved;
  } catch {
    return DEFAULT_REAL_DOC_URL;
  }
}

/**
 * Robust copy helper that handles both modern clipboard API and legacy execCommand fallback
 */
async function copyTextToClipboard(text: string): Promise<boolean> {
  if (!text) return false;

  // 1. Try modern navigator.clipboard
  if (navigator?.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // fallback below
    }
  }

  // 2. Fallback using invisible textarea
  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    textArea.style.top = '-9999px';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    console.error('All copy methods failed:', err);
    return false;
  }
}

export const GoogleDocModal: React.FC<GoogleDocModalProps> = ({
  isOpen,
  onClose,
  noteMarkdown = '',
}) => {
  const [docUrl, setDocUrl] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const activeContent = (noteMarkdown && noteMarkdown.trim().length > 0)
    ? noteMarkdown.trim()
    : DEFAULT_NOTE_TEXT;

  useEffect(() => {
    if (isOpen) {
      setDocUrl(getSavedDocUrl());
      setCopied(false);
    }
  }, [isOpen]);

  const handleCopyOnly = async () => {
    const success = await copyTextToClipboard(activeContent);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  const handleCreateNewDoc = async () => {
    await copyTextToClipboard(activeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
    window.open('https://docs.new', '_blank');
  };

  const handleSaveAndOpen = () => {
    let finalUrl = docUrl.trim();
    if (!finalUrl || isMockDocUrl(finalUrl)) {
      finalUrl = DEFAULT_REAL_DOC_URL;
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
    setDocUrl(DEFAULT_REAL_DOC_URL);
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
            Reset to real doc
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
              Open Google Doc
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-4 text-sm">
        {/* Notice Banner */}
        <div className="p-3.5 rounded-card bg-[#0b111e]/80 border border-teal-500/30 text-teal-200 text-xs leading-relaxed flex items-start gap-2.5">
          <FileText className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
          <div>
            <strong>Google Docs Sync & Export</strong>
            <p className="text-text-muted mt-0.5">
              Copy the synthesized weekly pulse note to your clipboard and paste it directly into your live Google Document.
            </p>
          </div>
        </div>

        {/* Action 1: Create New Doc or Copy Note */}
        <div className="p-4 rounded-card bg-[#0b111e]/50 border border-border-subtle space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-text-primary flex items-center gap-2 text-xs uppercase tracking-wider text-teal-400">
              <Plus className="w-4 h-4" /> Option A: Create or Copy Note
            </span>
            {copied && (
              <span className="text-xs text-teal-400 font-medium flex items-center gap-1 animate-pulse">
                <Check className="w-3.5 h-3.5" /> Copied to clipboard!
              </span>
            )}
          </div>
          <p className="text-xs text-text-muted">
            Copies the full 231-word weekly executive note to your clipboard so you can paste (<kbd className="px-1 py-0.5 rounded bg-surface-elevated border border-border text-[10px]">Ctrl+V</kbd>) into your document.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            <Button
              variant="secondary"
              size="sm"
              icon={copied ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
              onClick={handleCopyOnly}
              className="w-full justify-center"
            >
              {copied ? 'Copied to Clipboard!' : 'Copy Note Text'}
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<ExternalLink className="w-3.5 h-3.5" />}
              onClick={handleCreateNewDoc}
              className="w-full justify-center"
            >
              Open docs.new
            </Button>
          </div>

          {/* Quick Preview Toggle */}
          <div className="pt-2 border-t border-border-subtle/50">
            <button
              type="button"
              onClick={() => setShowPreview(!showPreview)}
              className="text-xs text-text-muted hover:text-text-primary transition-colors flex items-center gap-1.5"
            >
              <Eye className="w-3.5 h-3.5" />
              {showPreview ? 'Hide Note Text Preview' : 'Show / Select Note Text Manually'}
            </button>

            {showPreview && (
              <div className="mt-2.5">
                <textarea
                  readOnly
                  rows={8}
                  value={activeContent}
                  onClick={(e) => (e.target as HTMLTextAreaElement).select()}
                  className="w-full p-2.5 rounded-lg bg-[#0e1726] border border-[#2a3d5d] text-text-secondary text-xs font-mono focus:outline-none focus:border-teal-400 transition-colors"
                />
                <span className="text-[10px] text-text-muted block mt-1">
                  Click inside the box to select all text, then press Ctrl+C.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Action 2: Link Live Doc URL */}
        <div className="p-4 rounded-card bg-[#0b111e]/50 border border-border-subtle space-y-2.5">
          <span className="font-semibold text-text-primary flex items-center gap-2 text-xs uppercase tracking-wider text-text-secondary">
            <Link2 className="w-4 h-4 text-primary" /> Option B: Live Google Doc Link
          </span>
          <p className="text-xs text-text-muted">
            The dashboard will open this Google Doc when you click "Open Google Doc":
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
