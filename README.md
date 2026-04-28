# GeoTagCopy - GPS Tag Copy Utility

[![Release](https://img.shields.io/github/v/release/cloudsecmentor/geotagcopy)](https://github.com/cloudsecmentor/geotagcopy/releases)
[![CI](https://github.com/cloudsecmentor/geotagcopy/actions/workflows/release.yml/badge.svg)](https://github.com/cloudsecmentor/geotagcopy/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/cloudsecmentor/geotagcopy)](LICENSE)

Copy GPS coordinates from geotagged photos (e.g. iPhone) to untagged ones (e.g. Sony camera exports), matching by closest timestamp.

## Download

Get the latest release for your platform:

- **macOS**: [GeoTagCopy.app (zip)](https://github.com/cloudsecmentor/geotagcopy/releases/latest) or single executable
- **Windows**: [GeoTagCopy.exe (zip)](https://github.com/cloudsecmentor/geotagcopy/releases/latest) or single executable

See [Releases](https://github.com/cloudsecmentor/geotagcopy/releases) for all versions.

## Support the Project

GeoTagCopy is free and open source. If you find it useful, consider supporting
development through the [GeoTagCopy website](https://github.com/cloudsecmentor/geotagcopy).

## License

Licensed under the MIT License -- see `LICENSE`.

## Problem

Cameras like the Sony A6000 take great photos but lack GPS. Meanwhile, phones capture location with every shot. This tool bridges the gap by copying GPS tags from phone photos to camera photos based on when they were taken.

## How It Works

1. Point the app at two folders: one with **geotagged** photos (iPhone), one with **untagged** photos (camera)
2. The app reads EXIF metadata, matches each untagged file to the nearest-in-time tagged file with GPS
3. Results are grouped by GPS location so you can review at a glance
4. Select which files to tag, then apply -- GPS coordinates are written via ExifTool

## Requirements

- **Python 3.9+** with tkinter support
- **[ExifTool](https://exiftool.org/)** installed and on PATH when running from source
- **customtkinter** and **tkintermapview** (installed automatically via requirements.txt)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Usage

Launch the GUI:

```bash
python -m geotagcopy
```

Or pre-fill folder paths:

```bash
python -m geotagcopy \
  -t "/path/to/tagged/photos" \
  -u "/path/to/untagged/photos"
```

## Building from Source

GeoTagCopy can be packaged with PyInstaller on macOS and Windows. Packaged
builds bundle ExifTool so end users do not need a separate installation.

```bash
make build-deps      # install build dependencies
make build-macos     # macOS: dist/GeoTagCopy.app + dist/GeoTagCopy
make build-windows   # Windows: dist\GeoTagCopy\ + dist\GeoTagCopy.exe
```

See `CONTRIBUTING.md` for full setup, testing, and build instructions.

## GitHub Releases

The repository includes a GitHub Actions workflow that builds release
artifacts and publishes them to a GitHub Release.

Create a release by pushing a version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Or run **Build and Release** manually from the GitHub Actions tab and enter a
version such as `v0.1.0`.

Each release uploads:

- `GeoTagCopy-<version>-macos-app.zip`: draggable `GeoTagCopy.app`
- `GeoTagCopy-<version>-macos-onefile.zip`: single macOS executable
- `GeoTagCopy-<version>-windows-app.zip`: Windows app directory
- `GeoTagCopy-<version>-windows-onefile.zip`: single Windows executable

When `AZURE_STORAGE_ACCOUNT` is configured, the workflow also updates
`latest.json` on the website so download links reflect the new release.

### Running Tests

```bash
make test
```

## What Gets Written

For each file that receives GPS tags, the tool:
- Writes `XMP:GPSLatitude`, `XMP:GPSLongitude`, and `XMP:GPSAltitude`
- Sets `Label=GPSCopy` so you can filter these files later
- Adds a `Comment` noting which file the GPS was copied from

## Legacy Pipeline

The original 3-step pipeline is preserved under `src/`, now with Python-only export, matching, and Tkinter review steps.

## Similar Projects

- [pybatchgeotag](https://github.com/nperony/pybatchgeotag/blob/master/pybatchgeotag.py)
- [media_geotag_mapper](https://github.com/kburchfiel/media_geotag_mapper)
- [geotagger (PyPI)](https://pypi.org/project/geotagger/)
- [ExifTool](https://exiftool.org/)

