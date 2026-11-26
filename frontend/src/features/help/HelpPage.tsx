import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Cpu,
  Maximize2,
  Minimize2,
  ShieldCheck,
} from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Disclosure } from '../../components/Disclosure';
import { EmptyState } from '../../components/EmptyState';
import { SearchField } from '../../components/SearchField';
import { SectionTitle } from '../../components/SectionTitle';
import { FaqItem, FeatureDetail, HELP_TOPICS, HelpTopic } from './entries';
import { HOW_IT_WORKS_FAQS, HOW_IT_WORKS_FEATURES, SAMPLE_SCENARIOS } from './howItWorks';
import { LIVE_APP_FAQS, LIVE_APP_FEATURES } from './liveApps';

const FEATURES: FeatureDetail[] = [...LIVE_APP_FEATURES, ...HOW_IT_WORKS_FEATURES];
const FAQS: FaqItem[] = [...LIVE_APP_FAQS, ...HOW_IT_WORKS_FAQS];
const TOPICS = [{ id: 'all' as const, label: 'All topics' }, ...HELP_TOPICS];
const DETAIL_HEADING = 'text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 mb-2';

const matches = (query: string, ...texts: string[]) => {
  const q = query.trim().toLowerCase();
  return q === '' || texts.some((text) => text.toLowerCase().includes(q));
};

const toggled = (state: Record<string, boolean>, id: string) => ({ ...state, [id]: !state[id] });

export const HelpPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<HelpTopic | 'all'>('all');
  const [openFaqIds, setOpenFaqIds] = useState<Record<string, boolean>>({});
  const [expandedFeatureIds, setExpandedFeatureIds] = useState<Record<string, boolean>>({});

  const inTopic = (category: HelpTopic) => activeCategory === 'all' || category === activeCategory;
  const filteredFeatures = FEATURES.filter(
    (feat) =>
      inTopic(feat.category) &&
      matches(searchQuery, feat.title, feat.summary, feat.architecture, ...feat.keyCapabilities),
  );
  const filteredFaqs = FAQS.filter(
    (faq) => inTopic(faq.category) && matches(searchQuery, faq.question, faq.answer, faq.tag),
  );
  const nothingFound = filteredFeatures.length === 0 && filteredFaqs.length === 0;

  const resetFilters = () => {
    setSearchQuery('');
    setActiveCategory('all');
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">Help</h1>
            <Badge variant="gray">{FEATURES.length} features</Badge>
          </div>
        </div>
        <p className="text-xs text-text-secondary font-mono">
          How the weekly pulse works, what each label means, and what the sample pages show.
        </p>
      </div>

      <div className="space-y-3">
        <SearchField label="Search Help" value={searchQuery} onChange={setSearchQuery} />

        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Topics">
            {TOPICS.map((topic) => (
              <Button
                key={topic.id}
                variant={activeCategory === topic.id ? 'primary' : 'secondary'}
                size="sm"
                aria-pressed={activeCategory === topic.id}
                onClick={() => setActiveCategory(topic.id)}
              >
                {topic.label}
              </Button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              icon={<Maximize2 className="w-3.5 h-3.5" />}
              onClick={() => setExpandedFeatureIds(Object.fromEntries(FEATURES.map(({ id }) => [id, true])))}
            >
              Expand all
            </Button>
            <Button
              variant="ghost"
              size="sm"
              icon={<Minimize2 className="w-3.5 h-3.5" />}
              onClick={() => setExpandedFeatureIds({})}
            >
              Collapse all
            </Button>
          </div>
        </div>
      </div>

      {nothingFound && (
        <EmptyState headingLevel={2}
          title="Nothing matches"
          description="No feature or question matches this search and topic."
          actionLabel="Show everything"
          onAction={resetFilters}
        />
      )}

      {filteredFeatures.length > 0 && (
        <section>
          <SectionTitle aside={<span className="text-xs text-text-muted font-mono">{filteredFeatures.length} features</span>}>
            Features and how they work
          </SectionTitle>

          <div className="space-y-4">
            {filteredFeatures.map((feat) => {
              const isExpanded = expandedFeatureIds[feat.id] ?? false;
              const detailsId = `${feat.id}-details`;
              return (
                <Card key={feat.id}>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
                    <div>
                      <h3 className="text-base font-bold font-display text-white">{feat.title}</h3>
                      <p className="text-xs text-text-muted font-sans mt-0.5">{feat.summary}</p>
                    </div>
                    <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                      <Badge variant={feat.badgeVariant}>{feat.badge}</Badge>
                      <Button
                        variant="secondary"
                        size="sm"
                        aria-expanded={isExpanded}
                        aria-controls={detailsId}
                        icon={isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        onClick={() => setExpandedFeatureIds((state) => toggled(state, feat.id))}
                      >
                        {isExpanded ? 'Hide details' : 'Show details'}
                      </Button>
                    </div>
                  </div>

                  <div className="py-3">
                    <span className="text-2xs font-mono font-bold uppercase tracking-wider text-text-muted block mb-2">
                      What it does
                    </span>
                    <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-text-secondary">
                      {feat.keyCapabilities.map((cap) => (
                        <li key={cap} className="flex items-start gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" aria-hidden="true" />
                          <span>{cap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {isExpanded && (
                    <div
                      id={detailsId}
                      className="mt-3 pt-4 border-t border-border space-y-4 animate-fade-in bg-surface-dim/70 -mx-5 -mb-5 p-5 rounded-b-card"
                    >
                      <div>
                        <h4 className={`${DETAIL_HEADING} text-primary`}>
                          <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" /> Steps
                        </h4>
                        <ol className="list-decimal list-inside space-y-1.5 text-xs text-text-secondary">
                          {feat.workflow.map((step) => {
                            const [label, ...rest] = step.split(':');
                            return (
                              <li key={step} className="leading-relaxed">
                                <span className="text-white font-medium">{label}:</span>
                                {rest.join(':')}
                              </li>
                            );
                          })}
                        </ol>
                      </div>

                      <div>
                        <h4 className={`${DETAIL_HEADING} text-primary`}>
                          <Cpu className="w-3.5 h-3.5" aria-hidden="true" /> How it works
                        </h4>
                        <p className="text-xs text-text-secondary leading-relaxed bg-canvas-subtle p-3 rounded-lg border border-border">
                          {feat.architecture}
                        </p>
                      </div>

                      <div>
                        <h4 className={`${DETAIL_HEADING} text-critical-dark`}>
                          <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" /> Safeguards
                        </h4>
                        <ul className="space-y-1 text-xs text-text-secondary">
                          {feat.safetyGuardrails.map((guard) => (
                            <li key={guard} className="flex items-start gap-1.5">
                              <span className="w-1.5 h-1.5 rounded-full bg-critical-dark shrink-0 mt-1.5" aria-hidden="true" />
                              <span>{guard}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </section>
      )}

      <section>
        <SectionTitle aside={<span className="text-xs text-text-muted font-mono">Fixed sample data</span>}>
          Sample page scenarios
        </SectionTitle>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {SAMPLE_SCENARIOS.map((sc) => (
            <Card key={sc.scenario} padding="tight" className="flex flex-col justify-between">
              <div>
                <div className={`font-mono text-xs font-bold ${sc.color} mb-1`}>{sc.name}</div>
                <p className="text-2xs text-text-secondary leading-relaxed mb-3">{sc.desc}</p>
              </div>
              <Link
                to={sc.link}
                className="inline-flex items-center gap-1 text-2xs font-mono font-semibold text-primary hover:underline"
              >
                Launch &rarr;
              </Link>
            </Card>
          ))}
        </div>
      </section>

      {filteredFaqs.length > 0 && (
        <section>
          <SectionTitle aside={<span className="text-xs font-mono text-text-muted">{filteredFaqs.length} answers available</span>}>
            Frequently asked questions
          </SectionTitle>

          <div className="space-y-2.5">
            {filteredFaqs.map((faq) => (
              <Disclosure
                key={faq.id}
                id={faq.id}
                isOpen={openFaqIds[faq.id] ?? false}
                onToggle={() => setOpenFaqIds((state) => toggled(state, faq.id))}
                summary={
                  <>
                    <Badge variant="teal">{faq.tag}</Badge>
                    <span className="font-display font-bold text-sm text-white break-words">{faq.question}</span>
                  </>
                }
              >
                {faq.answer}
              </Disclosure>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
