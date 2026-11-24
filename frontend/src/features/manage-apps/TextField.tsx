import React, { useId } from 'react';

interface TextFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

export const TextField: React.FC<TextFieldProps> = ({ label, onChange, ...input }) => {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="block mb-1.5 text-xs font-semibold text-text-secondary">
        {label}
      </label>
      <input
        id={id}
        type="text"
        autoComplete="off"
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-lg bg-canvas-subtle border border-border-subtle text-text-primary text-xs focus:outline-none focus:border-primary transition-colors"
        {...input}
      />
    </div>
  );
};
