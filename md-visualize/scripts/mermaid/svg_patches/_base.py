"""Pure-function interface for SVG patches.

Each patch module exposes:
    NAME: str                     # short identifier, shown in logs/tests
    match(mmd: str, svg: str) -> bool
    apply(mmd: str, svg: str) -> str

match() decides whether this patch wants to touch the current diagram based
on the mermaid source and the current SVG. apply() returns the new SVG text;
callers ignore a patch's output when match() returned False.

Patches never read from or write to disk. The main pipeline handles IO.
"""

from __future__ import annotations

from typing import Protocol


class SvgPatch(Protocol):
    NAME: str

    def match(self, mmd: str, svg: str) -> bool: ...
    def apply(self, mmd: str, svg: str) -> str: ...
