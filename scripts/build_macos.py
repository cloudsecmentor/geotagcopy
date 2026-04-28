#!/usr/bin/env python3
"""Build macOS GeoTagCopy artifacts with PyInstaller."""

from __future__ import annotations

import argparse
import os
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
    PROJECT_ROOT,
    base_pyinstaller_command,
    download_file,
    pyinstaller_available,
    safe_extract_tar,
    verify_sha256,
    write_build_info,
)

BUNDLE_IDENTIFIER = "com.geotagcopy.app"
VENDORED_EXIFTOOL = PROJECT_ROOT / "vendor" / "exiftool"
DEFAULT_ENTITLEMENTS = PROJECT_ROOT / "packaging" / "macos" / "entitlements.plist"
EXIFTOOL_ARCHIVE_NAME = f"Image-ExifTool-{EXIFTOOL_VERSION}.tar.gz"
EXIFTOOL_ARCHIVE_URL = (
    f"https://sourceforge.net/projects/exiftool/files/{EXIFTOOL_ARCHIVE_NAME}/download"
)
EXIFTOOL_ARCHIVE_SHA256 = (
    "58f74f5cf84350693a00c4df236fd4810e5abaf25fab2d15eaa9dcc4872d4481"
)


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
    parser.add_argument(
        "--no-bundle-exiftool",
        action="store_true",
        help="Skip downloading and bundling ExifTool.",
    )
    parser.add_argument(
        "--codesign-identity",
        default=os.environ.get("MACOS_CODESIGN_IDENTITY", "").strip(),
        help="Developer ID Application identity for PyInstaller code signing.",
    )
    parser.add_argument(
        "--entitlements-file",
        default=os.environ.get("MACOS_ENTITLEMENTS_FILE", str(DEFAULT_ENTITLEMENTS)),
        help="Path to macOS entitlements plist used when signing.",
    )
    args = parser.parse_args()

    if platform.system() != "Darwin":
        print("This builder must run on macOS to produce macOS artifacts.", file=sys.stderr)
        return 2

    if not pyinstaller_available():
        print(
            "PyInstaller is not installed. Run: python3 -m pip install -r requirements-build.txt",
            file=sys.stderr,
        )
        return 2

    if not args.no_bundle_exiftool:
        _ensure_vendored_exiftool()

    write_build_info("scripts/build_macos.py")

    targets = ("app", "onefile") if args.target == "all" else (args.target,)
    for target in targets:
        _run_pyinstaller(
            target=target,
            clean=not args.no_clean,
            codesign_identity=args.codesign_identity,
            entitlements_file=args.entitlements_file,
        )

    _print_artifacts(targets)
    return 0


def _run_pyinstaller(
    target: str,
    clean: bool,
    codesign_identity: str = "",
    entitlements_file: str = "",
) -> None:
    cmd = base_pyinstaller_command()
    cmd.extend(["--osx-bundle-identifier", BUNDLE_IDENTIFIER])

    if codesign_identity:
        cmd.extend(["--codesign-identity", codesign_identity])
        entitlements = Path(entitlements_file).expanduser()
        if entitlements.is_file():
            cmd.extend(["--osx-entitlements-file", str(entitlements)])
        else:
            raise FileNotFoundError(f"Entitlements file not found: {entitlements}")

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


def _ensure_vendored_exiftool() -> None:
    if _has_vendored_exiftool() and (VENDORED_EXIFTOOL / "lib").is_dir():
        print(f"Using bundled ExifTool from {VENDORED_EXIFTOOL}")
        return

    print(f"Downloading ExifTool {EXIFTOOL_VERSION} for app bundling...")
    VENDORED_EXIFTOOL.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        archive_path = tmp_path / EXIFTOOL_ARCHIVE_NAME
        download_file(EXIFTOOL_ARCHIVE_URL, archive_path)
        verify_sha256(archive_path, EXIFTOOL_ARCHIVE_SHA256)

        extract_root = tmp_path / "extract"
        extract_root.mkdir()
        safe_extract_tar(archive_path, extract_root)

        source = extract_root / f"Image-ExifTool-{EXIFTOOL_VERSION}"
        if not (source / "exiftool").is_file() or not (source / "lib").is_dir():
            raise RuntimeError(f"Unexpected ExifTool archive layout in {source}")

        shutil.rmtree(VENDORED_EXIFTOOL, ignore_errors=True)
        VENDORED_EXIFTOOL.mkdir(parents=True)
        shutil.copy2(source / "exiftool", VENDORED_EXIFTOOL / "exiftool")
        shutil.copytree(source / "lib", VENDORED_EXIFTOOL / "lib")
        (VENDORED_EXIFTOOL / "exiftool").chmod(0o755)

    print(f"Vendored ExifTool installed at {VENDORED_EXIFTOOL}")


def _print_artifacts(targets: tuple[str, ...]) -> None:
    print("\nBuild complete.")
    if "app" in targets:
        print(f"- App bundle: {PROJECT_ROOT / 'dist' / (APP_NAME + '.app')}")
    if "onefile" in targets:
        print(f"- Single executable: {PROJECT_ROOT / 'dist' / APP_NAME}")


if __name__ == "__main__":
    raise SystemExit(main())
