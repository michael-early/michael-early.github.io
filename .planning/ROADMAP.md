# Roadmap: Portfolio Site Agent

## Overview

Build a GitHub Actions workflow that watches for issues filed by the repo owner, calls the Claude API to make the requested HTML/CSS edits, and opens a Pull Request for human review. The agent never pushes directly to main — every change goes through PR review first.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Workflow Scaffold** - Trigger, security guards, and secret wiring — no API calls yet
- [ ] **Phase 2: Claude Code Action Integration** - OAuth token wired, action fires on owner issue, PR opens with HTML edits on `agent/issue-{N}` branch

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
- [x] 01-01-PLAN.md — Create workflow YAML and Python agent stub
- [x] 01-02-PLAN.md — Write README setup docs and verify end-to-end in live GitHub

### Phase 2: Claude Code Action Integration
**Goal**: OAuth token wired, action fires on owner issue, PR opens with HTML edits on `agent/issue-{N}` branch
**Depends on**: Phase 1
**Requirements**: EDIT-01, SAFE-02, PR-01, PR-02
**Success Criteria** (what must be TRUE):
  1. Filing an owner issue triggers the workflow; non-owner issue does not
  2. The opened PR targets `main`, branch is `agent/issue-{N}`, diff contains only HTML/CSS files
  3. PR body includes `Closes #N`
  4. No binary files appear in the PR diff
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workflow Scaffold | 2/2 | Complete | 2026-03-12 |
| 2. Claude Code Action Integration | 0/TBD | Not started | - |
