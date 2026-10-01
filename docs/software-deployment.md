> The preferred data collector is now the [Kiro Crew app](crew-app.md). These wrappers remain diagnostic and firmware setup utilities; no OS background collector is required.

# Software and firmware deployment

The software currently reads a local Kiro usage cache and prints a JSON snapshot. It does not send data to the ESP32, animate the hardware display, or run as a background service. Kirometer firmware and a validated transport are still required. These scripts prepare the reader and provide explicit build/flash tooling for a separately supplied PlatformIO project.

## Requirements

- Python 3.10 or newer on macOS or Windows, with the `venv` module available.
- Kiro installed and used locally. The reader never requests credentials or changes Kiro's database.
- For firmware only: internet access to install PlatformIO and the project's toolchains; a trusted firmware project configured for **Waveshare ESP32-S3-Touch-AMOLED-2.16**; and a data-capable USB cable.

Commands below run from the Kirometer repository root. Paths containing spaces must remain quoted. The wrappers do not install Python or change the system's execution policy.

## macOS

```bash
./scripts/deploy-macos.sh setup
./scripts/deploy-macos.sh run
# Optional: select a different Kiro profile.
./scripts/deploy-macos.sh run --db "/path/to/state.vscdb"
```

## Windows PowerShell

```powershell
.\scripts\deploy-windows.ps1 setup
.\scripts\deploy-windows.ps1 run
# Optional: select a different Kiro profile.
.\scripts\deploy-windows.ps1 run --db "C:\path\to\state.vscdb"
```

If PowerShell blocks local script execution, use Python directly without changing the policy:

```powershell
py -3 .\scripts\deploy.py setup
py -3 .\scripts\deploy.py run
```

`setup` creates `.venv` in this checkout and runs the reader/deployment tests. It installs no application dependencies, background service or firmware. `run` prints one snapshot. Missing cached usage is reported as unavailable and stale; task activity remains unknown. A successful process exit means the reader ran, not that live usage was available.

The default macOS database is `~/Library/Application Support/Kiro/User/globalStorage/state.vscdb`. The Windows default is `%APPDATA%\Kiro\User\globalStorage\state.vscdb` (falling back to `~/AppData/Roaming`). Windows uses the conventional desktop profile path; real Windows Kiro telemetry has not yet been validated. Use `--db` for custom profiles or portable installations.

## Firmware tools and explicit flashing

There is no `platformio.ini` or device firmware in this repository. Do not substitute a generic ESP32 board profile: AMOLED, touch, button and USB settings must match the actual Waveshare hardware. Use only a trusted, compatible firmware project. PlatformIO projects can execute build scripts.

macOS example:

```bash
./scripts/deploy-macos.sh install-firmware-tools
./scripts/deploy-macos.sh ports
./scripts/deploy-macos.sh build --project "/path/to/firmware" --environment waveshare_amoled_216
# Review exact upload argv without executing or installing anything:
./scripts/deploy-macos.sh flash --project "/path/to/firmware" --environment waveshare_amoled_216 --port /dev/cu.usbmodem1101 --dry-run
# Explicitly upload to the selected device:
./scripts/deploy-macos.sh flash --project "/path/to/firmware" --environment waveshare_amoled_216 --port /dev/cu.usbmodem1101
```

Windows example:

```powershell
.\scripts\deploy-windows.ps1 install-firmware-tools
.\scripts\deploy-windows.ps1 ports
.\scripts\deploy-windows.ps1 build --project "C:\path\to\firmware" --environment waveshare_amoled_216
.\scripts\deploy-windows.ps1 flash --project "C:\path\to\firmware" --environment waveshare_amoled_216 --port COM4 --dry-run
.\scripts\deploy-windows.ps1 flash --project "C:\path\to\firmware" --environment waveshare_amoled_216 --port COM4
```

Replace the example environment with one declared in the supplied `platformio.ini`, and the example port with the device identified by `ports`. No serial port is selected automatically. `flash` overwrites the selected device's firmware; `setup`, `run`, `ports` and `build` never upload. An upload success does not verify screen rendering or telemetry transport; check those on hardware afterwards.

`install-firmware-tools` installs PlatformIO **6.1.18** into the project-local `.venv`, never globally. PlatformIO may also maintain its normal per-user toolchain/cache directory when building. `build` and `flash` require an existing project, explicitly named environment, and installed local tools; `flash` additionally requires an explicit port. Commands propagate subprocess exit codes. `--dry-run` validates the project/environment and prints argument arrays without executing commands.

`build` explicitly selects `buildprog`, overriding a project's default targets that might include upload. This target is defined by the [official Espressif32 builder](https://github.com/platformio/platform-espressif32/blob/develop/builder/main.py). CLI references: [PlatformIO device list](https://docs.platformio.org/en/latest/core/userguide/device/cmd_list.html) and [PlatformIO run](https://docs.platformio.org/en/latest/core/userguide/cmd_run.html).

## Validation status

The reader and deployment unit tests exercise platform cache paths, read-only cache access, stale data, explicit upload arguments, a build target that overrides default upload, and rejection of missing projects/environments/ports. The macOS setup wrapper successfully created a local environment and ran all six tests. macOS shell syntax and the PowerShell parser are checked locally. Windows PowerShell execution, actual firmware builds/uploads, USB communication, BLE transport and device behavior require further platform/hardware testing. No connected hardware was flashed while adding these scripts.
