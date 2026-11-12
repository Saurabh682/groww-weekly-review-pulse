# Groww Weekly Review Pulse

> Turn raw app-store feedback for **Groww (Stocks, Mutual Fund, IPO)** into a one-page weekly pulse that a team can scan in minutes: what users care about, what they actually said, and what to do next.

---

## Project Overview

Groww receives high volumes of public reviews. This project builds an automated, MCP-first pipeline focused on **Google Play Store** reviews (Apple App Store deferred for future iterations) to:
1. **Ingest & Scrub**: Ingest recent public reviews (last 8–12 weeks) and strictly scrub all PII (names, emails, phone numbers, account IDs).
2. **Cluster Themes**: Group reviews into at most 5 product-relevant themes.
3. **Generate Pulse Note**: Produce a concise (≤250 words) weekly note with top 3 themes, 3 verbatim user quotes, and 3 actionable ideas.
4. **Publish via MCP**: Create/update a Google Doc and create a Gmail draft addressed to self/alias using Model Context Protocol (MCP) integrations.

---

## Documentation

All project documentation, design plans, and specifications are maintained in the [`docs/`](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/README.md) directory:

- [Problem Statement (`docs/groww-weekly-review-pulse-problem.md`)](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/groww-weekly-review-pulse-problem.md)
- [Architecture Design (`docs/architecture.md`)](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/architecture.md)
- [Implementation Plan (`docs/implementation-plan.md`)](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/implementation-plan.md)
- [Edge Cases & Testing Matrix (`docs/edge-case.md`)](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/edge-case.md)
- [MCP Server Specification (`docs/mcp-server-problem-statement.md`)](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/mcp-server-problem-statement.md)
- [Gmail & Docs MCP Server Subproject (`gmail-docs-mcp/`)](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/gmail-docs-mcp/README.md)
- [Documentation Index (`docs/README.md`)](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/README.md)

---

## Architecture Layout

```
groww-weekly-review-pulse/
├── README.md
├── docs/                     # Central documentation directory (all .md files)
│   ├── README.md             # Documentation registry & maintenance guide
│   └── groww-weekly-review-pulse-problem.md
├── gmail-docs-mcp/           # Dedicated MCP Server subproject (Gmail & Docs)
│   ├── README.md
│   ├── docs/                 # MCP server documentation & problem statement
│   ├── package.json
│   └── src/
├── config/                   # Pulse & MCP capability configurations
├── data/
│   ├── imports/              # Manually exported public review files
│   └── raw/                  # Allowlisted, PII-stripped review payloads
├── src/
│   ├── ingest/               # Play Store CSV importers
│   ├── clean/                # Normalization, deduplication, PII scrubbing
│   ├── themes/               # Clustering + labeling
│   ├── note/                 # Note generation (word-count enforced)
│   ├── mcp/                  # MCP client wrappers & capability resolution
│   ├── store/                # SQLite storage
│   └── pipeline.py           # Orchestrates the weekly run
├── prompts/                  # LLM prompts for theming & note generation
├── tests/                    # PII verification, verbatim checks, word-count tests
└── outputs/                  # Local copies of weekly notes (Markdown fallback)
```
