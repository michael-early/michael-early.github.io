# michael-early.github.io

Personal portfolio site for Michael Early — MA Economics student and aspiring data/research/sports analytics professional. Hosted at [michael-early.github.io](https://michael-early.github.io).

---

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

---

## How It Works

- Filing an issue as the repo owner triggers the agent workflow
- Non-owner issues are silently skipped — no workflow run appears
- The agent reads the issue body, processes the request, and will open a Pull Request for review (Phase 2+)
- No change is ever pushed directly to `main`
