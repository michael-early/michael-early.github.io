# Phase 1: Workflow Scaffold - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the GitHub Actions workflow trigger, implement the owner-only actor check, add the bot-loop guard, assert secrets are present, and document branch protection setup. No Claude API calls in this phase — plumbing and security gates only.

</domain>

<decisions>
## Implementation Decisions

### Owner Guard
- Workflow triggers on `issues.opened` only — not `issues.edited` or any other activity type
- Owner check lives at the **workflow job level** as an `if:` condition: `github.event.issue.user.login == github.repository_owner`
- Use `github.event.issue.user.login` (issue author), not `github.actor` (workflow trigger actor)
- Non-owner issues: **silent skip** — workflow simply does not run; no comment posted on the issue

### Bot Loop Guard
- Bot check is a **separate step** inside the same job (not combined into the job-level `if:`)
- Exact match: `github.actor == 'github-actions[bot]'`
- When bot actor detected: exit 0 with log message `"Skipping: triggered by bot actor"`

### Secret Wiring
- `ANTHROPIC_API_KEY` is asserted non-empty in Phase 1 even though it isn't called yet
- Confirms secrets are wired correctly before Phase 2 depends on them

### Branch Protection
- Branch protection on `main` is a **manual setup step**, not automated
- Document in README with step-by-step GitHub UI instructions (Settings → Branches → Add rule: require PR before merge, no direct push)
- README also documents the `ANTHROPIC_API_KEY` secret setup

### Agent Script (Claude's Discretion)
- Language and structure left to Claude — Python stub is preferred since Phase 2 will use Python for the Claude API
- Script should print issue env vars and exit 0 to verify end-to-end plumbing

</decisions>

<specifics>
## Specific Ideas

- Phase 1 success is verified by the three end-to-end checks in the roadmap success criteria: owner-triggered run fires, bot-triggered run skips cleanly, and agent script prints env vars and exits 0
- README is part of Phase 1 deliverables (not deferred) because all setup instructions are for infra that must exist before Phase 2

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield. No existing workflow files, scripts, or GitHub Actions configuration.

### Established Patterns
- Static HTML/CSS site: no build step, no npm, no framework dependencies to install in the runner
- Site files are all in repo root and `projects/*/index.html` — future phases will read these paths

### Integration Points
- `.github/workflows/` directory (to be created in Phase 1)
- GitHub Actions secrets store: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN` (built-in)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-workflow-scaffold*
*Context gathered: 2026-03-11*
