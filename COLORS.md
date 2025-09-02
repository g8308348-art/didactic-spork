# Color System

This document defines the base color palette and how it maps to CSS variables used in the app (`public/css/style.css`).

## Palette (Ultramarine scale)

- U-10 — Navy — HEX: TBD (confirm exact hex)
- U-7 — Ultramarine — HEX: #0047FF
- U-5 — HEX: #4489FF
- U-3 — HEX: #A3CDFF
- U-1 — Sky — HEX: TBD (light sky; currently similar to very light blue backgrounds)

> Note: Please confirm the exact HEX values for U-10 (Navy) and U-1 (Sky). Once confirmed, update the variables in the stylesheet.

## CSS Variable Mapping

We expose the palette through variables and map existing theme tokens to them.

- `--u10-navy` → Navy (U-10)
- `--u7-ultramarine` → Ultramarine (U-7)
- `--u5` → U-5 (#4489FF)
- `--u3` → U-3 (#A3CDFF)
- `--u1-sky` → Sky (U-1)

Theme tokens that reference the palette:

- `--primary-color` = `var(--u7-ultramarine)`
- `--topbar-color` = `#ffffff` (kept white to contrast with primary accents)
- `--privacy-panel-bg` = uses a very light blue similar to U-1 for soft panels

## Usage Guidelines

- Primary UI accents (buttons, focus rings, navbar/footer background): use `--primary-color` (U-7).
- Informational highlights, borders, links: also `--primary-color` by default.
- Subtle backgrounds (tables, panels): prefer `--u1-sky` once its hex is confirmed.
- Progressively lighter blues for states/visualizations: U-5, U-3, U-1.

## Next Steps

- Provide exact HEX for U-10 (Navy) and U-1 (Sky) and I will finalize the variables.
- If there is a dark-mode palette, we can add dark variants (e.g., `--u7-ultramarine-dark`).
