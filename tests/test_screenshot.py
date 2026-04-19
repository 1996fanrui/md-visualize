"""Unit tests for screenshot.py."""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

# Stub out heavy third-party deps before importing the module under test.
_pw_mod = ModuleType("playwright")
_pw_sync = ModuleType("playwright.sync_api")
_pw_sync.sync_playwright = MagicMock()  # type: ignore[attr-defined]
sys.modules.setdefault("playwright", _pw_mod)
sys.modules.setdefault("playwright.sync_api", _pw_sync)

_pil_mod = ModuleType("PIL")
_pil_image = ModuleType("PIL.Image")
_pil_image.Image = MagicMock()  # type: ignore[attr-defined]
sys.modules.setdefault("PIL", _pil_mod)
sys.modules.setdefault("PIL.Image", _pil_image)

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "md-visualize" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import screenshot


class TestServe:
    """Tests for the _serve context manager."""

    def test_serve_starts_server(self, tmp_path):
        """_serve starts an HTTP server on a free port."""
        index = tmp_path / "index.html"
        index.write_text("<html><body>test</body></html>")
        with screenshot._serve(tmp_path) as port:
            assert isinstance(port, int)
            assert port > 0


class TestScreenshot:
    """Tests for the screenshot function."""

    def test_target_not_found(self, tmp_path):
        """screenshot() exits when target doesn't exist."""
        with pytest.raises(SystemExit):
            screenshot.screenshot(
                str(tmp_path / "nonexistent.html"),
                str(tmp_path / "out.png"),
            )

    def test_directory_without_index(self, tmp_path):
        """screenshot() exits when directory has no index.html."""
        with pytest.raises(SystemExit):
            screenshot.screenshot(
                str(tmp_path),
                str(tmp_path / "out.png"),
            )

    def test_screenshot_file_target(self, tmp_path):
        """screenshot() with file target calls playwright correctly."""
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body><h1>Test</h1></body></html>")
        output_png = tmp_path / "output.png"

        # Create a mock for PIL Image
        mock_img = MagicMock()
        mock_img.split.return_value = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]
        mock_img.split.return_value[-1].getbbox.return_value = (10, 10, 100, 100)
        mock_img.width = 200
        mock_img.height = 200
        mock_img.crop.return_value = mock_img

        # Mock playwright
        mock_page = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_chromium = MagicMock()
        mock_chromium.launch.return_value = mock_browser
        mock_pw = MagicMock()
        mock_pw.chromium = mock_chromium

        mock_pw_ctx = MagicMock()
        mock_pw_ctx.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw_ctx.__exit__ = MagicMock(return_value=False)

        # Write a fake PNG so Image.open works
        output_png.write_bytes(b"fake")

        with (
            patch("screenshot.sync_playwright", return_value=mock_pw_ctx),
            patch("screenshot.Image") as mock_image_mod,
        ):
            mock_image_mod.open.return_value = mock_img
            screenshot.screenshot(str(html_file), str(output_png))

        mock_page.goto.assert_called_once()
        mock_page.screenshot.assert_called_once()
