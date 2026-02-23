# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Personal portfolio site for Michael Early — an MA Economics student targeting data analyst, research analyst, and sports analytics roles. Hosted on GitHub Pages at `michael-early.github.io`.

## Guiding Principles (from AGENTS.md)

- Recruiter understands value in 10 seconds
- Each project follows: problem → method → result
- Emphasize Python, SQL, econometrics, machine learning, and data visualization
- Improve clarity, not fluff; keep a concise professional tone
- **Never invent experience, metrics, or employers**
- Always explain why a change improves hiring chances
- Do not modify build or config files unless necessary

## Site Structure

This is a static HTML/CSS site with no build step, bundler, or framework. No npm, no dependencies.

```
index.html               — Main portfolio page (hero, about, projects, skills, resume, contact)
resume.pdf               — Downloadable resume
headshot.jpeg            — Profile photo
CNAME                    — GitHub Pages custom domain config
projects/
  ab1228/index.html      — AB 1228 fast-food minimum wage case study
  super-bowl-odds/index.html
  nfl-qb-wage-discrimination/index.html
  nfl-sunday-ticket-bundling/index.html
  housing-ml/index.html  — (not linked from main page yet)
  */[project].pdf        — Full working papers for each project
```

## Development

No build process — open `index.html` directly in a browser, or run a local server:

```bash
python -m http.server 8000
# then visit http://localhost:8000
```

Deploy by pushing to the `main` branch; GitHub Pages serves the site automatically.

## CSS Design System

All styles are inlined in each HTML file. The main page uses CSS custom properties:

```css
--text: #111;
--muted: #555;
--accent: #2563eb;
--border: #e5e7eb;
--bg: #f7f1e3;
```

Project detail pages replicate this style inline but do not share a stylesheet. When editing styles, apply changes to all relevant pages.

## Project Pages

Each `projects/*/index.html` follows a case-study format:
1. Problem statement
2. Method/approach
3. Result/finding

They link to a corresponding PDF (the full paper). The `housing-ml` project exists as a folder but is not yet linked from `index.html`.
