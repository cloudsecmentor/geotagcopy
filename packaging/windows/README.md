# Windows Packaging

Release builds should prefer the one-directory PyInstaller output:

```powershell
python scripts/build_windows.py --target app
```

For the public launch, publish a signed installer once signing is configured.
Until then, GitHub Releases can carry the zipped app directory for smoke testing,
but the website should not promise a signed installer before the signing path is
ready.

Recommended signing order:

1. Use Azure Artifact Signing if the maintainer account is eligible.
2. Fall back to an OV code-signing certificate.
3. Treat EV signing as optional, not an MVP requirement.

Keep `exiftool.exe` and `exiftool_files` together inside the app directory.
