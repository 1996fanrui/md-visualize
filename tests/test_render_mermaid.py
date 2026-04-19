"""Unit tests for render_mermaid.py."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the scripts directory to sys.path so we can import the module
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "md-visualize" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import render_mermaid


class TestResolveChrome:
    """Tests for _resolve_chrome."""

    def test_raises_when_not_found(self, tmp_path, monkeypatch):
        """_resolve_chrome raises FileNotFoundError when no chrome binary exists."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        with pytest.raises(FileNotFoundError, match="chrome-headless-shell not found"):
            render_mermaid._resolve_chrome()


class TestLoadPatches:
    """Tests for _load_patches."""

    def test_loads_patch_modules(self):
        """_load_patches discovers edge_stroke and snake_layout."""
        patches = render_mermaid._load_patches()
        names = [getattr(p, "NAME", None) for p in patches]
        assert "edge_stroke" in names
        assert "snake_layout" in names

    def test_patches_have_interface(self):
        """Each patch has NAME, match(), and apply()."""
        patches = render_mermaid._load_patches()
        for p in patches:
            assert hasattr(p, "NAME"), f"Patch {p} missing NAME"
            assert callable(getattr(p, "match", None)), f"Patch {p} missing match()"
            assert callable(getattr(p, "apply", None)), f"Patch {p} missing apply()"

    def test_skips_underscore_files(self):
        """_load_patches skips files starting with _ (like _base.py)."""
        patches = render_mermaid._load_patches()
        for p in patches:
            assert not Path(p.__file__).name.startswith("_")


class TestRender:
    """Tests for the render() function."""

    def test_output_must_be_svg(self, tmp_path):
        """render() raises ValueError if output doesn't end in .svg."""
        with pytest.raises(ValueError, match="must end in .svg"):
            render_mermaid.render(tmp_path / "test.mmd", tmp_path / "test.png")

    def test_render_produces_files(self, tmp_path, monkeypatch):
        """render() produces SVG and PNG files with mocked external tools."""
        input_mmd = tmp_path / "test.mmd"
        input_mmd.write_text("graph LR\n    A --> B\n")
        output_svg = tmp_path / "output.svg"

        def fake_mmdc(input_path, output_path):
            output_path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><text>A</text></svg>'
            )

        def fake_rasterize(svg_path, png_path):
            png_path.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
                b"\r\n\xb4\x00"
                b"\x00\x00\x00\x00IEND\xaeB`\x82"
            )

        monkeypatch.setattr(render_mermaid, "_run_mmdc", fake_mmdc)
        monkeypatch.setattr(render_mermaid, "_rasterize", fake_rasterize)

        svg, raw, png = render_mermaid.render(input_mmd, output_svg)

        assert svg.exists()
        assert png.exists()
        assert svg.suffix == ".svg"
        assert png.suffix == ".png"
