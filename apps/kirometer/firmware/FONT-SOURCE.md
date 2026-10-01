# Firmware font source

Space Grotesk is Kiro Crew's default proportional interface font, verified in
https://github.com/kirodotdev/KiroCrew/blob/main/website/src/index.css on 2026-10-01.

Original unmodified Regular and Bold TTFs downloaded from:
- https://github.com/floriankarsten/space-grotesk/tree/master/fonts/ttf/static
- License: OFL.txt alongside these files (SIL Open Font License 1.1).

Generated 4-bit bitmap subsets cover printable ASCII plus U+2026 in 20/24 px
Regular and 36/48 px Bold. Regenerate with scripts/build_fonts.py (Pillow 12.3.0).
See ../../src/smooth_text.h for RGB565 blending. No LVGL runtime is required.

Kiro website AWS Diatype assets are not included: their embedded font license
restricts redistribution and modification. The app's Space Grotesk is used for
distributable device firmware instead.
