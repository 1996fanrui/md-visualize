---
description: "Self-check checklist after writing Vue component tags into Markdown."
---

# Component Tag Self-Check

After writing Vue component tags into Markdown, verify each item:

- [ ] Component tag names match the registered component names
- [ ] Tags are properly closed; slot structure matches the `usage-markdown` definition
- [ ] Color property values come from `{{SKILL_DIR}}/visual-components/styles/color-palettes.md`; no white or invented colors
- [ ] No prohibited gray values such as `#555` / `#666` / `#777`
- [ ] Width properties conform to a standard tier (full / medium / compact)
- [ ] Slot text fully preserves the original semantics; nothing is truncated or missing
- [ ] Original text from replaced paragraphs is fully removed; no leftover fragments
- [ ] Unprocessed paragraphs remain unchanged; no accidental edits
