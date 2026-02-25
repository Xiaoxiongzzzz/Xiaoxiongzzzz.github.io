# Homepage Layout Design — Option B

**Date:** 2026-02-25
**Scope:** `_pages/about.md` + `_sass/_custom.scss` (append)
**Principle:** Same content, radically better structure — replace all inline-style div soup with semantic HTML + CSS classes

---

## 1. Section Headings

Change all `# Section` (h1) in about.md to `## Section` (h2) so they inherit the existing left accent bar from `.page__content h2` in `_custom.scss`.

---

## 2. Education — Timeline

### HTML Structure

```html
<div class="edu-timeline">
  <div class="edu-entry">
    <div class="edu-dot"></div>
    <div class="edu-body">
      <div class="edu-header">
        <strong>Southern University of Science and Technology (SUSTech)</strong>
        <span class="edu-date">Sep. 2024 – Now</span>
      </div>
      <div class="edu-degree">Master in Control Science and Engineering</div>
    </div>
  </div>
  <div class="edu-entry">
    <div class="edu-dot"></div>
    <div class="edu-body">
      <div class="edu-header">
        <strong>Wuhan University of Technology (WHUT)</strong>
        <span class="edu-date">Sep. 2020 – Jul 2024</span>
      </div>
      <div class="edu-degree">Bachelor of Engineering in Mechanical Engineering &nbsp;·&nbsp; GPA: <strong>4.28/5.0</strong> &nbsp;·&nbsp; Rank: <strong>2/178</strong></div>
    </div>
  </div>
</div>
```

### CSS

```scss
.edu-timeline {
  border-left: 2px solid $accent;
  margin-left: 6px;
  padding-left: 1.4em;
  margin-top: 1em;
}

.edu-entry {
  position: relative;
  margin-bottom: 1.6em;

  &:last-child { margin-bottom: 0; }
}

.edu-dot {
  position: absolute;
  left: -1.82em;
  top: 0.35em;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background-color: $accent;
  border: 2px solid $warm-bg;
  box-shadow: 0 0 0 1.5px $accent;
}

.edu-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.3em;
}

.edu-date {
  font-size: 0.85em;
  font-style: italic;
  color: $muted-text;
  white-space: nowrap;
}

.edu-degree {
  margin-top: 0.2em;
  font-size: 0.92em;
  color: $muted-text;
}
```

---

## 3. Publications — Card

### HTML Structure

```html
<div class="pub-card">
  <div class="pub-media">
    <div class="pub-video-wrap">
      <iframe src="https://www.youtube.com/embed/fGzu_huiuvE" frameborder="0" allowfullscreen></iframe>
    </div>
  </div>
  <div class="pub-info">
    <div class="pub-title">Generative Visual Foresight Meets Task-Agnostic Pose Estimation in Robotic Table-top Manipulation</div>
    <div class="pub-authors">Chuye Zhang*, <strong>Xiaoxiong Zhang*</strong>, Wei Pan, Linfang Zheng<sup>†</sup>, Wei Zhang<sup>†</sup></div>
    <div class="pub-venue">
      <span class="venue-badge">CoRL 2025</span>
      <a href="https://clearlab-sustech.github.io/gvf-tape/" class="pub-link">[project page]</a>
    </div>
  </div>
</div>
```

### CSS

```scss
.pub-card {
  display: flex;
  gap: 1.4em;
  align-items: flex-start;
  padding: 1.2em 1.4em;
  background: rgba(136, 150, 179, 0.07);
  border: 1px solid $border-warm;
  border-radius: 6px;
  margin-top: 1em;
  flex-wrap: wrap;
}

.pub-media {
  flex: 0 0 280px;
  max-width: 280px;
}

.pub-video-wrap {
  position: relative;
  padding-bottom: 56.25%;
  height: 0;
  overflow: hidden;
  border-radius: 4px;

  iframe {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    border: none;
  }
}

.pub-info {
  flex: 1;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 0.5em;
}

.pub-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 1.02em;
  font-weight: 700;
  line-height: 1.4;
  color: $warm-text;
}

.pub-authors {
  font-size: 0.9em;
  color: $muted-text;
  line-height: 1.5;
}

.pub-venue {
  display: flex;
  align-items: center;
  gap: 0.8em;
  flex-wrap: wrap;
}

.venue-badge {
  display: inline-block;
  padding: 0.18em 0.6em;
  background: $accent;
  color: #fff;
  border-radius: 3px;
  font-size: 0.8em;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.pub-link {
  font-size: 0.9em;
  color: $accent;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s ease;

  &:hover {
    border-bottom-color: $accent;
  }
}
```

---

## 4. Honors & Awards — Year Badge rows

### HTML Structure

```html
<div class="award-list">
  <div class="award-entry">
    <div class="award-body">
      <strong>Outstanding Graduate</strong>
      <span class="award-org">Wuhan University of Technology</span>
    </div>
    <span class="award-year">2024</span>
  </div>
  <!-- repeat for each award -->
</div>
```

### CSS

```scss
.award-list {
  margin-top: 1em;
}

.award-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1em;
  padding: 0.6em 0;
  border-bottom: 1px solid $border-warm;

  &:last-child { border-bottom: none; }
}

.award-body {
  display: flex;
  flex-direction: column;
  gap: 0.1em;
}

.award-org {
  font-size: 0.85em;
  color: $muted-text;
}

.award-year {
  flex-shrink: 0;
  display: inline-block;
  padding: 0.18em 0.55em;
  background: $accent;
  color: #fff;
  border-radius: 3px;
  font-size: 0.75em;
  font-weight: 700;
  letter-spacing: 0.04em;
}
```

---

## Files Changed

| File | Action |
|------|--------|
| `_pages/about.md` | Rewrite HTML structure; change `#` → `##` for section headings; replace inline-style divs with semantic classes |
| `_sass/_custom.scss` | Append timeline, pub-card, and award-list styles |
