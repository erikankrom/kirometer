# Device notification sounds

Firmware 0.7.0 and Crew app 0.11.0 add opt-in sounds under **Customize → Notification sounds**. Enable sounds, choose Chime, Ding, Blip, Pop or Pulse, then save. Preferences are confirmed by the device and survive reboot. No laptop sound settings are changed.

Only **Needs Response** is supported: Crew's `waiting_input` health state. A new session entering that state generates an opaque random event ID. A second session can notify even while another session is already waiting. Permission approvals, working, ready, errors and normal completion are silent. Repeated polls, initial discovery and reconnects do not replay existing requests. Multiple changes between syncs may coalesce. This is local Crew session activity, not IDE-wide notification forwarding.

Sound selection and enablement travel over the existing authenticated BLE/USB usage contract (`controls.sound_enabled`, `controls.sound_preset`). The payload also includes `needs_response`, `response_event`, and `notification_baseline`. No conversation content or session IDs leave Crew. Firmware consumes IDs even when muted; enabling does not play an old event. Status exposes `sounds_supported`, `audio_ready`, saved settings and a `sound_events` dispatch counter. The counter is not proof that a physical speaker was audible.

## Sound source

Kiro Crew's installed frontend, inspected 2026-10-01, synthesizes its sounds rather than shipping recordings. Preset note frequencies, timing, relative gains and envelope behavior were transcribed from `MemoryTab-e91XvJr7.js` in the installed application. Kirometer's independently implemented 16 kHz PCM synthesizer reproduces those presets: sine oscillators, 5 ms eased attack/release, decay to 1% amplitude, preset compensation, and Crew's default 35% volume curve. Additional mixer headroom and a moderate codec gain suit the small speaker. Actual timbre/loudness differs by speaker. No Crew JavaScript bundle or recordings are redistributed.

Playback is TX-only I2S (BCLK 9, WS 45, data 8, MCLK 42) with ES8311 and amplifier GPIO46. Microphone capture is not enabled. A bounded FreeRTOS playback task keeps I2S writes off the rendering/Bluetooth loop. The amplifier is off while idle. Codec initialization failure is reported without preventing the screen from starting.

The ES8311 driver in `firmware/lib/es8311` is from Waveshare's official [2.16-inch Arduino example](https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-2.16/tree/main/examples/arduino/07_ES8311), retrieved 2026-10-01. Its Espressif copyright headers and Apache-2.0 license are retained; the app package includes that license. [Board audio documentation](https://docs.waveshare.com/ESP32-S3-Touch-AMOLED-2.16).
