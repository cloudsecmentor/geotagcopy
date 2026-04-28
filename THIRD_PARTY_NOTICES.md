# Third-Party Notices

GeoTagCopy is an open-source desktop app that uses third-party components. This
file is a maintainer-facing reminder for public releases; it is not legal
advice.

## ExifTool

Packaged GeoTagCopy builds bundle ExifTool so users do not need to install it
separately.

- Upstream: https://exiftool.org/
- Copyright: Phil Harvey
- License: distributed under the same terms as Perl
- macOS packaging: keep the `exiftool` executable and its `lib` directory
  together.
- Windows packaging: keep `exiftool.exe` and `exiftool_files` together.

GeoTagCopy should continue to present value beyond a button wrapper around
ExifTool: timestamp matching, grouped review, map context, safe batch selection,
logs, and clear previews before metadata is written. Revisit this before adding
paid licensing, paid-only features, or commercial redistribution terms.

## Python Dependencies

Runtime Python dependencies are listed in `requirements.txt`. Build-only
dependencies are listed in `requirements-build.txt`. Review their licenses
before publishing a new binary release.
