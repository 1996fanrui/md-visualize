---
description: "Self-check checklist after replacing original text with Vue component screenshots."
---

# Replaced Markdown Self-Check (Vue Component Path Only)

> Mermaid path replacement is fully automated by `md_render_mermaid.py`; this checklist does not apply.

After writing `<img>` tags and image-config into Markdown, verify each item:

- [ ] Each `<img>` tag's `src` path corresponds to a PNG file that actually exists
- [ ] `width` values conform to standard width tiers (800 / 600 / 400)
- [ ] File names in the image-config comment block match the actual images
- [ ] Original text from replaced paragraphs is fully removed; no leftover fragments
- [ ] Unprocessed paragraphs remain unchanged; no accidental edits
