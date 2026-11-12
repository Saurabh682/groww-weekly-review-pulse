# Phase 4 Test Report: MCP Publishing (Google Docs + Gmail)

**Date:** 2026-11-11  
**Status:** PASS (17 passed, 0 failed, 0 skipped in Phase 4 suite; 127 total passed across complete regression suite)  
**Suite:** `tests/test_phase4.py`  

---

## Summary

All required Phase 4 capabilities, fallbacks, and security invariants defined in `docs/edge-case.md` §16 (`MCP-*`) have been implemented, tested, and verified.

| Group | Test IDs Covered | Priority | Result | Key Capabilities Verified |
| :--- | :--- | :--- | :--- | :--- |
| **Publish Lifecycle & Idempotency** | `MCP-01`, `MCP-08`, `MCP-09` | P0 | **PASSED** | First publish stages Google Doc and creates Gmail draft with Doc link; identical rerun computes matching content hash and returns NO-OP with zero tool calls (`MCP-08`); modified content updates existing Doc and draft in place (`MCP-09`) |
| **Resilience & Fallback Handling** | `MCP-02`, `MCP-03`, `MCP-06`, `MCP-10`, `MCP-11` | P0 / P1 | **PASSED** | Partial failure resume: if Doc succeeded and Gmail failed, next run resumes at Gmail step reusing existing `doc_id` without creating duplicates (`MCP-06`); external deletion of Doc or Draft triggers clean recreation and updates `publish_state` (`MCP-10`, `MCP-11`); unsupported update tools trigger clean versioned fallbacks (`MCP-02`, `MCP-03`) |
| **Error Handling & Retries** | `MCP-04`, `MCP-05`, `MCP-13`, `MCP-15` | P0 / P1 | **PASSED** | Connection failure retries up to 3 times before raising `MCPConnectionError` (`MCP-04`); expired MCP host authorization raises clear actionable error instructing connector re-authorization (`MCP-05`); malformed responses lacking IDs/URLs fail closed (`MCP-13`); empty or invalid recipient emails fail fast (`MCP-15`) |
| **Security & Privacy Invariants** | `MCP-17`, `MCP-18`, `MCP-24` | P0 | **PASSED** | **Never Send:** Capability map and publishers strictly forbid send tools (`MCP-17`); static scan guarantees zero Google client SDK or direct REST imports across pipeline (`MCP-18`); **Pre-publish PII gate** re-scans draft subject and body immediately before draft creation, blocking publish on any PII detection (`MCP-24`) |
| **Email Formatting & Link Integrity** | `MCP-21`, `MCP-25`, `MCP-26` | P1 | **PASSED** | Returned Google Doc URL is cleanly embedded in email body (`MCP-25`); Unicode symbols (`₹`, `★`) survive without garbling (`MCP-21`); ISO week-start dates are consistent across title and subject (`MCP-26`) |

---

## Live Pipeline Execution Verification

The complete publish stage was verified against the real Groww review pulse note:

- **Command Executed:** `python -m src.pipeline publish --week 2026-11-10 --dry-run`
- **Initial Run:**
  - Status: `PUBLISHED`
  - Week Start: `2026-11-09`
  - Google Doc URL: `https://docs.google.com/document/d/doc_1001/edit`
  - Google Doc ID: `doc_1001`
  - Gmail Draft ID: `draft_2001`
  - Content Hash: `fc4c01338494aad2e73de886d343576950a1ec94ff5151f8ecbc7db0bfd1f02d`
- **Immediate Rerun:**
  - Status: `NOOP`
  - Message: `Content hash unchanged. Publish skipped (idempotent no-op).`
  - Tool Calls Made: `0`

---

## Deliverables Verified

1. `src/mcp/client.py`: Structured client layer with exponential backoff retries, error types (`MCPConnectionError`, `MCPTimeoutError`, `MCPAuthExpiredError`), and `MockMCPClient` for hermetic testing.
2. `src/mcp/capabilities.py`: Resolution engine mapping abstract capabilities (`docs.create`, `docs.update`, `gmail.create_draft`, `gmail.update_draft`) to concrete tools while forbidding send actions.
3. `src/mcp/publisher.py`: `DocsPublisher`, `DraftPublisher`, and `PulsePublisher` enforcing idempotency via SQLite `publish_state`, pre-publish PII gating, and partial-failure resume.
4. `src/pipeline.py publish`: CLI subcommand supporting `--week` and `--dry-run`.
5. `tests/test_phase4.py`: 17 passing contract and unit tests.
