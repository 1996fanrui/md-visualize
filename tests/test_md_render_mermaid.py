"""Unit tests for md_render_mermaid.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "md-visualize" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import md_render_mermaid


SAMPLE_MD = """\
# Test Document

Some text before.

```mermaid
graph LR
    A --> B --> C
```

Some text after.

```mermaid
graph TD
    X --> Y
```

Final text.
"""


class TestNewFilename:
    """Tests for new_filename."""

    def test_format(self):
        """new_filename produces mermaid-<8hex> format."""
        name = md_render_mermaid.new_filename()
        assert name.startswith("mermaid-")
        assert len(name) == len("mermaid-") + 8

    def test_unique(self):
        """new_filename produces unique names."""
        names = {md_render_mermaid.new_filename() for _ in range(100)}
        assert len(names) == 100


class TestNoGitHubUrls:
    """Verify that GitHub URL references have been removed."""

    def test_no_blogs_root(self):
        """Module should not reference BLOGS_ROOT."""
        assert not hasattr(md_render_mermaid, "BLOGS_ROOT")

    def test_no_github_raw(self):
        """Module should not reference GITHUB_RAW."""
        assert not hasattr(md_render_mermaid, "GITHUB_RAW")

    def test_no_github_url_func(self):
        """Module should not have github_url function."""
        assert not hasattr(md_render_mermaid, "github_url")


class TestImagesWrittenToImagesDir:
    """AT-R3M1: Mermaid blocks render to images/ with relative <img> paths."""

    def test_images_written_to_images_dir(self, tmp_path, monkeypatch):
        """Rendered images go to <md_dir>/images/ directory."""
        md_file = tmp_path / "test.md"
        md_file.write_text(SAMPLE_MD)

        render_calls = []

        def fake_render_block(mermaid_code, out_svg):
            out_svg.parent.mkdir(parents=True, exist_ok=True)
            out_svg.write_text("<svg></svg>")
            out_svg.with_suffix(".png").write_bytes(b"fake-png")
            render_calls.append(out_svg)

        monkeypatch.setattr(md_render_mermaid, "render_block", fake_render_block)
        md_render_mermaid.process(md_file, replace=True)

        images_dir = tmp_path / "images"
        assert images_dir.is_dir()
        assert len(render_calls) == 2
        for svg_path in render_calls:
            assert svg_path.parent == images_dir

    def test_img_tag_uses_relative_path(self, tmp_path, monkeypatch):
        """<img> tags use relative images/ path, not GitHub URLs."""
        md_file = tmp_path / "test.md"
        md_file.write_text(SAMPLE_MD)

        def fake_render_block(mermaid_code, out_svg):
            out_svg.parent.mkdir(parents=True, exist_ok=True)
            out_svg.write_text("<svg></svg>")
            out_svg.with_suffix(".png").write_bytes(b"fake-png")

        monkeypatch.setattr(md_render_mermaid, "render_block", fake_render_block)
        md_render_mermaid.process(md_file, replace=True)

        result = md_file.read_text()
        assert "githubusercontent.com" not in result
        assert "DaladaLee" not in result
        assert 'src="images/' in result


class TestNoReplaceMode:
    """AT-P7K2: --no-replace mode leaves markdown unchanged."""

    def test_no_replace_mode(self, tmp_path, monkeypatch):
        """With replace=False, markdown content stays byte-identical."""
        md_file = tmp_path / "test.md"
        md_file.write_text(SAMPLE_MD)
        original = md_file.read_text()

        def fake_render_block(mermaid_code, out_svg):
            out_svg.parent.mkdir(parents=True, exist_ok=True)
            out_svg.write_text("<svg></svg>")
            out_svg.with_suffix(".png").write_bytes(b"fake-png")

        monkeypatch.setattr(md_render_mermaid, "render_block", fake_render_block)
        md_render_mermaid.process(md_file, replace=False)

        assert md_file.read_text() == original
        images_dir = tmp_path / "images"
        assert images_dir.is_dir()
