# Roadmap: Portfolio Site — Claude Code Workflow

## Overview

Set up the portfolio repo so Claude Code can make site changes directly from the terminal. Remove the GitHub Actions workflow built in Phase 1 and improve CLAUDE.md with enough context that edits can be made without clarifying questions.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Workflow Scaffold** - Trigger, security guards, and secret wiring — no API calls yet
- [ ] **Phase 2: Cleanup + CLAUDE.md** - Remove GitHub Actions workflow, improve CLAUDE.md, link housing-ml

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

### Phase 2: Cleanup + CLAUDE.md
**Goal**: GitHub Actions workflow removed, CLAUDE.md comprehensive enough to make any portfolio change without clarifying questions
**Depends on**: Phase 1
**Requirements**: CLAUDE-01, CLEAN-01
**Success Criteria** (what must be TRUE):
  1. `.github/workflows/portfolio-agent.yml` deleted
  2. CLAUDE.md documents project card HTML structure, CSS design system, project page format, and what files to never touch
  3. housing-ml project linked from main page
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workflow Scaffold | 2/2 | Complete | 2026-03-12 |
| 2. Cleanup + CLAUDE.md | 0/TBD | Not started | - |
