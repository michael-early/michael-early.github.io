# Project Research Summary

**Project:** Portfolio Site Agent (GitHub Actions + Claude API)
**Domain:** GitHub Actions AI agent — issue-triggered portfolio editing for a static HTML/CSS site
**Researched:** 2026-03-11
**Confidence:** MEDIUM

## Executive Summary

This project is a single-turn AI agent that watches GitHub Issues and automatically opens pull requests with site edits. The canonical pattern for this class of problem is: trigger on the `issues: [opened]` event, read relevant site files, make one Claude API call with a structured output format, write the edits to a feature branch, open a PR for human review, and post a comment on the issue. The architecture is intentionally minimal — no agent frameworks, no multi-step reasoning loops, no autonomous deployment. A single Python script with the `anthropic` SDK and `PyGithub` (or the `gh` CLI) handles the core logic; GitHub Actions handles orchestration and scheduling.

The recommended stack is Python 3.12 on `ubuntu-latest`, calling `claude-3-5-sonnet` (verify current model ID at build time) with structured JSON output. The key architecture decision is to always pass complete file contents to the model and ask for complete file contents back — diffs are fragile to parse and this site's HTML files are small enough that full-file round-trips are acceptable. Relevance filtering (reading only files implicated by the issue text) keeps token costs manageable and should be implemented from the start.

The primary risks are security and cost: prompt injection via the issue body can cause arbitrary file edits or secret exfiltration if the path allow-list is not enforced in code (not just in the prompt); a trigger loop caused by the bot reacting to its own events can compound API costs with no hard stop. Both risks must be mitigated in Phase 1 (workflow scaffold) before any API calls are wired in. The human review gate — agent only opens PRs, never merges — is the single most important safety property of the entire system and must be preserved unconditionally.

## Key Findings

### Recommended Stack

The simplest viable stack is GitHub Actions (free, already co-located with the repo), Python 3.12 (pre-installed on `ubuntu-latest`), the `anthropic` Python SDK for Claude API calls, and either `PyGithub` or the pre-installed `gh` CLI for GitHub operations. No build toolchain, no agent framework, no external infra. Two PyPI dependencies cover the full implementation: `anthropic>=0.25,<1` and `PyGithub>=2.1,<3` (or drop `PyGithub` entirely and use `gh` CLI shell calls — both approaches are viable).

The choice of Claude model matters: `claude-3-5-sonnet` provides sufficient reasoning for HTML editing tasks with a 200k context window; `claude-haiku` is cheaper but risks hallucinating HTML structure. The default model should be Sonnet unless cost analysis during implementation suggests otherwise.

**Core technologies:**
- GitHub Actions (`ubuntu-latest`, `actions/checkout@v4`, `actions/setup-python@v5`): CI/CD runtime — already where the repo lives, issue event triggers are first-class
- `anthropic` Python SDK (`>=0.25,<1`): Claude API calls — handles auth, retries, typed responses
- `PyGithub` (`>=2.1,<3`) or `gh` CLI: GitHub operations — branch creation, PR creation; `gh` CLI avoids an extra dependency
- `GITHUB_TOKEN` (built-in): PR creation auth — auto-provisioned, scoped, no manual rotation required
- `ANTHROPIC_API_KEY` (repo secret): Claude auth — stored in GitHub Secrets, injected as env var

### Expected Features

The MVP needs six things: a label-gated issue trigger, file reading, a structured Claude call, a feature branch commit, a PR open, and an issue comment with the PR link. Everything else is hardening or polish.

**Must have (table stakes):**
- Issue trigger on `issues: [opened]` with `agent` label gate — nothing runs without it
- Read issue title + body from event payload — agent needs the instruction
- Read relevant site files before the LLM call — blind edits produce incoherent output
- Targeted file edits to `index.html` and `projects/*/index.html` — core deliverable
- PR opened against `main` with descriptive title and body — core deliverable; human reviews before merge
- Never push directly to `main` — stated safety requirement; enforce with branch protection
- `ANTHROPIC_API_KEY` stored as GitHub Secret — security baseline

**Should have (competitive):**
- Agent posts comment on issue linking to the opened PR — closes the feedback loop
- Structured system prompt with site context (CSS design system, tone, target files) — makes edits coherent
- Idempotency guard: skip if a PR already exists for this issue number — prevents duplicate PRs on retry
- Owner-only guard: only trigger if issue author is `github.repository_owner` — prevents public abuse on this single-owner repo
- HTML validation before PR creation — catches broken model output before human review

**Defer (v2+):**
- Dry-run mode (comment with proposed diff, no PR) — high complexity, low urgency for personal site
- Issue templates with structured fields — polish item, does not affect agent behavior
- Cost logging to Actions summary — useful visibility, add once agent is end-to-end working
- Two-stage relevance filtering (preliminary Claude call to identify target files) — add if simple heuristic produces bad edits

### Architecture Approach

The agent is a linear four-step pipeline: checkout → agent script (read issue, read files, call Claude, write edits) → branch+commit → open PR. All business logic lives in `scripts/agent.py`; the workflow YAML contains no logic beyond environment wiring. This keeps the script testable locally by setting env vars manually. Structured JSON output from Claude (`[{"file": "...", "content": "..."}]`) eliminates fragile regex parsing. The `gh` CLI (pre-installed on ubuntu runners) handles PR creation without adding a Python dependency.

**Major components:**
1. Workflow YAML (`.github/workflows/portfolio-agent.yml`) — trigger, permissions, env wiring, step orchestration; no business logic
2. Agent script (`scripts/agent.py`) — reads issue env vars, loads site files (HTML/CSS allowlist), calls Claude API, parses JSON response, writes edited files to disk
3. Claude API (Anthropic Messages endpoint) — generates file edits given full file contents + instruction; returns structured JSON
4. Branch manager (git shell steps in YAML) — creates `agent/issue-{N}` branch, commits changed files, pushes
5. PR creator (`gh pr create`) — opens PR against `main` with "Closes #N" in body; handles issue auto-close on merge

### Critical Pitfalls

1. **Infinite trigger loop** — bot reacting to its own PRs/events causes runaway API costs and duplicate branches. Prevent by triggering only on `issues: [opened]`, adding `if: github.event.issue.user.type != 'Bot'`, and adding the `agent` label gate. Address in Phase 1 before any API calls exist.

2. **Prompt injection via issue body** — malicious issue content can instruct the model to edit workflow files, CNAME, or exfiltrate secrets. Prevent with a code-enforced file path allowlist (not just prompt instructions) and the `github.repository_owner` guard. Address in Phase 2 when the prompt is first constructed.

3. **Stale file state** — agent edits files it has not read, hallucinating the current HTML and overwriting real content. Prevent by always reading every file before constructing the prompt and validating that key landmarks (hero section, project names) still exist in the model's output. Address in Phase 2 during prompt design.

4. **Unbounded API costs** — reading all HTML files on every run compounds with retries or a trigger loop. Prevent by implementing relevance filtering from day one, logging token counts, and setting a monthly spend cap in the Anthropic console. Address in Phase 2.

5. **Agent pushes to `main` directly** — a misconfigured `git push` or missing branch protection sends unreviewed edits live to GitHub Pages. Prevent by enabling branch protection on `main` before writing any agent code and naming branches deterministically as `agent/issue-{N}`. Address in Phase 1.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Workflow Scaffold and Security Baseline
**Rationale:** Pitfalls 1, 4, 5, and 7 (trigger loop, token over-permission, direct-to-main push, secret exposure) all manifest at the workflow layer and must be eliminated before API calls are introduced. Building the skeleton first also lets you verify the plumbing without any external API dependency.
**Delivers:** Working workflow that triggers on `issues: [opened]` with label gate, owner guard, correct permissions block, branch protection on `main`, and secret masking — but no API calls yet. Agent script exits 0 after printing issue env vars.
**Addresses:** Table stakes trigger, never-push-to-main, minimum permissions, secret storage
**Avoids:** Pitfalls 1 (loop), 4 (permissions), 5 (direct push), 7 (secret exposure), 10 (public abuse)

### Phase 2: Claude API Integration and Prompt Design
**Rationale:** The API integration depends on a working workflow scaffold (Phase 1). Prompt injection (Pitfall 2) and stale file state (Pitfall 6) both originate in prompt design and must be addressed here, not deferred.
**Delivers:** Agent reads issue body, loads relevant HTML/CSS files from an explicit allowlist, constructs a structured system prompt, calls Claude, parses the JSON response, writes updated files to disk, and validates that no disallowed paths were modified.
**Uses:** `anthropic` Python SDK, structured JSON output pattern, file path allowlist, token count check
**Implements:** Agent script core logic, relevance filtering heuristic, output validation (key landmark check)
**Avoids:** Pitfalls 2 (injection), 3 (unbounded costs), 6 (stale state), 12 (ambiguous instructions)

### Phase 3: PR Creation and Issue Close
**Rationale:** PR creation depends on the agent script writing valid edited files (Phase 2). This phase completes the end-to-end loop.
**Delivers:** Agent creates `agent/issue-{N}` branch, commits changed files, opens PR with "Closes #N" in body, posts comment on issue linking to the PR.
**Uses:** `gh` CLI (pre-installed), `GITHUB_TOKEN` with `pull-requests: write`
**Implements:** Branch manager, PR creator, issue commenter
**Avoids:** Pitfalls 8 (branch collision), 11 (stale issues)

### Phase 4: Output Hardening
**Rationale:** HTML validation and idempotency guards are correctness improvements that depend on the end-to-end loop existing (Phase 3). Separating them keeps Phase 3 focused on the happy path.
**Delivers:** HTML parse validation before commit (fail run with issue comment if broken), idempotency guard (check for open PR on same branch before creating), cost logging to Actions summary.
**Avoids:** Pitfalls 9 (invalid HTML), 3 (ongoing cost visibility)

### Phase Ordering Rationale

- Security and trigger-loop prevention come first because a bad workflow can cause runaway costs before a single line of agent logic is written. Phase 1 is a gate.
- The API integration (Phase 2) is isolated until the workflow plumbing is verified — this avoids debugging two layers simultaneously.
- PR creation (Phase 3) is separated from API integration (Phase 2) so each phase produces a testable, self-contained deliverable.
- Output hardening (Phase 4) adds correctness guarantees after the happy path is proven end-to-end, following the established pattern of "make it work, then make it safe."

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Prompt engineering specifics — the exact system prompt wording for structured output, the right relevance filtering heuristic, and the landmark validation approach all benefit from a dedicated prompt-design spike before implementation.
- **Phase 2:** Model name verification — `claude-3-5-sonnet-20241022` was current at knowledge cutoff; verify the current model ID against Anthropic docs before coding.

Phases with standard patterns (skip research-phase):
- **Phase 1:** GitHub Actions workflow structure is extremely well-documented; the exact YAML is provided in ARCHITECTURE.md with high confidence.
- **Phase 3:** `gh pr create` usage is standard and pre-installed on ubuntu runners; no research needed.
- **Phase 4:** Python's `html.parser` for validation is stdlib; no research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | GitHub Actions patterns are HIGH confidence; SDK/model version numbers need verification against live PyPI and Anthropic docs before pinning |
| Features | MEDIUM | Feature list is HIGH confidence from established GHA+LLM agent patterns; complexity estimates are MEDIUM — verify against actual implementation time |
| Architecture | HIGH | Workflow structure, permissions model, `gh` CLI usage, and structured output pattern are all well-documented stable behaviors |
| Pitfalls | MEDIUM-HIGH | All pitfalls are grounded in well-established GHA security behavior and LLM agent patterns; cost estimates for Pitfall 3 need validation against current Anthropic pricing |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **SDK and model versions:** `anthropic>=0.25,<1` and `claude-3-5-sonnet-20241022` were accurate at research time (August 2025 training cutoff). Verify both against https://pypi.org/project/anthropic/ and https://docs.anthropic.com/en/docs/about-claude/models before writing requirements and the agent script.
- **Token cost baseline:** Pitfall 3 recommends a token cap, but the right threshold depends on current Anthropic pricing. Calculate cost-per-run against current Sonnet input/output pricing before setting the abort threshold.
- **`PyGithub` vs `gh` CLI decision:** Both are viable; the ARCHITECTURE.md leans toward `gh` CLI to avoid an extra dependency. Confirm this decision in Phase 3 planning based on what's actually easier to test locally.
- **Relevance filtering heuristic:** The simple keyword-match approach (Phase 2) needs testing against real issue texts from this site. Define the heuristic precisely before implementation rather than discovering its failure modes in production.

## Sources

### Primary (HIGH confidence)
- GitHub Actions `issues` event and permissions model (training data, stable since 2020)
- Anthropic Python SDK `messages.create` API (training data through August 2025)
- `gh pr create` CLI (training data — pre-installed on ubuntu runners, stable)
- Structured JSON output pattern for LLM agents (widely documented, HIGH confidence)

### Secondary (MEDIUM confidence)
- `anthropic>=0.25,<1` version range (training data — verify before pinning)
- `PyGithub>=2.1,<3` version range (training data — verify before pinning)
- `claude-3-5-sonnet-20241022` model ID (training data — verify current model ID before pinning)
- Token cost estimates for Pitfall 3 (training data — verify against current Anthropic pricing)

### Tertiary (needs live validation)
- Specific prompt wording for structured output and landmark validation — inferred from patterns; needs empirical testing
- Relevance filtering heuristic effectiveness — inferred from first principles; needs testing against real issue inputs

---
*Research completed: 2026-03-11*
*Ready for roadmap: yes*
