"""Tests for support-site link visibility."""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch


class TestSupportVisibility(unittest.TestCase):
    @contextmanager
    def _support_module(
        self,
        *,
        frozen: bool,
        url: str = "",
        show_support: str = "",
    ):
        env = {}
        if url:
            env["GEOTAGCOPY_SUPPORT_URL"] = url
        if show_support:
            env["GEOTAGCOPY_SHOW_SUPPORT"] = show_support

        had_frozen = hasattr(sys, "frozen")
        original_frozen = getattr(sys, "frozen", None)

        with patch.dict(os.environ, env, clear=True):
            if frozen:
                sys.frozen = True
            elif hasattr(sys, "frozen"):
                delattr(sys, "frozen")

            sys.modules.pop("geotagcopy.support", None)
            support = importlib.import_module("geotagcopy.support")

            try:
                yield support
            finally:
                sys.modules.pop("geotagcopy.support", None)
                if had_frozen:
                    sys.frozen = original_frozen
                elif hasattr(sys, "frozen"):
                    delattr(sys, "frozen")

    def test_source_without_url_hides_support(self):
        with self._support_module(frozen=False) as support:
            self.assertFalse(support.should_show_support())

    def test_source_with_url_hides_support_by_default(self):
        with self._support_module(
            frozen=False,
            url="https://example.com/support",
        ) as support:
            self.assertFalse(support.should_show_support())

    def test_packaged_without_url_hides_support(self):
        with self._support_module(frozen=True) as support:
            self.assertFalse(support.should_show_support())

    def test_packaged_with_url_shows_support(self):
        with self._support_module(
            frozen=True,
            url="https://example.com/support",
        ) as support:
            self.assertTrue(support.should_show_support())

    def test_development_override_shows_support(self):
        with self._support_module(
            frozen=False,
            show_support="1",
        ) as support:
            self.assertTrue(support.should_show_support())

    def test_open_support_page_uses_configured_url(self):
        with self._support_module(
            frozen=True,
            url="https://example.com/support",
        ) as support:
            with patch("webbrowser.open") as open_browser:
                support.open_support_page()

        open_browser.assert_called_once_with("https://example.com/support")


if __name__ == "__main__":
    unittest.main()
