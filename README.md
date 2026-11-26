# Blog

## Add a post

Create `posts/YYYY-MM-DD-slug.md` with front matter and a short English post:

```markdown
---
title: A short title
date: 2026-01-01
summary: One sentence describing the post.
---

Your post goes here.
```

The date must match the filename and slugs must be unique. Run `python3 -I build.py`, then commit `posts/` and the generated `docs/` together. Use `python3 -I build.py --check` to check whether the committed output is current. GitHub Pages serves `main:/docs` as static files, with the CNAME `blog.kurenn.dev`; Jekyll is disabled.

## Markdown subset

Supported: paragraphs, `##` and `###` headings, flat unordered (`-`, `*`, `+`) and ordered (`1.`) lists, blockquotes (`>`), fenced code blocks using triple backticks with an optional language, inline code, `**bold**`, `*italic*`, and `[text](url)` links. Inline formatting is not nested. Separate blocks with blank lines. Raw HTML is escaped, not rendered. Links support HTTP, HTTPS, mailto, and relative URLs; other schemes render as plain text.
