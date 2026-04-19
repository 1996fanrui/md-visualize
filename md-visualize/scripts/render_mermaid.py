#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["Pillow", "lxml"]
# ///
"""Render a single mermaid diagram into SVG and PNG.

Usage:
    uv run render_mermaid.py <input.mmd> <output.svg>

Produces <output>.svg and <output>.png. If any patch in mermaid/svg_patches/
modifies the SVG, also keeps <output>.raw.svg as the unmodified mmdc
baseline for comparison (otherwise the snapshot is removed).

Pipeline:
    1. mmdc renders the mermaid source to <output>.svg
    2. Snapshot the raw output to <output>.raw.svg
    3. Discover svg_patches/<name>.py modules in sorted order. For each, if
       match(mmd, svg) returns True, apply(mmd, svg) replaces the SVG text.
    4. Drop the snapshot if no patch modified anything.
    5. Rasterize the final SVG to PNG via chrome-headless-shell, then trim
       transparent margins.

Requires globally installed `mmdc` (npm i -g @mermaid-js/mermaid-cli).
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

SCRIPT_DIR = Path(__file__).resolve().parent
MM_DIR = SCRIPT_DIR / "mermaid"
PATCHES_DIR = MM_DIR / "svg_patches"
def _resolve_chrome() -> Path:
    """Locate puppeteer's chrome-headless-shell binary across mac/linux caches."""
    cache_roots = [
        Path.home() / ".cache" / "puppeteer" / "chrome-headless-shell",
        Path.home() / "Library" / "Caches" / "Puppeteer" / "chrome-headless-shell",
    ]
    for root in cache_roots:
        if not root.is_dir():
            continue
        matches = sorted(root.glob("*/chrome-headless-shell-*/chrome-headless-shell"))
        if matches:
            return matches[-1]
    raise FileNotFoundError(
        "chrome-headless-shell not found. Run scripts/setup_env.sh to install."
    )


def _load_patches() -> list[ModuleType]:
    """Load every svg_patches/<name>.py whose name does not start with `_`."""
    patches: list[ModuleType] = []
    for path in sorted(PATCHES_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(
            f"svg_patches.{path.stem}", path
        )
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        patches.append(mod)
    return patches


def _run_mmdc(input_mmd: Path, output_svg: Path) -> None:
    cmd = [
        "mmdc",
        "-i", str(input_mmd),
        "-o", str(output_svg),
        "-c", str(MM_DIR / "config.json"),
        "--cssFile", str(MM_DIR / "extra.css"),
        "-p", str(MM_DIR / "puppeteer.json"),
        "-b", "transparent",
        "-s", "3",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def _rasterize(svg_path: Path, png_path: Path) -> None:
    """Render the SVG via chrome-headless-shell, then trim transparent margins."""
    chrome = _resolve_chrome()
    html = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<style>html,body{margin:0;padding:0;background:transparent;}'
        'svg{display:block;}</style></head><body>'
        + svg_path.read_text(encoding="utf-8")
        + "</body></html>"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        html_path = Path(f.name)
    try:
        subprocess.run(
            [
                str(chrome),
                "--headless", "--no-sandbox", "--disable-gpu",
                "--hide-scrollbars",
                "--default-background-color=00000000",
                "--force-device-scale-factor=3",
                f"--screenshot={png_path}",
                "--window-size=2400,2400",
                f"file://{html_path}",
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    finally:
        html_path.unlink(missing_ok=True)

    # Trim transparent margins.
    from PIL import Image
    img = Image.open(png_path).convert("RGBA")
    bbox = img.split()[-1].getbbox()
    if not bbox:
        return
    pad = 30
    l, t, r, b = bbox
    l = max(0, l - pad); t = max(0, t - pad)
    r = min(img.width, r + pad); b = min(img.height, b + pad)
    img.crop((l, t, r, b)).save(png_path)


def render(input_mmd: Path, output_svg: Path) -> tuple[Path, Path | None, Path]:
    """Render input.mmd -> (svg_path, raw_svg_path or None, png_path)."""
    if output_svg.suffix != ".svg":
        raise ValueError(f"Output must end in .svg (got: {output_svg})")

    output_png = output_svg.with_suffix(".png")
    output_raw = output_svg.with_suffix(".raw.svg")

    _run_mmdc(input_mmd, output_svg)
    raw_text = output_svg.read_text(encoding="utf-8")
    output_raw.write_text(raw_text, encoding="utf-8")

    mmd_text = input_mmd.read_text(encoding="utf-8")
    svg_text = raw_text
    structural_change = False
    for patch in _load_patches():
        if not patch.match(mmd_text, svg_text):
            continue
        svg_text = patch.apply(mmd_text, svg_text)
        # edge_stroke is a stylistic touch-up that doesn't justify keeping a
        # raw baseline; only structural patches do.
        if getattr(patch, "NAME", "") != "edge_stroke":
            structural_change = True

    if svg_text != raw_text:
        output_svg.write_text(svg_text, encoding="utf-8")
    if not structural_change:
        output_raw.unlink(missing_ok=True)

    _rasterize(output_svg, output_png)

    return output_svg, output_raw if output_raw.exists() else None, output_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a mermaid diagram to SVG + PNG")
    parser.add_argument("input", type=Path, help="input .mmd file")
    parser.add_argument("output", type=Path, help="output .svg file")
    args = parser.parse_args()

    svg, raw, png = render(args.input, args.output)
    print(f"SVG: {svg}")
    if raw is not None:
        print(f"RAW: {raw}")
    print(f"PNG: {png}")


if __name__ == "__main__":
    main()
