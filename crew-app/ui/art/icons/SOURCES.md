# Shared UI icons

Default library: **Lucide** (ISC license; see LUCIDE-LICENSE).

Kiro Crew imports `lucide-react` for its interface:
- https://github.com/kirodotdev/KiroCrew/blob/main/website/package.json
- https://github.com/kirodotdev/KiroCrew/blob/main/website/src/pages/ChatSidebar.tsx

SVGs retrieved October 1, 2026 from https://github.com/lucide-icons/lucide/tree/main/icons.
Original viewBox, paths, stroke width, caps, and joins are preserved.
Run `python3 scripts/build_icons.py` after adding assets. The generated module
serves the Crew app and canvas gallery; gallery thumbnails use the same SVGs.

Use the accompanying numeric percentage for exact battery level. Full >=95%,
medium >=40%, low >=10%, empty <10%; charging supersedes the fill glyph.
Unknown battery readings use battery-warning with an explicit text label.
A device reporting USB power without a battery uses plug, not a charging battery.
