# Website Beautification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the academic site into a Warm & Scholarly aesthetic using a zero-risk additive SCSS layer, without touching any theme core files.

**Architecture:** Three file changes only. A new `_sass/_custom.scss` holds all overrides and is appended last in `main.scss`, so CSS cascade ensures it wins. Google Fonts loaded via the existing `_includes/head/custom.html` hook.

**Tech Stack:** Jekyll 3.9, SCSS/Sass, Google Fonts (Playfair Display + Lato), GitHub Pages

---

## Verification Command (use after every task)

```bash
bundle exec jekyll build 2>&1 | tail -5
```

Expected output ends with: `done in X.XXX seconds.` — no error lines.

To preview live:
```bash
bundle exec jekyll serve --config _config.yml,_config.dev.yml
# open http://localhost:4000
```

---

### Task 1: Add Google Fonts

**Files:**
- Modify: `_includes/head/custom.html`

**Step 1: Add font preconnect + stylesheet link**

Open `_includes/head/custom.html`. Find the line `<!-- start custom head snippets -->` and insert immediately after it:

```html
<!-- Google Fonts: Warm & Scholarly -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:ital,wght@0,300;0,400;0,700;1,300;1,400&display=swap" rel="stylesheet">
```

**Step 2: Verify build**

```bash
bundle exec jekyll build 2>&1 | tail -5
```

Expected: clean build, no errors.

**Step 3: Commit**

```bash
git add _includes/head/custom.html
git commit -m "feat: add Playfair Display + Lato via Google Fonts"
```

---

### Task 2: Create `_custom.scss` — Foundation (colors + global)

**Files:**
- Create: `_sass/_custom.scss`

**Step 1: Create the file with color tokens and global body overrides**

Create `_sass/_custom.scss` with this exact content:

```scss
// ================================================================
//  CUSTOM OVERRIDES — Warm & Scholarly Theme
//  Appended last in main.scss; wins CSS cascade over all defaults.
// ================================================================

// ─── Color tokens (SCSS-only, used below) ───────────────────────
$warm-bg:       #faf8f5;
$warm-text:     #2c2825;
$accent:        #4a7c6b;
$accent-dark:   #2d5c4d;
$border-warm:   #e8e2d9;
$border-subtle: #e0d8cc;
$footer-bg:     #f0ece4;
$muted-text:    #5a5450;

// ─── Global ─────────────────────────────────────────────────────
body {
  background-color: $warm-bg;
  color: $warm-text;
  font-family: 'Lato', sans-serif;
}

// ─── Typography ─────────────────────────────────────────────────
h1, h2, h3, h4, h5, h6 {
  font-family: 'Playfair Display', Georgia, serif;
  color: $warm-text;
}

// ─── Links (global) ─────────────────────────────────────────────
a {
  color: $accent;

  &:visited {
    color: mix(#fff, $accent, 20%);
  }

  &:hover,
  &:active {
    color: $accent-dark;
  }
}
```

**Step 2: Wire it into main.scss**

Open `assets/css/main.scss`. After the last `@import` line (`@import "print";`), add:

```scss
@import "custom";
```

**Step 3: Verify build**

```bash
bundle exec jekyll build 2>&1 | tail -5
```

Expected: clean build.

**Step 4: Commit**

```bash
git add _sass/_custom.scss assets/css/main.scss
git commit -m "feat: scaffold custom SCSS layer with color tokens and global overrides"
```

---

### Task 3: Masthead & Navigation styles

**Files:**
- Modify: `_sass/_custom.scss` (append to bottom)

**Step 1: Append masthead section to `_sass/_custom.scss`**

```scss
// ─── Masthead ───────────────────────────────────────────────────
.masthead {
  background-color: $warm-bg;
  border-bottom-color: $border-subtle;
}

// Site title: italic Playfair
.masthead__menu-item--lg a {
  font-family: 'Playfair Display', Georgia, serif;
  font-style: italic;
  font-weight: 400;
  letter-spacing: 0.01em;
}

// Nav links
.greedy-nav {
  background: $warm-bg;

  a {
    font-family: 'Lato', sans-serif;
    color: $warm-text;

    &:hover {
      color: $accent-dark;
    }
  }

  // Hover underline: override color from gray to accent
  .visible-links a::before {
    background: $accent;
    height: 2px;
  }

  // Mobile hamburger button
  button {
    background-color: $accent;
  }

  // Overflow dropdown
  .hidden-links {
    background: $warm-bg;
    border-color: $border-warm;

    &::after {
      border-color: $warm-bg transparent;
    }

    a:hover {
      background: rgba(74, 124, 107, 0.08);
      color: $accent-dark;
    }
  }
}
```

**Step 2: Verify build**

```bash
bundle exec jekyll build 2>&1 | tail -5
```

**Step 3: Commit**

```bash
git add _sass/_custom.scss
git commit -m "feat: apply warm masthead and accent nav-underline"
```

---

### Task 4: Author Sidebar styles

**Files:**
- Modify: `_sass/_custom.scss` (append to bottom)

**Step 1: Append sidebar section**

```scss
// ─── Author Sidebar ─────────────────────────────────────────────
.author__avatar img {
  border-radius: 50%;
  border: 3px solid $accent;
  box-shadow: 0 2px 12px rgba(74, 124, 107, 0.18);
}

.author__name {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.1em;
  color: $warm-text;
}

.author__bio {
  font-family: 'Lato', sans-serif;
  font-weight: 300;
  font-style: italic;
  color: $muted-text;
}

// "Follow" button
.author__urls-wrapper .btn--inverse {
  border-color: $accent;
  color: $accent;

  &:hover {
    background-color: $accent;
    color: #fff;
  }
}

// Social links
.author__urls {
  a {
    color: $warm-text;
    text-decoration: none;
    transition: color 0.2s ease;

    &:hover {
      color: $accent;
    }
  }

  // Icons
  .fa, .fas, .fab, .far, .ai {
    color: $accent;
  }
}
```

**Step 2: Verify build**

```bash
bundle exec jekyll build 2>&1 | tail -5
```

**Step 3: Commit**

```bash
git add _sass/_custom.scss
git commit -m "feat: style author sidebar with accent border and Playfair name"
```

---

### Task 5: Page Content styles

**Files:**
- Modify: `_sass/_custom.scss` (append to bottom)

**Step 1: Append page content section**

```scss
// ─── Page Content ───────────────────────────────────────────────
#main {
  background-color: $warm-bg;
}

.page__content {
  // H2: replace bottom border with left accent bar
  h2 {
    border-bottom: none;
    border-left: 3px solid $accent;
    padding-left: 0.6em;
    padding-bottom: 0;
  }

  // H1: tighten tracking
  h1 {
    letter-spacing: -0.01em;
  }

  // Blockquote: warm accent tint
  blockquote {
    border-left-color: $accent;
    background-color: rgba(74, 124, 107, 0.05);
    border-radius: 0 4px 4px 0;
    padding: 0.8em 1.2em;
  }

  // Links in content: underline-slide on hover
  a {
    color: $accent;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s ease, color 0.2s ease;

    &:hover {
      color: $accent-dark;
      border-bottom-color: $accent;
      text-decoration: none;
    }
  }

  // Publication table: borderless with hover row tint
  table {
    border: none;
    border-collapse: collapse;

    tr {
      border: none;
      transition: background-color 0.15s ease;

      &:hover {
        background-color: rgba(74, 124, 107, 0.04);
      }
    }

    td {
      border: none;
    }
  }
}

// Venue labels (e.g., <i>CoRL 2025</i>) — small-caps accent color
.page__content strong i,
.page__content b i {
  font-variant: small-caps;
  color: $accent;
  font-style: normal;
}

// HR
hr {
  border-top-color: $border-warm;
}
```

**Step 2: Verify build**

```bash
bundle exec jekyll build 2>&1 | tail -5
```

**Step 3: Commit**

```bash
git add _sass/_custom.scss
git commit -m "feat: H2 accent bar, warm blockquote, borderless publication table"
```

---

### Task 6: Footer styles

**Files:**
- Modify: `_sass/_custom.scss` (append to bottom)

**Step 1: Append footer section**

```scss
// ─── Footer ─────────────────────────────────────────────────────
.page__footer {
  background-color: $footer-bg;
  border-top: 1px solid $border-subtle;
  color: $muted-text;

  a {
    color: $muted-text;
    transition: color 0.2s ease;

    &:hover {
      color: $accent;
      text-decoration: none;
    }
  }

  .fas, .fab, .far, .fal {
    color: $accent;
  }
}
```

**Step 2: Final full build + serve check**

```bash
bundle exec jekyll build 2>&1 | tail -5
```

Then start live server and visually verify all pages:

```bash
bundle exec jekyll serve --config _config.yml,_config.dev.yml
```

Check at `http://localhost:4000`:
- [ ] Body background is warm off-white (not pure white)
- [ ] Headings render in Playfair Display serif
- [ ] Nav site title is italic
- [ ] Nav hover underline is blue-green
- [ ] Author avatar has green circular border
- [ ] H2 sections have left accent bar (not bottom border)
- [ ] Footer is warm beige tone
- [ ] No SCSS compile errors in terminal

**Step 3: Commit**

```bash
git add _sass/_custom.scss
git commit -m "feat: warm footer background and accent icon colors"
```

---

### Task 7: Final commit message

After all visual checks pass:

```bash
git log --oneline -6
```

Should show 6 commits from this feature. No further action needed — the site deploys automatically when pushed to `master`.
