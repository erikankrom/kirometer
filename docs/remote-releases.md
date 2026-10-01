# Crew remote repository and release channel

The source app stays in `crew-app/` alongside firmware and CAD. The release workflow (`.github/workflows/crew-release.yml`) publishes a minimal Crew-compatible repository tree to branch `crew-release`:

```
app-registry.json
apps/kirometer/
  app.json
  README.md
  backend/
  ui/index.mjs
  ui/art/
  vendor/wheels/
  firmware/firmware.json
  firmware/kirometer-<version>-*.bin
```

Crew supports `gitUrl`, `branch`, and `subdirectory` in an external registry index. Generated metadata points to `apps/kirometer`. UI is already built; installation needs no npm build. The runtime ZIP includes only named artwork, checksummed tool wheels, and the four current flash regions. Personal data, pairing secrets, installed state, old firmware, build caches and unused artwork are excluded.

## Publish a release

1. This project is hosted in `https://github.com/erikankrom/kirometer`. The workflow derives the repository URL from GitHub; no hostname or personal token is embedded in source.
2. Change `crew-app/app.json` version. If firmware changed, build with `pio run -d firmware`, then run `python3 scripts/build_firmware_bundle.py`. Commit the generated binary files and manifest as well as app changes.
3. Publish a **non-prerelease** GitHub release named/tagged `v<app version>` (currently `v0.7.0`). Its tag must point to the versioned source commit.
4. GitHub Actions validates tests and checksums, attaches `kirometer-crew-app.zip`, and advances `crew-release` using a normal non-force push. Workflow write permission to repository contents must be allowed. Prereleases do not advance the stable channel.
5. Add that repository URL to Crew's external registries with branch **crew-release**. Install Kirometer from that registry and trust the app. An existing local install must be switched to the registry-backed source using Crew's supported lifecycle UI/API to retain correct update provenance; merely copying files does not establish it.

Updating the app does not automatically flash hardware or change bonding. Flash through the app over USB-C when ready.

## What is automatic

Publishing a GitHub release automatically produces and publishes the Crew package and advances the stable repository branch. Crew can discover the latest app metadata from that branch (its metadata cache can last 24 hours unless refreshed).

The current documented Crew update mechanism is **Sync/update in Apps** or `POST /api/apps/kirometer/update`. This is not unattended installation triggered by a GitHub release. No undocumented auto-update config, self-replacing backend, OS daemon, or scheduled agent is installed by this project. An unattended installation scheduler remains a separate integration requirement.

## Validate without publishing

```sh
python3 scripts/package_crew_app.py
python3 scripts/package_crew_app.py \
  --registry-dir .dist/crew \
  --repo https://github.com/erikankrom/kirometer
```

The registry destination must not already exist. No remote changes are made by this command. Install `.dist/crew/apps/kirometer` locally to test the exact release payload before publishing.

Official reference: [Crew publishing and guidelines](https://kiro.dev/docs/crew/apps/publishing/), verified October 1, 2026. The installed Crew registry implementation also supports nested apps and root `app-registry.json`.

## This repository

Registry URL: `https://github.com/erikankrom/kirometer.git`

Registry branch: `crew-release`

App name: `kirometer`

The repository is private. Crew needs a GitHub connection or Git credentials with read access as `erikankrom` (or another authorized collaborator). Browser sign-in alone does not grant the Crew gateway Git access. Keep credentials in Crew/Git credential storage, never in the registry URL.
