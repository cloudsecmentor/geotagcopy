#!/usr/bin/env python3
"""Generate GeoTagCopy app and website icons from a Pillow drawing."""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = PROJECT_ROOT / "assets" / "icon"
MASTER_PNG = ICON_DIR / "icon.png"
MACOS_ICNS = ICON_DIR / "icon.icns"
WINDOWS_ICO = ICON_DIR / "icon.ico"
FAVICON_ICO = ICON_DIR / "favicon.ico"
FAVICON_32 = ICON_DIR / "favicon-32.png"

MASTER_SIZE = 1024
ACCENT = "#1a6dcc"
ACCENT_DARK = "#145aa8"
WHITE = "#ffffff"


def main() -> int:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    master = _draw_master_icon()
    master.save(MASTER_PNG)

    _save_windows_icon(master)
    _save_favicons(master)
    _save_macos_icon(master)

    print(f"Wrote {MASTER_PNG}")
    print(f"Wrote {MACOS_ICNS}")
    print(f"Wrote {WINDOWS_ICO}")
    print(f"Wrote {FAVICON_ICO}")
    print(f"Wrote {FAVICON_32}")
    return 0


def _draw_master_icon() -> Image.Image:
    scale = 4
    size = MASTER_SIZE * scale
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def xy(values: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(v * scale for v in values)

    draw.rounded_rectangle(
        xy((64, 64, 960, 960)),
        radius=196 * scale,
        fill=ACCENT,
    )

    draw.rounded_rectangle(
        xy((108, 108, 916, 916)),
        radius=168 * scale,
        outline="#5da4f0",
        width=10 * scale,
    )

    # Map pin.
    draw.ellipse(xy((300, 164, 724, 588)), fill=WHITE)
    draw.polygon(
        [xy((512, 854))[0:2], xy((334, 472))[0:2], xy((690, 472))[0:2]],
        fill=WHITE,
    )
    draw.ellipse(xy((410, 276, 614, 480)), fill=ACCENT)

    # Copy glyph, offset like a stacked duplicate card.
    draw.rounded_rectangle(
        xy((604, 614, 820, 802)),
        radius=34 * scale,
        fill="#dcecff",
        outline=ACCENT_DARK,
        width=18 * scale,
    )
    draw.rounded_rectangle(
        xy((690, 690, 884, 870)),
        radius=34 * scale,
        fill=WHITE,
        outline=ACCENT_DARK,
        width=18 * scale,
    )
    draw.line(xy((732, 748, 840, 748)), fill=ACCENT_DARK, width=16 * scale)
    draw.line(xy((732, 806, 820, 806)), fill=ACCENT_DARK, width=16 * scale)

    return image.resize((MASTER_SIZE, MASTER_SIZE), Image.Resampling.LANCZOS)


def _save_windows_icon(master: Image.Image) -> None:
    master.save(
        WINDOWS_ICO,
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def _save_favicons(master: Image.Image) -> None:
    master.resize((32, 32), Image.Resampling.LANCZOS).save(FAVICON_32)
    master.save(FAVICON_ICO, sizes=[(16, 16), (32, 32), (48, 48)])


def _save_macos_icon(master: Image.Image) -> None:
    iconutil = shutil.which("iconutil")
    if platform.system() == "Darwin" and iconutil:
        _save_macos_icon_with_iconutil(master, iconutil)
        return

    try:
        master.save(
            MACOS_ICNS,
            sizes=[
                (16, 16),
                (32, 32),
                (64, 64),
                (128, 128),
                (256, 256),
                (512, 512),
                (1024, 1024),
            ],
        )
    except OSError as exc:
        raise RuntimeError(
            "Could not generate icon.icns. Run this script on macOS with iconutil."
        ) from exc


def _save_macos_icon_with_iconutil(master: Image.Image, iconutil: str) -> None:
    iconset_sizes = [
        (16, 1),
        (16, 2),
        (32, 1),
        (32, 2),
        (128, 1),
        (128, 2),
        (256, 1),
        (256, 2),
        (512, 1),
        (512, 2),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "GeoTagCopy.iconset"
        iconset.mkdir()

        for base_size, scale in iconset_sizes:
            pixel_size = base_size * scale
            suffix = "" if scale == 1 else "@2x"
            output = iconset / f"icon_{base_size}x{base_size}{suffix}.png"
            master.resize((pixel_size, pixel_size), Image.Resampling.LANCZOS).save(output)

        subprocess.run(
            [iconutil, "-c", "icns", str(iconset), "-o", str(MACOS_ICNS)],
            check=True,
        )


if __name__ == "__main__":
    raise SystemExit(main())
