# Release notes

## 0.7.0

- Restore automatic Bluetooth reconnection with bounded backoff after transient failures. Explicit disconnect cancels retries; a removed bond requires provisioning.
- Match USB status to the acknowledged sequence so old status cannot mask a new activity state.
- Initialize activity observation from device requests as well as the usage page.
- Bundle firmware 0.5.8: distinct directional ghost behavior for Ready, Working, Needs attention, Complete, Error and Unknown, at 20 FPS in reserved black space.
- Preserve touch-wake screensaver, device name, brightness and bonding during the four-region flash.
- Add reproducible Crew ZIP and GitHub release-channel packaging with firmware/tool checksums and a runtime-only file list.
