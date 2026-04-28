# Public Launch Release Runbook

This runbook tracks the direct-distribution launch path for GeoTagCopy.

## Release Shape

- Build with PyInstaller on each target OS.
- Prefer one-directory outputs for public artifacts.
- Bundle ExifTool per OS and keep its companion files together.
- Publish binaries to GitHub Releases.
- Host the static website on Azure Storage behind Azure Front Door.
- Use Cloudflare as registrar/DNS only unless there is a specific reason to add
  another proxy layer.

## macOS

Target artifact: signed, notarized `GeoTagCopy.app` inside a `.dmg`.

High-level sequence:

```bash
MACOS_CODESIGN_IDENTITY="Developer ID Application: YOUR NAME (TEAMID)" \
  python scripts/build_macos.py --target app
codesign --force --deep --options runtime --timestamp \
  --entitlements packaging/macos/entitlements.plist \
  --sign "Developer ID Application: YOUR NAME (TEAMID)" \
  dist/GeoTagCopy.app
hdiutil create -volname "GeoTagCopy" -srcfolder dist/GeoTagCopy.app \
  -ov -format UDZO dist/GeoTagCopy.dmg
codesign --force --timestamp \
  --sign "Developer ID Application: YOUR NAME (TEAMID)" \
  dist/GeoTagCopy.dmg
xcrun notarytool submit dist/GeoTagCopy.dmg \
  --keychain-profile "notary-profile" --wait
xcrun stapler staple dist/GeoTagCopy.dmg
spctl --assess --type open --context context:primary-signature -v \
  dist/GeoTagCopy.dmg
```

Do not publish macOS artifacts as trusted downloads until signing and
notarization are passing.

## Windows

Target artifact: signed installer. A zipped one-directory app is acceptable for
pre-release smoke testing, but the launch download should be signed.

Recommended path:

1. Build with `python scripts/build_windows.py --target app`.
2. Create MSI or EXE installer from `dist\GeoTagCopy`.
3. Sign the installer and any executable payloads.
4. Test install, launch, uninstall, and ExifTool lookup on a clean VM.

Prefer Azure Artifact Signing if the maintainer is eligible; otherwise use an OV
code-signing certificate.

## Updates

MVP releases should use manual updates:

- The app may open the latest GitHub Release in the browser.
- Avoid automatic updates until signing, key storage, and release-feed
  verification are fully documented.

Sparkle and WinSparkle can be revisited after the first signed release.

## Support Payments

Use Stripe-hosted Payment Links opened in the browser. Do not collect card data
inside the desktop app. Public copy should say "Support the project" or "Tip the
maintainer", not tax-deductible donation language.

## Privacy

The desktop app should remain telemetry-free by default. Do not send filenames,
folder names, EXIF data, coordinates, thumbnails, or crash payloads off-device
without an explicit opt-in design and a reviewed privacy notice.
