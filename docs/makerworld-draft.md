# MakerWorld listing draft

## Title
Kirometer Ghost — PLA Desk Enclosure for Waveshare 2.16″ AMOLED

## Short description
A compact Kiro-inspired ghost enclosure with a desk-friendly tilt, direct access to the factory top buttons, rear cable routing, and a screw-free printed friction fit. Designed for PLA and reduced support use.

## Description to paste
Give your AI usage display a little desk companion. Kirometer is a compact ghost-shaped enclosure designed around the **Waveshare ESP32-S3-Touch-AMOLED-2.16 in its complete factory housing**.

The ghost stands on its own lower lobes and leans back approximately 15° for easy viewing. The body envelope is approximately **66 × 80 × 29.9 mm**. A continuous recessed button well exposes the factory buttons directly, with filled surrounding surfaces and a forward extension on the removable cover. A lower channel and rear cutout accommodate a right-angle USB-C adapter, and the screen seating lip is reduced to 0.8 mm with a chamfer for easier edge swipes.

The rear cover presses straight into four vertical friction sockets using tapered pegs. Pegs and sockets build vertically in the supplied orientations, with no overhanging retaining lips. All parts can be PLA; there are no screws, bending clips, sliding steps, lock keys, or separate stand. The fit coupon includes three candidate socket diameters so you can check your printer's PLA fit before printing the body.

The print geometry uses an uncovered button well and rear adapter access, tapered pegs, gradual heel transitions, and vertical socket bosses supported by the housing cradle. Start with supports disabled and check the sliced layers before printing. This revision still requires a physical print and assembly check.

### Included files
- Main ghost body
- Removable rear cover
- Housing/window fit coupon
- Bambu Studio project for P1S, 0.4 mm nozzle

### Suggested starting settings
PLA, 0.4 mm nozzle, 0.2 mm layers, four walls, 20% infill, supports off. Use the supplied orientations: body front down, cover exterior down, coupon flat down. Print the fit coupon first.

The 3MF includes three named plates: a white fit coupon to print first, the white body, and the purple cover. White PLA is assigned to slot 1 and purple PLA to slot 2. Each plate uses one color; AMS is optional. The accent color is #9147FF, matching Kiro’s website purple-500 token (HSL 264° 100% 64%).

### Slicer estimate
All three supports-disabled P1S plates sliced without warnings. Per-plate estimates are in `exports/3mf-validation.json`. These are slicer estimates, not measured print results.

### Assembly
1. Print the white fit coupon and check the factory housing and glass opening.
2. Print the purple cover, and test a cover peg in the coupon's Ø2.64 / Ø2.68 / Ø2.72 mm holes. Ø2.68 mm matches the body sockets.
3. Print the body, deburr the passages and sockets, and check direct access to each factory button.
4. Check straight press-fit retention and removal on the empty shell before installing electronics.
5. Use the [UGREEN right-angle adapter supplied as the fit reference](https://www.amazon.com/dp/B0FNCT8NS7), or physically verify your alternative. Insert the factory-housed display with buttons up and USB down, route the cable, and press the cover straight into its sockets. Pull evenly to reopen.

### Project status
This is an **unprinted v9 revision based on feedback from a physical v6 print**. CAD checks confirm closed meshes and nominal clearances for the stock housing and cover assembly path. Physical clearance, button travel, peg friction, stability, cable fit, and printing performance remain to be tested.

The companion Crew app and device firmware are maintained separately in this project. These Blender renders illustrate the enclosure and use reference screen artwork. They are not photographs of a physical v9 assembly.

### Inspiration and credit
Inspired by [CodexMeter](https://github.com/tomatoeggs/CodexMeter), its [MakerWorld enclosure](https://makerworld.com/en/models/3046835-codexmeter-codex-remaining-usage-running-status-in), and the animated-mascot approach of [Clawdmeter](https://github.com/HermannBjorgvin/Clawdmeter). The ghost silhouette references the [Kiro](https://kiro.dev/) app mascot. This is an unofficial fan project and is not affiliated with Kiro, AWS, Waveshare, or Bambu Lab.

## Suggested tags
kiro, kirometer, ghost, esp32, waveshare, amoled, desktop, enclosure, pla, screwless, ai

## Before publishing
Replace or supplement the renders with photos of a successful print. Confirm the fit coupon, friction fit, free button travel, cable clearance, standing stability, and supports-off result. Add the measured print time and filament use after slicing with your actual PLA. Choose the model license deliberately; no license or branding rights are assigned by this draft. Keep the prototype status accurate until the build is physically validated.

Guidance reference: [MakerWorld print-profile upload documentation](https://wiki.bambulab.com/en/makerworld/tutorials/print-profile-upload). The documentation could not be fetched during drafting; verify current upload requirements in MakerWorld before submitting.

The v8 revision closes the former upper recesses, removes decorative rear slots, and uses squared white heels flush with the purple rear cover. The cable notch and button access remain functional openings.

Revision v9 corrects the button datum to 9.6 mm from the factory front and replaces the steep inner ramp with an almost vertical wall. Nominal front-wall clearance from button edges is at least 4.55 mm; Ø12 mm approach corridors pass CAD collision checks at all three buttons. Supersedes the v8 body, which interfered with the corrected button positions.
