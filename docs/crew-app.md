# Kirometer Crew app

The preferred collector is now `crew-app/`, a self-contained Kiro Crew app. Crew loads Python lifecycle hooks, starts one background polling task when enabled, cancels it on disable/shutdown, and hosts a native React app page. No login token, shell service, agent or scheduled AI session is required. USB tools are installed offline from bundled wheels. The app uses Crew's existing Python and UI runtime.

## Install and enable

In Crew's Apps page, install the local `crew-app` directory, or run:

```sh
kirocrew app install /absolute/path/to/kirometer/crew-app
kirocrew app enable kirometer
```

On this Mac the package has been installed as `kirometer` version 0.7.0. The user has granted app-specific trust and the app is enabled. On a new installation, add **kirometer** to **agent.apps_trusted**, then enable it in Apps. Trusting an app permits its Python to execute inside the gateway. Only this app needs trust; the global allow-all option is unnecessary.

Open Kirometer under Apps. The collector continues while its page is closed, as long as the Crew gateway runs. Disable the app to stop collection. There is no separate OS daemon to install.

## Data contract

Authenticated Crew app routes:

- `GET /api/apps/kirometer/snapshot`: normalized usage, freshness, source, activity and collection timestamp.
- `GET /api/apps/kirometer/health`: background-task liveness and cache availability; these are separate indicators.

The snapshot is schema version 1. `observed_at` and `age_seconds` describe the **Kiro cache**, whereas `collected_at` describes this collector's read. A recent read never makes an old cache fresh. Credit fields include `used`, `limit`, `remaining_plan_credits`, `used_percent`, `reset_at`, and `overage_used` (usage exceeding the base allotment). Missing data stays null/unavailable. Add-on packs and monetary overage costs are not inferred.

Default cadence is 15 seconds; default stale threshold is five minutes. Optional app config fields are `db_path`, `poll_seconds` (5–300), and `stale_after` (0–86400). Profile paths are detected for macOS, Windows and Linux. Real Windows Crew execution has not been validated.

The collector first reads Crew's existing signed-in billing cache through a version-bound in-process adapter; it never triggers billing refresh. If that cache is unavailable, it reads Kiro IDE's local SQLite usage cache in read-only mode. It does not read authentication stores, scan transcripts, refresh billing, or call a cloud API. This is an internal IDE cache schema and may change. The currently observed machine cache is stale.

Activity follows Crew session/task state (Ready, Working, Needs attention, Complete, Error or Unknown). It describes sessions visible to Crew, not every IDE session. Plan name is read from Crew’s validated billing cache; signed-in identity is not exported by this collector. The app page shows actual collector data rather than preview fixtures.

## Validation and next steps

`python3 -m unittest -v` includes missing-data, overage, read-only, invalid-number, and repeated startup/shutdown checks. `node --check crew-app/ui/index.mjs` checks the shipped UI module. Crew's installer accepted this manifest on 0.7.2. The app runs in the live gateway; UI and authenticated device APIs have been checked. Firmware 0.5.8 has been flashed and boot/status/Bluetooth sync verified; see device-management.md for physical display checks.

The app includes firmware installation and bidirectional USB usage/status transport. See [macOS device management](device-management.md). Bluetooth LE now carries usage sync and controls; USB is used for flashing and first-time provisioning.

References: [Crew apps](https://kiro.dev/docs/crew/apps/), [app manifest](https://kiro.dev/docs/crew/apps/manifest/), [SDK](https://kiro.dev/docs/crew/apps/sdk/).

Remote install and release publishing: [release channel](remote-releases.md).
