---
description: "Self-check checklist after generating JSON data files."
---

# JSON Data Self-Check

Before calling render.mjs, verify each JSON file against the following items:

- [ ] Field names and data types match the component's `usage-json` definition
- [ ] Color property values come from `{{SKILL_DIR}}/visual-components/styles/color-palettes.md`; no white or invented colors
- [ ] No prohibited gray values such as `#555` / `#666` / `#777`
- [ ] Text content fully preserves the original semantics; nothing is truncated or missing
- [ ] Font size properties use `--ave-*-size` variables; no hardcoded px values
- [ ] Font family properties use `--ave-font-*` variables
- [ ] Width conforms to a standard tier (full / medium / compact)
- [ ] Text length and item count satisfy the component's `layout-constraints` (read the `layout-constraints` field from the matched component's `.vue` file header comment; verify that text lengths, item counts, etc. in the JSON are within the specified bounds)

Fix any non-conforming JSON before proceeding.
