"""Tests for the legacy metadata analysis replacement."""

import csv
import os
import tempfile
import unittest
from datetime import datetime

from geotagcopy.legacy_analysis import (
    analyze_csv,
    build_metadata_rows,
    determine_author,
    add_gps_suggestions,
)


class TestLegacyAnalysis(unittest.TestCase):
    def test_determine_author_uses_path_patterns(self):
        self.assertEqual(determine_author("/photos/Irina/IMG_1.HEIC"), "authI")
        self.assertEqual(determine_author("/photos/tim/IMG_1.HEIC"), "authT")
        self.assertEqual(determine_author("/photos/mela/IMG_1.HEIC"), "authM")
        self.assertEqual(determine_author("/photos/unknown/IMG_1.HEIC"), "authS")

    def test_adds_nearest_same_author_gps_suggestion(self):
        rows = build_metadata_rows([
            {
                "SourceFile": "/photos/irina/tagged.HEIC",
                "EXIF:DateTimeOriginal": "2023:07:15 10:00:00",
                "QuickTime:CreateDate": "",
                "Composite:GPSPosition": "59.1 18.1",
                "Composite:GPSAltitude": "12.5",
            },
            {
                "SourceFile": "/photos/serg/tagged.HEIC",
                "EXIF:DateTimeOriginal": "2023:07:15 10:10:00",
                "QuickTime:CreateDate": "",
                "Composite:GPSPosition": "60.1 19.1",
                "Composite:GPSAltitude": "20",
            },
            {
                "SourceFile": "/photos/irina/untagged.JPG",
                "EXIF:DateTimeOriginal": "",
                "QuickTime:CreateDate": "2023:07:15 10:30:00",
                "Composite:GPSPosition": "",
                "Composite:GPSAltitude": "",
            },
        ])

        suggestion_count = add_gps_suggestions(rows)

        self.assertEqual(suggestion_count, 1)
        self.assertEqual(rows[2].suggested_source_file, "/photos/irina/tagged.HEIC")
        self.assertEqual(rows[2].suggested_media_date, datetime(2023, 7, 15, 10, 0))
        self.assertEqual(rows[2].suggested_gps_lat, 59.1)
        self.assertEqual(rows[2].suggested_gps_long, 18.1)
        self.assertEqual(rows[2].suggested_gps_alt, 12.5)
        self.assertAlmostEqual(rows[2].suggested_time_diff, 0.5)

    def test_analyze_csv_overwrites_with_review_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "metadata.csv")
            with open(path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=[
                        "SourceFile",
                        "EXIF:DateTimeOriginal",
                        "QuickTime:CreateDate",
                        "Composite:GPSPosition",
                        "Composite:GPSAltitude",
                    ],
                )
                writer.writeheader()
                writer.writerows([
                    {
                        "SourceFile": "/photos/serg/tagged.HEIC",
                        "EXIF:DateTimeOriginal": "2023:07:15 10:00:00",
                        "QuickTime:CreateDate": "",
                        "Composite:GPSPosition": "59.1 18.1",
                        "Composite:GPSAltitude": "12.5",
                    },
                    {
                        "SourceFile": "/photos/serg/untagged.JPG",
                        "EXIF:DateTimeOriginal": "",
                        "QuickTime:CreateDate": "2023:07:15 11:00:00",
                        "Composite:GPSPosition": "",
                        "Composite:GPSAltitude": "",
                    },
                ])

            suggestion_count = analyze_csv(path)

            self.assertEqual(suggestion_count, 1)
            with open(path, newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))

            self.assertEqual(rows[1]["cust.author"], "authS")
            self.assertEqual(rows[1]["cust.MediaDate"], "2023-07-15 11:00:00")
            self.assertEqual(rows[1]["suggested.SourceFile"], "/photos/serg/tagged.HEIC")
            self.assertEqual(rows[1]["suggested.time.diff"], "1.0")
            self.assertEqual(rows[1]["suggested.cust.GPSLatt"], "59.1")
            self.assertEqual(rows[1]["suggested.cust.GPSLong"], "18.1")


if __name__ == "__main__":
    unittest.main()
