/* motion-montage · motion.js
 * Pure, deterministic motion math. No DOM, no clocks, no randomness.
 * Every value is a function of time t (seconds). Same t → same frame. Always.
 * Exposes window.MM.{ease, bezier, spring, prog, kf, mix, clamp, remap, stagger, noise, vel, hold}
 */
(function (root) {
  const MM = (root.MM = root.MM || {});

  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const mix = (a, b, p) => a + (b - a) * p;
  const remap = (v, a, b, c, d) => c + ((v - a) / (b - a)) * (d - c);

  /* ---------- cubic-bezier solver (same maths as CSS / After Effects speed graph) ---------- */
  function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = (t) => ((ax * t + bx) * t + cx) * t;
    const sy = (t) => ((ay * t + by) * t + cy) * t;
    const dx = (t) => (3 * ax * t + 2 * bx) * t + cx;
    return function (x) {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      let t = x;
      for (let i = 0; i < 8; i++) {
        const e = sx(t) - x;
        if (Math.abs(e) < 1e-6) return sy(t);
        const d = dx(t);
        if (Math.abs(d) < 1e-6) break;
        t -= e / d;
      }
      let lo = 0, hi = 1; t = x;
      for (let i = 0; i < 30; i++) {
        const v = sx(t);
        if (Math.abs(v - x) < 1e-6) break;
        if (x > v) lo = t; else hi = t;
        t = (lo + hi) / 2;
      }
      return sy(t);
    };
  }

  /* ---------- easing vocabulary ----------
   * Named by FEEL, not by maths, so agents pick by intent.
   *  enter  → things arriving: decelerate hard (out curves)
   *  exit   → things leaving: accelerate (in curves), shorter than enters
   *  move   → things travelling on screen: inOut
   *  snap   → the "editor" curve: very fast start, long silky settle
   */
  const ease = {
    linear: (t) => t,
    inQuad: (t) => t * t,
    outQuad: (t) => 1 - (1 - t) * (1 - t),
    inCubic: (t) => t * t * t,
    outCubic: (t) => 1 - Math.pow(1 - t, 3),
    inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    inQuart: (t) => t * t * t * t,
    outQuart: (t) => 1 - Math.pow(1 - t, 4),
    inOutQuart: (t) => (t < 0.5 ? 8 * t ** 4 : 1 - Math.pow(-2 * t + 2, 4) / 2),
    outQuint: (t) => 1 - Math.pow(1 - t, 5),
    inExpo: (t) => (t === 0 ? 0 : Math.pow(2, 10 * t - 10)),
    outExpo: (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    inOutExpo: (t) =>
      t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2,
    outBack: (t, s = 1.4) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
    inBack: (t, s = 1.4) => (s + 1) * t * t * t - s * t * t,
    // signature curves
    snap: bezier(0.16, 1, 0.3, 1),        // "expo-out" feel, the pro default for enters
    glide: bezier(0.65, 0, 0.35, 1),      // smooth travel, camera moves
    whip: bezier(0.75, 0, 0.15, 1),       // whip pans / push transitions: slow-FAST-slow
    anticipate: bezier(0.36, 0, 0.66, -0.56), // tiny pull-back before going
    exit: bezier(0.55, 0, 1, 0.45),       // leave the frame, accelerating
    emphasized: bezier(0.2, 0, 0, 1),     // Material "emphasized" — confident UI motion
  };

  /* ---------- damped spring (closed form, deterministic) ----------
   * spring({ stiffness:170, damping:26, mass:1 })(tSeconds) → 0..~1
   * Use for pops, stickers, landing cards. damping < 2*sqrt(k*m) overshoots.
   */
  function spring({ stiffness = 170, damping = 26, mass = 1, velocity = 0 } = {}) {
    const w0 = Math.sqrt(stiffness / mass);
    const zeta = damping / (2 * Math.sqrt(stiffness * mass));
    return function (t) {
      if (t <= 0) return 0;
      let x;
      if (zeta < 1) {
        const wd = w0 * Math.sqrt(1 - zeta * zeta);
        const A = 1, B = (zeta * w0 - velocity) / wd;
        x = Math.exp(-zeta * w0 * t) * (A * Math.cos(wd * t) + B * Math.sin(wd * t));
      } else {
        const A = 1, B = w0 - velocity;
        x = Math.exp(-w0 * t) * (A + B * t);
      }
      return 1 - x;
    };
  }
  spring.pop = spring({ stiffness: 320, damping: 18 });   // stickers, highlight blocks
  spring.land = spring({ stiffness: 200, damping: 24 });  // cards landing
  spring.soft = spring({ stiffness: 120, damping: 20 });  // big type settling

  /* ---------- progress helpers ---------- */
  // prog(t, start, dur, easing) → eased 0..1, clamped
  function prog(t, start, dur, e = ease.snap) {
    if (dur <= 0) return t >= start ? 1 : 0;
    const p = clamp((t - start) / dur);
    return typeof e === 'function' ? e(p) : p;
  }
  // window: in → hold → out. Returns {in, out, v} where v = in * (1-out)
  function inOut(t, start, end, inDur = 0.45, outDur = 0.3, eIn = ease.snap, eOut = ease.exit) {
    const a = prog(t, start, inDur, eIn);
    const b = prog(t, end - outDur, outDur, eOut);
    return { in: a, out: b, v: a * (1 - b) };
  }

  /* ---------- keyframes ----------
   * kf(t, [[time, value, easeIntoThisKey?], ...])  — values may be numbers or arrays
   * Mirrors AE keyframes: the easing on a key describes the segment ARRIVING at it.
   */
  function kf(t, keys) {
    if (!keys.length) return 0;
    if (t <= keys[0][0]) return keys[0][1];
    const last = keys[keys.length - 1];
    if (t >= last[0]) return last[1];
    for (let i = 1; i < keys.length; i++) {
      const [t1, v1, e] = keys[i];
      if (t <= t1) {
        const [t0, v0] = keys[i - 1];
        const p = (e || ease.inOutCubic)((t - t0) / (t1 - t0));
        if (Array.isArray(v0)) return v0.map((x, j) => mix(x, v1[j], p));
        return mix(v0, v1, p);
      }
    }
    return last[1];
  }

  /* ---------- stagger ----------
   * stagger(i, n, each, from) → delay for item i of n.  from: 'start'|'end'|'center'|'edges'|'random'
   */
  function stagger(i, n, each = 0.06, from = 'start') {
    switch (from) {
      case 'end': return (n - 1 - i) * each;
      case 'center': return Math.abs(i - (n - 1) / 2) * each;
      case 'edges': return ((n - 1) / 2 - Math.abs(i - (n - 1) / 2)) * each;
      case 'random': return hash(i * 12.9898) * each * (n - 1);
      default: return i * each;
    }
  }

  /* ---------- seeded smooth noise (for handheld drift, never for chaos) ---------- */
  function hash(x) { const s = Math.sin(x * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
  function noise(seed, t) {
    const i = Math.floor(t), f = t - i;
    const u = f * f * (3 - 2 * f);
    return mix(hash(seed * 7.13 + i), hash(seed * 7.13 + i + 1), u) * 2 - 1;
  }
  // fractal drift, amplitude ~1
  function drift(seed, t, speed = 0.35) {
    return noise(seed, t * speed) * 0.65 + noise(seed + 9, t * speed * 2.1) * 0.35;
  }

  /* ---------- velocity of any f(t) — feeds motion blur ---------- */
  function vel(f, t, h = 1 / 240) { return (f(t + h) - f(t - h)) / (2 * h); }

  /* ---------- time remapping (speed ramps for footage) ----------
   * ramp(t, [[outT, srcT], ...]) piecewise with smooth easing between keys.
   * Typical ramp: real-time → 0.25x slow-mo on the hit → snap back to 1.5x.
   */
  function ramp(t, keys, e = ease.inOutCubic) { return kf(t, keys.map(([a, b]) => [a, b, e])); }

  Object.assign(MM, { clamp, mix, remap, bezier, ease, spring, prog, inOut, kf, stagger, hash, noise, drift, vel, ramp });
})(typeof window !== 'undefined' ? window : globalThis);
