"""Tests for geotagcopy.core."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from geotagcopy.core import (
    MediaFile,
    GeoMatch,
    LocationGroup,
    get_exiftool_exe,
    scan_folder,
    parse_exif_date,
    match_files,
    group_matches,
    format_time_diff,
    SUPPORTED_EXTENSIONS,
)


class TestMediaFile(unittest.TestCase):
    def test_has_gps_true(self):
        mf = MediaFile(path="/img.jpg", latitude=59.44, longitude=18.04)
        self.assertTrue(mf.has_gps)

    def test_has_gps_false_when_missing(self):
        mf = MediaFile(path="/img.jpg")
        self.assertFalse(mf.has_gps)

    def test_has_gps_false_when_partial(self):
        mf = MediaFile(path="/img.jpg", latitude=59.44)
        self.assertFalse(mf.has_gps)

    def test_filename_auto(self):
        mf = MediaFile(path="/some/folder/IMG_001.HEIC")
        self.assertEqual(mf.filename, "IMG_001.HEIC")

    def test_filename_explicit(self):
        mf = MediaFile(path="/some/folder/IMG_001.HEIC", filename="custom.jpg")
        self.assertEqual(mf.filename, "custom.jpg")


class TestLocationGroup(unittest.TestCase):
    def test_location_label_with_gps(self):
        donor = MediaFile(path="/d.jpg", latitude=59.4428, longitude=18.0452)
        group = LocationGroup(donor=donor)
        self.assertIn("59.4428", group.location_label)
        self.assertIn("18.0452", group.location_label)
        self.assertIn("N", group.location_label)
        self.assertIn("E", group.location_label)

    def test_location_label_south_west(self):
        donor = MediaFile(path="/d.jpg", latitude=-33.86, longitude=-151.21)
        group = LocationGroup(donor=donor)
        self.assertIn("S", group.location_label)
        self.assertIn("W", group.location_label)

    def test_location_label_no_gps(self):
        donor = MediaFile(path="/d.jpg")
        group = LocationGroup(donor=donor)
        self.assertEqual(group.location_label, "Unknown")


class TestScanFolder(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.files = ["photo1.jpg", "photo2.HEIC", "video.MOV", "readme.txt", "data.csv"]
        for f in self.files:
            open(os.path.join(self.tmpdir, f), "w").close()

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.remove(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_finds_supported_files(self):
        found = scan_folder(self.tmpdir, recursive=False)
        names = {os.path.basename(f) for f in found}
        self.assertIn("photo1.jpg", names)
        self.assertIn("photo2.HEIC", names)
        self.assertIn("video.MOV", names)
        self.assertNotIn("readme.txt", names)
        self.assertNotIn("data.csv", names)

    def test_returns_sorted(self):
        found = scan_folder(self.tmpdir, recursive=False)
        self.assertEqual(found, sorted(found))

    def test_empty_dir(self):
        empty = tempfile.mkdtemp()
        self.assertEqual(scan_folder(empty), [])
        os.rmdir(empty)

    def test_nonexistent_dir(self):
        self.assertEqual(scan_folder("/nonexistent/dir/12345"), [])

    def test_recursive(self):
        subdir = os.path.join(self.tmpdir, "sub")
        os.makedirs(subdir)
        open(os.path.join(subdir, "deep.png"), "w").close()

        found_recursive = scan_folder(self.tmpdir, recursive=True)
        names = {os.path.basename(f) for f in found_recursive}
        self.assertIn("deep.png", names)
        self.assertIn("photo1.jpg", names)

        found_flat = scan_folder(self.tmpdir, recursive=False)
        names_flat = {os.path.basename(f) for f in found_flat}
        self.assertNotIn("deep.png", names_flat)

        os.remove(os.path.join(subdir, "deep.png"))
        os.rmdir(subdir)

    def test_skips_hidden_files(self):
        open(os.path.join(self.tmpdir, ".hidden.jpg"), "w").close()
        found = scan_folder(self.tmpdir, recursive=False)
        names = {os.path.basename(f) for f in found}
        self.assertNotIn(".hidden.jpg", names)
        os.remove(os.path.join(self.tmpdir, ".hidden.jpg"))


class TestExifToolLookup(unittest.TestCase):
    def test_env_override_uses_executable_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "exiftool")
            with open(path, "w", encoding="utf-8") as f:
                f.write("#!/bin/sh\n")
            os.chmod(path, 0o755)

            with patch.dict(os.environ, {"GEOTAGCOPY_EXIFTOOL": path}):
                self.assertEqual(get_exiftool_exe(), path)

    def test_falls_back_to_path_lookup(self):
        with patch.dict(os.environ, {"GEOTAGCOPY_EXIFTOOL": ""}):
            with patch("geotagcopy.core.shutil.which", return_value="/usr/bin/exiftool"):
                self.assertEqual(get_exiftool_exe(), "/usr/bin/exiftool")


class TestParseExifDate(unittest.TestCase):
    def test_standard_format(self):
        result = parse_exif_date("2023:06:13 08:56:27")
        self.assertEqual(result, datetime(2023, 6, 13, 8, 56, 27))

    def test_iso_format(self):
        result = parse_exif_date("2023-06-13 08:56:27")
        self.assertEqual(result, datetime(2023, 6, 13, 8, 56, 27))

    def test_with_timezone_stripped(self):
        result = parse_exif_date("2021:12:26 10:23:05+01:00")
        self.assertEqual(result, datetime(2021, 12, 26, 10, 23, 5))

    def test_none_input(self):
        self.assertIsNone(parse_exif_date(None))

    def test_empty_string(self):
        self.assertIsNone(parse_exif_date(""))

    def test_zeroed_date(self):
        self.assertIsNone(parse_exif_date("0000:00:00 00:00:00"))

    def test_non_string(self):
        self.assertIsNone(parse_exif_date(12345))

    def test_garbage(self):
        self.assertIsNone(parse_exif_date("not a date"))


class TestMatchFiles(unittest.TestCase):
    def _make_tagged(self, date, lat=59.44, lon=18.04):
        return MediaFile(
            path=f"/tagged/{date.isoformat()}.heic",
            date=date,
            latitude=lat,
            longitude=lon,
        )

    def _make_untagged(self, date):
        return MediaFile(path=f"/untagged/{date.isoformat()}.jpg", date=date)

    def test_basic_matching(self):
        t1 = self._make_tagged(datetime(2023, 6, 13, 9, 0, 0))
        t2 = self._make_tagged(datetime(2023, 6, 13, 15, 0, 0), lat=60.0, lon=19.0)

        u1 = self._make_untagged(datetime(2023, 6, 13, 9, 30, 0))
        u2 = self._make_untagged(datetime(2023, 6, 13, 14, 0, 0))

        matches = match_files([t1, t2], [u1, u2])
        self.assertEqual(len(matches), 2)

        # u1 should match t1 (closer in time)
        self.assertEqual(matches[0].donor.path, t1.path)
        self.assertAlmostEqual(matches[0].time_diff_hours, 0.5, places=2)

        # u2 should match t2 (closer in time)
        self.assertEqual(matches[1].donor.path, t2.path)
        self.assertAlmostEqual(matches[1].time_diff_hours, 1.0, places=2)

    def test_no_donors_with_gps(self):
        tagged = [MediaFile(path="/t.heic", date=datetime(2023, 1, 1))]
        untagged = [self._make_untagged(datetime(2023, 1, 1))]
        matches = match_files(tagged, untagged)
        self.assertEqual(len(matches), 0)

    def test_no_untagged_with_date(self):
        tagged = [self._make_tagged(datetime(2023, 1, 1))]
        untagged = [MediaFile(path="/u.jpg")]
        matches = match_files(tagged, untagged)
        self.assertEqual(len(matches), 0)

    def test_skips_already_geotagged(self):
        tagged = [self._make_tagged(datetime(2023, 1, 1))]
        untagged = [MediaFile(
            path="/u.jpg", date=datetime(2023, 1, 1),
            latitude=50.0, longitude=10.0,
        )]
        matches = match_files(tagged, untagged)
        self.assertEqual(len(matches), 0)

    def test_empty_inputs(self):
        self.assertEqual(match_files([], []), [])
        self.assertEqual(match_files([self._make_tagged(datetime.now())], []), [])
        self.assertEqual(match_files([], [self._make_untagged(datetime.now())]), [])

    def test_large_time_difference(self):
        tagged = [self._make_tagged(datetime(2023, 6, 13, 10, 0, 0))]
        untagged = [self._make_untagged(datetime(2021, 12, 26, 10, 0, 0))]

        matches = match_files(tagged, untagged)
        self.assertEqual(len(matches), 1)
        self.assertGreater(matches[0].time_diff_hours, 10000)

    def test_all_match_same_donor(self):
        donor = self._make_tagged(datetime(2023, 6, 13, 10, 0, 0))
        untagged = [
            self._make_untagged(datetime(2023, 6, 13, 10, 5, 0)),
            self._make_untagged(datetime(2023, 6, 13, 10, 10, 0)),
            self._make_untagged(datetime(2023, 6, 13, 10, 15, 0)),
        ]
        matches = match_files([donor], untagged)
        self.assertEqual(len(matches), 3)
        for m in matches:
            self.assertEqual(m.donor.path, donor.path)


class TestGroupMatches(unittest.TestCase):
    def test_groups_by_donor(self):
        d1 = MediaFile(path="/d1.heic", date=datetime(2023, 6, 13, 9, 0),
                       latitude=59.44, longitude=18.04)
        d2 = MediaFile(path="/d2.heic", date=datetime(2023, 6, 13, 15, 0),
                       latitude=60.0, longitude=19.0)

        matches = [
            GeoMatch(untagged=MediaFile(path="/u1.jpg"), donor=d1, time_diff_hours=0.5),
            GeoMatch(untagged=MediaFile(path="/u2.jpg"), donor=d1, time_diff_hours=1.0),
            GeoMatch(untagged=MediaFile(path="/u3.jpg"), donor=d2, time_diff_hours=2.0),
        ]

        groups = group_matches(matches)
        self.assertEqual(len(groups), 2)

        group_d1 = [g for g in groups if g.donor.path == "/d1.heic"][0]
        self.assertEqual(len(group_d1.matches), 2)

        group_d2 = [g for g in groups if g.donor.path == "/d2.heic"][0]
        self.assertEqual(len(group_d2.matches), 1)

    def test_sorted_by_donor_date(self):
        d_early = MediaFile(path="/early.heic", date=datetime(2023, 1, 1),
                            latitude=1.0, longitude=1.0)
        d_late = MediaFile(path="/late.heic", date=datetime(2023, 12, 31),
                           latitude=2.0, longitude=2.0)

        matches = [
            GeoMatch(untagged=MediaFile(path="/u1.jpg"), donor=d_late, time_diff_hours=1),
            GeoMatch(untagged=MediaFile(path="/u2.jpg"), donor=d_early, time_diff_hours=2),
        ]

        groups = group_matches(matches)
        self.assertEqual(groups[0].donor.path, "/early.heic")
        self.assertEqual(groups[1].donor.path, "/late.heic")

    def test_matches_sorted_by_time_diff(self):
        donor = MediaFile(path="/d.heic", date=datetime(2023, 6, 13),
                          latitude=1.0, longitude=1.0)
        matches = [
            GeoMatch(untagged=MediaFile(path="/u3.jpg"), donor=donor, time_diff_hours=5.0),
            GeoMatch(untagged=MediaFile(path="/u1.jpg"), donor=donor, time_diff_hours=1.0),
            GeoMatch(untagged=MediaFile(path="/u2.jpg"), donor=donor, time_diff_hours=3.0),
        ]

        groups = group_matches(matches)
        diffs = [m.time_diff_hours for m in groups[0].matches]
        self.assertEqual(diffs, sorted(diffs))

    def test_empty_matches(self):
        self.assertEqual(group_matches([]), [])


class TestFormatTimeDiff(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(format_time_diff(0.5), "30min")

    def test_very_small(self):
        self.assertEqual(format_time_diff(0.001), "<1min")

    def test_hours(self):
        result = format_time_diff(3.5)
        self.assertIn("3h", result)
        self.assertIn("30min", result)

    def test_days(self):
        result = format_time_diff(48)
        self.assertIn("2d", result)

    def test_months(self):
        result = format_time_diff(24 * 45)
        self.assertIn("1mo", result)

    def test_years(self):
        result = format_time_diff(24 * 400)
        self.assertIn("1y", result)

    def test_zero(self):
        self.assertEqual(format_time_diff(0), "<1min")

    def test_complex(self):
        hours = 365 * 24 + 60 * 24 + 5 * 24 + 3
        result = format_time_diff(hours)
        self.assertIn("1y", result)
        self.assertIn("2mo", result)
        self.assertIn("5d", result)
        self.assertIn("3h", result)


class TestGeoMatchDefaults(unittest.TestCase):
    def test_approved_by_default(self):
        m = GeoMatch(
            untagged=MediaFile(path="/u.jpg"),
            donor=MediaFile(path="/d.jpg"),
            time_diff_hours=1.0,
        )
        self.assertTrue(m.approved)


if __name__ == "__main__":
    unittest.main()
