---
phase: 1
slug: workflow-scaffold
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — GitHub Actions behavioral testing is manual |
| **Config file** | none — Wave 0 has no automated test files |
| **Quick run command** | Manual: file a test issue as owner; observe Actions tab |
| **Full suite command** | Manual: verify all 4 success criteria in GitHub UI |
| **Estimated runtime** | ~5 minutes per full manual check |

---

## Sampling Rate

- **After every task commit:** Manual inspection of workflow YAML lint / file structure
- **After every plan wave:** Verify all success criteria manually in GitHub UI
- **Before `/gsd:verify-work`:** All 4 success criteria must be TRUE
- **Max feedback latency:** ~5 minutes (time to file test issue and observe Actions tab)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | TRIG-01 | Manual smoke | N/A — live GitHub | ❌ Wave 0 | ⬜ pending |
| 1-01-02 | 01 | 1 | SAFE-01 | Manual smoke | N/A — live GitHub | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] No automated test framework needed — all Phase 1 verification is manual via GitHub UI
- [ ] `act` (local GitHub Actions runner) can be used for YAML linting but not behavioral testing

*Note: GitHub Actions trigger behavior (owner guard, bot guard) cannot be unit-tested without an authenticated live GitHub environment. All success criteria are observable in the Actions tab after deploying the workflow.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Owner-filed issue triggers workflow | TRIG-01 | Requires authenticated GitHub repo and live Actions runner | File issue as repo owner → confirm workflow runs, agent stub prints vars, exits 0 |
| Non-owner issue does NOT trigger workflow | TRIG-01 | Requires second GitHub account | File issue from second account → confirm no workflow run appears in Actions tab |
| Bot-triggered run exits cleanly | SAFE-01 | Requires live bot actor trigger | Inspect Actions log → confirm bot guard step logs "Skipping: triggered by bot actor" |
| Direct push to main is blocked | Success Criteria 4 | GitHub branch protection is a UI setting | Attempt `git push origin main` directly → confirm GitHub rejects with protection error |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5 minutes
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
