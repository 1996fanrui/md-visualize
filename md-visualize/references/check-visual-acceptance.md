---
description: "Final visual acceptance workflow: shared by both paths, includes evaluation principles, execution flow, and termination rules."
---

# Final Visual Acceptance

Execute after each path completes, to perform visual acceptance of the final rendered output.

## Evaluation Principles

Only check items that require viewing the rendered result to judge. Evaluate each image against the following principles — each item must result in "pass" or a specific problem description. Generic "pass" without detail is prohibited.

1. **No visual defects**: Nothing in the image is obviously wrong at a glance (e.g., deformed shapes, overlapping/occluded elements, broken connecting lines, arrows that don't look like arrows)
2. **Readability**: All text is clearly readable on any background; not truncated or overflowing
3. **Structural correctness**: Alignment, spacing, and hierarchical relationships match the content's logical structure
4. **Color harmony and semantics**: Colors are not jarring on either light or dark backgrounds and are harmonious with the overall visual style; colors convey correct meaning (good/bad, in-progress/complete, etc.); unrelated elements have sufficient hue differentiation
5. **Information at a glance**: Readers can understand from the visual structure (color, layout, size) what the image conveys (comparison, process, progression, etc.) without reading every word

These are universal principles applicable to all types of visual output. Do not add checks here for specific components or specific pitfalls — the independent reviewer sub-agent reads images in a fresh context with visual understanding capabilities and can independently discover specific issues without a pre-set pitfall checklist.

## Issue Severity Levels

| Level | Definition | Action |
|---|---|---|
| L1 | Obvious error, not deliverable (text unreadable, component renders blank/errors, color semantics completely inverted) | Must fix; skipping is not allowed |
| L2 | Visual quality below standard (poor readability, obviously misaligned, information not discernible at a glance) | Must fix; skipping is not allowed |
| L3 | Detail preference (spacing slightly narrow, colors could be better but don't affect readability or semantics) | Collect and present to user for decision |

**L1 + L2 must all pass before delivery; L3 items are collected and shown to the user.**

L2 vs L3 criterion: affects content readability, color semantic understanding, or at-a-glance discernibility → L2; affects only aesthetic preference → L3.

## Obtaining Screenshots

The two paths obtain screenshots differently; after obtaining them, enter the unified acceptance workflow.

**Screenshot illustration path**: Directly read the generated PNG files under `images/`.

**Component tag path**:
1. Confirm the VitePress dev server is running (if not → read `package.json` to determine the start command → start it independently)
2. Infer the page URL from the target Markdown file path (e.g., `http://localhost:5173/path/to/page`)
3. Call screenshot.py on the target page: `uv run {{SKILL_DIR}}/scripts/screenshot.py <url> visual-check.png`

## Acceptance Workflow (Shared by Both Paths)

```
Screenshots obtained
  ↓
Launch independent visual-reviewer sub-agent (fresh context, not inherited from main thread):
  - Input: all PNG image paths to review + above evaluation principles
  - Output: per-image item-by-item evaluation results (L1/L2/L3) + fix suggestions
  ↓
Coordinator aggregates reviewer results
  ↓
Any L1 or L2?
  Yes → Coordinator fixes (mermaid path: modify mermaid code → re-run md_render_mermaid.py; Vue component screenshot path: modify JSON → render.mjs → re-screenshot; component tag path: modify tag attributes/slot → wait for hot reload → re-screenshot)
     → Launch new visual-reviewer sub-agent (fresh context) for re-acceptance
     → Loop
  No → L1+L2 passed, aggregate L3
  ↓
Execute termination rules
  ↓
Present to user: list of accepted images + L3 issues (if any), request final confirmation
```

## Termination Rules

1. Current round L1 + L2 all pass → terminate, proceed to L3 summary
2. Two consecutive rounds with only L3 issues → fix then terminate, no further loops
3. More than 3 rounds with L1 or L2 still failing → terminate loop, show current screenshots and failing items to user, ask user whether to accept or provide direction for changes

## Do Not Self-Limit

- When VitePress dev server needs to be started, you must do it independently; skipping or waiting for the user is not allowed
- When screenshots are needed, you must call screenshot.py independently; claiming "unable to verify" is not allowed
