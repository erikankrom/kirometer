# Device-manager UI checks

This harness renders the shipped Crew page using React and a simulated API. It never flashes or controls physical hardware. Install dependencies with `npm install` in this directory, then `npm run build`. Serve the repository and open `/tests/ui/index.html`.

Checks exercised on October 1, 2026:
- Light and dark palettes, connected device and usage summary.
- Rename draft → Save → pending → matching device confirmation.
- New device: Prepare → review firmware → explicit confirmation → Install → Connect.
- The previous successful flash does not enable Continue in a new setup.
- No-device state, no nearby devices, and unavailable API with disabled controls.

For a new UI change, rebuild the harness; it bundles the current `crew-app/ui/index.mjs`.
