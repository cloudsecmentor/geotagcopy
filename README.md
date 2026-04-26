# GeoTagCopy - GPS Tag Copy Utility

Copy GPS coordinates from geotagged photos (e.g. iPhone) to untagged ones (e.g. Sony camera exports), matching by closest timestamp.

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

## macOS App Builds

GeoTagCopy can be packaged on macOS with PyInstaller so the target Mac does not
need Python or the Python dependencies installed.

Install build dependencies:

```bash
make build-deps
```

Build a draggable macOS app bundle:

```bash
make build-macos-app
```

The app will be created at `dist/GeoTagCopy.app`. You can drag it into
`/Applications` or run it directly.

Build a single executable file:

```bash
make build-macos-onefile
```

The executable will be created at `dist/GeoTagCopy`. Run it from Terminal:

```bash
./dist/GeoTagCopy
```

Build both outputs:

```bash
make build-macos
```

### Bundling ExifTool

ExifTool is still required for reading and writing metadata. Packaged builds
automatically download a pinned ExifTool release into `vendor/exiftool/` before
running PyInstaller, then include it in the app bundle and one-file executable.
This makes `GeoTagCopy.app` work when launched from Finder without relying on a
Terminal `PATH`.

If you need to supply ExifTool manually, place the executable distribution here
before building:

```text
vendor/exiftool/exiftool
```

When that file exists, `scripts/build_macos.py` uses it instead of downloading.
You can also point a built app at a specific ExifTool binary with:

```bash
GEOTAGCOPY_EXIFTOOL="/path/to/exiftool" ./dist/GeoTagCopy
```

For sharing outside your own Mac, you may need Apple code signing and
notarization so Gatekeeper accepts the app without warnings.

## GitHub Releases

The repository includes a GitHub Actions workflow that builds macOS release
artifacts and publishes them to a GitHub Release.

Create a release by pushing a version tag:

```bash
git tag v2.0.0
git push origin v2.0.0
```

Or run **Build and Release** manually from the GitHub Actions tab and enter a
version such as `v2.0.0`.

Each release uploads:

- `GeoTagCopy-<version>-macos-app.zip`: draggable `GeoTagCopy.app`
- `GeoTagCopy-<version>-macos-onefile.zip`: single executable file

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

