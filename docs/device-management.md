# macOS device management in Crew

The Kirometer Crew app 0.6.0 with firmware 0.5.6 supports USB firmware flashing and Bluetooth LE usage sync and controls for the Waveshare ESP32-S3 Touch AMOLED 2.16. The offline tools target Crew's Python 3.12 on Apple Silicon macOS. Intel Macs and Windows are not yet validated.

1. **Your devices** shows the active Kirometer, its name and connection. One device can sync at a time. The page follows Crew’s current light or dark theme.
2. For a new board, choose **Add a device → New device**. The Prepare step installs bundled tools and selects the USB device; Install reviews and verifies the firmware bundle before explicit replacement confirmation; Connect prepares USB pairing and offers Bluetooth discovery. An older flash job cannot complete a new setup.
3. For an existing board, choose **Connect existing device** or **Add a device → Already set up**, then **Find nearby Kirometers**. Select a discovered device and connect. On a new Mac, open the USB option and connect once to provision pairing. Allow normal macOS Bluetooth prompts when shown.
4. **Customize** edits the device name, brightness and sleep behavior in one draft. **Save changes** waits for the device’s matching control sequence and returned settings before reporting success. Drafts survive background polls; **Discard** restores the device’s values. Names accept up to 26 UTF-8 bytes. **Preview screensaver / Wake display** is available when there are no unsaved changes.
5. **Connection** shows the transport, device ID, firmware and power; it also offers discovery, disconnect and USB fallback. Reconnect explicitly after a lost link or Crew restart. Connecting another device replaces the current link.
6. **Firmware** reviews the bundled update by default. A custom manifest is available under an advanced disclosure. Installation requires a USB-C data cable and replacement confirmation. A successful write is distinguished from a running firmware version reported by the device.

Bundled tools are checksum-verified esptool 5.1.0, pyserial 3.5 and Bleak 3.0.2. Setup runs offline in the app environment. USB provisioning names an unnamed device `<computer_username> kirometer`; existing custom names are preserved.

Wireless communication does not use Wi-Fi, HTTP or a corporate LAN. The app manifest requests no HTTP network permission. GATT writes require encrypted BLE; the app also authenticates packets with its USB-provisioned key. Pairing uses Bluetooth Just Works bonding without a passkey or MITM guarantee. The key stays in a mode-0600 app data file and reaches the worker through stdin, never command-line arguments or returned telemetry. Connecting a different Mac over USB reprovisions the board to that Mac's app key.

## Display and sleep

The screen uses the selected Ghost first layout: pure black, centered activity and a stationary blinking ghost, a purple plan badge, compact usage bar, remaining credits and red overage. Tap the credit area for large-text details and tap Back to ghost to return. Fonts use FreeSans. Top buttons also toggle usage details.

Auto sleep defaults to 120 seconds in Ready, adjustable to 30–3600 seconds. The screensaver keeps BLE and usage sync running while the screen is mostly black. Every 20 seconds the ghost peeks for 5.5 seconds, cycling through left, right, bottom and top. Rotation brings the crown and eyes into view first from every edge. Touching the screen or pressing a top button wakes the display. Waking manual Sleep switches it to Auto and saves that preference; touch resets the idle timeout. The CST9220 remains awake, using reset GPIO40 and interrupt GPIO11 on the shared I2C bus.

Crew activity is sampled every two seconds from structured slot/subagent state. Active/recovering/dependency waits map to Working, input/permission waits to Needs attention, stalled sessions to Error, and an observed active-to-idle transition to Complete for eight seconds. Complete indicates the turn ended, not task success. Missing telemetry stays Unknown. This version-bound adapter covers Crew-managed sessions, not standalone IDE/CLI sessions, and reads no transcripts or tool arguments.

## Transport and firmware contract

USB uses newline-delimited protocol-1 JSON at 115200 baud. The worker paces 64-byte chunks to avoid overflowing HWCDC during framebuffer transfers. BLE uses the same JSON contract, bounded to 4096 bytes and fragmented into 20-byte GATT writes/notifications.

- Service: `f3641400-00b0-4240-ba50-05ca45bf8abc`
- RX encrypted write: `f3641401-00b0-4240-ba50-05ca45bf8abc`
- TX notify: `f3641402-00b0-4240-ba50-05ca45bf8abc`
- Encrypted pairing read: `f3641403-00b0-4240-ba50-05ca45bf8abc`

Each usage snapshot has `type: kirometer.usage`, `protocol: 1` and a sequence. The app requires a matching accepted acknowledgement and status; BLE also requires the same `displayed_seq`. Status projects only known scalar telemetry, never arbitrary device text. In sleep, usage is received but `display_usage_available` is false. Link status becomes disconnected on the display after 30 seconds without usage updates.

The bundled firmware uses four explicit flash regions and excludes NVS, preserving pairing and settings on updates. Earlier merged factory bundles overwrote NVS padding; 0.5.2 added one-time device bond recovery and 0.5.3 explicitly triggers macOS pairing through an encrypted read.

Firmware manifests require the exact board/chip labels, SHA-256 for every binary, 4 KiB aligned offsets, nonoverlapping erase sectors and a 16 MiB ceiling. Binaries stay inside the bundle directory. Validated bytes are staged before flashing. No force, full-chip erase or secure-boot bypass is requested. Keep Crew running during flashing; interruption may require reflashing. If USB is stuck, close other serial owners and reconnect the cable; BOOT/RESET download mode is a fallback.

## App routes

`GET /api/apps/kirometer/devices` returns USB ports, tool readiness, default name, latest job and link. POST actions under that route are `setup`, `setup_bluetooth`, `bundle`, `flash`, `status`, `connect`, `disconnect`, `bluetooth_scan`, `bluetooth_connect` and `controls`. Only one flash/setup job runs at a time. Flashing closes the active connection first.

## Physical verification, October 1, 2026

Firmware 0.5.0 was uploaded and verified by esptool, then booted on device `10da608dbd44`. USB provisioned `erikankrom kirometer`. Bluetooth discovery and connection succeeded; BLE acknowledged usage and reported Ready with 0.1 / 1,000 credits and zero overage. Brightness 100, manual sleep, wake, temporary rename and restoration to brightness 180 / Auto 120 seconds / the default name were confirmed over BLE. Credit cache freshness remains independently reported.

Firmware 0.5.3 is flashed and has reconnected over encrypted Bluetooth. The CST9220 reports initialized. The user confirmed that tapping the screensaver wakes the normal screen. Device telemetry independently records the touch event and touch wake source. Edge rotation is implemented; visual acceptance of every edge remains a user observation.

Firmware 0.5.4 removes overlay flights and moving poses. The ghost stays inside a dedicated black area, with a half-second blink every five seconds and slow Working dots. Rendering is capped at four frames per second; the edge-peeking black screensaver and touch wake remain.

0.5.4 was flashed with esptool verification and reconnected over Bluetooth, reporting the saved name, brightness and auto sleep settings and real credit usage. All 23 host tests passed.

## Ghost first layout — 0.5.5

The selected Option 1 is implemented in firmware: pure black main and detail backgrounds, larger stationary mascot with occasional blinking, state title, plan badge, compact credits bar and red overage. Tap the credit area to open usage details and the Back to ghost button to return. One touch gesture performs one action; waking from sleep does not also open details. The rotated peeking screensaver and Bluetooth controls are retained. Firmware compilation and 23 host regression tests passed. Physical touch targeting still needs a tap on the device to confirm.

## Larger detail text — 0.5.6

Details now use 24-point credit values (previously 12-point), 12-point labels (previously 10-point), an 18-point reset date and 12-point Back button. Side padding is reduced from 30 to 18 pixels. Shorter labels leave a clear gap between label and value; unusually long numbers step down in font size to fit. Firmware compilation and actual font-width checks passed. Firmware updates currently require USB; Bluetooth carries usage and controls only.

## Crew page verification — 0.6.0

Live Crew light-mode rendering and the real Bluetooth device card were verified. The same shipped UI module was also exercised with simulated hardware in both themes: queued-to-confirmed save, new-device flash flow, rejection of a previous flash as completion, reconnect discovery with no results, empty-device state and API unavailability. Firmware and transport backend were unchanged for this UI release.

## Animation performance — firmware 0.5.7

Animation ticks now target 50 ms (20 FPS). The canvas is still composed in RAM, but main-screen animation sends only a 176 × 234 pixel black region. The ghost moves by three pixels within that region and blinks for 200 ms every five seconds; Working dots pulse there as well. Static text and credits redraw only when their visible state changes. Screensaver transfers are limited to the active edge region, with no transfers during the empty black interval. Full view transitions still transfer a complete frame.

Bluetooth replies use an 8 KiB bounded queue and send one 20-byte notification per service interval without sleeping the drawing loop. Status includes tick/transfer counters, render timing, maximum tick gap, and reply drops. A 50 ms target does not mean every visible pose changes every tick: slow movement is rounded to whole pixels.

On October 1, firmware 0.5.7 was flashed with four verified regions, preserving the saved name, pairing, brightness 127, and idle timeout. With Bluetooth usage sync active, ten status samples over about 19 device seconds measured approximately 20 partial redraws per second, a maximum partial-render time of 30.118 ms, zero full redraws in the sample, no dropped replies, and advancing acknowledged usage sequences. Full view transitions take approximately 98 ms and can cause a single longer frame gap. Manual screensaver and return to Auto were acknowledged over Bluetooth. Touch wake was retained; this release was not separately physically tap-tested. The native panel refresh rate is not specified in the vendor documentation.

Validation: 23 host regression tests; firmware build; an AddressSanitizer/UndefinedBehaviorSanitizer C++ check for reply queue wraparound/overflow and every visible pixel of all four peeking orientations staying inside its transfer region.

## App listing and spacing — app 0.6.1

The listing includes a CAD-derived ghost enclosure outline icon with a rounded square screen opening, separate light/dark banners and card art, and two screenshots per theme. Screenshots render the actual UI module with sample device data. Descriptions, use cases, setup guidance, author, tags, and features use Crew's supported manifest metadata. The installed app version is updated through Crew's update API.

The disconnected-device card now inherits the panel's 24 px padding on every side (18 px on mobile). Its previous empty-state rule accidentally replaced the horizontal padding with zero. Verified the empty and connected layouts in the UI harness, including light/dark screenshots.

## Directional activity and connection recovery (app 0.7.0 / firmware 0.5.8)

The ghost now changes its pose and motion by activity: Ready floats and occasionally glances; Working turns East/North/West while bobbing; Needs attention looks both ways; Complete makes an entrance turn and little hops; Error briefly shakes side to side; Unknown slowly looks around. Source art is from Spirit of Kiro; West mirrors East. Everything stays inside the 176 × 234 black animation rectangle at 50 ms intervals, away from status text and credit bars.

On October 1, firmware 0.5.8 was flashed and verified by esptool on the connected Waveshare board. All six test states were acknowledged and returned matching activity statuses. Partial rendering peaked at 28.430 ms during that tour. Live Crew Bluetooth sync was restored afterward; name, pairing and brightness 127 were retained. These are telemetry and bounded rendering checks, not a camera-based inspection of the physical display.

The app now retries temporary Bluetooth failures at 5, 10, 20, then 30 seconds. Cancel connection stops retries. A removed pairing bond still requires explicit repair. USB status is matched to the current usage sequence so stale responses cannot mask a new state.


## Screen gallery and typography (app 0.8.0 / firmware 0.5.10)

Customize → Screen gallery offers Ghost companion and Usage dashboard with visual
previews. Select a card and save; “On your device” appears only after the device
acknowledges its chosen layout. Firmware stores the choice in Preferences and
reports `screen_layout` plus `screen_layouts_supported`. Firmware before 0.5.9
keeps existing controls but cannot switch layouts.

Usage dashboard shows the plan banner, monthly credit usage and percentage/reset
date, a separate red overage meter, and connection status. Its overage meter is
explicitly relative to plan allowance, not an overage cap. Tap either usage card
for details. The small ghost animates only inside its own black region.

Firmware 0.5.10 embeds Kiro Crew's Space Grotesk at 20/24/36/48 px using 4-bit
coverage, blended into the RGB565 canvas. It does not change animation timing or
the display driver. Font source and OFL license are included. See DESIGN.md for
shared standards and scripts/build_fonts.py to regenerate the atlases.
