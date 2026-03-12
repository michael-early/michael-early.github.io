# Feature Landscape

**Domain:** GitHub Actions AI agent — issue-to-PR automation for a static HTML/CSS portfolio site
**Researched:** 2026-03-11
**Confidence:** MEDIUM (training data; web search unavailable in this session)

---

## Table Stakes

Features users expect. Missing = project feels incomplete or unsafe.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Issue trigger via `issues: [opened]` event | Foundational — nothing runs without it | Low | Workflow YAML event filter; add label filtering to avoid spurious triggers |
| Read issue title + body from event payload | Agent needs the instruction to act on | Low | `github.event.issue.title` + `.body` in Actions context |
| Read existing site files before editing | Without this, edits are blind and incoherent | Low-Med | Must pass current file content to the LLM as context |
| Make targeted file edits (index.html, project pages) | Core deliverable | Med | Requires LLM to produce a diff or full replacement; file write step in workflow |
| Open a Pull Request with the changes | Core deliverable; user must review before merge | Med | `gh pr create` or `peter-evans/create-pull-request` Action |
| PR title and description summarizing what changed | Required for review workflow to work | Low | Populated from LLM output or structured prompt |
| Never push directly to main | Safety guarantee stated in PROJECT.md | Low | Branch strategy: agent commits to a feature branch, never main |
| Anthropic API key stored as GitHub secret | Security baseline | Low | `${{ secrets.ANTHROPIC_API_KEY }}` — never hardcoded |
| Workflow permissions scoped to minimum required | Prevent over-privileged token abuse | Low | `permissions: contents: write, pull-requests: write` — nothing broader |
| Graceful failure when issue is malformed | Agent must not silently produce garbage or error-crash | Med | Catch empty body, nonsensical instructions; post comment explaining failure |

---

## Differentiators

Features that distinguish a polished agent from a bare-bones one. Not universally expected, but high value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Label-based routing (e.g., `agent` label required to trigger) | Prevents accidental triggers from unrelated issues | Low | `if: contains(github.event.issue.labels.*.name, 'agent')` |
| Agent posts a comment on the issue linking to the opened PR | Closes the feedback loop — user knows the agent ran | Low | `gh issue comment` after PR is created |
| Structured prompt with site context baked in | Makes edits coherent with existing style/tone | Med | Preload CSS design system, project page template, tone guidance into system prompt |
| Dry-run mode (comment with proposed diff, no PR) | Lets agent preview changes before committing | Med | Useful for ambiguous instructions; controlled by label or issue keyword |
| Inline validation: check HTML is well-formed before opening PR | Catches broken edits before they reach review | Med | Simple parse with Python's `html.parser`; no full lint required |
| Idempotency guard: skip if open PR already exists for this issue | Prevents duplicate PRs on retry or re-trigger | Low-Med | Query open PRs before creating; match by branch name or issue number |
| Cost logging: log token usage to Actions summary | Makes API spend visible; useful for a portfolio project showcasing awareness | Low | Log `usage.input_tokens` + `usage.output_tokens` from API response |
| Issue template with structured fields (instruction, target file) | Guides users to write cleaner instructions | Low | `.github/ISSUE_TEMPLATE/agent-request.md` with `Instruction:` and `Files affected:` sections |

---

## Anti-Features

Features to deliberately NOT build in this project.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Auto-merge after agent creates PR | Removes human review; a bad edit ships to production automatically | Always require manual merge; this is stated in PROJECT.md |
| Multi-turn issue conversation (agent replies, user clarifies, agent iterates) | Massively increases complexity; GitHub Issues is not a chat interface | Single-instruction-per-issue model; user files a new issue to iterate |
| Binary file / image editing | Out of scope for v1; requires different tooling and risk model | Scope to text/HTML/CSS only as stated in PROJECT.md |
| CNAME or config file editing | Could break GitHub Pages hosting entirely | Exclude these file paths explicitly in the agent's system prompt and file-write step |
| Workflow that runs on every issue regardless of label or keyword | Triggers on support questions, bug reports, etc. | Gate on label (`agent`) or keyword in title (`[agent]`) |
| LLM with unconstrained file discovery (recursive glob, reading secrets) | Security surface; agent could be prompted to read `.env` or GitHub token | Whitelist specific file paths; never pass directory listings of hidden files |
| Autonomous deployment pipeline (agent merges + deploys) | Far beyond this project's scope; introduces serious risk | PR-only output; GitHub Pages auto-deploy handles deployment after human merge |
| Overengineered retry logic / state machine | Complexity debt; not justified for a personal portfolio site | Fail fast with a clear error comment; user re-files if needed |

---

## Feature Dependencies

```
Issue trigger (opened event)
  → Read issue body
      → Read relevant site files (must precede LLM call)
          → LLM call with context + instruction
              → Parse LLM output (diff or full file)
                  → Write file(s) to working branch
                      → Open PR
                          → Post comment on issue linking PR

Label routing (optional gate)
  → Must resolve before workflow proceeds

Idempotency guard
  → Depends on: PR query before creation step

HTML validation
  → Depends on: file write step; runs before PR creation

Dry-run mode
  → Replaces: file write + PR creation
  → Produces: comment with proposed changes instead
```

---

## MVP Recommendation

Prioritize for v1:

1. Issue trigger with label gate (`agent` label)
2. Read issue body + read relevant site files
3. LLM call with structured system prompt including site context
4. Write edited file(s) to a feature branch
5. Open PR with descriptive title and body
6. Post comment on issue linking to the PR

Defer to later iterations:

- **Dry-run mode** — high complexity, lower urgency for a personal project with low issue volume
- **HTML validation** — useful but adds Python dependency; can add in phase 2
- **Issue templates** — polish item; doesn't affect agent behavior
- **Cost logging** — add once the agent is working end-to-end

---

## Confidence Notes

- Table stakes features are well-established patterns from GitHub Actions + LLM agent projects (Devin, PR agents, Claude Code Actions integrations) — HIGH confidence on the feature list itself
- Complexity ratings are estimates for a single-developer implementation in Python on GitHub Actions — MEDIUM confidence
- Web search was unavailable for this session; recommendations are based on training data through August 2025 and direct analysis of the PROJECT.md constraints

---

## Sources

- Project context: `/Users/mearly/michael-early.github.io/.planning/PROJECT.md`
- Training knowledge: GitHub Actions LLM agent patterns (Anthropic Claude API, `peter-evans/create-pull-request`, GitHub Actions event model)
- Confidence: MEDIUM — verified against project constraints, not against live documentation
