#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["Pillow", "lxml"]
# ///
"""Process every mermaid code block in a single markdown file.

Usage:
    uv run md_render_mermaid.py <md-file> [--no-replace]

Default behavior (production):
    1. For each ```mermaid ... ``` code block, render an SVG + PNG into
       <md_dir>/images/mermaid-<uuid>.{svg,png}.
    2. Replace the code block in the markdown with an <img> tag pointing at
       the relative image path.

With --no-replace (developer mode):
    Only render the images. Leave the markdown untouched.

Requires render_mermaid.py next to this script, plus its dependencies (mmdc,
chrome-headless-shell, lxml, Pillow).
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import render_mermaid  # type: ignore[import-not-found]  # local module

IMG_STYLE = "max-width: 600px; width: 100%; display: block; margin: 0 auto;"

MERMAID_BLOCK = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)


def new_filename() -> str:
    return f"mermaid-{uuid.uuid4().hex[:8]}"


def render_block(mermaid_code: str, out_svg: Path) -> None:
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as f:
        f.write(mermaid_code)
        tmp_path = Path(f.name)
    try:
        render_mermaid.render(tmp_path, out_svg)
    finally:
        tmp_path.unlink(missing_ok=True)


def process(md_path: Path, replace: bool) -> None:
    text = md_path.read_text(encoding="utf-8")
    images_dir = md_path.parent / "images"
    pieces: list[str] = []
    cursor = 0
    n = 0

    for m in MERMAID_BLOCK.finditer(text):
        if replace:
            pieces.append(text[cursor:m.start()])
        code = m.group(1).rstrip()
        n += 1

        name = new_filename()
        out_svg = images_dir / f"{name}.svg"
        render_block(code, out_svg)

        if replace:
            pieces.append(f'<img style="{IMG_STYLE}" src="images/{name}.png">')
            cursor = m.end()
        print(f"[{n}] {name}")

    if replace:
        pieces.append(text[cursor:])
        md_path.write_text("".join(pieces), encoding="utf-8")
        print(f"Done: {n} block(s) processed and replaced in {md_path}")
    else:
        print(f"Done: {n} block(s) rendered (markdown unchanged: --no-replace)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render mermaid blocks in a markdown file to SVG/PNG and (by default) replace them with <img>."
    )
    parser.add_argument("markdown", type=Path, help="markdown file to process")
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="developer mode: render images only, do not modify the markdown",
    )
    args = parser.parse_args()
    process(args.markdown.resolve(), replace=not args.no_replace)


if __name__ == "__main__":
    main()
