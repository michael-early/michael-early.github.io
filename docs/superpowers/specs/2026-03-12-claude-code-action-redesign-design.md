# Design: Claude Code Action Redesign

**Date:** 2026-03-12
**Status:** Approved
**Scope:** Replace custom Python agent with `anthropics/claude-code-action` using claude.ai Max subscription OAuth

## Context

The portfolio agent was originally designed to call the Anthropic API directly via a custom Python script (`agent/run.py`). This required an `ANTHROPIC_API_KEY` secret with per-token billing. The redesign replaces this with `claude-code-action`, which authenticates via the owner's claude.ai Max subscription — no API billing.

## Architecture

### What stays

- `issues.opened` trigger
- Job-level `if: github.event.issue.user.login == github.repository_owner` (owner-only guard)
- Bot-actor skip step
- Branch protection on `main`

### What changes

| Item | Before | After |
|------|--------|-------|
| Auth | `ANTHROPIC_API_KEY` secret (API billing) | `CLAUDE_CODE_OAUTH_TOKEN` secret (Max subscription) |
| Agent logic | `agent/run.py` custom Python | `anthropics/claude-code-action@v1` |
| File editing | Custom code (Phase 2) | Built into action |
| PR creation | Custom code (Phase 3) | Built into action |
| HTML validation | Explicit step (Phase 4) | Dropped — PR review is the safety net |
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
    if: github.event.issue.user.login == github.repository_owner
    permissions:
      contents: write
      pull-requests: write
      issues: write

    steps:
      - name: Skip if bot actor
        env:
          ACTOR: ${{ github.actor }}
        run: |
          if [ "$ACTOR" = "github-actions[bot]" ]; then
            echo "Skipping: triggered by bot actor"
            exit 0
          fi

      - uses: actions/checkout@v4

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

## Phase Structure

### Phase 1: Workflow Scaffold (update to close out)
- Update `portfolio-agent.yml`: remove secret assertion step, replace agent stub with `claude-code-action`, expand permissions
- Delete `agent/run.py`
- Update `README.md`: replace `ANTHROPIC_API_KEY` instructions with `CLAUDE_CODE_OAUTH_TOKEN` OAuth setup steps
- Close Phase 1 checkpoint

### Phase 2: Claude Code Action Integration
- OAuth setup: install Anthropic GitHub App, generate `CLAUDE_CODE_OAUTH_TOKEN`, add to repo secrets
- Verify end-to-end: file test issue → confirm PR opens on `agent/issue-{N}` branch
- Covers EDIT-01, SAFE-02, PR-01, PR-02

## Requirements Coverage

| Requirement | Description | Phase | How covered |
|---|---|---|---|
| TRIG-01 | Owner-only trigger | 1 | Job-level `if:` condition |
| SAFE-01 | Skip bot actor | 1 | Explicit skip step |
| EDIT-01 | Read HTML/CSS files | 2 | Action + prompt file-scope rule |
| SAFE-02 | No binary files | 2 | Prompt explicit rule |
| PR-01 | Branch + PR creation | 2 | Built into action |
| PR-02 | PR description with issue ref | 2 | Prompt instructs "Closes #N" |
| SAFE-03 | HTML validation | dropped | PR review is the safety net |

## OAuth Setup (one-time)

1. Go to claude.ai → Settings → Connections → GitHub
2. Install the Anthropic GitHub App on the repo
3. Generate an OAuth token
4. Add to repo secrets as `CLAUDE_CODE_OAUTH_TOKEN`

## Trade-offs

**Accepted:**
- Less control over exact agent behavior (prompt-driven vs. code-driven)
- SAFE-03 (HTML validation) dropped — acceptable given PR review gate

**Gained:**
- No API billing — usage from Max subscription
- No custom Python to maintain
- File I/O, git, and PR creation handled natively
- 4 phases → 2 phases
