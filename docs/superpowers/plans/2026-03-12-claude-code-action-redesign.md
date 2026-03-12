# Claude Code Action Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the custom Python agent and direct API key auth with `anthropics/claude-code-action` using claude.ai Max subscription OAuth, eliminating API billing and custom agent code.

**Architecture:** Keep the existing Phase 1 security scaffold (owner-only trigger, branch protection) but replace the "Assert secrets wired" and "Run agent stub" steps with a single `claude-code-action` step. Combine the owner and bot-actor guards into one job-level `if:` condition. Delete `agent/run.py`. Update README to document OAuth setup instead of API key setup.

**Tech Stack:** GitHub Actions, `anthropics/claude-code-action@v1`, YAML, Markdown

**Spec:** `docs/superpowers/specs/2026-03-12-claude-code-action-redesign-design.md`

---

## Chunk 1: Update workflow and delete Python agent

### Task 1: Rewrite portfolio-agent.yml

**Files:**
- Modify: `.github/workflows/portfolio-agent.yml`

- [ ] **Step 1: Replace the workflow file contents**

Replace `.github/workflows/portfolio-agent.yml` with:

```yaml
name: Portfolio Agent

on:
  issues:
    types: [opened]

jobs:
  agent:
    runs-on: ubuntu-latest
    # Job-level if: evaluates expressions natively without ${{ }} wrappers.
    # Owner-only guard and bot-actor skip combined here — a job-level condition
    # is the only reliable way to halt a job in GitHub Actions.
    if: |
      github.event.issue.user.login == github.repository_owner &&
      github.actor != 'github-actions[bot]'
    permissions:
      contents: write
      pull-requests: write
      issues: write

    steps:
      # persist-credentials: true (default) must remain so the action can push branches.
      - uses: actions/checkout@v4

      # Pin to a commit SHA in production to prevent supply-chain risk from tag mutation.
      # @v1 is acceptable for a personal project where the risk tolerance is higher.
      - uses: anthropics/claude-code-action@v1
        with:
          prompt: |
            You are a portfolio site assistant. The repo owner has filed a GitHub
            issue requesting a change to their portfolio site.

            Issue: ${{ github.event.issue.title }}
            Request: ${{ github.event.issue.body }}

            Rules:
            - Only edit HTML and CSS files: index.html and projects/*/index.html
            - Never read or modify binary files (PDFs, images, .jpeg, .pdf)
            - Create a branch named agent/issue-${{ github.event.issue.number }}
            - Open a PR against main summarizing what changed and why
            - Include "Closes #${{ github.event.issue.number }}" in the PR body

            Make the requested changes and open the PR.
        env:
          CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 2: Verify old API key reference is gone**

```bash
grep -n "ANTHROPIC_API_KEY\|claude-code-action" .github/workflows/portfolio-agent.yml
```

Expected: only `claude-code-action` line — no `ANTHROPIC_API_KEY` line

- [ ] **Step 3: Lint the workflow (if actionlint is available)**

```bash
which actionlint && actionlint .github/workflows/portfolio-agent.yml || echo "actionlint not installed — skip"
```

Expected: no errors, or "actionlint not installed — skip"

- [ ] **Step 4: Commit**

```bash
git status
git add .github/workflows/portfolio-agent.yml
git commit -m "feat(workflow): replace Python agent with claude-code-action, OAuth auth"
```

---

### Task 2: Delete agent/run.py

**Files:**
- Delete: `agent/run.py`

- [ ] **Step 1: Delete the file**

```bash
git rm agent/run.py
```

- [ ] **Step 2: Verify directory is gone (git handles cleanup automatically)**

```bash
ls agent 2>/dev/null && echo "agent dir has remaining files — review" || echo "agent dir removed"
```

Expected: "agent dir removed"

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(agent): remove Python agent stub — replaced by claude-code-action"
```

---

### Task 3: Update README for OAuth setup

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the Portfolio Agent Setup section**

Replace the entire "## Portfolio Agent Setup" section — from the `## Portfolio Agent Setup` heading through (and including) the trailing `---` separator that follows the "2. Enable Branch Protection on main" subsection — with:

```markdown
## Portfolio Agent Setup

This repository includes a GitHub Actions workflow that lets the repo owner file an issue to trigger automated portfolio updates via Claude (claude.ai Max subscription). The following one-time setup steps are required.

### 1. Connect Claude to GitHub

1. Go to [claude.ai](https://claude.ai) → **Settings → Connections → GitHub**
2. Install the **Anthropic GitHub App** on this repository
3. Generate an OAuth token
4. Add the token to repository **Settings → Secrets and variables → Actions** as a new secret named `CLAUDE_CODE_OAUTH_TOKEN`

No Anthropic API key is needed — usage counts against your claude.ai Max subscription.

### 2. Enable Branch Protection on main

1. Go to repository **Settings → Branches** (under "Code and automation")
2. Click **Add rule** (may appear as **Add branch ruleset** on newer GitHub UI)
3. Branch name pattern: `main`
4. Check **Require a pull request before merging**
5. Click **Create**

Note: On personal repos, branch protection applies to all pushes including the owner. The agent workflow always creates feature branches (`agent/issue-{N}`) and never pushes directly to `main`, so branch protection does not affect the agent.
```

- [ ] **Step 2: Verify the section was replaced correctly**

```bash
grep -n "ANTHROPIC_API_KEY\|CLAUDE_CODE_OAUTH_TOKEN" README.md
```

Expected: only `CLAUDE_CODE_OAUTH_TOKEN` lines — no `ANTHROPIC_API_KEY` lines

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README — OAuth setup replaces API key instructions"
```

---

## Chunk 2: Update GSD planning state

> **Depends on Chunk 1 being complete.** Do not run these tasks until the workflow, agent deletion, and README changes from Chunk 1 are committed.

### Task 4: Update Phase 1 plan and close checkpoint

**Files:**
- Modify: `.planning/phases/01-workflow-scaffold/01-02-PLAN.md`
- Create: `.planning/phases/01-workflow-scaffold/01-02-SUMMARY.md`
- Modify: `.planning/STATE.md`
- Modify: `.planning/ROADMAP.md`

- [ ] **Step 1: Update all stale ANTHROPIC_API_KEY references in 01-02-PLAN.md**

In `.planning/phases/01-workflow-scaffold/01-02-PLAN.md`, replace all occurrences of `ANTHROPIC_API_KEY` with `CLAUDE_CODE_OAUTH_TOKEN`. This covers the `must_haves.truths` entry, the `artifacts` block, the `<interfaces>` section, and the `<tasks>` section.

```bash
sed -i '' 's/ANTHROPIC_API_KEY/CLAUDE_CODE_OAUTH_TOKEN/g' .planning/phases/01-workflow-scaffold/01-02-PLAN.md
```

Verify:
```bash
grep -n "ANTHROPIC_API_KEY" .planning/phases/01-workflow-scaffold/01-02-PLAN.md
```
Expected: no output (all references replaced)

- [ ] **Step 2: Create 01-02-SUMMARY.md**

Create `.planning/phases/01-workflow-scaffold/01-02-SUMMARY.md`:

```markdown
---
plan: 01-02
phase: 01-workflow-scaffold
status: complete
---

# Summary: 01-02 README Setup Docs + Phase 1 Closeout

## What was built

- `README.md` updated with OAuth setup instructions (`CLAUDE_CODE_OAUTH_TOKEN`) replacing the original `ANTHROPIC_API_KEY` instructions
- Branch protection setup steps retained verbatim

## Checkpoint resolution

Phase 1 verification checkpoint was resolved by architectural redesign:
- Original plan required end-to-end verification with `ANTHROPIC_API_KEY`
- Redesigned to use `anthropics/claude-code-action` with claude.ai Max OAuth (no API billing)
- Workflow and README updated to match new architecture
- End-to-end verification deferred to Phase 2 (OAuth setup required first)

## Key files

- `README.md` — OAuth setup documentation (this plan)
- For workflow and agent changes, see Chunk 1 commits (Task 1 and Task 2)

## Self-Check: PASSED
```

- [ ] **Step 3: Mark Phase 1 complete**

Try the GSD tool first:
```bash
node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" phase complete "01" && echo "Tool succeeded" || echo "Tool failed — apply manually"
```

If the tool fails, apply these STATE.md changes manually:
- Set `status: in_progress` → `status: complete` for phase 01 (or add completion date)
- Update `stopped_at:` to `Completed 01-workflow-scaffold/01-02-PLAN.md`
- Update `completed_plans: 1` → `completed_plans: 2`
- Update `percent:` accordingly
- In ROADMAP.md: mark `- [ ] **Phase 1: Workflow Scaffold**` → `- [x] **Phase 1: Workflow Scaffold**` and add completion date to the Progress table

- [ ] **Step 4: Commit**

```bash
git add .planning/
git commit -m "docs(phase-01): close phase 1 — redesigned to claude-code-action OAuth"
```

---

### Task 5: Update ROADMAP.md for collapsed phase structure

**Files:**
- Modify: `.planning/ROADMAP.md`
- Modify: `.planning/REQUIREMENTS.md`

- [ ] **Step 1: Update Phase 2 description in ROADMAP.md**

Find the "### Phase 2: Claude Integration" section and replace it with:

```markdown
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
```

- [ ] **Step 2: Remove Phases 3 and 4 from ROADMAP.md**

Delete the "### Phase 3: PR Creation" and "### Phase 4: Output Hardening" sections entirely.

Replace the Execution Order note with:
```
**Execution Order:**
Phases execute in numeric order: 1 → 2
```

Replace the Progress table with:
```markdown
| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workflow Scaffold | 2/2 | Complete | 2026-03-12 |
| 2. Claude Code Action Integration | 0/TBD | Not started | - |
```

- [ ] **Step 3: Mark SAFE-03 dropped in REQUIREMENTS.md**

Find `SAFE-03` in `REQUIREMENTS.md` and update its entry:

```markdown
- ~~**SAFE-03**: Edited HTML is validated before committing; malformed output is rejected~~ *(dropped — owner reviews PR diff before merging)*
```

Also remove SAFE-03 from the traceability table or mark it as `dropped`.

- [ ] **Step 4: Commit**

```bash
git add .planning/ROADMAP.md .planning/REQUIREMENTS.md
git commit -m "docs(roadmap): collapse to 2 phases, drop SAFE-03 — claude-code-action redesign"
```
