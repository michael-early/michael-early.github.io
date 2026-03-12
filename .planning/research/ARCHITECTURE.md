# Architecture Patterns

**Domain:** GitHub Actions AI agent — issue-triggered portfolio editing with Claude API
**Researched:** 2026-03-11
**Confidence note:** Web research tools unavailable. Findings drawn from training knowledge of GitHub Actions (stable, well-documented) and Anthropic API (stable since mid-2023). Marked with confidence levels throughout.

---

## Recommended Architecture

The agent is a single GitHub Actions workflow that orchestrates four discrete operations in sequence: trigger parsing, context loading, AI generation, and PR creation.

```
GitHub Issue (opened)
        |
        v
[Workflow YAML] — triggered by issues: [opened]
        |
        v
[Step 1: Checkout] — actions/checkout@v4
        |
        v
[Step 2: Agent Script] ← ANTHROPIC_API_KEY (secret)
   |         |
   |         |-- reads: issue body (from $GITHUB_EVENT_PATH JSON)
   |         |-- reads: site files (index.html, projects/*/index.html)
   |         |-- calls: Claude API (messages endpoint)
   |         |-- writes: edited files to disk
   |
   v
[Step 3: Branch + Commit] — git operations via shell
        |
        v
[Step 4: Open PR] — gh pr create (GitHub CLI, pre-installed)
        |
        v
GitHub Pull Request (awaiting human review)
```

---

## Component Boundaries

| Component | Responsibility | Input | Output | Communicates With |
|-----------|---------------|-------|--------|-------------------|
| Workflow YAML (`.github/workflows/portfolio-agent.yml`) | Trigger, env wiring, step orchestration | GitHub issue event | Environment variables, step results | Agent Script, GitHub Actions runner |
| Agent Script (`scripts/agent.py`) | Core logic: read issue, load files, call Claude, write edits | Issue JSON, site files on disk, `ANTHROPIC_API_KEY` | Edited files on disk, exit code | Claude API (outbound), filesystem (read/write) |
| Claude API (Anthropic Messages endpoint) | Generate file edits given instructions + context | Prompt with issue + file contents | Text response with edits | Agent Script only |
| Branch Manager (shell steps in YAML or in script) | Create feature branch, commit changes | Edited files | Git branch with commit | GitHub runner git config |
| PR Creator (`gh` CLI) | Open pull request with description | Branch name, PR body string | GitHub PR URL | GitHub API (via `gh` CLI) |

**Key boundary principle:** The agent script owns all business logic. The YAML orchestrates steps but contains no logic beyond environment wiring and command invocation. This keeps the agent testable locally by running `python scripts/agent.py` with environment variables set manually.

---

## Data Flow

### Full sequence: issue to PR

```
1. GitHub fires `issues.opened` webhook
   - Payload written to: $GITHUB_EVENT_PATH (JSON file on runner)
   - Available via: github.event.issue.body, github.event.issue.title, etc.

2. Workflow YAML passes context to agent script:
   - ISSUE_TITLE  = ${{ github.event.issue.title }}
   - ISSUE_BODY   = ${{ github.event.issue.body }}
   - ISSUE_NUMBER = ${{ github.event.issue.number }}
   - ANTHROPIC_API_KEY = ${{ secrets.ANTHROPIC_API_KEY }}

3. Agent script reads site files:
   - Reads index.html, projects/*/index.html from working directory
   - Determines which files are relevant to the instruction
   - Builds a prompt containing: instruction + relevant file contents

4. Claude API call (POST /v1/messages):
   - Model: claude-opus-4-5 or claude-sonnet-4-5 (current stable)
   - System prompt: role definition, output format instructions
   - User message: instruction + file contents
   - Response: edited file contents (structured output preferred)

5. Agent script applies edits:
   - Parses Claude's response (file path + new content per file)
   - Writes updated files to disk (overwrite in place)

6. Branch + commit:
   - git checkout -b "agent/issue-{ISSUE_NUMBER}"
   - git add [changed files]
   - git commit -m "agent: {summary from Claude or issue title}"
   - git push origin [branch]

7. PR creation:
   - gh pr create --title "..." --body "..."
   - Body includes: what changed, issue reference (#N), agent attribution
   - PR targets main branch
```

### Information flow diagram

```
GitHub Issues API
    |
    | (webhook payload)
    v
GITHUB_EVENT_PATH (JSON on disk)
    |
    | (env var injection via YAML)
    v
Agent Script
    |---> filesystem read (site HTML files)
    |---> Claude API call
    |         |
    |         | (prompt: instruction + file contents)
    |         v
    |     Claude response (edited file contents)
    |         |
    |<--------/
    |
    |---> filesystem write (updated HTML files)
    |
    v
git + gh CLI
    |
    v
GitHub Pull Request
```

---

## Patterns to Follow

### Pattern 1: Structured Output from Claude

**What:** Ask Claude to return edits in a parseable format rather than prose, so the agent script can reliably extract file paths and content.

**When:** Always — free-form responses are brittle to parse.

**Example prompt instruction:**
```
Return your edits as a JSON array:
[
  {
    "file": "index.html",
    "content": "<complete updated file contents here>"
  }
]
Do not return partial files. Always return complete file contents.
```

**Why:** Partial diffs are hard to apply programmatically. Returning complete file contents is simpler to implement and less error-prone for small files (which this site has).

**Confidence:** HIGH — this is the standard approach for agentic file editing with LLMs.

---

### Pattern 2: Include Full File Contents in Prompt, Not Diffs

**What:** Pass the complete current contents of each relevant HTML file to Claude, not just snippets.

**When:** Site files are small (< 100KB each), so token cost is acceptable. Diffs require Claude to understand patch format; complete files are unambiguous.

**Implication:** Token usage scales with file size, not change size. Acceptable for this site. Would need revisiting if files grew large.

**Confidence:** HIGH — matches established patterns for small-file agentic editing.

---

### Pattern 3: Relevance Filtering Before API Call

**What:** The agent script decides which files to include in the prompt based on the issue text, rather than dumping all files every time.

**When:** Always — avoids unnecessary token usage and context dilution.

**Simple heuristic:** Keyword match issue body against file names and known content markers (e.g., "project" → include projects/*/index.html; "bio" or "about" → include index.html sections only).

**More robust:** Ask Claude in a cheap preliminary call to list which files it needs, then fetch those for the main editing call.

**Recommendation for v1:** Start with simple heuristic. Two-stage approach adds latency and complexity; revisit if relevance filtering causes bad edits.

**Confidence:** MEDIUM — pattern is established; specific heuristic choice depends on observed failure modes.

---

### Pattern 4: Idempotent Branch Naming

**What:** Name branches deterministically from the issue number: `agent/issue-{N}`.

**When:** Always.

**Why:** Prevents duplicate branches if the workflow re-runs (e.g., issue edited and reopened). Add a `git branch -D agent/issue-{N}` cleanup step before checkout if re-runs are expected.

**Confidence:** HIGH — standard practice.

---

### Pattern 5: GITHUB_TOKEN for PR Creation, ANTHROPIC_API_KEY for Claude

**What:** GitHub Actions provides `GITHUB_TOKEN` automatically with PR write permissions. `ANTHROPIC_API_KEY` must be stored as a repository secret.

**Permissions block required in YAML:**
```yaml
permissions:
  contents: write      # push branch
  pull-requests: write # open PR
  issues: read         # read issue (may be default, but explicit is safer)
```

**Confidence:** HIGH — this is the GitHub Actions permissions model. Without the explicit `pull-requests: write`, `gh pr create` will fail with a 403.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Pushing Directly to Main

**What:** Having the agent commit directly to `main` instead of opening a PR.

**Why bad:** No human review gate. A bad Claude response ships immediately to the live site (GitHub Pages auto-deploys on push to main).

**Instead:** Always push to a feature branch and open a PR. The PROJECT.md explicitly requires this.

---

### Anti-Pattern 2: Storing Secrets in Workflow YAML

**What:** Hardcoding the Anthropic API key in the workflow file.

**Why bad:** The YAML is public (public repo). Key gets scraped within minutes.

**Instead:** `secrets.ANTHROPIC_API_KEY` via GitHub repository secrets. Never echo secrets in workflow steps.

---

### Anti-Pattern 3: Using `pull_request` Event Instead of `issues` Event

**What:** Triggering on `pull_request` events for the agent.

**Why bad:** Wrong trigger entirely. The agent should trigger when a human files a GitHub Issue, not when a PR is opened.

**Instead:** `on: issues: types: [opened]`

---

### Anti-Pattern 4: Regex Parsing of Claude's Response

**What:** Using regex to extract file edits from free-form Claude output.

**Why bad:** Brittle. Any variation in Claude's phrasing breaks the parser.

**Instead:** Request structured JSON output (see Pattern 1). Parse with `json.loads()`. Validate schema before writing files.

---

### Anti-Pattern 5: No Size Guard on File Reads

**What:** Reading all site files unconditionally, including large PDFs in `projects/*/`.

**Why bad:** PDFs and binary files will hit token limits or corrupt the context.

**Instead:** Filter to text/HTML/CSS files only. Explicit allowlist: `*.html`, `*.css`. Skip `*.pdf`, `*.jpeg`, `CNAME`, etc.

---

## Suggested Build Order

Dependencies determine order. Each layer depends on the one above it.

```
Layer 1 (foundation — no dependencies):
  - Workflow YAML skeleton (trigger, checkout, secret wiring)
  - Agent script scaffolding (reads env vars, exits 0)

Layer 2 (depends on Layer 1):
  - Issue parsing (read GITHUB_EVENT_PATH or env vars, extract title + body)
  - File reader (read HTML files from disk, filter to allowlist)

Layer 3 (depends on Layer 2):
  - Claude API integration (send prompt, receive response)
  - Response parser (extract file edits from structured JSON response)

Layer 4 (depends on Layer 3):
  - File writer (apply edits to disk)
  - Branch + commit steps (git operations in YAML or script)

Layer 5 (depends on Layer 4):
  - PR creator (gh pr create with descriptive body)
  - End-to-end integration test (file a real issue, verify PR opens)
```

**Why this order:**
- Layers 1-2 are testable without any API calls — validate the plumbing first.
- Layer 3 introduces external dependency (Claude API) — isolate until layers 1-2 are solid.
- Layer 4 is pure local I/O — fast to implement and test.
- Layer 5 requires all prior layers working; run against a real repo to verify the full loop.

---

## Component: Workflow YAML Structure

```yaml
name: Portfolio Agent

on:
  issues:
    types: [opened]

permissions:
  contents: write
  pull-requests: write

jobs:
  agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install anthropic

      - name: Run agent
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          ISSUE_TITLE: ${{ github.event.issue.title }}
          ISSUE_BODY: ${{ github.event.issue.body }}
          ISSUE_NUMBER: ${{ github.event.issue.number }}
        run: python scripts/agent.py

      - name: Configure git
        run: |
          git config user.name "portfolio-agent[bot]"
          git config user.email "portfolio-agent@users.noreply.github.com"

      - name: Create branch and commit
        run: |
          BRANCH="agent/issue-${{ github.event.issue.number }}"
          git checkout -b "$BRANCH"
          git add -A
          git commit -m "agent: ${{ github.event.issue.title }}" || echo "No changes to commit"
          git push origin "$BRANCH"

      - name: Open PR
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh pr create \
            --title "agent: ${{ github.event.issue.title }}" \
            --body "Closes #${{ github.event.issue.number }}\n\nGenerated by portfolio-agent. Review before merging." \
            --base main
```

**Confidence:** HIGH for overall structure. MEDIUM for exact step sequencing — the git config step may need to run before the agent step if the agent script itself does git operations.

---

## Component: Agent Script Structure (`scripts/agent.py`)

```python
# Pseudocode — actual implementation in build phase
import os, json, anthropic
from pathlib import Path

ALLOWED_EXTENSIONS = {".html", ".css"}
SITE_ROOT = Path(".")

def load_site_files():
    """Read all HTML/CSS files, return dict of {path: content}."""
    files = {}
    for ext in ALLOWED_EXTENSIONS:
        for f in SITE_ROOT.rglob(f"*{ext}"):
            if ".github" not in str(f):
                files[str(f)] = f.read_text()
    return files

def build_prompt(issue_title, issue_body, files):
    """Assemble prompt for Claude."""
    file_block = "\n\n".join(
        f"=== {path} ===\n{content}"
        for path, content in files.items()
    )
    return f"""You are editing a personal portfolio website.

Instruction: {issue_title}
Details: {issue_body}

Current site files:
{file_block}

Return your edits as JSON:
[{{"file": "path/to/file.html", "content": "<complete updated file>"}}]
Only include files you actually changed."""

def apply_edits(edits):
    for edit in edits:
        Path(edit["file"]).write_text(edit["content"])

def main():
    issue_title = os.environ["ISSUE_TITLE"]
    issue_body = os.environ["ISSUE_BODY"]

    files = load_site_files()
    prompt = build_prompt(issue_title, issue_body, files)

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    edits = json.loads(message.content[0].text)
    apply_edits(edits)

if __name__ == "__main__":
    main()
```

**Confidence:** HIGH for structure. The `anthropic` Python SDK is the correct client. `client.messages.create` is the correct method. Model name should be verified at build time against current Anthropic model listings.

---

## Scalability Considerations

This is a single-user, low-frequency agent (one portfolio site). Scalability is not a concern. The architecture is intentionally minimal.

| Concern | At current scale | If reused for other sites |
|---------|-----------------|--------------------------|
| Token usage | Acceptable — HTML files are small | Add relevance filtering or chunking |
| API latency | 5-15 seconds per call, fine for async PR flow | Acceptable — no UX blocking |
| Rate limits | Not a concern at 1 user, occasional use | Add retry with exponential backoff |
| Concurrent runs | Not expected, but add concurrency: group if needed | Workflow-level concurrency group |

---

## Sources

- GitHub Actions `issues` event documentation (training knowledge, stable since 2020) — HIGH confidence
- GitHub Actions permissions model (`contents: write`, `pull-requests: write`) — HIGH confidence
- Anthropic Python SDK (`anthropic.Anthropic().messages.create`) — HIGH confidence, verified against training data through Aug 2025
- `gh pr create` CLI pattern — HIGH confidence, pre-installed on GitHub Actions ubuntu runners
- Structured JSON output pattern for LLM agents — HIGH confidence, widely documented practice
- Web research tools were unavailable during this research session. Claims above rely on training data; verify model names and SDK method signatures against current Anthropic docs before implementation.
