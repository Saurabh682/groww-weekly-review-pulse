import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '../../components/Button';

interface DropzoneProps {
  onFileUploaded: (file: File) => Promise<void>;
  isUploading: boolean;
}

export const Dropzone: React.FC<DropzoneProps> = ({
  onFileUploaded,
  isUploading,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const validateAndProcessFile = async (file: File) => {
    setValidationError(null);
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
      setValidationError('Invalid file format. Please upload a .csv or .json Google Play review export.');
      return;
    }

    if (file.name.endsWith('.csv')) {
      const textSample = await file.slice(0, 1024).text();
      const firstLine = textSample.split('\n')[0].toLowerCase();
      const hasReviewText = firstLine.includes('content') || firstLine.includes('review') || firstLine.includes('text');
      const hasRating = firstLine.includes('score') || firstLine.includes('rating') || firstLine.includes('star');

      if (!hasReviewText && !hasRating) {
        setValidationError('CSV missing required headers. Expecting columns: review_text/content, score/rating, date/at.');
        return;
      }
    }

    try {
      await onFileUploaded(file);
    } catch (err: any) {
      setValidationError(err?.message || 'Failed to process review batch');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-card p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 ${
          isDragOver
            ? 'border-primary bg-primary-tint/30 scale-[1.01] shadow-glow-teal-sm'
            : 'border-[#2a3d5d] bg-[#162238]/60 hover:border-primary/50 hover:bg-[#162238]'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="w-12 h-12 rounded-full bg-primary-tint border border-primary-border text-primary flex items-center justify-center mb-3 shadow-glow-teal-sm">
          {isUploading ? (
            <Loader2 className="w-6 h-6 animate-spin" />
          ) : (
            <UploadCloud className="w-6 h-6" />
          )}
        </div>

        <h3 className="text-sm font-bold font-display text-white mb-1">
          {isUploading
            ? 'Processing and sanitizing reviews...'
            : 'Drop Google Play Store review export here, or browse'}
        </h3>
        <p className="text-xs text-text-secondary max-w-sm mb-4 leading-relaxed font-sans">
          Accepts CSV or JSON exports with review text, star ratings, and timestamps.
          Automatic hygiene filtering, deduplication, and PII anonymization will run immediately.
        </p>

        <Button
          type="button"
          variant="secondary"
          size="sm"
          disabled={isUploading}
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
        >
          Select File (.csv, .json)
        </Button>
      </div>

      {validationError && (
        <div className="mt-3 p-3 rounded-lg bg-failure-tint border border-failure-border text-failure-dark text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-failure" />
          <span>{validationError}</span>
        </div>
      )}
    </div>
  );
};
