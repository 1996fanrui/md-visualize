#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright", "Pillow"]
# ///
"""Take a PNG screenshot of an HTML file or directory.

Usage:
    uv run screenshot.py <html-or-dir> <output-png> [--width N] [--selector CSS]
"""
#
# If the first argument is a file, it is opened via file:// (suitable for
# standalone HTML that does not rely on JS modules).
# If it is a directory, a transient HTTP server is started on that directory
# and the browser loads http://127.0.0.1:<port>/index.html — required for
# VitePress build artifacts which load ES module chunks that file:// blocks.
# With --selector, only the matching element is captured.
# Requires: playwright + Pillow (declared via PEP 723; run with uv run)

import argparse
import http.server
import socketserver
import sys
import threading
from contextlib import contextmanager
from functools import partial
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

PADDING = 5
DEVICE_SCALE = 3


@contextmanager
def _serve(directory: Path):
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    # Silence default access logs.
    handler.log_message = lambda *a, **k: None  # type: ignore[attr-defined]
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield port
        finally:
            httpd.shutdown()


def screenshot(target: str, output_path: str, viewport_width: int = 1400, selector: str | None = None) -> None:
    target_path = Path(target).resolve()
    if not target_path.exists():
        print(f"Error: {target_path} does not exist", file=sys.stderr)
        sys.exit(1)

    physical_padding = PADDING * DEVICE_SCALE

    if target_path.is_dir():
        index_html = target_path / "index.html"
        if not index_html.exists():
            print(f"Error: directory has no index.html: {target_path}", file=sys.stderr)
            sys.exit(1)
        serve_ctx = _serve(target_path)
    else:
        serve_ctx = None

    def _run(url: str) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": viewport_width, "height": 2000},
                device_scale_factor=DEVICE_SCALE,
            )
            page.goto(url)
            page.wait_for_load_state("networkidle")

            if selector:
                page.wait_for_selector(f"{selector} svg", state="attached", timeout=20000)
                page.add_style_tag(content="html,body{background:transparent !important;}")
                element = page.query_selector(selector)
                if element is None:
                    browser.close()
                    print(f"Error: selector not found: {selector}", file=sys.stderr)
                    sys.exit(1)
                element.screenshot(path=output_path, omit_background=True)
            else:
                page.screenshot(path=output_path, omit_background=True, full_page=True)
            browser.close()

    if serve_ctx is not None:
        with serve_ctx as port:
            _run(f"http://127.0.0.1:{port}/index.html")
    else:
        _run(f"file://{target_path}")

    img = Image.open(output_path)
    alpha = img.split()[-1]
    bbox = alpha.getbbox()
    if bbox is None:
        print("Warning: image is fully transparent, skipping trim", file=sys.stderr)
        return

    left, top, right, bottom = bbox
    crop_left = max(0, left - physical_padding)
    crop_top = max(0, top - physical_padding)
    crop_right = min(img.width, right + physical_padding)
    crop_bottom = min(img.height, bottom + physical_padding)

    img.crop((crop_left, crop_top, crop_right, crop_bottom)).save(output_path)
    print(f"Screenshot saved: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Screenshot HTML (or VitePress build dir) to PNG")
    parser.add_argument("target", help="HTML file, or directory containing index.html + assets/")
    parser.add_argument("output_png", help="Output PNG path")
    parser.add_argument("--width", type=int, default=1400, help="Viewport width (default: 1400)")
    parser.add_argument("--selector", help="CSS selector; if set, only screenshot that element")
    args = parser.parse_args()
    screenshot(args.target, args.output_png, args.width, args.selector)


if __name__ == "__main__":
    main()
