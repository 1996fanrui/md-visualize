---
model: sonnet
description: "Generate visual illustrations (PNG) or Vue component tags for Markdown articles or plain text."
argument-hint: "<markdown-file|text> [<output-dir>]"
---

## Prerequisites

Before running any script, execute `bash scripts/check_env.sh`. If any `[MISSING]` items appear, run `bash scripts/setup_env.sh` to auto-install what it can; remaining items require manual setup per the hints.

## Step 1: Input Parsing

Parse `$ARGUMENTS` to determine:

- **Entry point**: paragraph scan / data modification / screenshot / proofreading
- **Output mode**: screenshot illustration (default) / component tags
- **Output directory**: use the article's directory if it exists; otherwise the user must specify (never fabricate)
- **Processing scope**: all paragraphs / specified paragraphs / specified file

When the entry point is "screenshot", output mode is fixed to screenshot illustration. If the output directory or output mode cannot be inferred, ask the user via AskUserQuestion.

## Step 2: Paragraph Scan

> Skip this step when the entry point is "data modification", "screenshot", or "proofreading".

Evaluate each paragraph per `references/visualization-rules.md`. Skip paragraphs that already have images and whose content has not changed.

### Mermaid Code Blocks

**Always process with md_render_mermaid.py**, regardless of output mode:

```bash
uv run {{SKILL_DIR}}/scripts/md_render_mermaid.py <markdown-file>
```

The script auto-scans mermaid blocks → generates SVG + PNG into a sibling `images/` directory → replaces code blocks with `<img>` tags using relative paths. The mermaid path ends here — do not enter Vue component matching, screenshot parameter pre-check, or replacement self-check.

### Vue Component Matching for Other Paragraphs

1. Scan all `.vue` files under `{{SKILL_DIR}}/visual-components/components/`
2. Read only the `component` and `structure` fields from each file's header comment (skip notes/usage/body to save tokens)
3. Semantically match the current content to the best-fitting component `structure`
4. Partial match → create a variant based on the component, inform the user
5. No match → design a new Vue component from scratch, inform the user

When creating a variant or new component:
- Write the new component to `{{SKILL_DIR}}/visual-components/components/`
- Include `component` and `structure` fields in the header comment block
- Follow the component spec in `{{SKILL_DIR}}/visual-components/README.md`
- Verify it renders correctly via render.mjs in screenshot mode
- Once the user is satisfied, add it to the component library

Present matching results to the user and confirm before proceeding.

## ═══ Fork: Two Paths Based on Output Mode ═══

---

## [Screenshot Illustration Path]

### Step 4: Generate JSON Data + Render to HTML

#### Directory Structure

```
<output-dir>/
  ├─ images/
  │   ├─ data/xxx.json       ← AI-generated data file
  │   ├─ html/xxx.html       ← render.mjs output
  │   └─ xxx.png             ← screenshot.py output
```

#### Shared Styles

Screenshot mode uses `{{SKILL_DIR}}/visual-components/styles/ave-variables.css`, automatically referenced by render.mjs — no manual copying needed.

#### Generate or Modify

**Paragraph scan entry**: Step 2 only read `component`/`structure` from headers; now fully read the matched `.vue` file, extract `usage-json` from the header comment for JSON format, generate one JSON per paragraph into `images/data/` per `references/style-rules.md`, then call render.mjs.

**Data modification entry**: Edit the corresponding JSON in `images/data/`, re-run render.mjs.

**Proofreading entry**: Compare JSON against the latest content; only modify and re-run if there are substantive differences.

Run `references/check-json-data.md` self-check before calling render.mjs.

#### render.mjs Invocation

```bash
node {{SKILL_DIR}}/visual-components/scripts/render.mjs \
  --data images/data/xxx.json \
  --style {{SKILL_DIR}}/visual-components/styles/ave-variables.css \
  --output images/html/xxx.html
```

### Step 5: Screenshot

Determine the viewport for each HTML per `references/check-screenshot-params.md`. If it does not meet standards, adjust JSON/width first, then screenshot.

**Never write custom screenshot scripts or inline screenshot code. You must use:**

```bash
uv run {{SKILL_DIR}}/scripts/screenshot.py \
  <html-file> <output-png> [--width <viewport-width>]
```

After screenshotting, run visual acceptance per `references/check-visual-acceptance.md`.

### Step 6: Replace Original Text

Embed illustrations into the article. Keep JSON and HTML files in their directories.

**General format** (`article.md`):
- Generate an image-config block at the top of the file
- Replace visualized paragraphs with `<img>` tags
- Format: `<img src="./images/xxx.png" width="800" alt="content description">`
- Standard `width` tiers: full=800 / medium=600 / compact=400

```markdown
<!-- image-config
  hero: feature-cards.png, compare-table.png | width=800
  scenario: scenario-flow.png | width=750
  code: codeblock.png | width=600
-->
```

**Scope**: Only replace paragraphs processed in this run; leave everything else untouched.

After replacement, run `references/check-replaced-markdown.md` self-check; then run final visual acceptance per `references/check-visual-acceptance.md`.

Present to the user:
- List of generated images (filename + corresponding content)
- Output path for the article
- Prompt to review the results

---

## [Component Tag Path]

### Step 4: Write Vue Component Tags

**Paragraph scan entry**: Fully read the matched `.vue` file, extract `usage-markdown` from the header comment for slot syntax, apply colors per `references/style-rules.md`, and replace paragraphs.

**Data modification entry**: Directly edit text within component tags in the Markdown.

**Proofreading entry**: Compare tag text against the latest content; only modify if there are substantive differences.

After writing, run `references/check-component-tags.md` self-check; then run final visual acceptance per `references/check-visual-acceptance.md`.

### Steps 5 & 6

Skipped (Step 4 already completed the replacement).

---

Component usage details are maintained in each `.vue` file's header comment: use `usage-json` for screenshot mode, `usage-markdown` for component tag mode. Component specs are in `{{SKILL_DIR}}/visual-components/README.md`.
