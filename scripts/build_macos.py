#!/usr/bin/env python3
"""Build macOS GeoTagCopy artifacts with PyInstaller."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "GeoTagCopy"
BUNDLE_IDENTIFIER = "com.geotagcopy.app"
ENTRYPOINT = PROJECT_ROOT / "geotagcopy" / "__main__.py"
VENDORED_EXIFTOOL = PROJECT_ROOT / "vendor" / "exiftool"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build GeoTagCopy as a macOS .app bundle or one-file executable."
    )
    parser.add_argument(
        "--target",
        choices=("app", "onefile", "all"),
        default="app",
        help="Build target. Default: app",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Keep PyInstaller caches between builds.",
    )
    args = parser.parse_args()

    if platform.system() != "Darwin":
        print("This builder must run on macOS to produce macOS artifacts.", file=sys.stderr)
        return 2

    if not _pyinstaller_available():
        print(
            "PyInstaller is not installed. Run: python3 -m pip install -r requirements-build.txt",
            file=sys.stderr,
        )
        return 2

    targets = ("app", "onefile") if args.target == "all" else (args.target,)
    for target in targets:
        _run_pyinstaller(target=target, clean=not args.no_clean)

    _print_artifacts(targets)
    return 0


def _pyinstaller_available() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _run_pyinstaller(target: str, clean: bool) -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        APP_NAME,
        "--osx-bundle-identifier",
        BUNDLE_IDENTIFIER,
        "--collect-data",
        "customtkinter",
        "--collect-data",
        "imageio_ffmpeg",
        "--collect-submodules",
        "pillow_heif",
        "--hidden-import",
        "PIL._tkinter_finder",
    ]

    if clean:
        cmd.append("--clean")

    if _has_vendored_exiftool():
        cmd.extend(["--add-data", f"{VENDORED_EXIFTOOL}:exiftool"])

    if target == "app":
        cmd.extend(["--windowed", "--onedir"])
    elif target == "onefile":
        cmd.append("--onefile")
    else:
        raise ValueError(f"Unsupported target: {target}")

    cmd.append(str(ENTRYPOINT))

    print(f"Building {target} target...")
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def _has_vendored_exiftool() -> bool:
    return (VENDORED_EXIFTOOL / "exiftool").is_file()


def _print_artifacts(targets: tuple[str, ...]) -> None:
    print("\nBuild complete.")
    if "app" in targets:
        print(f"- App bundle: {PROJECT_ROOT / 'dist' / (APP_NAME + '.app')}")
    if "onefile" in targets:
        print(f"- Single executable: {PROJECT_ROOT / 'dist' / APP_NAME}")


if __name__ == "__main__":
    raise SystemExit(main())
