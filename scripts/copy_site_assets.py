#!/usr/bin/env python3
"""Copy generated app icons into the static site asset directory."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ICON_DIR = PROJECT_ROOT / "assets" / "icon"
SITE_ASSET_DIR = PROJECT_ROOT / "site" / "assets"
ASSETS = ["favicon.ico", "favicon-32.png", "icon.png"]


def main() -> int:
    SITE_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for name in ASSETS:
        source = SOURCE_ICON_DIR / name
        if not source.is_file():
            raise FileNotFoundError(f"Missing generated icon asset: {source}")
        shutil.copy2(source, SITE_ASSET_DIR / name)
        print(f"Copied {source} -> {SITE_ASSET_DIR / name}")
    _write_placeholder_screenshot()
    return 0


def _write_placeholder_screenshot() -> None:
    output = SITE_ASSET_DIR / "screenshot.png"
    if output.is_file():
        return

    image = Image.new("RGB", (1280, 720), "#0c1118")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((120, 96, 1160, 624), radius=36, fill="#141b25", outline="#273344", width=4)
    draw.text((180, 156), "GeoTagCopy screenshot placeholder", fill="#edf3fb")
    draw.text((180, 210), "Replace this with a real app screenshot before launch.", fill="#a8b4c4")
    draw.rounded_rectangle((180, 300, 520, 360), radius=16, fill="#1a6dcc")
    draw.rounded_rectangle((180, 390, 980, 430), radius=12, fill="#273344")
    draw.rounded_rectangle((180, 462, 860, 502), radius=12, fill="#273344")
    image.save(output)
    print(f"Wrote placeholder {output}")


if __name__ == "__main__":
    raise SystemExit(main())
