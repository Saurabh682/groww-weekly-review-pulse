export const HELP_TOPICS = [
  { id: 'apps', label: 'Your Apps' },
  { id: 'note', label: 'Weekly Note' },
  { id: 'themes', label: 'Themes' },
  { id: 'checks', label: 'Checks' },
  { id: 'publishing', label: 'Google Doc & Gmail' },
  { id: 'cleaning', label: 'Cleaning & Privacy' },
  { id: 'sample', label: 'Sample Pages' },
] as const;

export type HelpTopic = (typeof HELP_TOPICS)[number]['id'];

export interface FaqItem {
  id: string;
  category: HelpTopic;
  question: string;
  answer: string;
  tag: string;
}

export interface FeatureDetail {
  id: string;
  title: string;
  category: HelpTopic;
  badge: string;
  badgeVariant: 'teal' | 'coral' | 'blue' | 'gray' | 'amber';
  summary: string;
  keyCapabilities: string[];
  workflow: string[];
  architecture: string;
  safetyGuardrails: string[];
}
