---
phase: 01-workflow-scaffold
plan: "01"
subsystem: infra
tags: [github-actions, python, workflow, security, owner-guard, bot-guard]

requires: []
provides:
  - GitHub Actions workflow triggered on issues.opened with job-level owner guard
  - Bot actor guard as first step (exit 0 on github-actions[bot])
  - ANTHROPIC_API_KEY secret assertion step
  - Python agent stub reading ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY env vars
affects:
  - 02-claude-integration
  - 03-pr-automation

tech-stack:
  added: []
  patterns:
    - "Step-level env: blocks for context mapping (not set-env, not hardcoded)"
    - "Job-level if: for owner filtering using github.event.issue.user.login"
    - "Bot guard as first step with exit 0 (fail-fast, non-error)"
    - "Python agent entrypoint via main() + if __name__ == '__main__' guard"

key-files:
  created:
    - .github/workflows/portfolio-agent.yml
    - agent/run.py
  modified: []

key-decisions:
  - "Owner guard uses github.event.issue.user.login (issue author) not github.actor (PR merger) — prevents false skips on cross-actor flows"
  - "Bot guard uses exit 0 not exit 1 — skipping is intentional, not a failure"
  - "Secret assertion placed before checkout — fails fast before cloning repo on missing key"
  - "Agent script uses os.environ.get() not os.environ[] — avoids KeyError when env vars absent"

patterns-established:
  - "Step order: bot-guard → secret-assert → checkout → agent — locked for all future workflow modifications"
  - "Minimum permissions: issues: read, contents: read — expand only when Phase 3 requires write"

requirements-completed: [TRIG-01, SAFE-01]

duration: 1min
completed: "2026-03-12"
---

# Phase 1 Plan 01: Workflow Scaffold Summary

**GitHub Actions workflow with job-level owner guard, bot-loop protection, and secret assertion wired to a Python agent stub that logs ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY and exits 0**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-12T04:16:04Z
- **Completed:** 2026-03-12T04:24:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `.github/workflows/portfolio-agent.yml` with all required steps in the locked order
- Job-level `if:` condition uses `github.event.issue.user.login == github.repository_owner` (not `github.actor`)
- Bot guard (`Skip if bot actor`) is the first step, exits 0 on match to prevent error noise
- ANTHROPIC_API_KEY assertion exits 1 with clear error when secret is unset
- Python agent stub prints all three issue env vars and exits 0 cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Create GitHub Actions workflow** - `a298509` (feat)
2. **Task 2: Create Python agent stub** - `d22301f` (feat)

**Plan metadata:** (to be recorded in final commit)

## Files Created/Modified

- `.github/workflows/portfolio-agent.yml` - Workflow definition: issues.opened trigger, owner guard, bot guard, secret assertion, checkout, agent invocation
- `agent/run.py` - Python stub: reads ISSUE_NUMBER/ISSUE_TITLE/ISSUE_BODY, prints them, exits 0

## Decisions Made

- Owner guard uses `github.event.issue.user.login` not `github.actor` — the plan specified this and RESEARCH.md confirmed it prevents false skips when a different actor (e.g., bot) handles subsequent workflow events
- Bot guard exits 0 not 1 — skipping a bot-triggered run is intentional, treating it as failure would create alert noise
- Secret assertion placed as step 2 (before checkout step 3) — fails fast without cloning the repository
- Agent uses `os.environ.get()` not `os.environ[]` — prevents KeyError when running script outside Actions context

## Deviations from Plan

None - plan executed exactly as written. All step order decisions were pre-locked in the plan and followed precisely.

## Issues Encountered

- `pyyaml` not available in system Python (externally managed environment on macOS). Created a temporary venv (`/tmp/yaml-check-venv`) for YAML structure verification. No impact on deliverables — file contents are correct regardless of verification tooling.

## User Setup Required

**One external action required:** Add `ANTHROPIC_API_KEY` as a repository secret in GitHub.

Path: Repository Settings → Secrets and variables → Actions → New repository secret
- Name: `ANTHROPIC_API_KEY`
- Value: Your Anthropic API key

Without this secret, the `Assert secrets wired` step will fail with `ERROR: ANTHROPIC_API_KEY secret is not set`.

## Next Phase Readiness

- Workflow scaffold is complete and will activate on the next `issues.opened` event filed by the repo owner
- Phase 2 (Claude integration) can wire the real API call by replacing `agent/run.py` logic — the env vars (ISSUE_NUMBER, ISSUE_TITLE, ISSUE_BODY, ANTHROPIC_API_KEY) are already mapped
- Permissions will need to expand to `contents: write` and `pull-requests: write` when Phase 3 adds PR creation

## Self-Check: PASSED

- FOUND: `.github/workflows/portfolio-agent.yml`
- FOUND: `agent/run.py`
- FOUND: `01-01-SUMMARY.md`
- FOUND: commit `a298509`
- FOUND: commit `d22301f`

---
*Phase: 01-workflow-scaffold*
*Completed: 2026-03-12*
