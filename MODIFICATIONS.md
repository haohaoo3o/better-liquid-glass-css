# Modifications relative to upstream

Upstream: [gentpan/liquidglass](https://github.com/gentpan/liquidglass) — MIT, © 2026 gentpan.
This repository keeps the engine's architecture (SVG `feDisplacementMap` referenced from CSS
`filter: url(#…)`, one runtime-generated displacement map per element) and changes the parts that
decided how the glass *looks* and how it is *attached* to a card.

## 1. Nine spectral samples instead of three

`CHANNELS` in `src/liquid-glass.js` used to isolate R, G and B and displace each at its own scale.
With a large `chroma` that reads as three hard colour bands.

The engine now builds nine bands along the R→G→B axis and normalises the per-channel weights so
each channel still sums to 1. Colour energy is preserved (the glass does not darken) and the fringe
becomes a continuous spectrum, which is what lets the demo run with `blur: 0` and stay crisp.

Scales are `i / 8` for i in 0…8.

## 2. Linear interpolation in the lens profile

`const m = table[Math.min(N, Math.round(s * N))]` snapped the bend to the nearest table entry, which
shows up as concentric steps at high `refraction`. It now interpolates between `i0` and `i1`.

## 3. Noise dithering on the displacement bytes

The map stores the bend in 8-bit R/G channels. At `refraction: 92` one LSB is ≈ 0.7 CSS px, enough to
band. A 4×4 Bayer matrix was the first attempt, but a periodic pattern shows up as a visible dot lattice
once `refraction` grows. It is now interleaved gradient noise (non-repeating) at ~±0.4 LSB, which
reads as fine grain and vanishes at capture resolution.

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
