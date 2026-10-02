# Kirometer ghost enclosure — PLA prototype v9

Revision 9 corrects the factory-button depth reference and increases fingertip clearance, retaining the enclosed upper surfaces and squared feet from v8. It fits the complete factory-housed **Waveshare ESP32-S3-Touch-AMOLED-2.16**, nominally 46 × 46 × 22.5 mm. It does not mount a bare PCB. Reference: [Waveshare dimensional drawing](https://docs.waveshare.com/assets/images/ESP32-S3-Touch-AMOLED-2.16-details-size-9be8e99d5f546b1b8ce338c394d988fd.webp).

## Changes and dimensions

There are now **three STL parts**: body, rear cover, and fit coupon. The three separate button plungers have been removed. An opening through the top and rear gives direct access to the factory buttons.

| Feature | v9 geometry |
|---|---|
| Body envelope | 65.99 × 79.69 × 29.9 mm |
| Viewing tilt | 15° backward, self-standing |
| Factory housing pocket | 46.8 × 46.8 mm; 0.4 mm nominal clearance per side |
| Housing seating lip | 0.8 mm behind the front, reduced from 2.4 mm |
| Screen opening | 44.4 mm at throat, chamfered to 45.6 mm at front |
| Structural front web / cover thickness | 2.4 mm each outside the relieved seating lip |
| Button access | 34.8 mm wide continuous well; filled cheeks and almost vertical front wall, forward cover tongue; no printed moving parts |
| Factory button center depth | 10.4 mm from printed front: 0.8 mm seat + 9.6 mm from factory front |
| Button diameter / spacing | Ø5.3 mm / 10 mm between centers |
| Front-wall button clearance | At least 4.55 mm along the depth axis from cap edge; wall 3.85° from case vertical |
| Outer-button side clearance | 4.75 mm nominal |
| Fingertip approach | Ø12 mm cylindrical corridor checked at all three centers |
| USB adapter channel / rear opening width | 16.0 / 16.6 mm |
| Rear foot cutouts | Squared profile, 0.2 mm nominal side/top clearance; white heels end flush with cover rear |
| Cover pegs | 5 mm engagement; Ø2.30 mm tips to Ø2.64 mm roots |
| Body sockets | Ø2.68 mm; previously Ø2.60 mm |
| Nominal peg-root clearance | 0.04 mm diametral, previously 0.04 mm interference |
| Coupon sockets | Ø2.64 / Ø2.68 / Ø2.72 mm in increasing source Y order |
| Rear housing play | 0.2 mm nominal; retention pads extended for forward screen position |
| Accent | Purple PLA #9147FF |

The seating lip depth is a CAD dimension, not a measured assembled glass recess. The factory glass position, print variation, and fit determine the final result. The front chamfer reduces the edge encountered by a swipe while retaining the factory housing.

The upper shell now has filled cheeks and a continuous, nearly vertical front wall around the factory buttons. A tongue on the rear cover extends forward to within 0.2 mm of the factory housing, closing the former rear pocket while allowing straight cover removal. The buttons remain accessible in a shallow well; this is not a dust-sealed assembly.

The lower white heels and corresponding cover cutouts are squared, with their rear surfaces at the same 29.9 mm depth. The cover follows the lower outline, and the three decorative rear slots are removed. The rear adapter notch remains open for cable access. The shortened heels require a physical stability check with the actual cable attached.

## Button clearance correction

Do not use the v8 body: its button references incorrectly measured the drawing's 9.6 mm offset from the rear, placing them 3.3 mm too far back. Rechecking the v8 mesh with corrected button positions found approximately 6.84 mm³ of body interference per button. Revision 9 uses the front datum and removes the steep ramp.

The new wall retreats only 0.8 mm over 11.9 mm of height. Clearance checks include a Ø12 mm straight fingertip approach at each button and a Ø5.3 mm cap envelope extending 1.5 mm above the housing. These show zero body or cover interference. The official drawing does not specify button protrusion or actuation travel; the 0.8 mm rendered cap and 1.5 mm test envelope are assumptions, not manufacturer tolerances. Verify free travel and comfortable independent presses on the real assembly.

## Adapter reference

The user's [UGREEN right-angle adapter, ASIN B0FNCT8NS7](https://www.amazon.com/dp/B0FNCT8NS7) lists overall dimensions of 0.83 × 0.47 × 0.24 inches (approximately 21.1 × 11.9 × 6.1 mm). The lower channel and rear notch accommodate a simplified reference envelope inferred from the user's installed-adapter photos. The rear remains open for the mating cable.

The product listing is not a dimensioned mechanical drawing. Exact plug insertion position, adapter orientation, and the cable's overmold still require a physical check. The dark adapter block in the rear render is a simplified reference, not a printable part or an exact product model.

## Print settings and plates

`exports/kirometer-bambu.3mf` targets **Bambu P1S, 0.4 mm nozzle**, PLA, 0.2 mm layers, four walls, 20% infill, **supports disabled**. Parts are already oriented:

1. **Fit coupon — white:** flat/front down; print first.
2. **Body — white:** front face down; socket openings face up.
3. **Accents — purple:** rear cover exterior down; pads and tapered pegs point up.

White #FFFFFF uses slot 1, purple #9147FF slot 2. Each plate uses one color; AMS is optional. The button well has no roof over the factory buttons; its front and side surfaces are filled, and its rear closure belongs to the removable cover. The adapter notch remains open below. Small bridges remain elsewhere; slicing with supports off does not prove physical print quality.

## What the fit coupon does

The coupon is a small tolerance test for a rear-cover peg, not a screen adapter. Its three socket sizes let you compare retention and removal effort before printing the full body. Use a peg on the printed rear cover; the middle hole matches the current body. Its window and pocket also provide a preliminary check of the factory housing and bezel fit; it does not validate the complete enclosure or the combined force of all four pegs.

## Fit and assembly

1. Print the coupon and purple cover. Gently test a cover peg in the three coupon sockets. The middle Ø2.68 mm hole matches the body. Keep other pegs clear of the coupon. Do not force the peg.
2. If the middle fit is too tight or loose, adjust the socket diameter in `cad/build_enclosure.py`, regenerate, and retest. Nominal clearance intentionally reduces the v6 removal force; real retention depends on PLA and printer tolerances.
3. Print the body. Check all four cover connections together on the empty shell; install/remove evenly several times and inspect for cracks or whitening. A single-peg coupon does not prove complete-cover fit.
4. Insert the complete stock device with buttons up and USB down. Its front housing seats on the shallow lip. Confirm the glass and touch area remain clear.
5. Attach the right-angle adapter with its cable receptacle facing rearward. Check it clears the lower cradle and that the cable can connect through the rear opening.
6. Close the cover. Confirm each factory button is released at rest, reachable, independently pressable, and returns freely. Test normal startup and screen operation with the cover fitted.
7. Set the assembled device on a flat desk with its actual cable. The feet must carry the weight; neither adapter nor cable may lift or rock the enclosure.

## Validation and limits

`exports/geometry-validation.json` records closed, connected meshes, positive volumes, stock-housing clearance, zero seated cover collisions, and sampled straight insertion clearance. `cad/review_enclosure.py` additionally checks factory-button references and the approximate adapter envelope. `exports/stl-validation.json` independently checks the exported binary STL edges and volumes.

`exports/bambu-slice-validation.json` and `exports/3mf-validation.json` record this revision's slicing and packaging checks. Blender renders use the actual revised meshes; the stock device, screen artwork, adapter, lights, and desk are reference-only objects, excluded from STL/3MF exports.

**v9 has not been physically printed or fit-tested.** The earlier v6 print revealed the issues addressed here. Successful mesh and slicer checks do not establish button ergonomics, retention, repeated removal durability, adapter/cable fit, thermal behavior, or stability. Print the coupon before the complete enclosure.
