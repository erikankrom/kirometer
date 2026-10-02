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

Default usage collection cadence is five minutes; usage becomes stale only when its age exceeds one hour. Explicit upstream failed-cache readings and unknown timestamps remain stale. Activity checks run independently every 250 ms. Optional app config fields are `db_path`, `poll_seconds` (5–3600), and `stale_after` (0–86400). Profile paths are detected for macOS, Windows and Linux. Real Windows Crew execution has not been validated.

The collector first reads Crew's existing signed-in billing cache through a version-bound in-process adapter; it never triggers billing refresh. If that cache is unavailable, it reads Kiro IDE's local SQLite usage cache in read-only mode. It does not read authentication stores, scan transcripts, refresh billing, or call a cloud API. This is an internal IDE cache schema and may change. The currently observed machine cache is stale.

Activity follows Crew session/task state (Ready, Working, Needs attention, Complete, Error or Unknown). It describes sessions visible to Crew, not every IDE session. Plan name is read from Crew’s validated billing cache; signed-in identity is not exported by this collector. The app page shows actual collector data rather than preview fixtures.

## Validation and next steps

`python3 -m unittest -v` includes missing-data, overage, read-only, invalid-number, and repeated startup/shutdown checks. `node --check crew-app/ui/index.mjs` checks the shipped UI module. Crew's installer accepted this manifest on 0.7.2. The app runs in the live gateway; UI and authenticated device APIs have been checked. Firmware 0.5.8 has been flashed and boot/status/Bluetooth sync verified; see device-management.md for physical display checks.

The app includes firmware installation and bidirectional USB usage/status transport. See [macOS device management](device-management.md). Bluetooth LE now carries usage sync and controls; USB is used for flashing and first-time provisioning.

References: [Crew apps](https://kiro.dev/docs/crew/apps/), [app manifest](https://kiro.dev/docs/crew/apps/manifest/), [SDK](https://kiro.dev/docs/crew/apps/sdk/).

Remote install and release publishing: [release channel](remote-releases.md).

## AI screen designer (Beta)

Open **Create with Kiro · Beta** in the top header. Describe a design,
then generate or refine its preview, review normal/overage/unavailable sample data,
and save it to the local gallery. Generation uses the signed-in `kiro-cli` and can
consume plan credits. It also works without a connected device.

**Use as default** sends a saved face to a selected connected device with firmware
0.9.0 or later. The beta has one persistent custom slot per device, in addition to
all six built-in faces. Applying another design replaces that slot. Swipe through
all seven faces; changing faces manually does not replace the startup default.
Gallery deletion does not remove a device's installed copy.

The generator runs a tool-free custom agent in a temporary workspace, with no MCP
servers, no trusted tools, no repository context, and a 120-second timeout. It
returns JSON rather than source code. The app and firmware independently validate
schema version 1: at most 12 elements and 2 KB, fixed color/font choices, ASCII
labels, known metric bindings, and bounded rectangles inside the reserved content
area. Unknown properties, code, remote assets, and expressions are rejected.
The beta supports text, metrics, bars, panels, and the official ghost, without
custom animations. Core status indicators, gesture handling, power, Bluetooth,
updates, sleep and wake remain outside the face definition. A bad stored face
falls back to a built-in face at boot. Invalid uploads do not stop usage delivery.

The browser preview uses the shipped Space Grotesk fonts and ghost atlas. Browser
font rasterization differs from the device; preview text may differ slightly.

### App navigation

The right-aligned header links open Devices, Screen gallery, and Create with Kiro (Beta). Each has a bookmarkable fragment URL (`#/devices`, `#/gallery`, `#/create`) under the single Crew sidebar entry. Browser Back/Forward switches pages. Device information, default screen, customization, connection, and firmware remain body tabs on Devices; no nested page hierarchy is introduced. Switching pages preserves device settings and AI drafts for the current app session.
