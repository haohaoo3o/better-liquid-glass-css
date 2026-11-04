# Modifications relative to upstream

Upstream: [gentpan/liquidglass](https://github.com/gentpan/liquidglass) — MIT, © 2026 gentpan.
This repository keeps the engine's architecture (SVG `feDisplacementMap` referenced from CSS
`filter: url(#…)`, one runtime-generated displacement map per element) and changes the parts that
decided how the glass *looks* and how it is *attached* to a card.

## 1. Five weighted spectral samples instead of three

`CHANNELS` in `src/liquid-glass.js` used to isolate R, G and B and displace each at its own scale.
With a large `chroma` that reads as three hard colour bands.

The engine now uses five weighted samples spanning R→G→B, with weights that sum to exactly 1 on
every channel, so the fringe stays narrow and the glass keeps its colour. A nine-band variant was
tried; at the same `chroma` it filled the gap between bands and read as a wider, muddier rainbow,
so the five-band set is what ships.

Scales follow `CHROMA_T = [0, 0.35, 0.5, 0.75, 1]`.

## 2. Linear interpolation in the lens profile

`const m = table[Math.min(N, Math.round(s * N))]` snapped the bend to the nearest table entry, which
shows up as concentric steps at high `refraction`. It now interpolates between `i0` and `i1`.

## 3. Ordered dithering on the displacement bytes

The map stores the bend in 8-bit R/G channels. At `refraction: 92` one LSB is ≈ 0.7 CSS px, enough to
band. A 4×4 Bayer offset is added before rounding; the banding turns into fine grain that disappears at
capture resolution. An interleaved-gradient-noise variant was tested and reverted: at large
`refraction` the noise itself became visible as speckle along the rim.

## 4. `mapScale` raised to 4–5

The demo renders at 4× (optics page at 5×). Cost is memory for the offscreen map; the payoff is a
continuous edge instead of a 2 px staircase.

## 5. Refraction scales with the element

A 42 px tall pill given `refraction: 92` has its rounded caps dragged outward past their own border.
`glass-plate.js` now derives it from the short side: `clamp(shortSide * 0.30, 8 … 92)`, and per-element
`data-refraction` still wins.

## 6. `glass-plate.js` — the attachment layer

Replaces the per-card "clone the background inside the card and guess the offset" approach:

- one full-stage copy of the background layers, anchored at stage origin (0, 0);
- clipped to the card's border box with `clip-path: inset(… round …)` measured from
  `getBoundingClientRect()`;
- re-measured after `document.fonts.ready`, on `resize`, on the next two frames, and after 600 ms.

Offset drift is structurally impossible: the copy never moves, only the clip changes.

## Not changed

Engine detection, the SVG filter graph, fallback to `backdrop-filter`, the lens-profile maths
(`profileTable`, `bendScale`, specular rim), and the public `createGlass()` signature.
