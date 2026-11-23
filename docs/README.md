# Documentation Index & Registry

This folder (`docs/`) is the central repository for all project documentation, specifications, architectural decisions, and tracking logs for the **Groww Weekly Review Pulse** project. All future markdown documents will be maintained here and updated as milestones are achieved.

---

## Document Registry

| Document | Description | Status |
| :--- | :--- | :--- |
| [groww-weekly-review-pulse-problem.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/groww-weekly-review-pulse-problem.md) | Problem statement v2: up to 5 apps, both stores, scheduled collection, per-app Docs/drafts, dashboard | Active / v2 |
| [multi-app-architecture.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/multi-app-architecture.md) | v2 architecture: registry, resolution, collectors, Supabase schema, matrix workflow, Composio, API, dashboard | Active / v2 |
| [architecture.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/architecture.md) | v1 architecture: pipeline stages, themes, note, validation, privacy (still applies per app) | Active / v1 (partly superseded) |
| [implementation-plan.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/implementation-plan.md) | Step-by-step development roadmap and phase-wise tasks | Active / Baseline |
| [edge-case.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/edge-case.md) | Comprehensive edge cases, corner scenarios, and test catalogue (P0/P1/P2) | Active / Baseline |
| [data-source-decision.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/data-source-decision.md) | Data source decision, Play Store import contract & identity exclusion rules | Active / Baseline |
| [tooling-selection.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/tooling-selection.md) | Tooling, model selection, local embeddings, and privacy agreements | Active / Baseline |
| [mcp-server-problem-statement.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/mcp-server-problem-statement.md) | Problem statement & specification for the Gmail + Google Docs MCP server | Active / Baseline |
| [eval.md](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/docs/eval.md) | Evaluation metrics, automated checks (word count ≤ 250, verbatim quotes, PII gate) | Planned |

---

## Current Decisions & Scope Adjustments

* **Multi-app (v2, 2026-11-23)**: Up to 5 apps, registered by name with confirm-from-top-3. Both stores, collected automatically (ADR-9) with backfill, daily and monthly reconcile (ADR-10). Supabase storage, one matrix workflow, Composio MCP, per-app dashboard (ADR-11 to ADR-16 in `multi-app-architecture.md`). Build continues as Phases 7-13 in `implementation-plan.md`.
* ~~**Data Ingestion Focus (ADR-8)**: Google Play Store only.~~ Superseded by ADR-9.
* **MCP Server Location**: The Gmail + Google Docs MCP server is developed in a dedicated subproject folder at [`groww-weekly-review-pulse/gmail-docs-mcp/`](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/gmail-docs-mcp/README.md) with its own [`docs/`](file:///D:/VibeCode/Applied%20Generative%20AI%20Bootcamp/groww-weekly-review-pulse/gmail-docs-mcp/docs/README.md).

---

## Maintenance Guidelines

1. **Location**: All project-related documentation, design notes, plans, and evaluation records must live inside this `docs/` folder.
2. **Registry Updates**: Whenever a new `.md` file is added or its status changes, update this registry table with its description and status.
3. **Change Tracking**: Keep existing documents in sync with code and pipeline changes as the project evolves.
