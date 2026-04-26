"""Python replacement for the legacy R metadata recommendation step."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional


AUTHORS = (
    ("authI", "irina", False),
    ("authT", "tim", False),
    ("authM", "mela", False),
    ("authS", "serg", True),
)

OUTPUT_COLUMNS = [
    "SourceFile",
    "cust.author",
    "cust.MediaDate",
    "cust.GPSAlt",
    "cust.GPSLatt",
    "cust.GPSLong",
    "suggested.SourceFile",
    "suggested.time.diff",
    "suggested.cust.MediaDate",
    "suggested.cust.GPSLatt",
    "suggested.cust.GPSLong",
    "suggested.cust.GPSAlt",
]

MISSING_VALUES = {"", "na", "n/a", "nan", "none", "null"}


@dataclass
class MetadataRow:
    source_file: str
    author: str
    media_date: Optional[datetime]
    gps_alt: Optional[float]
    gps_lat: Optional[float]
    gps_long: Optional[float]
    suggested_source_file: str = ""
    suggested_time_diff: Optional[float] = None
    suggested_media_date: Optional[datetime] = None
    suggested_gps_lat: Optional[float] = None
    suggested_gps_long: Optional[float] = None
    suggested_gps_alt: Optional[float] = None

    @property
    def has_gps(self) -> bool:
        return self.gps_lat is not None and self.gps_long is not None


def is_missing(value) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in MISSING_VALUES


def coerce_float(value) -> Optional[float]:
    if is_missing(value):
        return None
    try:
        return float(str(value).strip().strip('"'))
    except ValueError:
        return None


def parse_datetime(value) -> Optional[datetime]:
    if is_missing(value):
        return None

    clean = str(value).strip().replace("T", " ")[:19]
    if clean == "0000:00:00 00:00:00":
        return None

    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


def format_datetime(value: Optional[datetime]) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else ""


def format_number(value: Optional[float]) -> str:
    return "" if value is None else str(value)


def determine_author(source_file: str) -> str:
    source_lower = source_file.lower()
    for author, pattern, _ in AUTHORS:
        if pattern in source_lower:
            return author

    for author, _, is_default in AUTHORS:
        if is_default:
            return author

    raise RuntimeError("No default author configured")


def parse_gps_position(position: str) -> tuple[Optional[float], Optional[float]]:
    if is_missing(position):
        return None, None

    parts = re.split(r"[\s,]+", str(position).strip())
    numbers = [coerce_float(part) for part in parts]
    numbers = [number for number in numbers if number is not None]

    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    return None, None


def extract_gps(row: dict[str, str]) -> tuple[Optional[float], Optional[float]]:
    lat, lon = parse_gps_position(row.get("Composite:GPSPosition", ""))
    if lat is not None and lon is not None:
        return lat, lon

    return (
        coerce_float(row.get("Composite:GPSLatitude")),
        coerce_float(row.get("Composite:GPSLongitude")),
    )


def build_metadata_rows(csv_rows: Iterable[dict[str, str]]) -> list[MetadataRow]:
    rows: list[MetadataRow] = []
    for row in csv_rows:
        source_file = row.get("SourceFile", "")
        lat, lon = extract_gps(row)
        media_date = parse_datetime(
            row.get("EXIF:DateTimeOriginal")
            if not is_missing(row.get("EXIF:DateTimeOriginal"))
            else row.get("QuickTime:CreateDate")
        )

        rows.append(
            MetadataRow(
                source_file=source_file,
                author=determine_author(source_file),
                media_date=media_date,
                gps_alt=coerce_float(row.get("Composite:GPSAltitude")),
                gps_lat=lat,
                gps_long=lon,
            )
        )

    return rows


def add_gps_suggestions(rows: list[MetadataRow]) -> int:
    donors = [
        row
        for row in rows
        if row.has_gps and row.media_date is not None
    ]

    suggestion_count = 0
    for row in rows:
        if row.has_gps or row.media_date is None:
            continue

        candidates = [
            donor for donor in donors if donor.author == row.author
        ]
        if not candidates:
            continue

        best = min(
            candidates,
            key=lambda donor: abs(
                (donor.media_date - row.media_date).total_seconds()
            ),
        )
        time_diff = abs((best.media_date - row.media_date).total_seconds()) / 3600.0

        row.suggested_source_file = best.source_file
        row.suggested_time_diff = time_diff
        row.suggested_media_date = best.media_date
        row.suggested_gps_lat = best.gps_lat
        row.suggested_gps_long = best.gps_long
        row.suggested_gps_alt = best.gps_alt
        suggestion_count += 1

    return suggestion_count


def to_output_record(row: MetadataRow) -> dict[str, str]:
    return {
        "SourceFile": row.source_file,
        "cust.author": row.author,
        "cust.MediaDate": format_datetime(row.media_date),
        "cust.GPSAlt": format_number(row.gps_alt),
        "cust.GPSLatt": format_number(row.gps_lat),
        "cust.GPSLong": format_number(row.gps_long),
        "suggested.SourceFile": row.suggested_source_file,
        "suggested.time.diff": format_number(row.suggested_time_diff),
        "suggested.cust.MediaDate": format_datetime(row.suggested_media_date),
        "suggested.cust.GPSLatt": format_number(row.suggested_gps_lat),
        "suggested.cust.GPSLong": format_number(row.suggested_gps_long),
        "suggested.cust.GPSAlt": format_number(row.suggested_gps_alt),
    }


def analyze_csv(file_path: str, output_path: Optional[str] = None) -> int:
    output_path = output_path or file_path

    with open(file_path, newline="", encoding="utf-8-sig") as input_file:
        csv_rows = list(csv.DictReader(input_file))

    rows = build_metadata_rows(csv_rows)
    suggestion_count = add_gps_suggestions(rows)

    with open(output_path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(to_output_record(row) for row in rows)

    return suggestion_count


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Add GPS donor suggestions to an exported metadata CSV."
    )
    parser.add_argument("--file", required=True, help="Path to metadata CSV")
    parser.add_argument(
        "--output",
        help="Output CSV path. Defaults to overwriting --file, matching the legacy step.",
    )
    args = parser.parse_args(argv)

    print(f"Reading data from file: {args.file}")
    suggestion_count = analyze_csv(args.file, args.output)
    print(f"Wrote {suggestion_count} GPS suggestion(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
