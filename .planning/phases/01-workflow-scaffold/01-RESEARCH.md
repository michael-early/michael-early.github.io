# Phase 1: Workflow Scaffold - Research

**Researched:** 2026-03-11
**Domain:** GitHub Actions workflow triggers, job conditions, secrets, branch protection
**Confidence:** HIGH

## Summary

Phase 1 wires the GitHub Actions plumbing that all future phases depend on. The work is entirely GitHub Actions YAML plus a minimal Python stub — no external libraries, no API calls. All key technical decisions were locked in CONTEXT.md, so research validates the exact syntax for those decisions rather than exploring alternatives.

The owner-only guard (`github.event.issue.user.login == github.repository_owner`) is a standard job-level `if:` condition supported directly in GitHub Actions expression syntax. The bot-loop guard using `github.actor == 'github-actions[bot]'` is the canonical pattern cited in GitHub community discussions. Secrets evaluate to empty string when not set, making an assertion step (`[ -z "$VAR" ] && exit 1`) the right tool. Branch protection is a UI-only manual step with no Actions equivalent for personal repos.

**Primary recommendation:** Write the workflow YAML first, then the Python stub, then the README documentation — in that order. The YAML drives everything; the script and docs follow from it.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Owner Guard**
- Workflow triggers on `issues.opened` only — not `issues.edited` or any other activity type
- Owner check lives at the **workflow job level** as an `if:` condition: `github.event.issue.user.login == github.repository_owner`
- Use `github.event.issue.user.login` (issue author), not `github.actor` (workflow trigger actor)
- Non-owner issues: **silent skip** — workflow simply does not run; no comment posted on the issue

**Bot Loop Guard**
- Bot check is a **separate step** inside the same job (not combined into the job-level `if:`)
- Exact match: `github.actor == 'github-actions[bot]'`
- When bot actor detected: exit 0 with log message `"Skipping: triggered by bot actor"`

**Secret Wiring**
- `ANTHROPIC_API_KEY` is asserted non-empty in Phase 1 even though it isn't called yet
- Confirms secrets are wired correctly before Phase 2 depends on them

**Branch Protection**
- Branch protection on `main` is a **manual setup step**, not automated
- Document in README with step-by-step GitHub UI instructions (Settings → Branches → Add rule: require PR before merge, no direct push)
- README also documents the `ANTHROPIC_API_KEY` secret setup

**Agent Script**
- Language and structure left to Claude — Python stub is preferred since Phase 2 will use Python for the Claude API
- Script should print issue env vars and exit 0 to verify end-to-end plumbing

### Claude's Discretion

- Agent script language and internal structure (Python stub preferred)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TRIG-01 | Agent only runs when the issue author is the repository owner | Job-level `if: github.event.issue.user.login == github.repository_owner` — verified against GitHub Actions expression docs |
| SAFE-01 | Workflow skips if triggered by the bot actor (prevents infinite loops) | Step-level bash check on `github.actor` passed via env var, exit 0 on match — canonical pattern confirmed in GitHub community discussions |
</phase_requirements>

## Standard Stack

### Core

| Component | Version/Source | Purpose | Why Standard |
|-----------|---------------|---------|--------------|
| GitHub Actions YAML | Current (2025) | Workflow definition, trigger, job conditions | Platform-native; no external CI needed |
| `ubuntu-latest` runner | GitHub-hosted | Execution environment | Free tier, Python pre-installed, `gh` CLI available |
| Python | 3.x (pre-installed on runner) | Agent stub script | No install step needed; consistent with Phase 2 Claude API work |
| `GITHUB_TOKEN` | Built-in secret | Authentication | Automatically injected; `issues: read` permission sufficient for Phase 1 |

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `gh` CLI | GitHub API calls (Phase 3+) | Pre-installed on runner; not needed in Phase 1 |
| `secrets.ANTHROPIC_API_KEY` | Anthropic API auth | Assert non-empty in Phase 1; first called in Phase 2 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Job-level `if:` for owner guard | Step-level `if:` | Job-level is cleaner: skipped job shows as "skipped" in UI, not "failed". Job-level is the locked decision. |
| Separate bot-guard step | Include in job-level `if:` | Separate step gives a log message; combined would silently skip with no distinction from owner check |

**Installation:** None. No npm, no pip installs required in Phase 1. Python is pre-installed on `ubuntu-latest`.

## Architecture Patterns

### Recommended File Structure

```
.github/
└── workflows/
    └── portfolio-agent.yml    # Main workflow file
agent/
└── run.py                     # Python stub (Phase 1: print vars, exit 0)
README.md                      # Branch protection + secret setup docs
```

### Pattern 1: Issues-Triggered Workflow with Job-Level Owner Guard

**What:** Workflow triggers on `issues: types: [opened]`. The single job has a job-level `if:` that compares the issue author to the repo owner. If false, the job is skipped silently.

**When to use:** Always — this is the locked architecture.

**Example:**
```yaml
# Source: https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
on:
  issues:
    types: [opened]

jobs:
  agent:
    runs-on: ubuntu-latest
    if: github.event.issue.user.login == github.repository_owner
    permissions:
      issues: read
    steps:
      - uses: actions/checkout@v4
```

Note: The `${{ }}` wrapper is optional in `if:` conditions — GitHub evaluates them as expressions automatically. Both `if: github.event.issue.user.login == github.repository_owner` and `if: ${{ github.event.issue.user.login == github.repository_owner }}` are valid.

### Pattern 2: Bot-Loop Guard as a Separate Step

**What:** Inside the job, the first step checks `github.actor` (passed in via env) and exits 0 with a log message when the actor is the bot.

**When to use:** Always — this is the locked architecture for SAFE-01.

**Example:**
```yaml
# Source: https://github.com/orgs/community/discussions/74772
steps:
  - name: Skip if bot actor
    env:
      ACTOR: ${{ github.actor }}
    run: |
      if [ "$ACTOR" = "github-actions[bot]" ]; then
        echo "Skipping: triggered by bot actor"
        exit 0
      fi
```

### Pattern 3: Secret Assertion Step

**What:** Check that `ANTHROPIC_API_KEY` is non-empty. When a secret is not set in the repo, GitHub Actions injects an empty string — so `[ -z "$VAR" ]` reliably detects it.

**When to use:** After the bot guard, before any real work.

**Example:**
```yaml
# Source: https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions
- name: Assert secrets wired
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    if [ -z "$ANTHROPIC_API_KEY" ]; then
      echo "ERROR: ANTHROPIC_API_KEY secret is not set"
      exit 1
    fi
    echo "Secrets check passed"
```

### Pattern 4: Passing Event Payload to Python Script via Env Vars

**What:** Issue data (number, title, body) is in `github.event.issue.*` context — NOT in default env vars. Must be explicitly mapped to env vars for the script to read.

**When to use:** Any step that invokes the agent script.

**Example:**
```yaml
# Source: https://docs.github.com/en/actions/reference/workflows-and-actions/variables
- name: Run agent
  env:
    ISSUE_NUMBER: ${{ github.event.issue.number }}
    ISSUE_TITLE: ${{ github.event.issue.title }}
    ISSUE_BODY: ${{ github.event.issue.body }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: python agent/run.py
```

### Pattern 5: Python Stub

**What:** `agent/run.py` reads env vars and prints them, then exits 0. No Claude API calls. Verifies end-to-end plumbing.

**Example:**
```python
import os
import sys

def main():
    issue_number = os.environ.get("ISSUE_NUMBER", "")
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_body = os.environ.get("ISSUE_BODY", "")

    print(f"Issue #{issue_number}: {issue_title}")
    print(f"Body:\n{issue_body}")
    print("Agent stub complete — no API calls in Phase 1")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Anti-Patterns to Avoid

- **Combining owner check and bot guard into one `if:`**: Loses the ability to distinguish "skipped because non-owner" from "skipped because bot". Locked decision requires them separate.
- **Using `github.actor` for the owner check**: `github.actor` is who triggered the workflow run, not necessarily who filed the issue. When GitHub Actions re-runs, `github.actor` changes. Use `github.event.issue.user.login`.
- **Hardcoding the owner username in the workflow**: `github.repository_owner` is dynamic; hardcoded strings break on repo transfers and are fragile.
- **Direct bash env var access for context values**: `$GITHUB_EVENT_ISSUE_NUMBER` does not exist as a default env var. Issue data must be explicitly mapped via `env:`.
- **Setting `contents: write` permissions in Phase 1**: Phase 1 only reads. Minimum permission is `issues: read`. Future phases add permissions incrementally.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Owner identity check | Custom API call to GitHub REST to get repo owner | `github.repository_owner` context property | Built-in, always accurate, zero API calls |
| Secret existence check | Try/catch around API call | `[ -z "$SECRET" ] && exit 1` bash one-liner | Secrets evaluate to empty string when unset — simple shell check is correct and reliable |
| Bot detection | Parse commit messages or user-agent strings | `github.actor == 'github-actions[bot]'` exact match | The canonical actor name is fixed and documented |

**Key insight:** GitHub Actions context properties (`github.*`) do the heavy lifting for identity and event data. Avoid REST API calls for information already in the workflow context.

## Common Pitfalls

### Pitfall 1: Wrong Field for Issue Author
**What goes wrong:** Using `github.actor` instead of `github.event.issue.user.login` for the owner check. The workflow appears to work but silently fails for edge cases (re-runs triggered by an admin, Actions UI re-run by a different user).
**Why it happens:** `github.actor` is the most visible "who ran this" field.
**How to avoid:** The locked decision is explicit: use `github.event.issue.user.login`.
**Warning signs:** Owner-created issues being skipped after a workflow re-run by another user.

### Pitfall 2: Secret Not Wired — Silent Failure
**What goes wrong:** `ANTHROPIC_API_KEY` is not added to repo secrets. The assertion step in Phase 1 passes because... wait, it should fail. But if the assertion is skipped (e.g., bot guard exits 0 first), downstream code gets an empty string.
**Why it happens:** Empty string is falsy in Python — API calls would fail with unhelpful auth errors in Phase 2.
**How to avoid:** Assert the secret is non-empty AFTER the bot guard, before the agent script runs. Both conditions need to be exercised in testing.
**Warning signs:** Phase 2 sees `401 Unauthorized` from Anthropic — likely empty key.

### Pitfall 3: Bot Guard Step Ordering
**What goes wrong:** Placing the secret assertion BEFORE the bot guard. If the bot triggers the workflow (which wouldn't happen in Phase 1 since there's no commit step, but will in Phase 3+), the assertion step would run and potentially emit error output before the bot guard kills the run.
**Why it happens:** Logical ordering feels like "check secrets first".
**How to avoid:** Bot guard step must be FIRST. Fail fast on bot actor before any other work.

### Pitfall 4: `if:` at Wrong Level
**What goes wrong:** Putting the owner check at step level instead of job level. The job still appears in GitHub UI as "ran" (not skipped), which creates noise and costs runner minutes.
**Why it happens:** Step-level `if:` is more common in tutorials.
**How to avoid:** Use `jobs.<job_id>.if:` — job-level `if:` causes the job to show as "skipped" in the UI. Locked decision specifies job level.

### Pitfall 5: Branch Protection Blocking the Workflow's Own Pushes (Phase 3 Preview)
**What goes wrong:** Branch protection on `main` blocks the workflow from pushing directly to `main`. This is intentional for Phase 1, but Phase 3 needs the agent to push to feature branches — not `main` — so it works fine.
**Why it happens:** Confusion about what branch protection protects.
**How to avoid:** The workflow will always push to `agent/issue-{N}` branches, never to `main`. Branch protection on `main` does not affect pushes to other branches.

## Code Examples

### Complete Phase 1 Workflow Skeleton

```yaml
# Source: GitHub Actions docs — https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
name: Portfolio Agent

on:
  issues:
    types: [opened]

jobs:
  agent:
    runs-on: ubuntu-latest
    if: github.event.issue.user.login == github.repository_owner
    permissions:
      issues: read
      contents: read

    steps:
      - name: Skip if bot actor
        env:
          ACTOR: ${{ github.actor }}
        run: |
          if [ "$ACTOR" = "github-actions[bot]" ]; then
            echo "Skipping: triggered by bot actor"
            exit 0
          fi

      - name: Assert secrets wired
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo "ERROR: ANTHROPIC_API_KEY secret is not set"
            exit 1
          fi
          echo "Secrets check passed"

      - uses: actions/checkout@v4

      - name: Run agent stub
        env:
          ISSUE_NUMBER: ${{ github.event.issue.number }}
          ISSUE_TITLE: ${{ github.event.issue.title }}
          ISSUE_BODY: ${{ github.event.issue.body }}
        run: python agent/run.py
```

### GitHub Context Variables Available in Phase 1

| Expression | Default Env Var | Notes |
|-----------|----------------|-------|
| `github.actor` | `GITHUB_ACTOR` | Who initiated the workflow run |
| `github.repository_owner` | `GITHUB_REPOSITORY_OWNER` | Repo owner login |
| `github.event.issue.user.login` | None — must map via `env:` | Issue author login |
| `github.event.issue.number` | None — must map via `env:` | Issue number |
| `github.event.issue.title` | None — must map via `env:` | Issue title |
| `github.event.issue.body` | None — must map via `env:` | Issue body text |
| `secrets.ANTHROPIC_API_KEY` | None — must map via `env:` | Undefined = empty string |

### Branch Protection UI Steps (README content)

```
To block direct pushes to main:
1. Go to repository Settings → Branches (under "Code and automation")
2. Click "Add rule"
3. Branch name pattern: main
4. Check "Require a pull request before merging"
5. Click "Create"

Note: Personal repositories cannot add bypass actors — the protection applies to all users including the owner.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `actions/checkout@v2` | `actions/checkout@v4` | 2023 | v4 uses Node 20; v2/v3 deprecated |
| Hardcoded `if: github.actor != 'github-actions[bot]'` at job level | Separate step with explicit log message | Ongoing best practice | Easier to debug which guard fired |
| `set-env` for passing values between steps | `env:` block per step or `$GITHUB_ENV` | 2020 (set-env deprecated) | Security: set-env was a shell injection vector |

**Deprecated/outdated:**
- `set-env` command: removed in 2020 after CVE; use `$GITHUB_ENV` file or step-level `env:` block
- `actions/checkout@v2`, `@v3`: deprecated, use `@v4`

## Open Questions

1. **Does the `issues` event trigger when the owner files from a mobile app or GitHub.com issue form?**
   - What we know: `github.event.issue.user.login` reflects the authenticated GitHub user who created the issue, regardless of client
   - What's unclear: No explicit verification needed — it's standard GitHub auth behavior
   - Recommendation: LOW risk, proceed as designed

2. **What happens if `github.repository_owner` differs from the authenticated user when repo is in an org?**
   - What we know: This is a personal portfolio repo (`michael-early.github.io`) — owner is always the individual
   - What's unclear: N/A for this project
   - Recommendation: Not applicable; ignore

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None installed — workflow testing is manual (GitHub Actions runs) |
| Config file | None — see Wave 0 |
| Quick run command | Manual: file a test issue as owner; observe Actions tab |
| Full suite command | Manual: run all 4 success criteria checks |

GitHub Actions workflows cannot be unit-tested locally without a tool like `act`. The success criteria for Phase 1 are all behavioral end-to-end checks that require a live GitHub repo.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRIG-01 | Owner-filed issue triggers workflow; non-owner does not | Manual smoke test | N/A — requires live GitHub repo | ❌ Wave 0 |
| SAFE-01 | Bot-triggered workflow exits cleanly with log message | Manual smoke test | N/A — requires live GitHub repo | ❌ Wave 0 |

All Phase 1 tests are manual-only. Rationale: GitHub Actions trigger behavior cannot be tested without an authenticated GitHub environment. The success criteria are observable in the GitHub Actions tab after deploying the workflow.

**Manual test checklist (run after deployment):**
1. File an issue as the repo owner — confirm workflow runs, agent stub prints vars, exits 0
2. Verify that a test issue filed from a second GitHub account does NOT trigger a workflow run
3. Inspect Actions log to confirm bot guard step logs the correct message when applicable
4. Attempt a direct push to `main` — confirm branch protection rejects it

### Sampling Rate

- Per task commit: Manual inspection of Actions run log
- Per wave merge: All 4 success criteria manually verified
- Phase gate: All 4 success criteria TRUE before proceeding to Phase 2

### Wave 0 Gaps

- [ ] No existing test infrastructure — Phase 1 testing is entirely manual via GitHub UI
- [ ] `act` (local GitHub Actions runner) is an option for local workflow linting but not behavioral testing

## Sources

### Primary (HIGH confidence)

- GitHub Actions docs — [Workflow syntax: `on` trigger](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions) — issues event types, `types: [opened]` syntax
- GitHub Actions docs — [Events that trigger workflows: issues](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#issues) — activity types confirmed
- GitHub Actions docs — [Using conditions to control job execution](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/using-conditions-to-control-job-execution) — job-level `if:` syntax, skipped status behavior
- GitHub Actions docs — [Using secrets in GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions) — secrets evaluate to empty string when not set, `env:` injection pattern
- GitHub Actions docs — [Variables reference](https://docs.github.com/en/actions/reference/workflows-and-actions/variables) — confirmed `GITHUB_ACTOR`, `GITHUB_REPOSITORY_OWNER` as default env vars; confirmed issue data requires explicit `env:` mapping
- GitHub Actions docs — [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule) — UI steps, personal vs org repo differences

### Secondary (MEDIUM confidence)

- [GitHub community discussion #74772](https://github.com/orgs/community/discussions/74772) — bot loop prevention patterns, `github.actor == 'github-actions[bot]'` confirmed as canonical check
- [GitHub community discussion #26970](https://github.com/orgs/community/discussions/26970) — workflow infinite loop patterns and prevention approaches

### Tertiary (LOW confidence)

None — all findings verified against official GitHub documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — GitHub Actions is the platform; all syntax verified against official docs
- Architecture: HIGH — patterns verified against official docs; locked decisions from CONTEXT.md are sound
- Pitfalls: HIGH — owner-guard field confusion and step ordering are verified patterns; secret empty-string behavior confirmed in docs

**Research date:** 2026-03-11
**Valid until:** 2026-09-11 (GitHub Actions syntax is stable; context variables and expression syntax change rarely)
