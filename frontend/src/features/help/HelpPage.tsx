import React, { useState } from 'react';
import { Card } from '../../components/Card';
import { Badge } from '../../components/Badge';
import { FaqItem, FeatureDetail, HELP_TOPICS, HelpTopic } from './entries';
import { HOW_IT_WORKS_FAQS, HOW_IT_WORKS_FEATURES, SAMPLE_SCENARIOS } from './howItWorks';
import { LIVE_APP_FAQS, LIVE_APP_FEATURES } from './liveApps';
import {
  HelpCircle,
  BookOpen,
  ShieldCheck,
  Search,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Cpu,
  SlidersHorizontal,
  Zap,
  Compass,
  ArrowRight,
  Maximize2,
  Minimize2,
} from 'lucide-react';

export const HelpPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<HelpTopic | 'all'>('all');
  const [openFaqIds, setOpenFaqIds] = useState<Record<string, boolean>>({});
  const [expandedFeatureIds, setExpandedFeatureIds] = useState<Record<string, boolean>>({});

  const toggleFaq = (id: string) => {
    setOpenFaqIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleFeature = (id: string) => {
    setExpandedFeatureIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const expandAllFeatures = () => {
    const allExpanded: Record<string, boolean> = {};
    features.forEach((f) => {
      allExpanded[f.id] = true;
    });
    setExpandedFeatureIds(allExpanded);
  };

  const collapseAllFeatures = () => {
    setExpandedFeatureIds({});
  };

  const features: FeatureDetail[] = [...LIVE_APP_FEATURES, ...HOW_IT_WORKS_FEATURES];
  const faqs: FaqItem[] = [...LIVE_APP_FAQS, ...HOW_IT_WORKS_FAQS];

  // Filtering features
  const filteredFeatures = features.filter((feat) => {
    if (activeCategory !== 'all' && feat.category !== activeCategory) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        feat.title.toLowerCase().includes(q) ||
        feat.summary.toLowerCase().includes(q) ||
        feat.architecture.toLowerCase().includes(q) ||
        feat.keyCapabilities.some((k) => k.toLowerCase().includes(q))
      );
    }
    return true;
  });

  // Filtering FAQs
  const filteredFaqs = faqs.filter((faq) => {
    if (activeCategory !== 'all' && faq.category !== activeCategory) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        faq.question.toLowerCase().includes(q) ||
        faq.answer.toLowerCase().includes(q) ||
        faq.tag.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary-tint border border-primary-border flex items-center justify-center text-primary shadow-glow-teal-sm">
              <HelpCircle className="w-5 h-5" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">
              App Guide & Knowledge Base
            </h1>
          </div>
          <p className="text-xs text-text-secondary mt-1 font-mono">
            How the weekly pulse works, what each label means, and what the sample pages show.
          </p>
        </div>

      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2 px-3.5 py-2.5 bg-[#162238] border border-[#2a3d5d] rounded-xl shadow-card focus-within:border-primary/60 transition-colors">
          <Search className="w-4 h-4 text-text-muted shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search Help..."
            aria-label="Search Help"
            className="w-full bg-transparent text-xs text-white placeholder:text-text-muted focus:outline-none font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="text-xs text-text-muted hover:text-white font-mono px-1"
            >
              ✕
            </button>
          )}
        </div>

        {/* Category Pills & Expand/Collapse Controls */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
            {[{ id: 'all' as const, label: 'All Topics' }, ...HELP_TOPICS].map((cat) => (
              <button
                key={cat.id}
                type="button"
                aria-pressed={activeCategory === cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`px-3 py-1 rounded-full transition-all ${
                  activeCategory === cat.id
                    ? 'bg-primary text-[#0b111e] font-bold shadow-glow-teal-sm'
                    : 'bg-[#162238] border border-[#2a3d5d] text-text-muted hover:text-white hover:bg-[#1b2a47]'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={expandAllFeatures}
              className="px-2.5 py-1 text-[11px] font-mono rounded bg-[#162238] border border-[#2a3d5d] text-text-muted hover:text-white transition-colors flex items-center gap-1"
            >
              <Maximize2 className="w-3 h-3 text-teal-400" /> Expand All
            </button>
            <button
              type="button"
              onClick={collapseAllFeatures}
              className="px-2.5 py-1 text-[11px] font-mono rounded bg-[#162238] border border-[#2a3d5d] text-text-muted hover:text-white transition-colors flex items-center gap-1"
            >
              <Minimize2 className="w-3 h-3 text-text-muted" /> Collapse All
            </button>
          </div>
        </div>
      </div>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold font-display text-white">
              Features and How They Work
            </h2>
          </div>
          <span className="text-xs text-text-muted font-mono">
            {filteredFeatures.length} features
          </span>
        </div>

        <div className="space-y-4">
          {filteredFeatures.map((feat) => {
            const isExpanded = expandedFeatureIds[feat.id] ?? false;
            return (
              <Card
                key={feat.id}
                className="p-5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card transition-all hover:border-primary/40"
              >
                {/* Feature Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1e293b]">
                  <div className="flex items-start sm:items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-primary-tint border border-primary-border flex items-center justify-center text-primary shrink-0 mt-0.5 sm:mt-0">
                      <Zap className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold font-display text-white">
                        {feat.title}
                      </h3>
                      <p className="text-xs text-text-muted font-sans mt-0.5">
                        {feat.summary}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    <Badge variant={feat.badgeVariant}>{feat.badge}</Badge>
                    <button
                      type="button"
                      onClick={() => toggleFeature(feat.id)}
                      className="px-3 py-1.5 rounded-lg bg-[#0e1726] border border-[#2a3d5d] text-xs font-mono text-teal-400 hover:text-white hover:bg-[#1b2a47] transition-all flex items-center gap-1.5"
                    >
                      <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
                      {isExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Key Capabilities Bullet Grid */}
                <div className="py-3">
                  <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-text-muted block mb-2">
                    What It Does
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-text-secondary">
                    {feat.keyCapabilities.map((cap, i) => (
                      <div key={i} className="flex items-start gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                        <span>{cap}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* EXPANDABLE DEEP DIVE SECTION */}
                {isExpanded && (
                  <div className="mt-3 pt-4 border-t border-[#1e293b] space-y-4 animate-fade-in bg-[#0c1424]/70 -mx-5 -mb-5 p-5 rounded-b-card">
                    {/* Step-by-Step Workflow */}
                    <div>
                      <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-teal-400 flex items-center gap-1.5 mb-2">
                        <ArrowRight className="w-3.5 h-3.5" /> Steps
                      </h4>
                      <ol className="list-decimal list-inside space-y-1.5 text-xs text-text-secondary">
                        {feat.workflow.map((step, idx) => (
                          <li key={idx} className="leading-relaxed">
                            <span className="text-white font-medium">{step.split(':')[0]}:</span>
                            {step.includes(':') ? step.split(':').slice(1).join(':') : ''}
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* Architecture & Implementation Details */}
                    <div>
                      <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-teal-400 flex items-center gap-1.5 mb-1.5">
                        <Cpu className="w-3.5 h-3.5" /> How It Works
                      </h4>
                      <p className="text-xs text-text-secondary leading-relaxed bg-[#090d16] p-3 rounded-lg border border-[#1e293b]">
                        {feat.architecture}
                      </p>
                    </div>


                    {/* Safety Guardrails & Edge Cases */}
                    <div>
                      <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-rose-400 flex items-center gap-1.5 mb-1.5">
                        <ShieldCheck className="w-3.5 h-3.5" /> Safeguards
                      </h4>
                      <ul className="space-y-1 text-xs text-text-secondary">
                        {feat.safetyGuardrails.map((guard, gi) => (
                          <li key={gi} className="flex items-start gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0 mt-1.5" />
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

      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-bold font-display text-white">
            Sample Page Scenarios
          </h2>
          <span className="text-xs text-text-muted font-mono">
            Fixed sample data
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {SAMPLE_SCENARIOS.map((sc) => (
            <Card
              key={sc.scenario}
              className="p-3.5 bg-[#162238]/90 border border-[#2a3d5d] shadow-card flex flex-col justify-between"
            >
              <div>
                <div className={`font-mono text-xs font-bold ${sc.color} mb-1`}>
                  {sc.name}
                </div>
                <p className="text-[11px] text-text-secondary leading-relaxed mb-3">
                  {sc.desc}
                </p>
              </div>
              <a
                href={sc.link}
                className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold text-primary hover:underline"
              >
                <span>Launch &rarr;</span>
              </a>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold font-display text-white">
              Frequently Asked Questions
            </h2>
          </div>
          <span className="text-xs font-mono text-text-muted">
            {filteredFaqs.length} answers available
          </span>
        </div>

        <div className="space-y-2.5">
          {filteredFaqs.map((faq) => {
            const isOpen = openFaqIds[faq.id] ?? false;
            return (
              <div
                key={faq.id}
                className="bg-[#162238]/90 border border-[#2a3d5d] rounded-xl overflow-hidden shadow-card transition-colors"
              >
                <button
                  type="button"
                  aria-expanded={isOpen}
                  onClick={() => toggleFaq(faq.id)}
                  className="w-full text-left p-4 flex items-center justify-between gap-3 text-xs font-semibold text-white hover:bg-[#1b2a47]/60 transition-colors"
                >
                  <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1.5 min-w-0">
                    <span className="px-2 py-0.5 rounded-full bg-[#0e1726] border border-[#1e293b] text-[10px] font-mono text-primary shrink-0">
                      {faq.tag}
                    </span>
                    <span className="font-display font-bold text-sm text-white break-words">
                      {faq.question}
                    </span>
                  </div>
                  <ChevronDown
                    className={`w-4 h-4 text-text-muted shrink-0 transition-transform duration-200 ${
                      isOpen ? 'rotate-180 text-primary' : ''
                    }`}
                  />
                </button>

                {isOpen && (
                  <div className="px-4 pb-4 pt-1 text-xs text-text-secondary leading-relaxed font-sans border-t border-[#1e293b]/60 bg-[#0e1726]/40">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

    </div>
  );
};
