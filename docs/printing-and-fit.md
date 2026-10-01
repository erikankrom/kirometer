# Kirometer ghost enclosure — PLA friction-fit prototype v6

The enclosure fits the complete factory-housed **Waveshare ESP32-S3-Touch-AMOLED-2.16**, nominally 46 × 46 × 22.5 mm. It does not mount a bare PCB. The [official dimensional drawing](https://docs.waveshare.com/assets/images/ESP32-S3-Touch-AMOLED-2.16-details-size-9be8e99d5f546b1b8ce338c394d988fd.webp) supplies the housing dimensions.

## Parts and dimensions

There are six printable STL parts: body, cover, fit coupon, and three button plungers. The previous lock key and slide connectors have been removed.

| Feature | Dimension |
|---|---|
| Body envelope | Approximately 66 × 80 × 36 mm |
| Viewing tilt | 15° backward; stands on its own lobes |
| Factory housing pocket | 46.8 × 46.8 mm, nominal 0.4 mm clearance per side |
| Screen opening | 44.4 × 44.4 mm |
| Front plate / rear cover | 2.4 mm each |
| Friction pegs | Four; 5 mm engagement; Ø2.30 mm tips taper to Ø2.64 mm roots |
| Body sockets | Ø2.60 mm, approximately 5.5 mm usable depth |
| Nominal interference | 0.04 mm diametral at each peg root |
| Coupon test holes | Ø2.56, Ø2.60, Ø2.64 mm, from lower to upper Y in the source |
| Accent | Kiro website purple #9147FF; ordinary PLA |

The small interference is intentional. Printed fit depends on extrusion and hole compensation; no claim of guaranteed retention is made before a physical test. The cover presses straight in and pulls straight out. No sliding, bending latch, separate lock key, screws, magnets, or glue are needed.

## Print orientations and support settings

All STLs are exported in their intended print orientations:

- Body front face down. Socket bosses rise from the front plate and cradle; socket openings face upward.
- Cover exterior face down. Pegs rise vertically and narrow toward their tips, with no widening heads or retaining ledges.
- Plungers cap down; their flanges transition gradually.
- Coupon flat face down; test sockets are vertical through-holes.

**Supports disabled** is the supplied setting. The connectors have no horizontal ceilings or overhanging lips. USB and button passages elsewhere in the shell retain their pointed roofs. The complete enclosure still contains small bridges; slicer processing alone does not establish physical print quality.

Starting settings: P1S, 0.4 mm nozzle, 0.2 mm layers, four walls, 20% infill, PLA. Select your actual filament and bed surface. Do not scale the parts.

## Fit checks and assembly

1. Print plate 1, the white fit coupon. Check the factory housing pocket and visible glass opening.
2. Print the purple cover and buttons on plate 3. Test one cover peg in the coupon's three candidate holes before printing the full body. Ø2.60 mm matches the body sockets; the neighboring sizes help identify printer-dependent tightness. Keep the other pegs clear of the coupon while testing.
3. If Ø2.60 mm is too tight, lightly polish the pegs or adjust socket diameter in the CAD generator and regenerate both STL and 3MF. If it is loose, reduce the socket diameter. Do not force PLA pegs into a tight socket. The coupon does not prove simultaneous alignment of all four pegs, so also test the empty shell.
4. Print plate 2, the white body. Deburr the passages, peg tips and socket mouths. Insert the three captive plungers from inside, shaft first, and check free travel.
5. Test the cover's straight press fit on the empty shell. It should seat with light pressure and reopen with a gentle, even pull. The factory housing must remain removable.
6. Insert the intact Waveshare unit with its buttons up and USB down, route the cord through the lower passage, and press the cover into place. Printed pads leave nominal 0.2 mm play behind the stock housing.

No separate stand is needed. Check desk stability with the actual power cable attached. Top-button travel and cable connector clearance require a physical fit test.

## Bambu Studio project

`exports/kirometer-bambu.3mf` has three separately selectable plates:

1. **Fit coupon — white:** housing and friction-fit checks.
2. **Body — white:** main shell.
3. **Accents — purple:** rear cover and three buttons.

White PLA (#FFFFFF) is assigned to slot 1; purple PLA (#9147FF) to slot 2. Each plate prints one color. AMS is optional; change filament manually between plates if desired. Print the coupon first; the cover can be printed before the body to test its pegs.

## Validation and limits

The generator checks closed connected meshes, positive volume, the stock-housing envelope, the seated cover, and straight insertion. Small overlap at the peg roots is the specified friction-fit interference, not an accidental housing collision. `exports/geometry-validation.json` records it. `exports/stl-validation.json` checks the exported meshes independently. Bambu Studio slice results are recorded in `exports/bambu-slice-validation.json` and `exports/3mf-validation.json`.

This is an unprinted prototype. Friction retention, wear after reopening, dimensional accuracy, button travel, cable fit, thermal behavior, stability, and drop resistance remain unverified. Print and inspect the coupon before committing to the full shell.
