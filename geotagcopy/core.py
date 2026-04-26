"""Core logic for GeoTagCopy: scanning, metadata, matching, grouping, applying."""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

SUPPORTED_EXTENSIONS = frozenset({
    "jpg", "jpeg", "heic", "png", "mov", "mp4",
    "tif", "tiff", "arw", "cr2", "nef", "dng",
})

EXIFTOOL_DATE_TAGS = [
    "-DateTimeOriginal", "-CreateDate", "-FileModifyDate",
]

EXIFTOOL_GPS_TAGS = [
    "-GPSLatitude", "-GPSLongitude", "-GPSAltitude",
]


def get_exiftool_exe() -> Optional[str]:
    """Return a bundled ExifTool executable when present, otherwise PATH."""
    env_path = os.environ.get("GEOTAGCOPY_EXIFTOOL", "").strip()
    if env_path and _is_executable(env_path):
        return env_path

    for candidate in _bundled_exiftool_candidates():
        if _is_executable(candidate):
            return str(candidate)

    return shutil.which("exiftool")


def _bundled_exiftool_candidates() -> list[Path]:
    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.extend(_exiftool_locations(Path(bundle_root)))
        candidates.extend(_exiftool_locations(Path(bundle_root).parent / "Resources"))

    app_root = Path(sys.executable).resolve().parent
    candidates.extend(_exiftool_locations(app_root))
    candidates.extend(_exiftool_locations(app_root.parent / "Resources"))
    return candidates


def _exiftool_locations(root: Path) -> list[Path]:
    return [
        root / "exiftool" / "exiftool",
        root / "bin" / "exiftool",
    ]


def _is_executable(path: str | Path) -> bool:
    path = Path(path).expanduser()
    return path.is_file() and os.access(path, os.X_OK)


@dataclass
class MediaFile:
    path: str
    filename: str = ""
    date: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None

    def __post_init__(self):
        if not self.filename:
            self.filename = os.path.basename(self.path)

    @property
    def has_gps(self) -> bool:
        return self.latitude is not None and self.longitude is not None


@dataclass
class GeoMatch:
    untagged: MediaFile
    donor: MediaFile
    time_diff_hours: float
    approved: bool = True


@dataclass
class LocationGroup:
    donor: MediaFile
    matches: list[GeoMatch] = field(default_factory=list)

    @property
    def location_label(self) -> str:
        if self.donor.has_gps:
            lat = self.donor.latitude
            lon = self.donor.longitude
            lat_dir = "N" if lat >= 0 else "S"
            lon_dir = "E" if lon >= 0 else "W"
            return f"{abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}"
        return "Unknown"


def check_exiftool() -> bool:
    """Return True if ExifTool is bundled or available on PATH."""
    exiftool = get_exiftool_exe()
    if not exiftool:
        return False

    try:
        result = subprocess.run(
            [exiftool, "-ver"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def scan_folder(folder: str, recursive: bool = True) -> list[str]:
    """Find all supported media files in a folder."""
    folder = os.path.expanduser(folder)
    if not os.path.isdir(folder):
        return []

    files = []
    if recursive:
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.startswith("."):
                    continue
                ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                if ext in SUPPORTED_EXTENSIONS:
                    files.append(os.path.join(root, f))
    else:
        for f in os.listdir(folder):
            if f.startswith("."):
                continue
            full = os.path.join(folder, f)
            if os.path.isfile(full):
                ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                if ext in SUPPORTED_EXTENSIONS:
                    files.append(full)

    files.sort()
    return files


def parse_exif_date(date_str) -> Optional[datetime]:
    """Parse EXIF date strings into datetime objects."""
    if not date_str or not isinstance(date_str, str):
        return None
    clean = date_str.strip()[:19]
    if clean == "0000:00:00 00:00:00":
        return None
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


def read_metadata(
    file_paths: list[str],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[MediaFile]:
    """Read EXIF metadata from files using exiftool CLI (JSON + numeric GPS)."""
    if not file_paths:
        return []

    exiftool = get_exiftool_exe()
    if not exiftool:
        return [MediaFile(path=fp) for fp in file_paths]

    batch_size = 50
    all_meta: list[dict] = []

    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i : i + batch_size]
        try:
            cmd = (
                [exiftool, "-json", "-n"]
                + EXIFTOOL_DATE_TAGS
                + EXIFTOOL_GPS_TAGS
                + batch
            )
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            if result.stdout.strip():
                all_meta.extend(json.loads(result.stdout))
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            for fp in batch:
                all_meta.append({"SourceFile": fp})

        if progress_callback:
            progress_callback(min(i + batch_size, len(file_paths)), len(file_paths))

    media_files: list[MediaFile] = []
    for meta in all_meta:
        path = meta.get("SourceFile", "")

        date = (
            parse_exif_date(meta.get("DateTimeOriginal"))
            or parse_exif_date(meta.get("CreateDate"))
            or parse_exif_date(meta.get("FileModifyDate"))
        )

        lat = meta.get("GPSLatitude")
        lon = meta.get("GPSLongitude")
        alt = meta.get("GPSAltitude")

        if lat is not None and lon is not None:
            if lat == 0 and lon == 0:
                lat, lon = None, None

        media_files.append(
            MediaFile(
                path=path,
                date=date,
                latitude=float(lat) if lat is not None else None,
                longitude=float(lon) if lon is not None else None,
                altitude=float(alt) if alt is not None else None,
            )
        )

    return media_files


def match_files(
    tagged: list[MediaFile], untagged: list[MediaFile]
) -> list[GeoMatch]:
    """Match each untagged file to the nearest-in-time tagged file with GPS.

    Only tagged files that have both a date and GPS coordinates are considered.
    Untagged files that already have GPS or lack a date are skipped.
    """
    donors = [t for t in tagged if t.has_gps and t.date is not None]
    if not donors:
        return []

    donors_sorted = sorted(donors, key=lambda f: f.date)

    matches: list[GeoMatch] = []
    for uf in untagged:
        if uf.date is None or uf.has_gps:
            continue

        best_donor = None
        best_diff = float("inf")

        for d in donors_sorted:
            diff = abs((uf.date - d.date).total_seconds()) / 3600.0
            if diff < best_diff:
                best_diff = diff
                best_donor = d

        if best_donor is not None:
            matches.append(
                GeoMatch(
                    untagged=uf,
                    donor=best_donor,
                    time_diff_hours=best_diff,
                )
            )

    return matches


def group_matches(matches: list[GeoMatch]) -> list[LocationGroup]:
    """Group matches by donor file path."""
    groups_dict: dict[str, LocationGroup] = {}

    for m in matches:
        key = m.donor.path
        if key not in groups_dict:
            groups_dict[key] = LocationGroup(donor=m.donor)
        groups_dict[key].matches.append(m)

    groups = list(groups_dict.values())
    for g in groups:
        g.matches.sort(key=lambda m: m.time_diff_hours)

    groups.sort(key=lambda g: g.donor.date or datetime.min)
    return groups


def format_time_diff(hours: float) -> str:
    """Format a time difference in hours to a human-readable string."""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes}min" if minutes > 0 else "<1min"

    total_minutes = int(hours * 60)
    days = total_minutes // (60 * 24)
    remaining = total_minutes % (60 * 24)
    h = remaining // 60
    m = remaining % 60

    years = days // 365
    remaining_days = days % 365
    months = remaining_days // 30
    d = remaining_days % 30

    parts: list[str] = []
    if years > 0:
        parts.append(f"{years}y")
    if months > 0:
        parts.append(f"{months}mo")
    if d > 0:
        parts.append(f"{d}d")
    if h > 0:
        parts.append(f"{h}h")
    if m > 0 and years == 0 and months == 0:
        parts.append(f"{m}min")

    return " ".join(parts) if parts else "<1min"


def apply_gps_tags(
    matches: list[GeoMatch],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> tuple[int, list[str]]:
    """Apply GPS tags from donors to untagged files.

    Returns (success_count, error_messages).
    """
    approved = [m for m in matches if m.approved]
    success = 0
    errors: list[str] = []
    exiftool = get_exiftool_exe()

    if not exiftool:
        return 0, ["ExifTool not found. Install it or bundle it with GeoTagCopy."]

    for i, match in enumerate(approved):
        donor = match.donor
        target = match.untagged

        comment = f"GPS copied from {donor.filename}"

        cmd = [
            exiftool,
            "-overwrite_original_in_place",
            f"-XMP:GPSLatitude={donor.latitude}",
            f"-XMP:GPSLongitude={donor.longitude}",
            f"-Label=GPSCopy",
            f"-Comment={comment}",
            f"-XMP:UserComment={comment}",
        ]

        if donor.altitude is not None:
            cmd.append(f"-XMP:GPSAltitude={donor.altitude}")

        cmd.append(target.path)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                success += 1
            else:
                errors.append(f"{target.filename}: {result.stderr.strip()}")
        except Exception as e:
            errors.append(f"{target.filename}: {e}")

        if progress_callback:
            progress_callback(i + 1, len(approved))

    return success, errors
