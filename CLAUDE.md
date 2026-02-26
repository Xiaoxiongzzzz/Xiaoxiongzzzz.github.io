# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an academic personal website for Xiaoxiong Zhang, built on the [academicpages](https://github.com/academicpages/academicpages.github.io) Jekyll theme (a fork of Minimal Mistakes). It deploys automatically to GitHub Pages at https://Xiaoxiongzzzz.github.io when pushed to `master`.

## Local Development Commands

```bash
# Install dependencies (first time or after Gemfile changes)
bundle install

# Serve locally with live reload (recommended for development)
bundle exec jekyll liveserve

# Serve with dev config overrides (disables analytics, uses localhost URL)
bundle exec jekyll serve --config _config.yml,_config.dev.yml

# Clean build artifacts
bundle clean
```

The site is available at `http://localhost:4000`. Changes to `_config.yml` require a server restart; other files hot-reload automatically.

## Architecture

The site uses Jekyll's **collections** system to organize academic content. Each collection maps to a directory and generates individual pages:

- `_publications/` → `/publications/:path/` — Academic papers
- `_talks/` → `/talks/:path/` — Conference presentations
- `_portfolio/` → `/portfolio/:path/` — Projects
- `_teaching/` → `/teaching/:path/` — Teaching entries

**Content flow:**
1. Individual collection entries are markdown files with YAML front matter
2. `_pages/` contains top-level pages (homepage at `_pages/about.md` with `permalink: /`)
3. Layouts in `_layouts/` use Liquid templates; `single` is the default for most content, `talk` for talks
4. SCSS lives in `_sass/` and is compiled via `assets/css/main.scss`

**Key configuration files:**
- `_config.yml` — Site-wide settings: author profile, collection definitions, plugin list, default front matter per collection
- `_config.dev.yml` — Dev overrides (sets `url: http://localhost:4000`, disables analytics)
- `_data/ui-text.yml` — Localization strings for the theme UI
- `_data/authors.yml` — Additional author profiles

## Adding Content

**Publications** (`_publications/YYYY-MM-DD-slug.md`):
```yaml
---
title: "Paper Title"
collection: publications
permalink: /publication/YYYY-MM-DD-slug
excerpt: 'Short description'
date: YYYY-MM-DD
venue: 'Conference or Journal Name'
paperurl: 'URL to PDF'
citation: 'Full citation string'
---
```

**Talks** (`_talks/YYYY-MM-DD-slug.md`) and other collections follow the same pattern. The `markdown_generator/` directory contains Python scripts and Jupyter notebooks to batch-generate collection entries from TSV files.

## Important Notes

- `_site/` is the build output directory — do not edit files there directly
- `vendor/` contains bundled Ruby gems — do not modify
- The homepage content lives in `_pages/about.md` (not `index.html`)
- Images go in `images/`, downloadable files (PDFs) go in `files/`
- `_config.yml` is not hot-reloaded; restart `jekyll serve` after changes
