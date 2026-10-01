# Kiro ghost artwork

Unmodified PNG assets downloaded from https://github.com/kirodotdev/spirit-of-kiro/tree/main/client/src/assets/kiro-ghost

Repository main revision at download: `ff0c8c22cb4026f83df5aa9155e9b7f410809f30`.

Copyright Amazon.com, Inc. or its affiliates. Repository license: MIT No Attribution (included in LICENSE).

The HTML preview renders directional poses and adds runtime eye overlays for blinking. Original PNG files are unchanged.

Firmware 0.5.8 uses South, East and North originals plus a mirrored East for West (upstream has no West asset). scripts/build_ghost_sprites.py crops and scales these into RGB565 on pure black and generates blink variants; source PNGs are unchanged.
