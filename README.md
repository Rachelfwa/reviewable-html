<p align="center">
  <img src="assets/hero.svg" alt="Reviewable HTML — portable visual feedback for any static HTML file" width="100%">
</p>

<h1 align="center">Reviewable HTML</h1>

<p align="center"><strong>Turn any static HTML into a portable visual review file.</strong><br>No extension. No server. No account. No runtime dependency.</p>

Review AI-generated prototypes, reports, dashboards, and exported web pages by clicking the exact element that needs work. Comments stay anchored to the DOM, survive in a shareable HTML file, and can be copied as a structured prompt for Codex, Claude Code, Cursor, or another coding agent.

## The 30-second workflow

```bash
python3 scripts/inject_annotation.py report.html --zip --lang en
```

1. Open `report_reviewable.html`.
2. Click **Annotate**, then click any element.
3. Add all feedback in one pass.
4. Click **Copy for AI** to paste a selector-aware change list into your coding agent—or click **Share HTML** to send a standalone file with comments embedded.

Already using the ChatGPT/Codex skill? Attach an HTML file and ask:

> Use `@html-review-annotation` to make this file reviewable.

## Why it is different

| | Reviewable HTML | Browser extension | SaaS review tool | Annotation library |
|---|---:|---:|---:|---:|
| Double-click a local `.html` file | Yes | Varies | No | Requires integration |
| Install a browser extension | No | Yes | No | No |
| Account or server | No | Varies | Usually | Your choice |
| Feedback travels inside HTML | Yes | No | No | Custom work |
| AI-ready selector context | Yes | Varies | Rarely | Custom work |

## What ships in one file

- Click-to-comment on text, cards, buttons, inputs, tables, and custom UI
- Stable selector-first anchoring with relative-coordinate fallback
- Correct marker layering across dialogs, drawers, popovers, and nested modals
- Local autosave plus a visible “local vs embedded” state
- Search, status, priority, author, module, timestamps, edit, and delete
- **Copy for AI** with selector, context, priority, and requested change
- Markdown change list and JSON import/export
- Standalone share HTML with embedded comments
- Automatic English/Chinese UI
- Responsive, keyboard-accessible controls (`A` annotate, `L` list, `Esc` exit)
- Re-injection without duplicate engines; legacy comment migration

## Try the demo

```bash
python3 scripts/inject_annotation.py examples/demo.html --lang en --zip
```

Open the generated file and comment on both the dashboard and its decision dialog. Base-page pins stay below the dialog; only comments in the top visible modal are shown above it.

## Design boundaries

This project intentionally stays local, portable, and dependency-free. It does not add accounts, real-time collaboration, a hosted backend, a browser extension, or framework-specific source rewriting. Strict Content Security Policies may block injected inline assets; the validator reports that limitation without weakening the policy.

## Development

```bash
python3 -m unittest discover -s tests -v
node --check assets/annotation.js
python3 scripts/validate_annotation.py examples/demo_reviewable.html
```

Python 3.9+ is sufficient. The injected browser runtime is vanilla JavaScript and CSS.

## 中文简介

它能把任意静态 HTML 变成离线可批注、批注可随文件发送、修改清单可直接交给 AI 的单文件评审页。无需浏览器插件、服务器或账号；中文页面会自动显示中文界面。

## License

MIT
