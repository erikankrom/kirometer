# Release notes

## 0.9.1

- Move default-face selection into the first Default screen tab.
- Use the existing Crew app enclosure icon on connected, setup, and empty device cards.

## 0.9.0

- Add Orbit, Sidekick, Credit ticket, and The big number in firmware 0.6.0.
- Swipe through all six faces from any face or detail view; Crew controls the separate startup default.
- Embed larger Space Grotesk metrics and antialiased Lucide status icons.
- Browse every screen preview before connecting a device.
- Show live firmware console output and retain the last eight update results locally.

## 0.8.0

- Embed Kiro Crew’s Space Grotesk in firmware 0.5.10 with 4-bit antialiasing at four native sizes.
- Document shared typography, color, layout, icon, motion, and gallery standards in DESIGN.md.

- Visual screen gallery with previews, descriptions, on-device and pending-selection labels.
- New Usage dashboard: plan banner, credits used/allowance, percentage, reset date, and a red overage meter. Overage is compared with plan allowance, never an invented cap or timed window.
- Firmware 0.5.10 saves the selected layout across restart and includes it in USB/Bluetooth status.
- Both layouts retain black backgrounds, bounded ghost animations, touch for metric details and touch-wake screensaver.
- Devices on older firmware can keep using existing controls; the gallery explains the firmware requirement.

## 0.7.0

- Restore automatic Bluetooth reconnection with bounded backoff after transient failures. Explicit disconnect cancels retries; a removed bond requires provisioning.
- Match USB status to the acknowledged sequence so old status cannot mask a new activity state.
- Initialize activity observation from device requests as well as the usage page.
- Bundle firmware 0.5.8: distinct directional ghost behavior for Ready, Working, Needs attention, Complete, Error and Unknown, at 20 FPS in reserved black space.
- Preserve touch-wake screensaver, device name, brightness and bonding during the four-region flash.
- Add reproducible Crew ZIP and GitHub release-channel packaging with firmware/tool checksums and a runtime-only file list.
