import React, { useState } from 'react';
import { Mail, ExternalLink, Copy, Check, Inbox, ShieldCheck, Eye } from 'lucide-react';
import { Modal } from './Modal';
import { Button } from './Button';

interface GmailDraftModalProps {
  isOpen: boolean;
  onClose: () => void;
  to?: string;
  subject?: string;
  body?: string;
}

export const DEFAULT_GMAIL_RECIPIENTS = 'product-leadership@groww.in, founders-office@groww.in';
export const DEFAULT_GMAIL_SUBJECT = '[Weekly Pulse] Groww App Play Store Reviews — Week of 09 Nov 2026';
export const DEFAULT_GMAIL_BODY = `Hi Team,

Here is the synthesized Groww Weekly Review Pulse for the week of 09 Nov 2026.

Executive Summary:
• Reviews Analyzed: 662 reviews (Total Volume: 1,435)
• Average Rating: 2.7★ (Pulse Score: 58/100)
• Period: 17 Aug 2026 to 09 Nov 2026

Top Customer Themes:
1. Charges & Pricing (31.0% share, 2.6★) — Unexpected fee deductions and transparent DP charge breakdown requests.
2. App Performance & Bugs (28.8% share, 2.4★) — Market-open lag and terminal chart freezes during peak hours.
3. Positive UX & Simplicity (26.1% share, 3.6★) — Praises for intuitive mutual fund investing and clean navigation.

Customer Voice (Verbatim Quotes):
• "Withdrawal request placed on Monday, still pending on Friday" (1★ review)
• "added USD 216 (21k rupees), 8 days ago and it was never added to my account" (1★ review)
• "Hi team your nifty terminal lagging in the desktop and everything 20 to 25 minutes auto frezze please resolve this issue" (5★ review)

Recommended Operational Actions:
1. [Core Brokerage Team] Deploy in-app fee breakdown calculator & itemized DP charges on order confirmation.
2. [Mobile Reliability Team] Load test morning websocket channels and patch chart rendering memory leaks.
3. [Product Design Team] Maintain simplified mutual fund flow while streamlining advanced equity tools.

Live Google Doc:
https://docs.google.com/document/d/1BPe7HxJWozrCPsyr_xR1LEYDb04mTxFOKSyB340REKE/edit

Best regards,
Groww Review Pulse Engine (Draft Staged for Leadership Review)
`;

async function copyTextToClipboard(text: string): Promise<boolean> {
  if (!text) return false;
  if (navigator?.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // fallback below
    }
  }
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
  } catch {
    return false;
  }
}

export const GmailDraftModal: React.FC<GmailDraftModalProps> = ({
  isOpen,
  onClose,
  to = DEFAULT_GMAIL_RECIPIENTS,
  subject = DEFAULT_GMAIL_SUBJECT,
  body = DEFAULT_GMAIL_BODY,
}) => {
  const [copied, setCopied] = useState(false);
  const [showFullBody, setShowFullBody] = useState(false);

  const handleOpenInGmailCompose = () => {
    // Gmail web direct compose URL with recipients, subject and pre-filled body
    const composeUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(to)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.open(composeUrl, '_blank');
  };

  const handleOpenDraftsFolder = () => {
    window.open('https://mail.google.com/mail/u/0/#drafts', '_blank');
  };

  const handleCopyEmail = async () => {
    const textToCopy = `To: ${to}\nSubject: ${subject}\n\n${body}`;
    const ok = await copyTextToClipboard(textToCopy);
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Gmail Draft Review & Staging"
      maxWidth="lg"
      footer={
        <div className="flex items-center justify-between w-full">
          <button
            type="button"
            onClick={handleOpenDraftsFolder}
            className="text-xs text-text-muted hover:text-text-primary transition-colors flex items-center gap-1.5 underline"
          >
            <Inbox className="w-3.5 h-3.5" />
            Open Gmail Drafts folder
          </button>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
            <Button
              variant="primary"
              size="sm"
              icon={<ExternalLink className="w-3.5 h-3.5" />}
              onClick={handleOpenInGmailCompose}
            >
              Open & Stage in Gmail
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-4 text-sm">
        {/* Safety Policy Banner */}
        <div className="p-3.5 rounded-card bg-[#0b111e]/80 border border-emerald-500/30 text-emerald-200 text-xs leading-relaxed flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong>Strict Human-in-the-Loop Policy</strong>
            <p className="text-text-muted mt-0.5">
              The engine operates under strict draft-only mode. Emails are prepared as drafts and never sent automatically. Click below to open and save this draft directly into your personal Gmail compose workspace.
            </p>
          </div>
        </div>

        {/* Draft Metadata Card */}
        <div className="p-4 rounded-card bg-[#0b111e]/50 border border-border-subtle space-y-2.5">
          <div className="flex justify-between items-center text-xs pb-2 border-b border-border-subtle">
            <span className="text-text-muted">Status:</span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium font-mono text-[11px] border border-emerald-500/20">
              Draft Staged (Manual Review Required)
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <span className="text-text-muted font-medium w-20 shrink-0">Recipients:</span>
              <span className="font-mono text-text-primary text-[11px] break-all bg-surface-elevated px-2 py-1 rounded border border-border-subtle w-full sm:w-auto">
                {to}
              </span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <span className="text-text-muted font-medium w-20 shrink-0">Subject:</span>
              <span className="font-semibold text-white text-xs truncate">
                {subject}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <Button
            variant="primary"
            size="sm"
            icon={<Mail className="w-3.5 h-3.5" />}
            onClick={handleOpenInGmailCompose}
            className="w-full justify-center"
          >
            Open in Gmail Compose
          </Button>

          <Button
            variant="secondary"
            size="sm"
            icon={copied ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
            onClick={handleCopyEmail}
            className="w-full justify-center"
          >
            {copied ? 'Email Copied!' : 'Copy Subject & Body'}
          </Button>
        </div>

        {/* Email Body Preview */}
        <div className="p-3.5 rounded-card bg-[#0b111e]/40 border border-border-subtle/70">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5" /> Email Body Preview
            </span>
            <button
              type="button"
              onClick={() => setShowFullBody(!showFullBody)}
              className="text-[11px] text-teal-400 hover:text-teal-300 transition-colors underline"
            >
              {showFullBody ? 'Collapse' : 'Expand Full Text'}
            </button>
          </div>

          <pre
            className={`font-sans text-xs text-text-muted leading-relaxed whitespace-pre-wrap p-2.5 rounded bg-[#090d16] border border-[#1e293b] overflow-y-auto ${
              showFullBody ? 'max-h-72' : 'max-h-36'
            }`}
          >
            {body}
          </pre>
        </div>
      </div>
    </Modal>
  );
};
