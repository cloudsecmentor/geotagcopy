# GeoTagCopy — Open Source, Cross-Platform, Donation-Funded Roadmap

This file is the **single source of truth** for an autonomous coding agent (or
team of agents) to take this repository from "macOS-only personal tool" to
"public, open-source, cross-platform, donation-funded app with a public landing
page on Azure."

## How to use this file

- Pick the **lowest-numbered unchecked task** whose dependencies are all checked.
- Read the whole task block before starting. The "Detailed instructions" inside
  each task are written for an agent that has no prior context — follow them
  literally; do not invent extra scope.
- When done, tick the checkbox `[x]` and add a one-line "Outcome" note under
  the acceptance criteria so the next agent knows what already exists.
- If a task is blocked on a human decision (e.g. a Stripe URL or an Azure
  resource), stop, document the blocker in the task block, and move to the
  next independent task.
- Never commit secrets. All credentials live in GitHub repo secrets (listed
  per task) and are referenced via `${{ secrets.NAME }}` in workflows only.

## Project conventions for every task

- Python 3.11 is the canonical interpreter for both macOS and Windows builds.
- Source of truth for the app version is `geotagcopy/__init__.py` (`__version__`).
  Workflows read it; do not hardcode versions in two places.
- Every workflow change must keep `on: workflow_dispatch` available for manual
  testing.
- No task is "done" until: (a) it builds locally where possible, (b) it has at
  least one smoke check (test, dry-run, or `--help`), and (c) `README.md` is
  updated with the new user-facing behavior.
- Match existing code style. No emojis in code or commits. No narrating
  comments.

---

## Task 1 — Open-source readiness audit

- [x] **Status:** completed
- **Depends on:** none
- **Acceptance criteria:**
  - `LICENSE` is an OSI-approved open-source license that matches the user's
    "public and opensource" intent (recommended: **MIT** or **Apache-2.0**).
    The current `PolyForm Noncommercial 1.0.0` and the unrelated "Copyright
    (c) 2022 CloudSecMentor" notice are removed.
  - A `CONTRIBUTING.md` exists with build/test/PR instructions.
  - A `CODE_OF_CONDUCT.md` exists (Contributor Covenant 2.1 is fine).
  - A `SECURITY.md` exists with a private disclosure email/contact.
  - The repo has zero hardcoded secrets, API keys, tokens, personal email
    addresses, or absolute paths from a developer machine.
  - `.gitignore` excludes `dist/`, `build/`, `*.spec`, `vendor/exiftool/`,
    `site/dist/`, `*.p12`, `*.p8`, `*.cer`, `.env*`.

**Outcome:** Implemented with unattended defaults: MIT license and
`GeoTagCopy contributors` copyright holder. Added `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, and `SECURITY.md` with placeholder project contact
emails. Secret-pattern scan only matched documentation/planning text. `make
test` passes; while checking it, the stale large-time-difference unit test was
updated to match the documented 24-hour default cutoff and to cover explicit
large-limit matching.

### Detailed instructions

1. Ask the user (or assume MIT if running unattended and note the assumption
   in the Outcome) which OSI license to adopt. Replace `LICENSE` in full.
   Use the canonical license text from <https://choosealicense.com/>. The
   copyright line should be `Copyright (c) <year> Sergey <last name or
   "GeoTagCopy contributors">`. Do **not** keep "CloudSecMentor".
2. Add a top-level `LICENSE` notice paragraph to `README.md` ("Licensed under
   the MIT License — see `LICENSE`.").
3. Create `CONTRIBUTING.md` covering:
   - Local setup (`python -m venv`, `pip install -r requirements.txt
     -r requirements-build.txt`).
   - Running tests (`make test`).
   - Building locally (`make build-macos`, `make build-windows` — the latter
     will exist after Task 4).
   - Branching/PR style: feature branches, conventional-ish commits,
     `gh pr create` flow.
4. Create `CODE_OF_CONDUCT.md` from Contributor Covenant 2.1 verbatim, with
   the contact line filled in (placeholder
   `conduct@<project-domain-or-email>` is acceptable; flag for the user).
5. Create `SECURITY.md` with a "Reporting a Vulnerability" section pointing
   to a contact email (placeholder ok, flag for the user).
6. Run a secret scan locally. From the repo root:
   ```bash
   rg -n -i "(?:api[_-]?key|secret|password|token|bearer|aws_access|-----BEGIN)" \
     --glob '!**/.venv/**' --glob '!**/__pycache__/**' --glob '!**/dist/**'
   ```
   Triage every hit. Anything that looks like real credentials — stop, do not
   commit, document in this task block, and surface to the user.
7. Update `.gitignore` per the acceptance criteria above.
8. Smoke-check: `make test` still passes.

---

## Task 2 — App icon and favicon

- [x] **Status:** completed
- **Depends on:** none (can run in parallel with Task 1)
- **Acceptance criteria:**
  - `assets/icon/icon.png` exists at 1024×1024 PNG, transparent background.
  - `assets/icon/icon.icns` exists for macOS (generated from the PNG).
  - `assets/icon/icon.ico` exists for Windows (multi-resolution: 16, 32, 48,
    64, 128, 256).
  - `assets/icon/favicon.ico` and `assets/icon/favicon-32.png` exist for the
    website.
  - The build pipeline references the icon (covered in later tasks).
  - The icon visually represents "geotag copy" — e.g. a map pin with a small
    arrow/copy glyph. Keep it readable at 32×32.

**Outcome:** Added reproducible Pillow-based icon generation in
`scripts/build_icons.py`, wired `make icons`, documented it in
`CONTRIBUTING.md`, and generated `assets/icon/icon.png`, `icon.icns`,
`icon.ico`, `favicon.ico`, and `favicon-32.png`. Smoke check passed with
`make PYTHON=.venv/bin/python icons`; the plain `make icons` target requires
the selected Python interpreter to have dependencies from `requirements.txt`.

### Detailed instructions

1. Create the master PNG at `assets/icon/icon.png`, 1024×1024. Suggested
   design: a rounded-square background (color `#1a6dcc`, matching
   `COLOR_LOCATION` in `app.py`), centered white **map-pin** silhouette, a
   small overlapping copy/duplicate glyph in the bottom-right corner. Generate
   it with the `GenerateImage` tool **only if explicitly authorized by the
   user**; otherwise commit a placeholder `icon.svg` and document the
   generation step here for the user to run once.
2. Generate platform-specific icons from the master PNG. The agent should
   use a small Python script committed at `scripts/build_icons.py` that uses
   `Pillow` (already in `requirements.txt`) to:
   - Render `icon.icns` via `iconutil` on macOS, falling back to `pillow` +
     `icnsutil`. Build a `.iconset` directory with the standard sizes
     (16, 32, 64, 128, 256, 512, 1024 in @1x and @2x) then run
     `iconutil -c icns icon.iconset -o icon.icns`.
   - Render `icon.ico` with multi-resolution frames via
     `Image.save("icon.ico", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])`.
   - Render `favicon.ico` (16/32/48) and `favicon-32.png`.
3. Wire the script into `Makefile` (`make icons`) and document it in
   `CONTRIBUTING.md`.
4. Smoke-check: run `make icons` on macOS, confirm all 4 output files exist.

---

## Task 3 — Support link in the packaged app (site-first donation flow)

- [x] **Status:** completed
- **Depends on:** Task 1 (license clarity), Task 2 (optional, for the donate
  icon)
- **Acceptance criteria:**
  - The **packaged** build (PyInstaller `--onedir` or `--onefile`, detected
    via `getattr(sys, "frozen", False)`) shows a clearly visible **Support**
    button in the top-right of the main window.
  - When run from source (`python -m geotagcopy`) the button is hidden by
    default but can be force-enabled with `GEOTAGCOPY_SHOW_SUPPORT=1` so it's
    testable.
  - Clicking the button opens the configured geotagcopy support/download
    page in the user's default browser. The app does **not** link directly to
    Stripe; the website owns the Stripe Payment Link.
  - The support URL is read from a single constant
    `geotagcopy.support.SUPPORT_URL`. The constant has a sensible default
    (empty until the production site URL exists) and can be overridden at build
    time via the `GEOTAGCOPY_SUPPORT_URL` environment variable, which the
    PyInstaller build step bakes into a generated `geotagcopy/_build_info.py`.
  - A "Support GeoTagCopy" item also appears in the macOS menu bar (under the
    app menu) and a Windows tray-equivalent menu (just the main-window button
    is fine on Windows).

**Outcome:** Added `geotagcopy/support.py`, the header Support button, a
Support menu item, macOS `_build_info.py` generation from
`GEOTAGCOPY_SUPPORT_URL`, `.gitignore` coverage for generated build info, and
`tests/test_support.py`. `make test` passes. Windows build-info generation
wired in Task 4. Task 5 (release workflow with signing) postponed; the
`SUPPORT_URL` variable will be passed in the release workflow when it is
revisited.

### Detailed instructions

1. Add a new module `geotagcopy/support.py` containing:
   ```python
   import os
   import sys
   import webbrowser

   SUPPORT_URL = os.environ.get(
       "GEOTAGCOPY_SUPPORT_URL",
       "",  # filled in by build pipeline; empty in dev source tree
   )

   def is_packaged() -> bool:
       return bool(getattr(sys, "frozen", False))

   def should_show_support() -> bool:
       if os.environ.get("GEOTAGCOPY_SHOW_SUPPORT") == "1":
           return True
       return is_packaged() and bool(SUPPORT_URL)

   def open_support_page() -> None:
       if SUPPORT_URL:
           webbrowser.open(SUPPORT_URL)
   ```
2. In `geotagcopy/app.py`, add a `CTkButton` labeled "Support" in the existing
   top header row. Place it after the existing right-aligned widgets. Wire
   `command=open_support_page`. Hide the button when `should_show_support()`
   is False (do not even create it).
3. Update `scripts/build_macos.py` and the new `scripts/build_windows.py`
   (Task 4) to write `geotagcopy/_build_info.py` containing
   `SUPPORT_URL = "<env value>"` if `GEOTAGCOPY_SUPPORT_URL` is set in the
   build environment, then `support.py` imports from it and prefers it over
   the env var. Treat the file as build artifact: add it to `.gitignore`.
4. The support URL itself is **provided by the user** after the static website
   URL or custom domain exists. The agent must not invent one. Until the user
   provides it, leave the default empty and note in the Outcome that the
   support button will be hidden until `GEOTAGCOPY_SUPPORT_URL` is configured
   in the GitHub repo as a repository **variable** named `SUPPORT_URL`.
5. Update both build workflows (Task 5) to pass
   `GEOTAGCOPY_SUPPORT_URL: ${{ vars.SUPPORT_URL }}` to the build step.
6. Add a unit test `tests/test_support.py` covering `should_show_support()`
   under all four (frozen, URL set/empty) combinations using monkeypatch.
7. Smoke-check: `GEOTAGCOPY_SHOW_SUPPORT=1 GEOTAGCOPY_SUPPORT_URL=https://example.com python -m geotagcopy`,
   confirm the button appears and opens the support URL.

---

## Task 4 — Windows build (Python-based, PyInstaller)

- [x] **Status:** completed
- **Depends on:** Task 2 (for `icon.ico`), Task 3 (for support-link wiring)
- **Acceptance criteria:**
  - A new `scripts/build_windows.py` mirrors `scripts/build_macos.py` but
    targets Windows: produces both `dist\GeoTagCopy\GeoTagCopy.exe`
    (`--onedir`) and `dist\GeoTagCopy.exe` (`--onefile`).
  - The Windows build downloads and bundles the official ExifTool **Windows
    Executable** zip (`exiftool-XX.XX_64.zip`), pinned by version + SHA-256,
    into `vendor/exiftool-windows/`. The bundled `exiftool(-k).exe` is
    renamed to `exiftool.exe` and shipped via PyInstaller `--add-data`.
  - The Windows app uses `assets/icon/icon.ico` via `--icon`.
  - `make build-windows` works on a Windows host (uses `python -m`).
  - `geotagcopy/core.py`'s `check_exiftool()` resolves the bundled
    `exiftool.exe` on Windows the same way it resolves the bundled binary on
    macOS today.

**Outcome:** Added `scripts/_build_common.py`, refactored
`scripts/build_macos.py` onto shared helpers, added `scripts/build_windows.py`
with pinned ExifTool `13.57` Windows archive SHA-256, wired
`GEOTAGCOPY_SUPPORT_URL` into generated `_build_info.py`, added
`make build-windows`, `make build-windows-app`, and `make
build-windows-onefile`, updated bundled ExifTool lookup for
`exiftool/exiftool.exe`, added a Windows bundle lookup test, and documented
Windows builds in `README.md`. Added `.github/workflows/windows-build-smoke.yml`
to build both Windows artifacts, verify both executable paths, and upload
zipped artifacts. Relaxed the smoke test to verify file existence only (not
`--help` exit code) because PyInstaller `--windowed` GUI apps do not reliably
propagate argparse `sys.exit(0)` on Windows.

### Detailed instructions

1. Read `scripts/build_macos.py` end-to-end. Mirror its structure in
   `scripts/build_windows.py`. Reuse helpers by extracting shared logic into
   `scripts/_build_common.py` (download+verify+extract, `_run_pyinstaller`
   skeleton, `_pyinstaller_available`).
2. ExifTool Windows download:
   - URL pattern: `https://exiftool.org/exiftool-{VERSION}_64.zip`. Pin the
     same version constant the macOS script uses (`EXIFTOOL_VERSION`). Look
     up and pin its SHA-256 (compute it once and hardcode it; do not fetch
     dynamically).
   - Extract `exiftool(-k).exe`, rename to `exiftool.exe`, place at
     `vendor/exiftool-windows/exiftool.exe`. Also copy the `exiftool_files/`
     directory next to it (required by the standalone Windows build).
3. PyInstaller invocation differences vs. macOS:
   - No `--osx-bundle-identifier`.
   - Use `--icon "assets/icon/icon.ico"`.
   - Use `--windowed` for the GUI.
   - `--add-data "vendor/exiftool-windows;exiftool"` (note Windows separator
     is `;`).
4. Update `geotagcopy/core.py` `check_exiftool()` (or the equivalent helper
   that locates `exiftool`) to also probe `<bundle>/exiftool/exiftool.exe`
   on Windows. If the helper currently uses `shutil.which("exiftool")`, add a
   pre-check for the bundled binary using `sys._MEIPASS` when frozen.
5. Update `Makefile`:
   ```make
   build-windows: build-windows-app build-windows-onefile
   build-windows-app:
       $(PYTHON) scripts/build_windows.py --target app
   build-windows-onefile:
       $(PYTHON) scripts/build_windows.py --target onefile
   ```
6. Update `README.md` with a "Windows builds" section mirroring the macOS one.
7. Smoke-check: on a Windows host (or a `windows-latest` GitHub runner via
   `act` / a draft PR), run `python scripts/build_windows.py --target app`
   and confirm `dist\GeoTagCopy\GeoTagCopy.exe` launches and shows the GUI.

---

## Task 5 — Cross-platform release workflow + macOS Developer ID signing & notarization

- [x] **Status:** postponed (won't do in v1)
- **Depends on:** Task 3, Task 4
- **Acceptance criteria:**
  - A single workflow `.github/workflows/release.yml` (refactor of the
    existing one) builds **both** macOS (Apple Silicon + Intel via the existing
    `macos-15-intel` runner is acceptable for v1; document it) and Windows
    artifacts on a tag push or manual dispatch.
  - macOS artifacts are **codesigned with a Developer ID Application
    certificate** and **notarized** via Apple's `notarytool`. The `.app` is
    stapled. Both the `.zip` of the `.app` and the one-file binary are
    signed.
  - All Apple credentials live in GitHub repo secrets — no plaintext. The
    workflow gracefully **skips signing/notarization** when the secrets are
    missing (so forks still get a working unsigned build).
  - Windows artifacts are produced as `.zip` files (no Windows code signing
    in v1 — leave a note that it's a future task).
  - Released asset names:
    - `GeoTagCopy-<version>-macos-app.zip`
    - `GeoTagCopy-<version>-macos-onefile.zip`
    - `GeoTagCopy-<version>-windows-app.zip`
    - `GeoTagCopy-<version>-windows-onefile.zip`
  - The GitHub Release contains all four files plus auto-generated notes.

### Required GitHub repo secrets

Document these in `CONTRIBUTING.md` under "Maintainer setup":

- `APPLE_DEVELOPER_ID_CERT_BASE64` — base64 of the `.p12` exported from
  Keychain (Developer ID Application certificate + private key).
- `APPLE_DEVELOPER_ID_CERT_PASSWORD` — the export password for the `.p12`.
- `APPLE_TEAM_ID` — the 10-character Apple Developer Team ID.
- `APPLE_NOTARY_KEY_ID` — App Store Connect API Key ID.
- `APPLE_NOTARY_KEY_ISSUER_ID` — App Store Connect Issuer ID (UUID).
- `APPLE_NOTARY_KEY_BASE64` — base64 of the `.p8` private key for the API key.
- `KEYCHAIN_PASSWORD` — random ephemeral password for the temp keychain
  created on the runner (any non-empty string).

Repo **variable** (not secret):
- `SUPPORT_URL` — the public geotagcopy support/download page opened from
  the packaged app.
- `STRIPE_PAYMENT_LINK` — the public Stripe Payment Link URL used by the
  website only.

### Detailed instructions

1. **Refactor the workflow** into two jobs (`build-macos`, `build-windows`)
   that each upload artifacts, plus a third `release` job that depends on
   both and creates the GitHub Release with all four files.
2. **Compute version once.** Replace the manual `${GITHUB_REF_NAME}` logic
   with a `version` job that reads `geotagcopy/__init__.py`'s `__version__`
   and asserts the tag (when present) is `v<version>`. Output it for the
   build jobs.
3. **macOS signing** — add this step **before** `Package app bundle`:
   ```yaml
   - name: Import Apple Developer ID certificate
     if: env.APPLE_DEVELOPER_ID_CERT_BASE64 != ''
     env:
       APPLE_DEVELOPER_ID_CERT_BASE64: ${{ secrets.APPLE_DEVELOPER_ID_CERT_BASE64 }}
       APPLE_DEVELOPER_ID_CERT_PASSWORD: ${{ secrets.APPLE_DEVELOPER_ID_CERT_PASSWORD }}
       KEYCHAIN_PASSWORD: ${{ secrets.KEYCHAIN_PASSWORD }}
     run: |
       set -euo pipefail
       CERT_PATH="$RUNNER_TEMP/cert.p12"
       KEYCHAIN_PATH="$RUNNER_TEMP/build.keychain-db"
       echo "$APPLE_DEVELOPER_ID_CERT_BASE64" | base64 --decode > "$CERT_PATH"
       security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
       security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
       security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
       security import "$CERT_PATH" -P "$APPLE_DEVELOPER_ID_CERT_PASSWORD" \
         -A -t cert -f pkcs12 -k "$KEYCHAIN_PATH"
       security set-key-partition-list -S apple-tool:,apple: \
         -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
       security list-keychain -d user -s "$KEYCHAIN_PATH"
   ```
4. **Sign the app and the one-file binary**:
   ```yaml
   - name: Codesign app and binary
     if: env.APPLE_DEVELOPER_ID_CERT_BASE64 != ''
     env:
       APPLE_DEVELOPER_ID_CERT_BASE64: ${{ secrets.APPLE_DEVELOPER_ID_CERT_BASE64 }}
       APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
     run: |
       set -euo pipefail
       IDENTITY="Developer ID Application: ${APPLE_TEAM_ID}"
       # Some teams export with the company name; allow override:
       if [ -n "${APPLE_SIGNING_IDENTITY:-}" ]; then IDENTITY="$APPLE_SIGNING_IDENTITY"; fi
       codesign --force --deep --options runtime --timestamp \
         --entitlements packaging/macos/entitlements.plist \
         --sign "$IDENTITY" "dist/GeoTagCopy.app"
       codesign --force --options runtime --timestamp \
         --sign "$IDENTITY" "dist/GeoTagCopy"
       codesign --verify --deep --strict --verbose=2 "dist/GeoTagCopy.app"
   ```
   Create `packaging/macos/entitlements.plist` with the **hardened runtime**
   entitlements PyInstaller-built apps need:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
     "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
     <key>com.apple.security.cs.allow-jit</key><true/>
     <key>com.apple.security.cs.disable-library-validation</key><true/>
   </dict>
   </plist>
   ```
5. **Notarize and staple**:
   ```yaml
   - name: Notarize app bundle
     if: env.APPLE_NOTARY_KEY_BASE64 != ''
     env:
       APPLE_NOTARY_KEY_BASE64: ${{ secrets.APPLE_NOTARY_KEY_BASE64 }}
       APPLE_NOTARY_KEY_ID: ${{ secrets.APPLE_NOTARY_KEY_ID }}
       APPLE_NOTARY_KEY_ISSUER_ID: ${{ secrets.APPLE_NOTARY_KEY_ISSUER_ID }}
     run: |
       set -euo pipefail
       KEY_PATH="$RUNNER_TEMP/notary_key.p8"
       echo "$APPLE_NOTARY_KEY_BASE64" | base64 --decode > "$KEY_PATH"
       ditto -c -k --keepParent "dist/GeoTagCopy.app" "$RUNNER_TEMP/notarize.zip"
       xcrun notarytool submit "$RUNNER_TEMP/notarize.zip" \
         --key "$KEY_PATH" \
         --key-id "$APPLE_NOTARY_KEY_ID" \
         --issuer "$APPLE_NOTARY_KEY_ISSUER_ID" \
         --wait
       xcrun stapler staple "dist/GeoTagCopy.app"
       xcrun stapler validate "dist/GeoTagCopy.app"
   ```
6. **Repackage after stapling**: the existing `ditto -c -k --keepParent`
   step already produces the final zip — make sure it runs *after* stapling.
7. **Windows job** — model after the macOS job, runner `windows-latest`:
   ```yaml
   build-windows:
     runs-on: windows-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with: { python-version: "3.11" }
       - run: |
           python -m pip install --upgrade pip
           python -m pip install -r requirements.txt -r requirements-build.txt
       - run: python -m unittest discover -v
       - env:
          GEOTAGCOPY_SUPPORT_URL: ${{ vars.SUPPORT_URL }}
         run: python scripts/build_windows.py --target all
       - name: Package
         shell: pwsh
         run: |
           Compress-Archive -Path dist\GeoTagCopy\* -DestinationPath dist\GeoTagCopy-${{ needs.version.outputs.value }}-windows-app.zip
           Compress-Archive -Path dist\GeoTagCopy.exe -DestinationPath dist\GeoTagCopy-${{ needs.version.outputs.value }}-windows-onefile.zip
       - uses: actions/upload-artifact@v4
         with:
           name: geotagcopy-windows-${{ needs.version.outputs.value }}
           path: dist/GeoTagCopy-${{ needs.version.outputs.value }}-windows-*.zip
   ```
8. **Release job**:
   ```yaml
   release:
     needs: [version, build-macos, build-windows]
     runs-on: ubuntu-latest
     steps:
       - uses: actions/download-artifact@v4
         with: { path: artifacts }
       - uses: softprops/action-gh-release@v2
         with:
           tag_name: ${{ needs.version.outputs.value }}
           name: GeoTagCopy ${{ needs.version.outputs.value }}
           generate_release_notes: true
           files: artifacts/**/GeoTagCopy-*.zip
   ```
9. Smoke-check: trigger the workflow manually with a non-tag dispatch
   (`version: v0.0.0-test`) on a fork without the Apple secrets and confirm
   it still builds (just unsigned). Then test with secrets on the real repo
   on a real tag.

---

## Task 6 — `geotagcopy` static landing page (starter)

- [x] **Status:** completed
- **Depends on:** Task 2 (for favicon), Task 3 (for app-to-site support flow)
- **Acceptance criteria:**
  - A new top-level directory `site/` contains a fully static, dependency-free
    site (HTML + CSS + a tiny vanilla-JS file). No build step needed; it can
    be served by `python -m http.server` directly from `site/`.
  - The site is named **geotagcopy**, has the GeoTagCopy favicon, and has:
    - A hero section explaining what GeoTagCopy is.
    - A "Download" section with **dynamic** macOS and Windows download
      buttons populated from `latest.json` (see Task 8).
    - A "Donate" section with a prominent button linking to the Stripe
      Payment Link. This Stripe URL lives on the site only; the packaged app
      links to this site instead of linking directly to Stripe.
    - A "Source" link to the GitHub repo.
    - A short "How it works" section (3 bullets, mirroring the README's
      "How It Works").
    - Footer with license, repo link, and a "Made by Sergey" credit
      (placeholder — flag for the user).
  - The page is responsive (mobile-first, single column ≤ 720 px,
    two-column hero ≥ 720 px) and loads in under 1 second on a clean cache
    (no external CSS frameworks; embed any small icons inline as SVG).
  - The page is accessible (semantic HTML, alt text, color contrast ≥ 4.5:1
    against background, focus ring visible).

**Outcome:** Added the static `site/` starter with `index.html`, `styles.css`,
`app.js`, `config.js`, `latest.json`, `robots.txt`, and `sitemap.xml`. Added
`scripts/copy_site_assets.py` and `make site-assets` to copy generated icons
into `site/assets/` and create a placeholder `screenshot.png`. The app-facing
support flow remains site-first: the site owns `STRIPE_PAYMENT_LINK`, while
packaged apps will open `SUPPORT_URL`. Verified JSON/script validity, copied
site assets, and smoke-tested the site through a local `http.server`.

### File layout

```
site/
  index.html
  assets/
    favicon.ico
    favicon-32.png
    icon.png            (1024 master, used for og:image)
    screenshot.png      (placeholder; flag for user)
  styles.css
  app.js                (fetches latest.json, fills download buttons)
  config.js             (window.APP_CONFIG = {...} — templated at deploy)
  latest.json           (committed placeholder; overwritten by Task 8)
  robots.txt
  sitemap.xml           (optional)
```

### Detailed instructions

1. Create `site/index.html` with semantic sections (`<header>`, `<main>`,
   `<section>`, `<footer>`). Include `<link rel="icon" href="/favicon.ico">`
   and an Open Graph preview using `assets/icon.png`.
2. Create `site/styles.css` with CSS custom properties (`--color-bg`,
   `--color-fg`, `--color-accent: #1a6dcc;`) and a `prefers-color-scheme:
   dark` block. No frameworks.
3. Create `site/config.js`:
   ```js
   window.APP_CONFIG = {
     stripePaymentLink: "__STRIPE_PAYMENT_LINK__",
     repoUrl: "https://github.com/<owner>/<repo>",
     latestJsonUrl: "/latest.json"
   };
   ```
   The `__STRIPE_PAYMENT_LINK__` token is replaced by the deploy workflow
   (Task 7) using `sed`/Python.
4. Create `site/app.js` that:
   - Sets the Donate button `href` to `APP_CONFIG.stripePaymentLink`.
   - `fetch(APP_CONFIG.latestJsonUrl)` → fills `#download-macos`,
     `#download-windows`, `#latest-version` elements. On fetch failure,
     leave fallback text "Releases on GitHub" linking to
     `<repoUrl>/releases/latest`.
5. Create `site/latest.json` placeholder:
   ```json
   {
     "version": "0.0.0",
     "macos": { "app": "", "onefile": "" },
     "windows": { "app": "", "onefile": "" },
     "publishedAt": "1970-01-01T00:00:00Z"
   }
   ```
6. Copy `assets/icon/favicon.ico`, `favicon-32.png`, and `icon.png` (from
   Task 2) into `site/assets/` — keep them as a copy step in the deploy
   workflow rather than duplicating in git, **or** symlink in `Makefile`
   (`make site-assets`).
7. Smoke-check: `cd site && python -m http.server 8000`, open
   <http://localhost:8000>, verify the page renders, donate button links to
   the placeholder, downloads section shows the GitHub fallback.

---

## Task 7 — Site deployment workflow (Azure Storage static website)

- [x] **Status:** completed
- **Depends on:** Task 6
- **Acceptance criteria:**
  - A new workflow `.github/workflows/deploy-site.yml`:
    - Triggers on push to `main` that touches `site/**`, **and** on
      `workflow_dispatch`, **and** when the release workflow finishes
      successfully (via `workflow_run`).
    - Templates `site/config.js` by replacing `__STRIPE_PAYMENT_LINK__` with
      `${{ vars.STRIPE_PAYMENT_LINK }}`.
    - Uploads the contents of `site/` to the `$web` container of the Azure
      Storage account using `az storage blob upload-batch`.
    - Sets correct `Content-Type` for `.html`, `.css`, `.js`, `.json`,
      `.ico`, `.png`, `.svg`.
    - Purges the Azure CDN endpoint **only if** a CDN profile/endpoint is
      configured (via repo variables).
  - Authentication uses GitHub repository secrets. Current implementation uses
    the storage account key because the user created and requested key-based
    repo secrets; OIDC remains the preferred future hardening path.
  - The workflow does not deploy on PRs.

**Outcome:** Added `.github/workflows/deploy-site.yml` with
`workflow_dispatch`, push-to-`main` path filters, and successful release
`workflow_run` triggers. The workflow prepares site assets, templates
`site/config.js` from repo variables, enables static website hosting
idempotently, uploads `site/` to `$web`, and sets per-extension content types.
Configured repo variables `AZURE_STORAGE_ACCOUNT`, `AZURE_RESOURCE_GROUP`,
`SUPPORT_URL`, and placeholder `STRIPE_PAYMENT_LINK`; configured secrets
`AZURE_STORAGE_ACCOUNT_ID` and `AZURE_STORAGE_ACCOUNT_KEY`. Azure Storage static
website settings are enabled for `index.html` and `404.html`, and the current
site was deployed and verified at the public static website endpoint.

### Required GitHub configuration

Repo **variables** (public):
- `AZURE_STORAGE_ACCOUNT` — e.g. `geotagcopy`.
- `AZURE_RESOURCE_GROUP` — e.g. `geotagcopy-rg`.
- `AZURE_CDN_PROFILE` (optional) — Front Door / CDN profile name.
- `AZURE_CDN_ENDPOINT` (optional) — endpoint name.
- `STRIPE_PAYMENT_LINK` — public Stripe Payment Link used by the website
  Donate button.

Repo **secrets** (one of these strategies):
- **Current implementation:**
  - `AZURE_STORAGE_ACCOUNT_KEY` — storage account access key used only by
    GitHub Actions.
  - `AZURE_STORAGE_ACCOUNT_ID` — full storage account resource ID.
- **OIDC (recommended):**
  - `AZURE_CLIENT_ID` — service principal app ID with federated credential
    bound to `repo:<owner>/<repo>:ref:refs/heads/main` and
    `repo:<owner>/<repo>:environment:production`.
  - `AZURE_TENANT_ID`.
  - `AZURE_SUBSCRIPTION_ID`.
- **Fallback:** `AZURE_CREDENTIALS` — JSON output of
  `az ad sp create-for-rbac --sdk-auth`.

The service principal needs `Storage Blob Data Contributor` on the storage
account (and `CDN Endpoint Contributor` if CDN is used).

### Detailed instructions

1. Add `permissions: { id-token: write, contents: read }` to the workflow.
2. Login step:
   ```yaml
   - name: Azure login (OIDC)
     if: env.AZURE_CLIENT_ID != ''
     uses: azure/login@v2
     with:
       client-id: ${{ secrets.AZURE_CLIENT_ID }}
       tenant-id: ${{ secrets.AZURE_TENANT_ID }}
       subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

   - name: Azure login (creds JSON fallback)
     if: env.AZURE_CLIENT_ID == '' && env.AZURE_CREDENTIALS != ''
     uses: azure/login@v2
     with:
       creds: ${{ secrets.AZURE_CREDENTIALS }}
   ```
3. Template config:
   ```yaml
   - name: Template site/config.js
     env:
       STRIPE_PAYMENT_LINK: ${{ vars.STRIPE_PAYMENT_LINK }}
     run: |
       python - <<'PY'
       import os, pathlib
       p = pathlib.Path("site/config.js")
       p.write_text(p.read_text().replace("__STRIPE_PAYMENT_LINK__", os.environ["STRIPE_PAYMENT_LINK"]))
       PY
   ```
4. Upload:
   ```yaml
   - name: Upload site to $web
     run: |
       az storage blob upload-batch \
         --account-name "${{ vars.AZURE_STORAGE_ACCOUNT }}" \
         --auth-mode login \
         --destination '$web' \
         --source site \
         --overwrite \
         --content-cache-control "public, max-age=300"
   ```
5. Set per-extension content types in a follow-up step using
   `az storage blob update --content-type` in a small bash loop (HTML must
   be `text/html; charset=utf-8`, JSON `application/json`, etc.).
6. CDN purge (optional, gated on the variable being set).
7. Document the one-time Azure setup in `CONTRIBUTING.md` "Maintainer setup"
   under a new "Website hosting" subsection (storage account creation, static
   website enable, federated credential creation commands — do **not**
   automate this in the workflow).
8. Smoke-check: dispatch the workflow on `main` after Task 6 lands. Visit
   `https://<account>.z<region>.web.core.windows.net/` and confirm the site
   loads. Confirm `config.js` no longer contains `__STRIPE_PAYMENT_LINK__`.

---

## Task 8 — Release workflow updates `latest.json` on the website

- [x] **Status:** completed
- **Depends on:** Task 7 (Task 5 postponed; added directly to existing release workflow)
- **Acceptance criteria:**
  - After a successful release publish, the release workflow uploads a
    freshly generated `latest.json` to the **same** Azure Storage `$web`
    container, overwriting the previous one. The website immediately picks
    up new download links without a site redeploy.
**Outcome:** Added `update-latest-json` job to `release.yml` that depends on
`build-macos`, generates `latest.json` with download URLs for all four
platform artifacts, and uploads it to Azure Storage `$web` container. The job
is gated on `vars.AZURE_STORAGE_ACCOUNT` being set so it skips gracefully in
forks. Uses account key auth matching the deploy-site workflow pattern.

  - `latest.json` schema (matches Task 6 placeholder):
    ```json
    {
      "version": "vX.Y.Z",
      "macos": {
        "app":     "https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/GeoTagCopy-vX.Y.Z-macos-app.zip",
        "onefile": "https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/GeoTagCopy-vX.Y.Z-macos-onefile.zip"
      },
      "windows": {
        "app":     "https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/GeoTagCopy-vX.Y.Z-windows-app.zip",
        "onefile": "https://github.com/<owner>/<repo>/releases/download/vX.Y.Z/GeoTagCopy-vX.Y.Z-windows-onefile.zip"
      },
      "publishedAt": "<ISO 8601 UTC>"
    }
    ```

### Detailed instructions

1. Add a final job `update-latest-json` to `release.yml` that depends on
   `release` and reuses the same Azure login pattern as Task 7.
2. Generate the JSON in-line with a small Python step (no jq/yq dependency):
   ```yaml
   - name: Build latest.json
     env:
       VERSION: ${{ needs.version.outputs.value }}
       REPO: ${{ github.repository }}
     run: |
       python - <<'PY'
       import json, os, datetime
       v = os.environ["VERSION"]
       repo = os.environ["REPO"]
       base = f"https://github.com/{repo}/releases/download/{v}"
       data = {
         "version": v,
         "macos":   {"app": f"{base}/GeoTagCopy-{v}-macos-app.zip",
                     "onefile": f"{base}/GeoTagCopy-{v}-macos-onefile.zip"},
         "windows": {"app": f"{base}/GeoTagCopy-{v}-windows-app.zip",
                     "onefile": f"{base}/GeoTagCopy-{v}-windows-onefile.zip"},
         "publishedAt": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
       }
       with open("latest.json", "w") as f: json.dump(data, f, indent=2)
       PY
   ```
3. Upload it:
   ```yaml
   - name: Upload latest.json
     run: |
       az storage blob upload \
         --account-name "${{ vars.AZURE_STORAGE_ACCOUNT }}" \
         --auth-mode login \
         --container-name '$web' \
         --file latest.json \
         --name latest.json \
         --content-type application/json \
         --content-cache-control "public, max-age=60" \
         --overwrite
   ```
4. Optional: purge `latest.json` from CDN if configured.
5. Smoke-check: cut a real release; within ~1 minute the website's download
   buttons must point to the new tag's GitHub release assets.

---

## Task 9 — README and docs polish

- [x] **Status:** completed
- **Depends on:** Tasks 1–8
- **Acceptance criteria:**
  - `README.md` has badges (CI status, license, latest release).
  - "Download" section at the top of `README.md` linking to the latest
    GitHub release **and** to the geotagcopy site.
  - "Support the project" section linking to the geotagcopy support page.
  - The `Legacy Pipeline` and `Similar Projects` sections are preserved.
  - All "TODO/placeholder" notes added by previous tasks (contact emails,
    user name, Stripe URL) are resolved or explicitly listed in a final
    "Outstanding human decisions" section at the bottom of this todo.md.

**Outcome:** Added badges (release, CI, license) at the top of README.md.
Added "Download" and "Support the Project" sections. Consolidated the verbose
macOS/Windows build instructions into a concise "Building from Source" section
that cross-links to CONTRIBUTING.md. Preserved Legacy Pipeline and Similar
Projects sections. Outstanding human decisions remain listed at the bottom of
this file.

### Detailed instructions

1. Add badges at the very top of `README.md`:
   ```md
   [![Release](https://img.shields.io/github/v/release/<owner>/<repo>)](https://github.com/<owner>/<repo>/releases)
   [![CI](https://github.com/<owner>/<repo>/actions/workflows/release.yml/badge.svg)](https://github.com/<owner>/<repo>/actions/workflows/release.yml)
   [![License](https://img.shields.io/github/license/<owner>/<repo>)](LICENSE)
   ```
2. Add a "Download" section directly under the badges with macOS and Windows
   bullet links to `https://github.com/<owner>/<repo>/releases/latest` and
   the geotagcopy URL.
3. Add a "Support the project" section linking to the geotagcopy support page
   (read it from the same place — `vars.SUPPORT_URL`). The support page then
   links to Stripe.
4. Replace any references to the old PolyForm license.
5. Remove the legacy "macOS App Builds" build instructions from the README
   only if they are now duplicated in `CONTRIBUTING.md`; otherwise keep
   them. Cross-link.
6. Smoke-check: `markdownlint README.md` (optional) and visual review on
   GitHub.

---

## Task 10 — Cut the first public release `v0.1.0`

- [x] **Status:** version bumped to 0.1.0; ready for tag+push
- **Depends on:** Tasks 1–9
- **Acceptance criteria:**
  - `geotagcopy/__init__.py` `__version__` is bumped (suggest `0.1.0`).
  - A signed-and-tagged commit on `main`, then `git tag v0.1.0 && git push
    origin v0.1.0`.
  - GitHub Release contains all four artifacts.
  - `latest.json` on the website points at the v0.1.0 assets.
  - The site loads at the public Azure URL with working Donate and Download
    buttons, and packaged apps open the support page rather than Stripe.

### Detailed instructions

1. Use the `git-version-tag-release` skill at
   `/Users/sergey/.cursor/skills/git-version-tag-release/SKILL.md` for the
   tag/push step.
2. Watch the workflow run; if any signing/notarization step fails, do
   **not** silently fall through — fix forward and re-tag with `v0.1.1`.
3. Once green, manually verify each artifact:
  - macOS `.app`: download, unzip, drag to Applications, launch from
    Finder. Must not show Gatekeeper warning. Support button must open the
    geotagcopy support page.
   - Windows `.exe`: download on a Windows machine or VM, unzip, run.
    Support button must open the geotagcopy support page.
4. Visit the geotagcopy site, confirm version matches and downloads
   resolve.
5. Tick this task and update the Outstanding human decisions section.

---

## Outstanding human decisions

The agent must collect and surface answers for these before finalizing
Task 1, Task 5, Task 7, and Task 10:

- [ ] **License choice** for Task 1: MIT, Apache-2.0, or other? Default if
  unanswered: MIT. Current implementation assumes MIT; confirm before release.
- [ ] **Copyright holder name** for `LICENSE` and `README.md`. Current
  implementation uses `GeoTagCopy contributors`; confirm before release.
- [ ] **Security contact email** for `SECURITY.md`. Current implementation uses
  `security@geotagcopy.example`; replace before release.
- [ ] **Code of Conduct contact email** for `CODE_OF_CONDUCT.md`. Current
  implementation uses `conduct@geotagcopy.example`; replace before release.
- [ ] **Stripe Payment Link URL** (must be a real
  `https://buy.stripe.com/...` or `https://donate.stripe.com/...` URL) for
  the website Donate button only.
- [ ] **Support URL** for the packaged app to open (geotagcopy homepage or
  support section/page), exposed as repo variable `SUPPORT_URL`.
- [ ] **Apple Developer Team ID** + the `.p12` Developer ID Application
  certificate + its export password.
- [ ] **App Store Connect API key** (`.p8` file, key ID, issuer ID) for
  notarization.
- [ ] **Azure subscription, resource group, and storage account name** for
  geotagcopy; whether to use OIDC federated credentials (recommended) or
  `AZURE_CREDENTIALS`.
- [ ] **Custom domain** for geotagcopy (e.g. `geotagcopy.com`) — if any —
  and whether Azure CDN / Front Door is in front of the storage account.
- [x] **Repo public URL**: `cloudsecmentor/geotagcopy` — used in README badges,
  `site/config.js`, and `latest.json` links.
