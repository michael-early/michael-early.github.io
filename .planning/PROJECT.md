# Portfolio Site — Claude Code Workflow

## What This Is

A well-documented portfolio site set up so Claude Code can make changes directly from the terminal. Open `claude` in this repo, describe the change, and it happens — no GitHub Actions, no issues, no PRs required.

## Core Value

Open `claude`, say what to change, it changes — CLAUDE.md gives Claude everything it needs to edit the site correctly without clarifying questions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] CLAUDE.md comprehensive enough to make changes without clarifying questions
- [ ] GitHub Actions workflow removed (no longer needed)
- [ ] housing-ml project linked from main page

### Out of Scope

- GitHub Actions automation — direct Claude Code usage is sufficient
- PR-based workflow — direct edits are fine for a personal site

## Context

- Static HTML/CSS site, no build step, no framework, no npm
- Hosted on GitHub Pages (`michael-early.github.io`)
- Site files: `index.html`, `projects/*/index.html`, inline CSS throughout
- The "agent" is Claude Code running locally in this repo

## Constraints

- **Scope**: Text/HTML/CSS edits only — no binary files, no config changes (CNAME, etc.)
- **Style**: All CSS is inlined per-file, no shared stylesheet
- **Deploy**: Push to main → GitHub Pages deploys automatically

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Claude Code as agent | Already in use, no extra infrastructure | ✓ Good |
| Direct edits, no PR workflow | Personal site, no review gate needed | — Pending |

---
*Last updated: 2026-03-14 after pivot — removed GitHub Actions approach*
