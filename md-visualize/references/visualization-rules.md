---
description: "Rules for identifying visualizable content from Markdown."
---

# Visualization Content Identification Rules

## Mermaid Code Blocks

When encountering a ` ```mermaid ` code block, **always** call `md_render_mermaid.py` to render and replace it with an `<img>` tag. Do not perform further structural analysis or enter the Vue component path.

**Exception**: Code blocks used solely as syntax examples (context clearly indicates "example code" rather than an actual diagram).

## Content Suitable for Visualization (Vue Component Path)

When the following types of structured information appear in Markdown, consider visualization (screenshot illustration or component tags):

- Parallel feature/capability lists
- Multi-option horizontal comparisons
- Decision dilemmas or choice contrasts
- Process/experience comparisons
- Multiple instances working in parallel
- Lifecycle/cyclic processes
- Code examples that benefit from enhanced visual presentation
- Nested hierarchy/boundary relationships
- Other information with clear structural patterns

Component matching is done by reading Vue component files under `{{SKILL_DIR}}/visual-components/components/`. See `{{SKILL_DIR}}/visual-components/README.md`.

## Content NOT Suitable for Image Replacement

- Narrative paragraphs (introductions, background descriptions, etc.)
- Code blocks (keep native Markdown rendering unless special visual effects are needed)
- Scenario stories (text narrative is more immersive than images)
- Single-line conclusions/summaries

## Semantic Understanding Requirements

- Different scenarios have different core relationships; choose a matching visual structure
- Multiple scenarios may use the same template, provided their core relationships are genuinely similar
- For new scenarios not in the template library, first understand the core relationship, then decide the layout
