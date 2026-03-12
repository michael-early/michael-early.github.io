# Design: Claude Code Action Redesign

**Date:** 2026-03-12
**Status:** Approved
**Scope:** Replace custom Python agent with `anthropics/claude-code-action` using claude.ai Max subscription OAuth

## Context

The portfolio agent was originally designed to call the Anthropic API directly via a custom Python script (`agent/run.py`). This required an `ANTHROPIC_API_KEY` secret with per-token billing. The redesign replaces this with `claude-code-action`, which authenticates via the owner's claude.ai Max subscription — no API billing.

## Architecture

### What stays

- `issues.opened` trigger
- Branch protection on `main`

### What changes

| Item | Before | After |
|------|--------|-------|
| Auth | `ANTHROPIC_API_KEY` secret (API billing) | `CLAUDE_CODE_OAUTH_TOKEN` secret (Max subscription) |
| Agent logic | `agent/run.py` custom Python | `anthropics/claude-code-action@v1` |
| Bot-actor guard | Separate step using `exit 0` (ineffective) | Combined into job-level `if:` |
| File editing | Custom code (Phase 2) | Built into action |
| PR creation | Custom code (Phase 3) | Built into action |
| HTML validation | Explicit step (Phase 4) | Dropped — owner manually reviews PR diff before merging |
| Job permissions | `issues: read`, `contents: read` | `contents: write`, `pull-requests: write`, `issues: write` |

### Deleted

- `agent/run.py` — no longer needed

## Workflow

```yaml
name: Portfolio Agent

on:
  issues:
    types: [opened]

jobs:
  agent:
    runs-on: ubuntu-latest
    # Owner-only guard and bot-actor skip combined at job level.
    # github.actor is the account that triggered the event (may differ from issue author).
    # github.event.issue.user.login is the issue author.
    # Both conditions must pass for the job to run.
    # Job-level if: evaluates expressions natively without ${{ }} wrappers.
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

**Security note:** Issue title and body are interpolated into the prompt. This is safe because the job-level `if:` guard restricts execution to issues filed by the repo owner — no external user can trigger the workflow or inject instructions.

## Phase Structure

### Phase 1: Workflow Scaffold (update to close out)

Deliverables:
- Update `portfolio-agent.yml`: combine owner + bot guards into job-level `if:`, remove secret assertion step, replace agent stub with `claude-code-action`, expand permissions
- Delete `agent/run.py`
- Update `README.md`: replace `ANTHROPIC_API_KEY` instructions with `CLAUDE_CODE_OAUTH_TOKEN` OAuth setup steps
- Close Phase 1 checkpoint

### Phase 2: Claude Code Action Integration

Deliverables:
- OAuth setup: install Anthropic GitHub App, generate `CLAUDE_CODE_OAUTH_TOKEN`, add to repo secrets
- Verify end-to-end: file test issue as owner → PR opens on `agent/issue-{N}` branch with actual HTML edits

Acceptance criteria:
- [ ] Filing an owner issue triggers the workflow run (visible in Actions tab)
- [ ] Non-owner issue does not trigger a run
- [ ] The opened PR targets `main`, is named `agent/issue-{N}`, and contains a diff of HTML/CSS files only
- [ ] PR body includes `Closes #N`
- [ ] No binary files appear in the PR diff

## Requirements Coverage

| Requirement | Description | Phase | How covered |
|---|---|---|---|
| TRIG-01 | Owner-only trigger | 1 | Job-level `if:` condition |
| SAFE-01 | Skip bot actor | 1 | Job-level `if:` condition (combined with TRIG-01) |
| EDIT-01 | Read HTML/CSS files | 2 | Action + prompt file-scope rule |
| SAFE-02 | No binary files | 2 | Prompt explicit rule |
| PR-01 | Branch + PR creation | 2 | Built into action |
| PR-02 | PR description with issue ref | 2 | Prompt instructs "Closes #N" |
| SAFE-03 | HTML validation | dropped | Owner reviews PR diff before merging — manual gate |

## OAuth Setup (one-time)

1. Go to claude.ai → Settings → Connections → GitHub
2. Install the Anthropic GitHub App on the repo
3. Generate an OAuth token
4. Add to repo secrets as `CLAUDE_CODE_OAUTH_TOKEN`

## Trade-offs

**Accepted:**
- Less control over exact agent behavior (prompt-driven vs. code-driven)
- SAFE-03 (HTML validation) dropped — owner manually reviews the PR diff before merging; malformed HTML would be visible in the diff
- `@v1` tag pin carries supply-chain risk; acceptable for a personal project (upgrade path: pin to commit SHA)

**Gained:**
- No API billing — usage from Max subscription
- No custom Python to maintain
- File I/O, git, and PR creation handled natively
- 4 phases → 2 phases
