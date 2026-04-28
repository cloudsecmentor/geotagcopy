#!/usr/bin/env python3
"""Build Windows GeoTagCopy artifacts with PyInstaller."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _build_common import (
    APP_NAME,
    ENTRYPOINT,
    EXIFTOOL_VERSION,
    ICON_ICO,
    PROJECT_ROOT,
    base_pyinstaller_command,
    download_file,
    pyinstaller_available,
    safe_extract_zip,
    verify_sha256,
    write_build_info,
)


VENDORED_EXIFTOOL = PROJECT_ROOT / "vendor" / "exiftool-windows"
EXIFTOOL_ARCHIVE_NAME = f"exiftool-{EXIFTOOL_VERSION}_64.zip"
EXIFTOOL_ARCHIVE_URL = f"https://exiftool.org/{EXIFTOOL_ARCHIVE_NAME}"
EXIFTOOL_ARCHIVE_SHA256 = (
    "2e59d9de0cd520394e8f64b05592a1a1617991108f8c1c5074aec294ae548351"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build GeoTagCopy as a Windows app directory or one-file executable."
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
    parser.add_argument(
        "--no-bundle-exiftool",
        action="store_true",
        help="Skip downloading and bundling ExifTool.",
    )
    args = parser.parse_args()

    if platform.system() != "Windows":
        print("This builder must run on Windows to produce Windows artifacts.", file=sys.stderr)
        return 2

    if not pyinstaller_available():
        print(
            "PyInstaller is not installed. Run: python -m pip install -r requirements-build.txt",
            file=sys.stderr,
        )
        return 2

    if not ICON_ICO.is_file():
        print("Windows icon not found. Run: make icons", file=sys.stderr)
        return 2

    if not args.no_bundle_exiftool:
        _ensure_vendored_exiftool()

    write_build_info("scripts/build_windows.py")

    targets = ("app", "onefile") if args.target == "all" else (args.target,)
    for target in targets:
        _run_pyinstaller(target=target, clean=not args.no_clean)

    _print_artifacts(targets)
    return 0


def _run_pyinstaller(target: str, clean: bool) -> None:
    cmd = base_pyinstaller_command()
    cmd.extend(["--icon", str(ICON_ICO)])

    if clean:
        cmd.append("--clean")

    if _has_vendored_exiftool():
        cmd.extend(["--add-data", f"{VENDORED_EXIFTOOL};exiftool"])

    if target == "app":
        cmd.extend(["--windowed", "--onedir"])
    elif target == "onefile":
        cmd.extend(["--windowed", "--onefile"])
    else:
        raise ValueError(f"Unsupported target: {target}")

    cmd.append(str(ENTRYPOINT))

    print(f"Building {target} target...")
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)


def _has_vendored_exiftool() -> bool:
    return (
        (VENDORED_EXIFTOOL / "exiftool.exe").is_file()
        and (VENDORED_EXIFTOOL / "exiftool_files").is_dir()
    )


def _ensure_vendored_exiftool() -> None:
    if _has_vendored_exiftool():
        print(f"Using bundled ExifTool from {VENDORED_EXIFTOOL}")
        return

    print(f"Downloading ExifTool {EXIFTOOL_VERSION} for Windows app bundling...")
    VENDORED_EXIFTOOL.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive_path = tmp_path / EXIFTOOL_ARCHIVE_NAME
        download_file(EXIFTOOL_ARCHIVE_URL, archive_path)
        verify_sha256(archive_path, EXIFTOOL_ARCHIVE_SHA256)

        extract_root = tmp_path / "extract"
        extract_root.mkdir()
        safe_extract_zip(archive_path, extract_root)

        source = extract_root / f"exiftool-{EXIFTOOL_VERSION}_64"
        source_exe = source / "exiftool(-k).exe"
        source_files = source / "exiftool_files"
        if not source_exe.is_file() or not source_files.is_dir():
            raise RuntimeError(f"Unexpected ExifTool archive layout in {source}")

        shutil.rmtree(VENDORED_EXIFTOOL, ignore_errors=True)
        VENDORED_EXIFTOOL.mkdir(parents=True)
        shutil.copy2(source_exe, VENDORED_EXIFTOOL / "exiftool.exe")
        shutil.copytree(source_files, VENDORED_EXIFTOOL / "exiftool_files")

    print(f"Vendored ExifTool installed at {VENDORED_EXIFTOOL}")


def _print_artifacts(targets: tuple[str, ...]) -> None:
    print("\nBuild complete.")
    if "app" in targets:
        print(f"- App directory: {PROJECT_ROOT / 'dist' / APP_NAME}")
    if "onefile" in targets:
        print(f"- Single executable: {PROJECT_ROOT / 'dist' / (APP_NAME + '.exe')}")


if __name__ == "__main__":
    raise SystemExit(main())
