# Tooling & Architecture Decisions (Task 0.6)

**Status:** Approved  
**Date:** 2026-11-11  

---

## 1. Component Selection

| Component | Selected Tool / Technology | Rationale |
| :--- | :--- | :--- |
| **Language & Runtime** | Python 3.11+ / 3.13 | Native support for standard ML, SQLite, and MCP tooling |
| **Local Data Store** | SQLite (`data/pulse.db`) | Zero-ops, single-file relational store with strict PII-free schemas |
| **Embeddings** | `sentence-transformers` / `all-MiniLM-L6-v2` (or Gemini text-embedding-004) | Fast local inference without external API transmission of raw text; reproducible |
| **Clustering** | `scikit-learn` (`AgglomerativeClustering` / `KMeans`) | Deterministic grouping, cosine distance support, hard cap of `k ≤ 5` enforced in code |
| **LLM Provider** | Google Gemini (`gemini-2.5-flash`) | Fast, structured outputs with schema enforcement for theme labeling and action drafting |
| **MCP Integration** | Python MCP SDK / Stdio Transport | Standardized protocol, credentials remain inside MCP host environment |

### v2 changes (2026-11-23)

| Component | Selected Tool / Technology | Rationale |
| :--- | :--- | :--- |
| **Production Store** | Supabase Postgres (free tier) | Reachable from GitHub Actions, the HF backend and (through the backend) the dashboard; constraints and triggers enforce the 5-app cap. SQLite stays for tests and local runs behind `PulseStore` |
| **MCP Integration** | Composio MCP (Google Docs + Gmail toolkits), Python MCP SDK over Streamable HTTP | Google auth lives in Composio connected accounts; replaces the custom `gmail-docs-mcp` server |
| **Play Store data** | `google-play-scraper` (`search`, `app`, `reviews`) | Public, login-free; unofficial (risk in ADR-9) |
| **App Store data** | iTunes Search API, iTunes Lookup API, customer-reviews RSS (JSON) | Public and published by Apple; ~500 most recent reviews per fetch |
| **Scheduler** | GitHub Actions, one workflow with a matrix | Free, close to the repo, no extra infrastructure |
| **Backend API** | FastAPI on Hugging Face Spaces | Existing deploy target |
| **Operator auth** | Supabase Auth (magic link) + email allowlist | No passwords stored by us |
| **Secret scanning** | `gitleaks` in CI | The v1 repo had a committed MCP token |

---

## 2. Privacy & Data Handling Agreement

1. **Zero Raw PII to LLM:** Reviews undergo complete PII scrubbing (`clean/pii.py`) before entering any embedding or LLM prompt.
2. **Deterministic Validation Gate:** Word count (≤ 250 words), verbatim quote matching, and theme count (≤ 5) are verified by deterministic Python code before publishing; the LLM is not trusted for constraint enforcement.
3. **No Credential Exposure:** Secrets like API keys are read via environment variables (`.env`) and never logged or written to output artifacts.
