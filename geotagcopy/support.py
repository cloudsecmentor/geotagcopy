"""Support-site link helpers for packaged GeoTagCopy builds."""

from __future__ import annotations

import os
import sys
import webbrowser

try:
    from geotagcopy import _build_info
except ImportError:
    _BUILD_SUPPORT_URL = ""
else:
    _BUILD_SUPPORT_URL = getattr(_build_info, "SUPPORT_URL", "")


SUPPORT_URL = _BUILD_SUPPORT_URL or os.environ.get(
    "GEOTAGCOPY_SUPPORT_URL",
    "",
).strip()


def is_packaged() -> bool:
    return bool(getattr(sys, "frozen", False))


def should_show_support() -> bool:
    if os.environ.get("GEOTAGCOPY_SHOW_SUPPORT") == "1":
        return True
    return is_packaged() and bool(SUPPORT_URL)


def open_support_page() -> None:
    if SUPPORT_URL:
        webbrowser.open(SUPPORT_URL)
