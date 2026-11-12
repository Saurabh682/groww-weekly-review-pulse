---
name: Indian Fintech Analytics Pulse
colors:
  surface: '#f8f9fb'
  surface-dim: '#d9dadc'
  surface-bright: '#f8f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#edeef0'
  surface-container-high: '#e7e8ea'
  surface-container-highest: '#e1e2e4'
  on-surface: '#191c1e'
  on-surface-variant: '#3c4a43'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f3'
  outline: '#6c7a73'
  outline-variant: '#bbcac1'
  surface-tint: '#006c4f'
  primary: '#006c4f'
  on-primary: '#ffffff'
  primary-container: '#00b386'
  on-primary-container: '#003d2c'
  inverse-primary: '#50ddad'
  secondary: '#5a5e69'
  on-secondary: '#ffffff'
  secondary-container: '#dfe2ef'
  on-secondary-container: '#60646f'
  tertiary: '#904d00'
  on-tertiary: '#ffffff'
  tertiary-container: '#ea841b'
  on-tertiary-container: '#542a00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#71fac8'
  primary-fixed-dim: '#50ddad'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#dfe2ef'
  secondary-fixed-dim: '#c3c6d2'
  on-secondary-fixed: '#181c24'
  on-secondary-fixed-variant: '#434751'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#f8f9fb'
  on-background: '#191c1e'
  surface-variant: '#e1e2e4'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  metric-num-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.02em
  metric-num-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-tablet: 1.5rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style
The brand personality represents precision, calm financial authority, and instantaneous clarity tailored for high-velocity investment analysis. The experience is engineered for product managers, growth leads, and financial analysts reviewing weekly platform performance, portfolio engagement, and customer journey friction points.

The design style is a calibrated synthesis of Modern Corporate SaaS and High-Density Fintech Minimalism:
- **Atmosphere:** Cool, disciplined, scannable, and reassuringly robust.
- **Surface Philosophy:** Crisp, elevated white data modules floating over an airy, muted off-white foundation to reduce cognitive fatigue during extended analytical sessions.
- **Micro-Interactions:** Subtle, swift state transitions (150ms ease-out) that reinforce a zero-latency operational feel.
- **Visual Weight:** Intentional distribution of contrast, where numbers and tabular data lead the visual hierarchy, complemented by purposeful pill badges and categorical status cues.

## Colors
The palette leverages deliberate status signaling against a quiet, neutral baseline to ensure mission-critical metrics and anomalies stand out effortlessly.

- **Primary Accent (`#00B386`):** The signature growth teal-green. Optimized for WCAG AA compliance against pure white and light surfaces. Communicates upward momentum, completed milestones, positive delta percentages, and active transactional touchpoints.
- **Secondary / Ink (`#1E222B`):** Deep graphite-slate. Delivers high contrast for primary metrics, headers, and key financial values without the harshness of pure black. Paired with `#44475B` for secondary analytical notes and metadata labels.
- **Tertiary / Friction Highlight (`#D97706`):** Warm burnished amber. Reserved strictly for attention-required signals, drop-offs, throughput slowdowns, and moderate operational friction.
- **Negative / Alert (`#E53935` / `#F43F5E`):** Soft coral and crimson. Used exclusively for critical churn, API errors, down-trend regressions, and compliance anomalies.
- **Neutral Canvas (`#F7F8FA`):** An ultra-soft, cool grey canvas that establishes natural perimeter framing around pure white (`#FFFFFF`) content tiles.
- **Structural Outlines (`#E6E8EC`):** A hairline grey separating cards, table rows, and filters without interrupting scanning flow.

## Typography
Typographic hierarchy is achieved using Inter throughout all viewport sizes, capitalizing on its balanced proportions and open counters.

- **Tabular Figures:** Always apply `font-feature-settings: 'tnum' on, 'cv05' on, 'cv11' on` across all metric levels, charts, and table rows to align values vertically and preserve data integrity across currency and percentage columns.
- **Indian Numbering Format:** Ensure layout containers accommodate the standard Indian lakhs/crores formatting (e.g., ₹12,45,200) without artificial breaks or awkward word wraps.
- **Hierarchy Rules:**
  - `metric-num-lg` and `metric-num-md` are exclusively paired with uppercase `label-sm` tracking to anchor rapid KPI absorption.
  - Body copy uses relaxed letter-spacing for explanatory friction notes, maintaining immediate readability against dense data grids.

## Layout & Spacing
The layout follows a 12-column responsive fluid grid anchored within a maximum width of 1440px to ensure ultra-wide monitors do not stretch analytical tables beyond natural peripheral scan bounds.

- **Breakpoints & Behavior:**
  - **Desktop (≥ 1024px):** 12-column system, 24px (`gutter-desktop`) column gutters, 32px (`margin-desktop`) canvas margins. Sidebar remains fixed at 240px width with multi-pane metric dashboard cards spanning 3, 4, 6, or 12 columns.
  - **Tablet (768px – 1023px):** 8-column layout, 16px (`gutter`) column gutters, 24px (`margin-tablet`) outer canvas margins. Analytical cards re-flow to equal half-width modules (4 columns each) or full-width blocks.
  - **Mobile (< 768px):** 4-column layout, 12px gutters, 16px (`margin`) outer margins. KPI blocks collapse to 2x2 grids or full-width vertical stacks; tables transition to horizontal swipe or nested accordion summaries.
- **Rhythm & Density:** Standardize card interior padding to `space-xl` (24px) for major widgets and `space-lg` (16px) for compact metric cards, maintaining an uncluttered, focused cadence throughout.

## Elevation & Depth
The system relies on tonal differentiation combined with an ultra-diffused, micro-ambient elevation model rather than heavy, dramatic shadows.

- **Ground Plane:** `#F7F8FA` acts as the base neutral surface tier.
- **Base Cards & Modules:** Solid white (`#FFFFFF`) surfaces elevated with a crisp border outline (`1px solid #E6E8EC`) combined with an ultra-soft ambient shadow: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05)`.
- **Hover & Active States:** Interactive cards and active row selections shift to `box-shadow: 0 4px 12px rgba(30, 34, 43, 0.06)` with the border shifting to `#D6D9E0`, creating tactile feedback without visual agitation.
- **Popovers, Select Panels, & Modals:** Elevated containers use `box-shadow: 0 8px 24px rgba(30, 34, 43, 0.08)` bordered by `#E6E8EC`, preserving separation over complex data charts and graphs below.

## Shapes
A unified 12px border radius across structural components maintains a friendly, modern fintech aesthetic while respecting high visual density.

- **Cards & Data Modules:** Enforce a strict `12px` (equivalent to level 2 `rounded-lg`) corner radius for standard metrics cards, charts, and summary containers.
- **Interactive Buttons & Form Inputs:** Set to `8px` corner radius for an accurate, click-targeted control profile.
- **Pill Badges & Status Indicators:** Rendered with full radial caps (`rounded-full` / 9999px) to distinctly segregate meta-tags, tags, and status labels from rectangular metric cards and square inputs.

## Components

### Buttons
- **Primary:** Filled `#00B386` background, `#FFFFFF` text, `8px` radius, medium font weight (`label-md`). Hover transitions to `#00A37A`. Active scale `0.99`.
- **Secondary / Outline:** White background with `1px solid #E6E8EC`, text `#1E222B`. Hover state applies `#F7F8FA` background and `#D6D9E0` border.
- **Ghost:** Transparent background, `#44475B` text; hover reveals `#F0F2F5` tint with zero border.

### Status Badges & Pill Chips
- **Success / Positive:** Pill-shaped (`9999px`), background `#E6F8F3`, text `#00B386`, `label-sm` typography with leading positive icon or up-trend glyph.
- **Warning / Friction:** Background `#FEF3C7`, text `#D97706`, tracking localized funnel drop-offs.
- **Critical / Negative:** Background `#FEE2E2`, text `#E53935`, flagging system degradation, failed KYC, or churn spikes.
- **Neutral:** Background `#F0F2F5`, text `#44475B`, utilized for versioning, metadata timestamps, and category indicators.

### Metric & KPI Cards
- Crisp `#FFFFFF` surface with `12px` border radius, `1px solid #E6E8EC`, and ambient shadow.
- Interior layout incorporates an upper label row (title + optional help tooltip), a prominent numerical value (`metric-num-lg` in `#1E222B`), and a lower performance row showcasing comparative trend pills (e.g., `+14.2% vs last week`) alongside micro sparkline visualizations.

### Input Fields & Filters
- Height `40px`, corner radius `8px`, border `1px solid #E6E8EC`, background `#FFFFFF`. Text set to `#1E222B` with placeholder `#8C91A0`.
- Focus state activates an outline halo: `border-color: #00B386; box-shadow: 0 0 0 3px rgba(0, 179, 134, 0.15)`.

### Checkboxes & Radio Controls
- Base size `16px x 16px`, corner radius `4px` (checkbox) or circular (radio), border `1.5px solid #C4C8D2`.
- Checked state fills with `#00B386` exhibiting an internal pure white check/bullet graphic.

### Tables & Dense Analytical Lists
- **Header:** Sticky `#F7F8FA` background, uppercase `label-sm` text in `#6B7280`, subtle bottom border `1px solid #E6E8EC`.
- **Rows:** Alternating clear/white canvas with `48px` cell height. Hover triggers `#F9FAFB` row tinting.
- **Cell Content:** Left-align categoricals; strictly right-align numerical values, amounts in Rupees (₹), and percentage shifts using tabular figures.

### Funnel & Cohort Visualizers
- Multi-step conversion containers encased in white cards with step bars shaded in `#00B386` with drop-off corridors accented with `#F5A623` / `#D97706` friction markers.