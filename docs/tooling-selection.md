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

---

## 2. Privacy & Data Handling Agreement

1. **Zero Raw PII to LLM:** Reviews undergo complete PII scrubbing (`clean/pii.py`) before entering any embedding or LLM prompt.
2. **Deterministic Validation Gate:** Word count (≤ 250 words), verbatim quote matching, and theme count (≤ 5) are verified by deterministic Python code before publishing; the LLM is not trusted for constraint enforcement.
3. **No Credential Exposure:** Secrets like API keys are read via environment variables (`.env`) and never logged or written to output artifacts.
