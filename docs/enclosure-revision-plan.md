# Kirometer enclosure revision plan

Status: implementation authorized by the user on October 1, 2026. Revision v9 implements changes 1–7 and the direct-access button alternative. Physical validation remains pending; see printing-and-fit.md for dimensions and checks.

## 1. Bring the touch surface closer to flush

Reference: user photo `IMG_3135.jpeg`, supplied October 1, 2026, showing the inside of the printed front enclosure.

**Observed problem:** The screen sits too far behind the front face. The surrounding ridge interferes with left, right, and upward swipes.

**Requested result:** Move the front screen-retention ledge toward the front so the installed touch surface sits as close to flush with the exterior as practical. Keep only the clearance needed for reliable assembly and secure retention without pressure on the glass.

**Planned investigation and changes, after feedback collection:**

- Measure the assembled glass-to-front recess and distinguish the factory housing's own recess from the printed enclosure's added recess.
- Reduce the printed ledge setback and review its overlap with the factory housing. Keep the touchable area accessible at the edges.
- Check the complete mounting stack: factory housing, rear retention pads, cover closure, top button alignment and travel, and power connector routing. Moving the unit forward may require coordinated changes to these features.
- Select the smallest practical recess and clearance after checking dimensions and print tolerances. No exact target dimension is established from the photograph alone.

**Acceptance checks:** The assembled screen appears nearly flush; fingers can swipe left/right/up without catching on the bezel; the display stays secure without glass pressure; buttons, cable routing, and cover fit remain functional. Check a small front-edge fit sample before committing to another complete shell where feasible.

## 2. Clear the lower opening for a right-angle USB-C adapter

References: user photos `IMG_3139.jpeg`, `IMG_3142.jpeg`, and `IMG_3141.jpeg`, supplied October 1, 2026.

**Observed problem:** A cable routed directly downward does not have enough clearance for the enclosure to sit flat on the desk. The user reports that their right-angle USB-C adapter works well after removing the obstructing material around the lower opening; the photos show the modified opening and adapter installed.

**Requested result:** Replace the restrictive lower cable passage with an open clearance area for the right-angle adapter, incorporating the user's physical modification into the model. The enclosure must rest on its intended desk contact surfaces with the adapter and cable connected.

**Planned investigation and changes, after feedback collection:**

- Measure the actual adapter body, inserted position, mating cable plug, and clearance needed to connect and disconnect it. Exact cutout dimensions and compatibility with other adapters remain unconfirmed.
- Remove the obstructing lower passage material and shape a clean clearance notch around the adapter and cable route, using the photographed modification as the reference.
- Provide a matching opening in the rear plate so the right-angle adapter can project out the back and accept the cable. This must clear the adapter body and mating plug, not just the cable diameter. The user explicitly confirmed rearward exit with photos `IMG_3143.jpeg` and `IMG_3136.jpeg`.
- Coordinate the notch with change 1: moving the screen unit forward also moves its USB-C port and the attached adapter.
- Check rear-cover clearance with the adapter installed, sufficient material around nearby retention features, and the strength and stability of the remaining feet.
- Preserve support-free printability and the self-standing shape without increasing height or adding a base just to accommodate a downward cable.

**Acceptance checks:** The adapter fully seats without force from the printed enclosure; the cable can be connected with the cover installed; neither adapter nor cable lifts or rocks the enclosure on a flat desk; the port is not loaded by desk contact; the cover closes and the remaining lower structure stays secure. Verify using the user's actual adapter and cable before claiming fit.

## 3. Correct the offset of the back plate's bottom cutouts

References: user photos `IMG_3143.jpeg` and `IMG_3136.jpeg`, supplied October 1, 2026.

**Observed problem:** The bottom cutouts of the back plate are offset relative to the corresponding frame/foot geometry. The user clarified that this is a cutout alignment issue, not a snugness or friction-fit issue. Exact offsets remain to be measured.

**Requested result:** Align the back plate's lower cutouts with the frame and feet in the assembled position. Include the rear adapter opening described in change 2. Friction fit is addressed separately in change 4.

**Planned investigation and changes, after feedback collection:**

- Compare the lower cutout positions and profiles with the matching frame/foot geometry in assembled coordinates, accounting for the enclosure's tilt.
- Measure and correct the cutout offsets and contours so the lower edges follow the intended frame clearances. Do not change peg/socket tolerances as part of this item.
- Integrate the rear adapter cutout while retaining enough material around the lower edge and nearby connections. Preserve support-free printing.

**Acceptance checks:** In the assembled enclosure, the bottom cutouts align with the corresponding frame/foot features without unintended offset or overlap. The rear adapter opening provides the clearance specified in change 2. Verify alignment in assembly views and a physical print; assess friction fit separately under change 4.

## 4. Increase friction-fit clearance for easier cover removal

Reference: user photo `IMG_3138.jpeg`, supplied October 1, 2026, showing the inside of the purple rear plate and a broken peg.

**Observed problem:** The plate requires excessive force to push in and is especially difficult to remove. The user reports that a peg broke during removal.

**Requested result:** Increase peg/socket clearance to reduce insertion and removal force, while keeping the cover secure during normal handling. Preserve removable, hardware-free PLA construction and support-free printing.

**Planned investigation and changes, after feedback collection:**

- Review the current peg/socket dimensions and reduce interference by increasing socket clearance, rather than assuming the existing fit is acceptable.
- Select the clearance increment with a revised fit coupon offering several looser fits. Specify whether each adjustment is radial or diametral to avoid ambiguity; exact dimensions remain to be determined.
- Inspect peg roots, entry taper, engagement length, and alignment for binding or concentrated bending during removal. Any supplementary geometry adjustment must preserve easy removal and support-free printing.
- Validate all four connections together after coupon testing; a single peg's fit does not establish the force required to remove the complete cover.

**Acceptance checks:** The cover installs and removes by hand without excessive force or levering that bends the pegs. Repeated assembly/removal produces no broken pegs, cracks, or visible stress damage, and the plate stays attached during ordinary handling. Test using the intended white and purple PLA and P1S print settings before claiming the revised fit is reliable.

## 5. Align button clearances with the fully seated screen unit

Reference: user photo `IMG_3137.jpeg`, supplied October 1, 2026, showing the factory top buttons relative to the printed enclosure openings.

**Observed problem:** When the device was pushed fully forward, the button openings did not align with its factory buttons. The user reports that this held buttons depressed and prevented correct screen operation.

**Requested result:** Correct the front-to-back offset of all three button openings and their plungers for the device's final seated position, including the reduced screen recess from change 1. No button may be held down by the enclosure or plunger at rest.

**Planned investigation and changes, after feedback collection:**

- Establish the final screen seating position from change 1 before locating the button openings. Derive their offsets from that same seating reference so later screen-depth changes also move the button geometry appropriately.
- Measure the factory button positions, protrusion, and actuation travel. Check all three individually rather than assuming their geometry is identical.
- Align the openings and plunger contact surfaces with the factory buttons; provide lateral running clearance and an appropriate resting gap so insertion and cover closure cannot preload them.
- Check plunger length, captive flange clearance, available press travel, and free return with the device fully forward and the rear plate installed. Ensure surrounding cradle material also clears the factory buttons.
- Account for print tolerances and allowed device movement. Select exact offsets and gaps from measurements and a physical fit check, not the photograph alone.

**Acceptance checks:** With the unit fully seated and the cover closed, all three buttons remain released at rest, press independently, and return freely. Installing the device or closing the cover does not actuate a button. Confirm normal startup and screen operation in the assembled enclosure, as well as intentional button operation. Preserve support-free printing.

### Proposed alternative: direct access to factory buttons

The user reports that the separate top plungers do not work well and requested an alternative. **Selected by the user for v7:** replace the three plunger passages with a broad recessed top access opening, with sloped/chamfered edges that let a fingertip reach and press each factory button directly. A purple trim piece could preserve the accent without contacting the buttons.

This removes the added sliding mechanisms and their potential to bind or preload the factory buttons. The tradeoff is an exposed, recessed control area instead of three raised purple caps. Finger access, independent presses, shell strength, and support-free printing must be checked after the final screen seating depth is established. Do not assume the available space is sufficient from the photograph alone.

If direct fingertip access would require an excessively large opening or remains too deep, review a guided button cartridge as a fallback: three short, independently moving captive caps aligned to the device, with controlled travel and resting gaps. This still requires physical tolerance testing and is not the preferred first option.

The plunger-specific steps above apply only if a plunger solution is retained. The alignment and no-preload requirements apply to either approach. The direct-access opening is implemented in v7; the separate plungers are removed.

## Requirements to preserve

- Compact, self-standing ghost with a desk viewing tilt; no separate stand or base.
- Complete Waveshare ESP32-S3-Touch-AMOLED-2.16 factory housing fit.
- Hardware-free PLA friction connections and print orientations that do not require enabled supports.
- Functional top buttons and room for the power cord.
- Bambu P1S, 0.4 mm nozzle; separate white body and purple accent plates, with a separate fit-coupon plate.

## Remaining feedback

The user authorized implementation after all five items and the button alternative were discussed. Await physical feedback on the v9 coupon and enclosure. Adapter reference: UGREEN B0FNCT8NS7, supplied by the user; exact installed fit still needs testing.

## 6. Close dust-catching recesses and square the lower transitions

Implemented in v8 following the annotated v7 render: fill the upper front and side cavities into a continuous button well; extend the removable cover forward with a tongue that closes the gap behind the factory housing; square the lower white heels and cover cutouts, and make their rear surfaces flush. Extend the cover to the lower silhouette and remove decorative rear slots. Retain access to the factory buttons and the rear cable notch.

CAD checks show no housing, button, adapter-reference, or cover interference, including sampled straight cover insertion. The two rear surfaces meet at Z 29.9 mm, with 0.2 mm nominal clearance around the squared heels. The cover tongue has 0.2 mm nominal clearance behind the factory housing. Physical finger access, fit, printing, and stability with the shorter heels still require testing.

## 7. Correct button datum and increase front-wall clearance

The user flagged the v8 ramp as too close to the buttons. The official top-view drawing locates the button centers 9.6 mm from the factory front; v8 mistakenly used the rear datum, displacing the references by 3.3 mm. At corrected positions, each button intersected the v8 body by about 6.84 mm³. Supersede the v8 body.

In v9 the button center depth is 10.4 mm from the printed front. The inner front wall is nearly vertical (3.85°), with a minimum 4.55 mm depth gap to the Ø5.3 mm cap edge. The outer buttons have 4.75 mm side clearance. All three Ø12 mm fingertip approach corridors and 1.5 mm-tall cap test envelopes must clear both body and cover. Button height/travel is not dimensioned in the manufacturer drawing, so actual release, pressing, and return remain physical checks.
