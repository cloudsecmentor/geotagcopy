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
- **[ExifTool](https://exiftool.org/)** installed and on PATH
- **customtkinter** (installed automatically via requirements.txt)

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

### Running Tests

```bash
python -m unittest tests.test_core -v
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

