/**
 * glass-plate.js — page-anchored backdrop copies for liquid-glass.js
 *
 * The problem this solves: liquid-glass.js bends whatever pixels sit *behind* the filtered
 * element. A card that is painted over a page background needs an exact copy of that background
 * inside itself, otherwise the lens has nothing to bend and the result is a flat tint.
 *
 * Naive implementations clone the background into the card and guess the offset. Any border,
 * padding or webfont reflow makes the copy drift, and the glass stops lining up with the card.
 *
 * This module instead:
 *   1. lays one full-stage copy of the background layers at the stage origin (0, 0),
 *   2. clips it to the card's exact border box with `clip-path: inset(… round …)`,
 *   3. tells the lens engine to bend only inside that same rectangle.
 *
 * Because the copy never moves and the clip is measured from `getBoundingClientRect()`, the
 * alignment is exact by construction — no offsets to tune. Everything is re-measured after
 * webfonts settle and on resize.
 *
 * Usage:
 *   import { mountGlassPlate } from './glass-plate.js';
 *   const glass = mountGlassPlate(document.querySelector('.stage'));
 *
 * Mark cards with `data-glass`. Optional per-element overrides:
 *   data-refraction="60"  data-chroma="0.3"  data-bezel="0.4"  data-radius="24"
 */

import { createGlass } from './liquid-glass.js';

const DEFAULTS = {
  targets: '[data-glass]',
  /** Background layers to copy, in paint order. Each is cloned once per plate. */
  layers: ['.lg-bg', '.lg-scrim'],
  /** Lens defaults; tune per project. */
  // Rim model borrowed from kubai087/glasswork: the refracting band is an absolute
  // width in CSS px, the very edge samples `edge * rim` inward, and dispersion is a
  // small fraction (0.15 = red 15% further than blue), not a broad rainbow.
  rim: 68,
  edge: 1.05,
  refraction: null, // null = auto: min(rim * edge, shortSide * 0.5)
  bezel: 0.56,
  curvature: 4,
  chroma: 0.45,
  specular: 0.86,
  specularWidth: 2.4,
  blur: 0,
  mapScale: 4,
  // Under-glass treatment borrowed from glasswork: a light blur plus saturation/brightness
  // lift keeps the glass clear instead of milky. Set frost.blur = 0 to disable.
  frost: { blur: 0.8, saturate: 1.35, brightness: 1.04 },
};

const num = (el, name) => {
  const v = el.getAttribute(name);
  return v === null || v === '' ? null : Number(v);
};

/**
 * @param {HTMLElement} stage  positioned element that wraps the background layers and the cards
 * @param {object} [options]
 * @returns {{ refresh: () => void, destroy: () => void, instances: Array }}
 */
export function mountGlassPlate(stage, options = {}) {
  if (!stage) throw new Error('mountGlassPlate: stage element is required');
  const o = { ...DEFAULTS, ...options };
  const instances = [];

  const stageRect = () => stage.getBoundingClientRect();

  function layerHost() {
    let host = null;
    for (const sel of o.layers) {
      const el = stage.querySelector(sel);
      if (el) host = el;
    }
    return host || stage.lastElementChild;
  }

  function buildPlate(card) {
    const plate = document.createElement('div');
    plate.className = 'lg-plate';
    plate.setAttribute('aria-hidden', 'true');
    plate.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;';

    const inner = document.createElement('div');
    inner.className = 'lg-plate-inner';
    inner.style.cssText = 'position:absolute;left:0;top:0;';

    for (const sel of o.layers) {
      const src = stage.querySelector(sel);
      if (!src) continue;
      const copy = src.cloneNode(true);
      copy.classList.add('lg-layer-copy');
      copy.style.position = 'absolute';
      copy.style.inset = '0';
      copy.style.margin = '0';
      inner.appendChild(copy);
    }

    plate.appendChild(inner);
    layerHost().insertAdjacentElement('afterend', plate);
    return { plate, inner };
  }

  function measure(card, plate, inner) {
    const r = card.getBoundingClientRect();
    const s = stageRect();
    if (r.width < 2 || r.height < 2) return;

    const w = Math.round(s.width);
    const h = Math.round(s.height);
    const x = r.left - s.left;
    const y = r.top - s.top;

    const radius = num(card, 'data-radius') ?? (parseFloat(getComputedStyle(card).borderTopLeftRadius) || 24);
    const shortSide = Math.min(r.width, r.height);
    const rim = num(card, 'data-rim') ?? o.rim;
    const edge = num(card, 'data-edge') ?? o.edge;
    const refraction = num(card, 'data-refraction') ?? o.refraction ?? Math.min(rim * edge, shortSide * 0.5);
    const bezel = num(card, 'data-bezel') ?? Math.min(1, rim / Math.max(1, shortSide / 2));

    plate.style.width = `${w}px`;
    plate.style.height = `${h}px`;
    inner.style.width = `${w}px`;
    inner.style.height = `${h}px`;
    plate.style.clipPath =
      `inset(${y}px ${w - (x + r.width)}px ${h - (y + r.height)}px ${x}px round ${radius}px)`;

    return {
      x, y, width: r.width, height: r.height, radius, refraction,
      bezel,
      curvature: num(card, 'data-curvature') ?? o.curvature,
      chroma: num(card, 'data-chroma') ?? o.chroma,
      specular: num(card, 'data-specular') ?? o.specular,
      specularWidth: num(card, 'data-specular-width') ?? o.specularWidth,
      blur: num(card, 'data-blur') ?? o.blur,
      mapScale: num(card, 'data-map-scale') ?? o.mapScale,
    };
  }

  function mount(card) {
    if (card.dataset.lgMounted === '1') return;
    card.dataset.lgMounted = '1';

    const { plate, inner } = buildPlate(card);
    const geometry = measure(card, plate, inner);
    if (!geometry) return;

    applyFrost(inner);
    const ctrl = createGlass(inner, geometry);
    instances.push({ card, plate, inner, ctrl });
  }

  function applyFrost(inner) {
    const f = o.frost;
    if (!f || !f.blur) return;
    for (const layer of inner.children) {
      layer.style.filter = `blur(${f.blur}px) saturate(${f.saturate}) brightness(${f.brightness})`;
    }
  }

  function refresh() {
    for (const it of instances) {
      const geometry = measure(it.card, it.plate, it.inner);
      if (geometry) it.ctrl.update(geometry);
    }
  }

  function run() {
    stage.querySelectorAll(o.targets).forEach(mount);
  }

  run();
  requestAnimationFrame(run);
  requestAnimationFrame(() => requestAnimationFrame(refresh));
  if (document.fonts?.ready) document.fonts.ready.then(() => requestAnimationFrame(refresh));
  window.addEventListener('resize', refresh);
  const settle = setTimeout(refresh, 600);

  return {
    refresh,
    instances,
    destroy() {
      clearTimeout(settle);
      window.removeEventListener('resize', refresh);
      for (const it of instances) {
        it.ctrl.destroy?.();
        it.plate.remove();
        delete it.card.dataset.lgMounted;
      }
      instances.length = 0;
    },
  };
}
