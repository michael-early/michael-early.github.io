# Technology Stack

**Project:** Portfolio Site Agent (GitHub Actions + Claude API)
**Researched:** 2026-03-11
**Note on sourcing:** WebSearch, WebFetch, and Bash tools were unavailable during this research session. All version numbers and recommendations are drawn from training data (cutoff August 2025). Confidence levels reflect this limitation — verify pinned versions against PyPI before implementation.

---

## Recommended Stack

### Runtime: GitHub Actions

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| GitHub Actions | N/A (hosted) | CI/CD runtime | Already where the repo lives; no external infra needed; issue event triggers are first-class |
| `ubuntu-latest` runner | ~24.04 | Execution environment | Standard for Python workloads; free for public repos; includes git, Python 3.12 |
| `actions/checkout@v4` | v4 | Clone the repo inside the runner | Current major version; v3 EOL'd; v4 uses Node 20 |
| `actions/setup-python@v5` | v5 | Install Python on the runner | v5 targets Node 20; correct for 2024-2025 |

**Confidence:** HIGH — GitHub Actions major versions and ubuntu runner behavior are stable and well-documented.

---

### AI Layer: Anthropic Python SDK

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `anthropic` (PyPI) | `>=0.25,<1` | Call the Claude API from the Python script | Official SDK; typed; handles retries and streaming; actively maintained |
| Model | `claude-3-5-sonnet-20241022` | Text understanding + HTML/CSS editing | Best reasoning-to-cost ratio for code editing; supports 200k context window for reading full HTML files |

**Why Python SDK over curl/raw HTTP:**
The SDK handles auth headers, retry logic on 529/529 rate limit responses, and typed response objects. For a GitHub Actions script that runs infrequently (one call per issue), the overhead is negligible and the ergonomics are significantly better.

**Why not the TypeScript/Node SDK:**
The repo is a static HTML site with no Node.js toolchain. Introducing Node just for the agent script adds dependencies and maintenance surface. Python is already on the ubuntu runner by default.

**Confidence:** MEDIUM — `anthropic` SDK 0.25+ is the stable series as of mid-2025. The model ID `claude-3-5-sonnet-20241022` was current at knowledge cutoff. Verify both against https://pypi.org/project/anthropic/ and https://docs.anthropic.com/en/docs/about-claude/models before pinning.

---

### GitHub API Layer: PyGithub

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `PyGithub` (PyPI) | `>=2.1,<3` | Read issue body, create branch, open PR | Pythonic wrapper around GitHub REST API v3; well-maintained; avoids raw REST calls |

**Why PyGithub over `gh` CLI:**
The `gh` CLI is available on ubuntu runners, but orchestrating branch creation, file commits, and PR creation through shell subprocesses is fragile and harder to test. PyGithub keeps all GitHub operations in Python with proper error handling.

**Why PyGithub over `httpx`/direct REST:**
Writing raw REST calls for the GitHub API (branch ref creation, blob creation, tree creation, commit creation, PR creation) requires implementing the git data API correctly — a non-trivial sequence. PyGithub abstracts this correctly.

**Why not GitHub's official `octokit` (JS):**
Same reason as avoiding the Node SDK — no Node toolchain in the repo.

**Confidence:** MEDIUM — PyGithub 2.x is the current major version. The `>=2.1` lower bound covers the rewrite to typed responses. Verify current version at https://pypi.org/project/PyGithub/.

---

### Agent Script: Plain Python

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12 | Script runtime | Default on ubuntu-latest as of 2024+; no setup needed |
| Standard library only (beyond SDK deps) | — | File I/O, string manipulation | No additional parsing library needed — files are HTML/CSS text; `pathlib` and `os` are sufficient |

**No LangChain, no agent frameworks:**
This is a single-turn, single-call agent: read issue, read files, call Claude once with a well-crafted prompt, write output files, open PR. LangChain/LlamaIndex add significant complexity and dependency footprint for what is effectively one `client.messages.create()` call. The "agentic" part is the GitHub Actions loop, not a framework.

**Confidence:** HIGH — single-turn Claude API call is the correct and simplest architecture for this use case.

---

### Auth and Secrets

| Secret | Storage | Access Pattern |
|--------|---------|---------------|
| `ANTHROPIC_API_KEY` | GitHub Actions Secret | Injected as env var: `env: ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}` |
| `GITHUB_TOKEN` | Automatic (built-in) | `${{ secrets.GITHUB_TOKEN }}` — no manual setup; scoped to the repo; can create PRs when `pull-requests: write` permission is set |

**Why use `GITHUB_TOKEN` over a PAT:**
`GITHUB_TOKEN` is automatically provisioned per-job, scoped to the repo, and rotates automatically. A personal access token (PAT) would require manual rotation and has broader scope. The only case where a PAT is required is cross-repo operations — this project operates on a single repo.

**Required permissions block in workflow YAML:**
```yaml
permissions:
  contents: write      # create branch, push commits
  pull-requests: write # open PR
  issues: read         # read issue body and metadata
```

**Confidence:** HIGH — `GITHUB_TOKEN` permissions model is stable and well-documented.

---

### Workflow Trigger

```yaml
on:
  issues:
    types: [opened]
```

**Why `opened` only (not `edited`, `reopened`):**
Simplest to reason about for v1. Re-opened or edited issues could re-trigger the agent on already-handled issues, creating duplicate PRs. Scope to `opened` and handle re-runs manually.

**Optional label filter (recommended for v1):**
```yaml
if: contains(github.event.issue.labels.*.name, 'agent')
```
Prevents every issue (bug reports, questions) from triggering the agent. User applies a label to issues they want the agent to act on.

**Confidence:** HIGH — GitHub Actions issue event triggers are stable and the `if` condition with label filtering is standard practice.

---

## Full Dependency File

```
# requirements.txt for the agent script
anthropic>=0.25,<1
PyGithub>=2.1,<3
```

Install in the workflow step:
```yaml
- name: Install dependencies
  run: pip install anthropic>=0.25,<1 PyGithub>=2.1,<3
```

No `requirements.txt` checked into the repo is needed — the workflow can install inline. If the project grows, add a `requirements.txt` at `.github/agent/requirements.txt` to keep the root clean.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| AI SDK | `anthropic` Python SDK | Raw HTTP (`httpx`) | SDK handles retries, auth, typed responses; no reason to reimplement |
| GitHub API | `PyGithub` | `gh` CLI via subprocess | Python-native error handling; no shell quoting issues; easier to unit test |
| GitHub API | `PyGithub` | Direct GitHub REST via `httpx` | Would need to implement the multi-step git data API manually (blob → tree → commit → ref) |
| Agent framework | None (plain SDK call) | LangChain, LlamaIndex | Single-turn task; frameworks add 20+ transitive dependencies with no benefit |
| Language | Python | Node.js / TypeScript | No Node toolchain in repo; Python is default on ubuntu runner |
| Model | claude-3-5-sonnet-20241022 | claude-3-haiku | Haiku may hallucinate HTML structure; Sonnet's reasoning handles "edit this section" instructions reliably |
| Model | claude-3-5-sonnet-20241022 | claude-3-opus | Opus is slower and more expensive; Sonnet is sufficient for HTML editing |
| PR creation | `PyGithub` | `git` CLI via subprocess | Git CLI approach works but requires managing branch state manually; PyGithub abstracts the ref/commit sequence |

---

## Sources

- Training data (cutoff August 2025) — all library selections and version ranges
- Confidence: MEDIUM for version numbers (verify before pinning)
- Anthropic SDK: https://docs.anthropic.com/en/docs/quickstart (verify current)
- Anthropic model list: https://docs.anthropic.com/en/docs/about-claude/models (verify current model IDs)
- PyGithub: https://pygithub.readthedocs.io/en/latest/ (verify current major version)
- GitHub Actions permissions: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token (HIGH confidence — stable)
- GitHub Actions issue events: https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#issues (HIGH confidence — stable)
