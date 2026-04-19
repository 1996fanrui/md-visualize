---
description: "Pre-screenshot parameter check: estimate optimal viewport width based on content structure."
---

# Screenshot Parameter Pre-Check (Vue Component Path Only)

> Mermaid path is fully automated by `md_render_mermaid.py` with no viewport parameters; this section does not apply.

Before calling screenshot.py, determine the viewport width for each HTML file using the rules below. Never blindly use the default value.

## Viewport Width for Vue Component Images

### 1. Estimate the Maximum Natural Content Width

Read the corresponding JSON data and evaluate horizontal space requirements:

| Content Characteristic | Estimated Natural Width |
|---------|------------|
| Table: sum of character counts of longest text in each column × ~12px + column gaps + margins | Actual estimate |
| Card grid: cols × single card width (~250px) + gaps | Actual estimate |
| Left-right split: two-column content widths + gap + margins | Actual estimate |
| Vertical list: longest line text × ~12px + icon + margins | Actual estimate |

### 2. Select Viewport Width

Choose the smallest standard tier (1400 / 900 / 600) that is ≥ the estimated natural width. If no standard tier fits, a non-standard value (e.g., 1100) is allowed, but the reasoning must be documented.

### 3. Validation Rules

- The estimated longest text line should not wrap at the selected width
- The estimated width should not result in more than 30% horizontal whitespace (i.e., content width / viewport width ≥ 0.7)
- If the two conditions conflict (narrower causes wrapping, wider causes too much whitespace), prioritize preventing wrapping, then reduce text length in the JSON data to address whitespace

## Self-Check Checklist

For each HTML to be screenshotted:

- [ ] Viewport width selected with clear reasoning
- [ ] Estimated longest text line does not wrap at the selected width
- [ ] Estimated content width / viewport width ≥ 0.7 (no excessive whitespace)
