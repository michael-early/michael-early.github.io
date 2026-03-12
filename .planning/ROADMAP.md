# Roadmap: Portfolio Site Agent

## Overview

Build a GitHub Actions workflow that watches for issues filed by the repo owner, calls the Claude API to make the requested HTML/CSS edits, and opens a Pull Request for human review. The agent never pushes directly to main — every change goes through PR review first. Four phases move from security-first scaffolding through API integration, PR creation, and output hardening, each delivering a testable capability before the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Workflow Scaffold** - Trigger, security guards, and secret wiring — no API calls yet
- [ ] **Phase 2: Claude Integration** - Agent reads files, calls Claude, writes edits to disk
- [ ] **Phase 3: PR Creation** - Branch, commit, open PR, and post issue comment
- [ ] **Phase 4: Output Hardening** - HTML validation and idempotency guard before commit

## Phase Details

### Phase 1: Workflow Scaffold
**Goal**: The workflow fires exactly when it should and never when it should not — owner-only, no bot loops, no direct-to-main pushes, secrets wired correctly
**Depends on**: Nothing (first phase)
**Requirements**: TRIG-01, SAFE-01
**Success Criteria** (what must be TRUE):
  1. Filing an issue as the repo owner causes the workflow to run; filing an issue as any other user does not
  2. The workflow exits cleanly when triggered by the bot actor (no infinite loop)
  3. The agent script prints issue env vars and exits 0 — end-to-end plumbing verified with no API calls
  4. Pushing to main is blocked by branch protection; the workflow only creates feature branches
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Create workflow YAML and Python agent stub
- [ ] 01-02-PLAN.md — Write README setup docs and verify end-to-end in live GitHub

### Phase 2: Claude Integration
**Goal**: The agent reads the issue body and relevant site files, calls Claude, and writes the edited files to disk — no branch or PR yet
**Depends on**: Phase 1
**Requirements**: EDIT-01, SAFE-02
**Success Criteria** (what must be TRUE):
  1. Agent loads only HTML/CSS files that are relevant to the issue instruction (allowlist enforced in code)
  2. Agent never opens, reads, or writes a binary file (PDF, image) regardless of what the issue body requests
  3. The Claude API returns a structured JSON response and the agent writes the specified file contents to disk
  4. Token count is logged after every API call so cost-per-run is visible in the Actions log
**Plans**: TBD

### Phase 3: PR Creation
**Goal**: The agent creates a deterministic feature branch, commits the edited files, opens a PR against main, and posts a comment on the original issue
**Depends on**: Phase 2
**Requirements**: PR-01, PR-02
**Success Criteria** (what must be TRUE):
  1. Filing an issue end-to-end produces a PR on `agent/issue-{N}` branch — no manual steps required
  2. The PR description names what changed, why it changed, and includes "Closes #N" referencing the original issue
  3. The bot posts a comment on the issue with a direct link to the opened PR
**Plans**: TBD

### Phase 4: Output Hardening
**Goal**: Malformed HTML from the model is caught before it reaches the PR; duplicate PRs for the same issue are blocked
**Depends on**: Phase 3
**Requirements**: SAFE-03
**Success Criteria** (what must be TRUE):
  1. If the Claude response contains invalid HTML, the workflow fails and posts an error comment on the issue — no PR is created
  2. Re-triggering the workflow for the same issue number does not open a duplicate PR if one is already open
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workflow Scaffold | 1/2 | In Progress|  |
| 2. Claude Integration | 0/TBD | Not started | - |
| 3. PR Creation | 0/TBD | Not started | - |
| 4. Output Hardening | 0/TBD | Not started | - |
