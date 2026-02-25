# Website Beautification Design

**Date:** 2026-02-25
**Scope:** Global visual overhaul via additive custom SCSS layer
**Approach:** Append `_sass/_custom.scss`, import at end of `main.scss` — zero modifications to theme core files

---

## Design Direction

**Style:** Warm & Scholarly
**Principle:** Simple but artistic — refined typographic hierarchy, warm neutral palette, a single calm accent color, no decorative clutter

---

## 1. Color System

| Purpose | Token | Value |
|---------|-------|-------|
| Page background | `$background-color` override | `#faf8f5` (warm off-white) |
| Body text | `$text-color` override | `#2c2825` (deep warm brown) |
| Primary accent | `$primary-color` override | `#4a7c6b` (calm blue-green) |
| Link color | `$link-color` override | `#4a7c6b` |
| Link hover | `$link-color-hover` override | `#2d5c4d` |
| Border / divider | `$border-color` override | `#e8e2d9` (warm gray) |
| Masthead bottom border | inline style | `1px solid #e0d8cc` |
| Code background | override | `#f3f0ea` |

---

## 2. Typography

Loaded via `_includes/head/custom.html` (Google Fonts):

```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
```

| Element | Font | Weight |
|---------|------|--------|
| h1–h4, author name | Playfair Display | 700 (h1/h2), 400 (h3/h4) |
| Site title in masthead | Playfair Display italic | 400 |
| Body text, nav, sidebar | Lato | 400 |
| Author bio | Lato italic | 300 |
| Captions, meta | Lato | 300 |

---

## 3. Author Sidebar

- Avatar: `border-radius: 50%`, `border: 3px solid #4a7c6b`, `box-shadow: 0 2px 12px rgba(74,124,107,0.18)`
- Author name: Playfair Display, font-size 1.1em, color `#2c2825`
- Bio text: Lato italic 300, color `#5a5450`
- Social links: hover triggers `border-bottom: 1px solid #4a7c6b` sliding in via CSS transition
- Location/employer icon color: `#4a7c6b`

---

## 4. Page Content Area

- `body` background: `#faf8f5`
- `h2` in `.page__content`: left accent bar `border-left: 3px solid #4a7c6b`, `padding-left: 0.6em`, remove bottom border rule
- `h1` (page title): Playfair Display, tracked slightly with `letter-spacing: -0.01em`
- `blockquote`: left border color `#4a7c6b`, background `rgba(74,124,107,0.05)`, slight padding
- `a` in content: color `#4a7c6b`, underline on hover only
- `hr`: `border-top: 1px solid #e8e2d9`

---

## 5. Masthead / Navigation

- Background: `#faf8f5` (blends with page, no visual cut)
- Bottom border: `1px solid #e0d8cc`
- Site title: Playfair Display italic
- Nav links: Lato 400, color `#2c2825`
- Active/hover: `border-bottom: 2px solid #4a7c6b` with `transition: border-color 0.2s ease`

---

## 6. Footer

- Background: `#f0ece4` (slightly darker warm tone)
- Text: `#6b6560` (muted)
- Top border: `1px solid #e0d8cc`

---

## 7. Publication Table (homepage)

The homepage `about.md` uses an HTML `<table>` for publications:
- Remove default table borders
- Add subtle `border-radius: 8px` card-like wrapper via CSS on `table` inside `.page__content`
- Row hover: `background: rgba(74,124,107,0.04)`
- Paper title bold in Playfair Display
- Venue label (CoRL 2025): `color: #4a7c6b`, small caps via `font-variant: small-caps`

---

## Implementation Files

| File | Action |
|------|--------|
| `_sass/_custom.scss` | **Create** — all visual overrides |
| `assets/css/main.scss` | **Edit** — append `@import "custom"` |
| `_includes/head/custom.html` | **Edit** — add Google Fonts link |

---

## Constraints

- Do NOT modify `_sass/_variables.scss` or any `_sass/vendor/` file
- All overrides use CSS specificity or SCSS variable re-declaration after the original `@import "variables"`
- The result must compile with `bundle exec jekyll serve` without errors
