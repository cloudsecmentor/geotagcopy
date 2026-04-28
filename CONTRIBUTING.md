# Contributing to GeoTagCopy

Thanks for helping improve GeoTagCopy. This project is intended to be a public,
open-source, voluntarily supported desktop app.

## Local setup

Use Python 3.11 for development and packaging.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-build.txt
```

On Windows:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-build.txt
```

## Running tests

```bash
make test
```

Or directly:

```bash
python -m unittest discover -v
```

## Running from source

```bash
python -m geotagcopy
```

You can pre-fill source folders:

```bash
python -m geotagcopy \
  --tagged "/path/to/tagged/photos" \
  --untagged "/path/to/untagged/photos"
```

## Building locally

Install build dependencies first:

```bash
make build-deps
```

Regenerate app and website icons:

```bash
make icons
```

Build macOS artifacts on a macOS host:

```bash
make build-macos
```

Build Windows artifacts on a Windows host:

```bash
make build-windows
```

Packaged builds vendor ExifTool into the app so users do not need a separate
ExifTool installation.

One-file PyInstaller builds are available as explicit targets for local
experiments:

```bash
make build-macos-onefile
make build-windows-onefile
```

They are not the preferred public release artifacts.

## Pull requests

1. Create a feature branch from `main`.
2. Keep changes focused on one task or behavior.
3. Run tests before opening a PR.
4. Use clear commit messages such as `fix GPS matching tolerance` or
   `add Windows PyInstaller build`.
5. Open a PR with `gh pr create` or through GitHub.

Unless explicitly agreed otherwise, intentional contributions are submitted
under the Apache License 2.0, matching the repository license.

## Maintainer setup

The release and site workflows use GitHub repo secrets and variables. Never
commit credentials, certificates, private keys, `.env` files, or generated
build artifacts.

Public launch release notes are in `docs/release/public-launch.md`.
