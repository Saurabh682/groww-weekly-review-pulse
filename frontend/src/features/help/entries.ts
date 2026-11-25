export interface FaqItem {
  id: string;
  category: 'apps' | 'core' | 'pipeline' | 'hygiene' | 'mcp' | 'scenarios';
  question: string;
  answer: string;
  tag: string;
}

export interface FeatureDetail {
  id: string;
  title: string;
  category: 'apps' | 'core' | 'themes' | 'pipeline' | 'mcp' | 'hygiene' | 'invariants' | 'testing';
  badge: string;
  badgeVariant: 'teal' | 'coral' | 'blue' | 'gray' | 'amber';
  summary: string;
  keyCapabilities: string[];
  workflow: string[];
  architecture: string;
  codeSnippet?: string;
  safetyGuardrails: string[];
}
