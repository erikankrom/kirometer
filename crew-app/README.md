# Kirometer for Kiro Crew

A little companion for your Kiro day: credits and activity on a small AMOLED desk display, with the original Kiro ghost.

![Kirometer](ui/art/banner-kiro-light.svg)

## What it does

- Shows monthly credits, remaining allowance, overage and Crew session activity.
- Choose Ghost companion or Usage dashboard from a visual gallery; the selection is saved on the device.
- Connects over Bluetooth LE without joining Wi-Fi.
- Guides initial USB-C firmware flashing and pairing on macOS.
- Controls brightness, device name and display sleep; touch wakes the device.
- Reconnects automatically after a temporary Bluetooth interruption.
- Includes directional ghost animations and a black screensaver.

Requires Kiro Crew 0.7.2 or later. Device tools currently target Apple Silicon macOS with Crew's bundled Python 3.12. Other platforms are not yet validated. Hardware: Waveshare ESP32-S3-Touch-AMOLED-2.16.

## Install

Install this folder through Crew Apps, trust `kirometer` in `agent.apps_trusted`, and enable it. Keep existing trusted entries when adding this one. Open **Apps → Kirometer → Add a device**. Use a data-capable USB-C cable for first setup. Allow Crew Bluetooth access when macOS requests it. After provisioning, Bluetooth handles usage sync and controls.

Firmware updates currently require USB-C. Updating the Crew app makes the new firmware bundle available; it does not flash a connected device automatically.

## Data and privacy

Reads Crew's local billing cache, with the Kiro IDE SQLite cache as a fallback. Activity describes sessions visible to Crew, not all IDE activity. It does not read prompts or source code, collect account credentials, or refresh cloud billing. Old usage is labeled stale and unavailable data is not fabricated. The gateway must remain running for background collection and Bluetooth sync.

Pairing credentials and device tools belong in Crew's app data directory, outside this distributable package. Crew preserves that data during ordinary app updates. Removing device bonding may require provisioning again over USB.

## Updates

The repository release workflow publishes a complete package to the `crew-release` branch, including built UI, artwork, offline macOS tools and checksummed firmware. Configure that branch as a Crew external registry. The index points to `apps/kirometer`.

Crew checks repository metadata and applies updates using its Sync/update action. A GitHub release does not, by itself, silently install on a user's computer. Unattended installation needs an additional supported Crew update scheduler; this package does not create an OS service or bypass Crew's trust controls.

## Artwork

Kiro artwork is from Amazon's [Spirit of Kiro](https://github.com/kirodotdev/spirit-of-kiro). See `ui/art/SOURCES.md` and `firmware/GHOST-LICENSE`. West is a mirrored East pose. Screenshots use illustrative data. This is a community hardware project.
