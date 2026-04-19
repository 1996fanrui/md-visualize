---
description: "Visual component style rules: colors, widths, style variables, branding. Reference for AI when generating JSON data or filling slot content. Component internal CSS/font/layout specs are in {{SKILL_DIR}}/visual-components/README.md."
---

# Visual Component Style Rules

> This document covers only the rules that AI must actively decide when generating JSON data or filling slot content. Internal component implementation (background, font, font-weight, layout CSS) is handled by the component itself and is not listed here.

## 1. Color Basics

Before generating color properties (e.g., `cardBg`, `accentColor`), read `{{SKILL_DIR}}/visual-components/styles/color-palettes.md` and select colors following these steps:

1. Determine the current element's semantic meaning (create/execute/output/delete/compare/neutral...)
2. Find the semantically matching color family in color-palettes.md
3. Choose value by usage: Solid for small areas, Semi-transparent (0.75) for large areas (card backgrounds)

Prohibited:
- Using white (`rgba(255,255,255,...)`) as a card background
- Inventing color values not found in color-palettes.md
- Using mid-grays such as `#555`/`#666`/`#777` (too faint on dark backgrounds)

## 2. Standard Width Tiers (Screenshot Path Only)

> Applies only to the screenshot path. Component tag path widths are controlled by VitePress layout and component CSS; AI does not need to specify them.

| Tier | viewport `--width` | embed `<img width>` | Use case |
|---|---|---|---|
| full | `1400` (default) | `800` | Comparison tables, multi-column card grids, flowcharts, and other wide content |
| medium | `900` | `600` | Code blocks, two-column comparisons, medium-complexity cards |
| compact | `600` | `400` | Single-column cards, short conclusion boxes, small charts |

Content width is determined by structural pattern — do not stretch to fill width. Prefer larger text on a wider image over smaller text on a narrow image.

## 3. Style Variables

When JSON data or slot content involves font size, font family, color, or other style properties, always use `--ave-*` variables. Hardcoded px values or color values are prohibited.

Available variables are defined in the source files; read the corresponding file to confirm variable names before use:
- Screenshot mode: `{{SKILL_DIR}}/visual-components/styles/ave-variables.css`

## 4. Brand Mentions

- In promotional articles, naturally mention the project name in appropriate places
- Not every image needs it, but scenario descriptions and comparison charts should include natural mentions

## Core Principles (Fallback When Rules Do Not Cover a Case)

- What is the visual purpose? (compare? emphasize? show a process? show hierarchy?)
- Does it display correctly on both light and dark backgrounds?
- Do the colors carry semantic meaning? (do not use colors randomly for aesthetics)

> Vue component technical specs (header comment format, scoped styles, etc.) are in `{{SKILL_DIR}}/visual-components/README.md`.
