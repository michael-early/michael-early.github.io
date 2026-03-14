# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Personal portfolio site for Michael Early — an MA Economics student targeting data analyst, research analyst, and sports analytics roles. Hosted on GitHub Pages at `michael-early.github.io`.

Open `claude` in this repo, describe what to change, and make the edit directly. Push to main to deploy.

## Guiding Principles

- Recruiter understands value in 10 seconds
- Each project follows: problem → method → result
- Emphasize Python, SQL, econometrics, machine learning, and data visualization
- Improve clarity, not fluff; keep a concise professional tone
- **Never invent experience, metrics, or employers**
- Always explain why a change improves hiring chances
- Do not modify build or config files unless necessary

## Site Structure

Static HTML/CSS site — no build step, bundler, or framework. No npm, no dependencies.

```
index.html                              — Main portfolio page
resume.pdf                              — Downloadable resume (never edit)
headshot.jpeg                           — Profile photo (never edit)
CNAME                                   — GitHub Pages domain config (never edit)
projects/
  ab1228/index.html                     — AB 1228 fast-food minimum wage case study
  super-bowl-odds/index.html            — Super Bowl odds forecasting
  nfl-qb-wage-discrimination/index.html — NFL QB wage discrimination
  nfl-sunday-ticket-bundling/index.html — NFL Sunday Ticket pricing model
  housing-ml/index.html                 — Housing price ML model (linked from main page)
  */[project].pdf                       — Full working papers (never edit)
```

**Never touch:** `resume.pdf`, `headshot.jpeg`, `CNAME`, any `.pdf` file.

## Development

No build process — open `index.html` directly in a browser, or run a local server:

```bash
python -m http.server 8000
# then visit http://localhost:8000
```

Deploy: push to `main` branch → GitHub Pages serves automatically.

## CSS Design System

All styles are **inlined in each HTML file**. There is no shared stylesheet.

### Main page (`index.html`) CSS variables:
```css
--text: #111;
--muted: #555;
--accent: #2563eb;
--border: #e5e7eb;
--bg: #f7f1e3;
```

### Project detail pages CSS variables:
```css
--text: #0f172a;
--muted: #64748b;
--accent: #2563eb;
--accent-light: #eff6ff;
--border: #e2e8f0;
```

When editing styles, apply changes to all relevant pages (they don't share a stylesheet).

## Project Card Structure (index.html)

The projects section uses a CSS grid. Each card looks like this:

```html
<div class="project">
  <div class="project-title">
    <a href="projects/[slug]/">[Project Title]</a>
  </div>
  <div class="project-desc">
    [1-2 sentence description: method + what it tests/measures]
  </div>
</div>
```

Cards live inside `<div class="projects-grid">` inside `<section id="projects">`.

To **add a project card**: copy the block above, set the `href` to `projects/[slug]/`, write a tight description following problem → method → result.

To **reorder cards**: move the `<div class="project">` blocks within the grid.

## Project Detail Page Structure

Each `projects/*/index.html` follows a case-study format:

```
1. Problem statement — what question is being answered
2. Method/approach  — how it's answered (techniques, data)
3. Result/finding   — what was found, with specific numbers if available
```

Pages link to a corresponding PDF (`[project].pdf`) in the same folder.

Use the ab1228 page as the reference template when creating a new project page.

## Projects Reference

| Slug | Title | Status |
|------|-------|--------|
| `ab1228` | Fast-Food Minimum Wage (AB 1228) | Linked from main |
| `super-bowl-odds` | Forecasting Super Bowl Odds | Linked from main |
| `nfl-qb-wage-discrimination` | NFL Quarterback Wage Discrimination | Linked from main |
| `nfl-sunday-ticket-bundling` | NFL Sunday Ticket Pricing Model | Linked from main |
| `housing-ml` | Housing Price ML Model | Linked from main |

**housing-ml**: ML model predicting housing prices. The folder and page exist at `projects/housing-ml/index.html`.

## Common Tasks

**Add a new project to the main page:**
1. Create `projects/[slug]/index.html` using the ab1228 page as template
2. Add a `<div class="project">` card to the `projects-grid` in `index.html`

**Update bio or hero text:**
Edit the `<section id="about">` or `<header class="hero">` in `index.html`.

**Update skills:**
Edit `<section id="skills">` in `index.html`. Skills use `.skill-tag` spans inside `.skill-tags` divs.

**Update experience:**
Edit `<section id="experience">` in `index.html`. Each job is a `.exp` div with `.exp-title`, `.exp-company`, `.exp-date`, and `.exp-bullets`.

**Edit a project page:**
Edit `projects/[slug]/index.html` directly. Follow the problem → method → result structure.
