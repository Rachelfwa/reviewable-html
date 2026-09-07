---
name: html-review-annotation
description: Convert one or more static .html/.htm files into self-contained, reviewable HTML with element-anchored comments, offline persistence, modal-aware markers, searchable review status, AI-ready change lists, JSON interchange, and portable share files. Use when a user asks to annotate, comment on, mark up, review, or share feedback on an HTML prototype, report, dashboard, or exported web page.
---

# HTML Review Annotation

Preserve the input page. Inject only the isolated block between:

`<!-- HTML-REVIEW-ANNOTATION:START -->` and `<!-- HTML-REVIEW-ANNOTATION:END -->`.

Never redesign, refactor, rename, or alter existing business logic unless the user separately requests it.

## Convert

1. Resolve every input `.html` or `.htm` file.
2. Keep each original unchanged.
3. Run the bundled injector for each file:

```bash
python3 scripts/inject_annotation.py "/path/input.html" \
  --output "/path/input_可批注版.html" \
  --zip "/path/input_可批注版.zip"
```

Use `--lang en` or `--lang zh-CN` only when the user requests a fixed UI language. The default `auto` follows the document language.

4. Validate every output:

```bash
python3 scripts/validate_annotation.py "/path/input_可批注版.html"
node --check assets/annotation.js
```

5. Deliver the ZIP by default. Also provide raw HTML when the user asks for it or direct opening is useful.

## Required guarantees

- Keep one injection block when re-run; preserve `#hra-meta`, embedded annotations, and `documentId`.
- Anchor comments with a stable DOM selector plus relative and fallback coordinates.
- Support base pages, drawers, dialogs, popovers, and nested modal layers without leaking lower-layer markers above the top modal.
- Keep page counts stable when related dialogs open or close.
- Leave the author blank unless explicitly configured.
- Save drafts locally and clearly distinguish them from comments embedded in the file.
- Generate a standalone share HTML with a new revision key so stale local cache cannot override embedded comments.
- Export Markdown, copy an AI-ready change prompt, and import/export JSON.
- Intercept page actions while annotation mode is active.
- Add no runtime dependency and upload no review data.

## Compatibility and safety

- Migrate legacy `pm-annotations-seed` / `pmAnnoState` data when possible and hide the legacy review UI.
- Do not remove or weaken Content Security Policy. Report a CSP warning if validation finds one.
- Use this workflow for static or exported HTML. Modify framework/server source only when explicitly asked for source integration.

## Completion

State that the file was converted, mention `生成分享版` / `Share HTML`, provide the ZIP link, and report only validation or CSP warnings.
