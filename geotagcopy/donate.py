"""Donation link helpers for packaged GeoTagCopy builds."""

from __future__ import annotations

import os
import sys
import webbrowser

try:
    from geotagcopy import _build_info
except ImportError:
    _BUILD_STRIPE_PAYMENT_LINK = ""
else:
    _BUILD_STRIPE_PAYMENT_LINK = getattr(_build_info, "STRIPE_PAYMENT_LINK", "")


STRIPE_PAYMENT_LINK = _BUILD_STRIPE_PAYMENT_LINK or os.environ.get(
    "GEOTAGCOPY_STRIPE_PAYMENT_LINK",
    "",
).strip()


def is_packaged() -> bool:
    return bool(getattr(sys, "frozen", False))


def should_show_donate() -> bool:
    if os.environ.get("GEOTAGCOPY_SHOW_DONATE") == "1":
        return True
    return is_packaged() and bool(STRIPE_PAYMENT_LINK)


def open_donate_page() -> None:
    if STRIPE_PAYMENT_LINK:
        webbrowser.open(STRIPE_PAYMENT_LINK)
