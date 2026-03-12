# Requirements: Portfolio Site Agent

**Defined:** 2026-03-11
**Core Value:** File an issue from anywhere, get a PR back — update the portfolio without needing a local development environment.

## v1 Requirements

### Triggering

- [x] **TRIG-01**: Agent only runs when the issue author is the repository owner

### File Editing

- [ ] **EDIT-01**: Agent reads all HTML/CSS site files before making any edits

### Pull Requests

- [ ] **PR-01**: Agent creates a branch, commits changes, and opens a Pull Request automatically
- [ ] **PR-02**: PR description summarizes what changed and why, referencing the original issue

### Safety

- [x] **SAFE-01**: Workflow skips if triggered by the bot actor (prevents infinite loops)
- [ ] **SAFE-02**: Agent never reads or writes binary files (PDFs, images)
- ~~**SAFE-03**: Edited HTML is validated before committing; malformed output is rejected~~ *(dropped — owner reviews PR diff before merging)*

## v2 Requirements

### Triggering

- **TRIG-02**: Label gate — agent only fires when issue has an `agent` label (secondary filter on top of owner guard)

### File Editing

- **EDIT-02**: File allowlist — agent restricted to editing only `index.html` and `projects/*/index.html`
- **EDIT-03**: Dry-run mode — agent logs what it would change without committing

### Pull Requests

- **PR-03**: Agent comments on the original issue with a link to the opened PR

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-merge | All changes go through PR review — human always approves |
| Multi-turn conversations in issues | Single instruction per issue for v1 simplicity |
| Video/image asset management | Binary files only; scope is HTML/CSS text edits |
| Public issue handling | Owner-only guard means public contributors cannot trigger the agent |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRIG-01 | Phase 1 | Complete |
| SAFE-01 | Phase 1 | Complete |
| EDIT-01 | Phase 2 | Pending |
| SAFE-02 | Phase 2 | Pending |
| PR-01 | Phase 2 | Pending |
| PR-02 | Phase 2 | Pending |
| SAFE-03 | — | dropped |

**Coverage:**
- v1 requirements: 7 total
- Mapped to phases: 6 (SAFE-03 dropped)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-11*
*Last updated: 2026-03-12 — phase assignments updated after claude-code-action redesign (phases 3+4 collapsed into phase 2, SAFE-03 dropped)*
