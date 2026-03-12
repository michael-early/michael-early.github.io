# Portfolio Site Agent

## What This Is

A GitHub Actions-powered AI agent that watches for GitHub Issues on the portfolio repository. When an issue is filed with a natural-language instruction (e.g., "add my housing-ml project" or "update my bio"), the agent reads the issue, edits the relevant HTML/CSS files, and opens a Pull Request for review and merge.

## Core Value

File an issue from anywhere, get a PR back — update the portfolio without needing a local development environment or Claude Code open.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] GitHub Actions workflow triggers on new issue creation
- [ ] Agent reads the issue body and understands what change to make
- [ ] Agent can edit any file in the repo (index.html, project pages, CSS)
- [ ] Agent opens a Pull Request with the changes made
- [ ] PR description summarizes what was changed and why
- [ ] User reviews the PR and merges manually

### Out of Scope

- Auto-merge — changes always go through PR review first
- Multi-turn conversations within an issue — single instruction per issue
- Image uploads or binary file changes — text/HTML/CSS only for v1

## Context

- Static HTML/CSS site, no build step, no framework, no npm
- Hosted on GitHub Pages (`michael-early.github.io`)
- Site files: `index.html`, `projects/*/index.html`, inline CSS throughout
- Agent will need to read existing site files to make coherent edits
- Anthropic API (Claude) will power the agent via GitHub Actions

## Constraints

- **Platform**: GitHub Actions only — no external servers or hosting required
- **Auth**: Anthropic API key stored as GitHub Actions secret
- **Scope**: Text/HTML/CSS edits only — no binary files, no config changes (CNAME, etc.)
- **Review**: All changes go through PR — agent never pushes directly to main

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GitHub Issues as input | Accessible from anywhere, no local setup needed | — Pending |
| PR-based output | User maintains control, can reject bad changes | — Pending |
| Claude via Anthropic API | Already using Claude Code, consistent tooling | — Pending |

---
*Last updated: 2026-03-11 after initialization*
