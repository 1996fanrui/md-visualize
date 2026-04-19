"""Inject stroke-width on mermaid flowchart edges.

mmdc serializes SVG without baking CSS-only properties into attributes, so
the stroke-width rule from extra.css never makes it into the file. This
patch adds `stroke-width:2px` inline on every edge <path> that lacks one.

Node rounded corners (rx/ry) are already baked in by mermaid itself, so this
patch only handles stroke width.
"""

from __future__ import annotations

import re

NAME = "edge_stroke"
EDGE_WIDTH = "2"

_EDGE_RE = re.compile(
    r'<path\b[^>]*\bclass="[^"]*\bflowchart-link\b[^"]*"[^>]*>'
)


def match(mmd: str, svg: str) -> bool:
    for m in _EDGE_RE.finditer(svg):
        if "stroke-width" not in m.group(0):
            return True
    return False


def apply(mmd: str, svg: str) -> str:
    def _inject(m: re.Match) -> str:
        tag = m.group(0)
        if "stroke-width" in tag:
            return tag
        if 'style="' in tag:
            return tag.replace(
                'style="', f'style="stroke-width:{EDGE_WIDTH}px;', 1
            )
        return tag[:-1] + f' stroke-width="{EDGE_WIDTH}">'

    return _EDGE_RE.sub(_inject, svg)
