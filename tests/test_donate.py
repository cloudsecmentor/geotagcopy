"""Tests for donation link visibility."""

from __future__ import annotations

import importlib
import os
import sys
import unittest
from contextlib import contextmanager
from unittest.mock import patch


class TestDonateVisibility(unittest.TestCase):
    @contextmanager
    def _donate_module(
        self,
        *,
        frozen: bool,
        link: str = "",
        show_donate: str = "",
    ):
        env = {}
        if link:
            env["GEOTAGCOPY_STRIPE_PAYMENT_LINK"] = link
        if show_donate:
            env["GEOTAGCOPY_SHOW_DONATE"] = show_donate

        had_frozen = hasattr(sys, "frozen")
        original_frozen = getattr(sys, "frozen", None)

        with patch.dict(os.environ, env, clear=True):
            if frozen:
                sys.frozen = True
            elif hasattr(sys, "frozen"):
                delattr(sys, "frozen")

            sys.modules.pop("geotagcopy.donate", None)
            donate = importlib.import_module("geotagcopy.donate")

            try:
                yield donate
            finally:
                sys.modules.pop("geotagcopy.donate", None)
                if had_frozen:
                    sys.frozen = original_frozen
                elif hasattr(sys, "frozen"):
                    delattr(sys, "frozen")

    def test_source_without_link_hides_donate(self):
        with self._donate_module(frozen=False) as donate:
            self.assertFalse(donate.should_show_donate())

    def test_source_with_link_hides_donate_by_default(self):
        with self._donate_module(
            frozen=False,
            link="https://example.com/donate",
        ) as donate:
            self.assertFalse(donate.should_show_donate())

    def test_packaged_without_link_hides_donate(self):
        with self._donate_module(frozen=True) as donate:
            self.assertFalse(donate.should_show_donate())

    def test_packaged_with_link_shows_donate(self):
        with self._donate_module(
            frozen=True,
            link="https://example.com/donate",
        ) as donate:
            self.assertTrue(donate.should_show_donate())

    def test_development_override_shows_donate(self):
        with self._donate_module(
            frozen=False,
            show_donate="1",
        ) as donate:
            self.assertTrue(donate.should_show_donate())

    def test_open_donate_page_uses_configured_link(self):
        with self._donate_module(
            frozen=True,
            link="https://example.com/donate",
        ) as donate:
            with patch("webbrowser.open") as open_browser:
                donate.open_donate_page()

        open_browser.assert_called_once_with("https://example.com/donate")


if __name__ == "__main__":
    unittest.main()
