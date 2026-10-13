/* motion-montage · transitions.js
 * The edit: scene visibility + a library of transitions, driven by one call.
 *
 *   MM.edit(t, scenes, cuts)
 *     scenes: [{el, start, end}]   (scene i ends where scene i+1 starts)
 *     cuts:   [{type:'push', dur:0.45, dir:'left', at?}]  cuts[i] sits between scene i and i+1.
 *             `at` defaults to scenes[i].end — the cut centre. Put it ON a spoken word.
 *
 * Every transition gets p ∈ [0,1] across [at - dur/2, at + dur/2] and sets styles on
 * the two .scene roots (A = outgoing, B = incoming) and the shared overlay.
 * The camera lives on the scene's [data-depth] layers, so transitions never fight it.
 */
(function (root) {
  const MM = root.MM;
  const { clamp, mix, ease, set } = MM;
  const W = () => MM.SAFE.W, H = () => MM.SAFE.H;

  let overlay = null;
  function getOverlay() {
    if (overlay) return overlay;
    overlay = document.createElement('div');
    overlay.id = 'mm-overlay';
    Object.assign(overlay.style, { position: 'absolute', inset: '0', pointerEvents: 'none', zIndex: 900, overflow: 'hidden' });
    for (let i = 0; i < 3; i++) {
      const p = document.createElement('div');
      Object.assign(p.style, { position: 'absolute', left: '-10%', top: '-10%', width: '120%', height: '120%', display: 'none' });
      overlay.appendChild(p);
    }
    (MM.$('#frame') || document.body).appendChild(overlay);
    return overlay;
  }

  const NORMAL = { x: 0, y: 0, scale: 1, rot: 0, resetT: true, opacity: 1, clip: 'none', blur: 0, mb: [0, 0], bright: 1, z: '' };
  // velocity-based blur amount for an eased 0..1 travel over `dist` px in `dur` s
  function mbAmt(e, p, dist, dur, k = 0.5) {
    const h = 0.004;
    const v = ((e(clamp(p + h)) - e(clamp(p - h))) / (2 * h)) * (dist / dur); // px/s
    return clamp((v / 60) * 0.5 * k, 0, 80); // 60fps, 180° shutter
  }
  const dirVec = { left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] };

  const TX = {
    cut() {},

    /* hard-edged wipe: B revealed by a moving edge; A drifts away from the edge */
    wipe(p, A, B, o) {
      const e = o.ease || ease.inOutQuart, q = e(p), d = o.dir || 'up';
      const r = (1 - q) * 100;
      const clip = { up: `inset(${r}% 0 0 0)`, down: `inset(0 0 ${r}% 0)`, left: `inset(0 0 0 ${r}%)`, right: `inset(0 ${r}% 0 0)` }[d];
      const [vx, vy] = dirVec[d];
      set(A, { x: vx * q * 90, y: vy * q * 160, bright: 1 - q * 0.25 });
      set(B, { clip, z: 2 });
    },

    /* the "rising panel" — B arrives as a rounded sheet from below, A recedes (AEasyI signature) */
    panel(p, A, B, o) {
      const q = (o.ease || ease.inOutQuart)(p);
      const rad = mix(o.radius ?? 64, 0, ease.inCubic(p));
      set(B, { clip: `inset(${((1 - q) * 100).toFixed(2)}% 0 0 0 round ${rad.toFixed(1)}px ${rad.toFixed(1)}px 0 0)`, z: 2, y: (1 - q) * 140 });
      set(A, { scale: 1 - q * 0.06, y: -q * 120, bright: 1 - q * 0.35, origin: '50% 30%' });
    },

    /* push: both scenes travel together. Directional motion blur from real velocity. */
    push(p, A, B, o, ctx) {
      const e = o.ease || ease.whip, q = e(p), d = o.dir || 'left';
      const [vx, vy] = dirVec[d];
      const dist = vx ? W() : H();
      const b = mbAmt(e, p, dist, ctx.dur, o.blur ?? 0.6);
      const mb = vx ? [b, 0] : [0, b];
      set(A, { x: vx * q * W(), y: vy * q * H(), mb });
      set(B, { x: vx * (q - 1) * W(), y: vy * (q - 1) * H(), mb, z: 2 });
    },

    /* whip pan: a short push with heavy blur and a breath of zoom — energy cuts */
    whip(p, A, B, o, ctx) {
      TX.push(p, A, B, Object.assign({ ease: ease.whip, blur: 1.4 }, o), ctx);
      const s = 1 + Math.sin(p * Math.PI) * (o.zoom ?? 0.06);
      A.style.transform += ` scale(${s.toFixed(4)})`; A.__tr = null;
      B.style.transform += ` scale(${s.toFixed(4)})`; B.__tr = null;
    },

    /* zoom-through: A rushes at camera and blows out, B lands from depth */
    zoom(p, A, B, o) {
      const a = clamp(p / 0.55), b = clamp((p - 0.4) / 0.6);
      const ea = ease.inExpo(a), eb = ease.outExpo(b);
      set(A, { scale: mix(1, o.to ?? 2.8, ea), blur: ea * 22, opacity: 1 - clamp((a - 0.6) / 0.4), origin: o.origin || '50% 50%' });
      set(B, { scale: mix(o.from ?? 0.72, 1, eb), blur: (1 - eb) * 18, opacity: clamp(b * 2.5), z: 2, origin: o.origin || '50% 50%' });
    },

    /* iris: a circle opens from a point (a dot, a word, a button) */
    iris(p, A, B, o) {
      const q = (o.ease || ease.inOutQuart)(p);
      const x = o.x ?? 50, y = o.y ?? 50;
      set(B, { clip: `circle(${(q * 120).toFixed(2)}% at ${x}% ${y}%)`, z: 2 });
      set(A, { scale: 1 - q * 0.05, bright: 1 - q * 0.3 });
    },

    /* slats: B arrives in N staggered stripes (graphic, editorial) */
    slats(p, A, B, o) {
      const n = o.n || 6, each = o.each ?? 0.5 / n, dur = 1 - each * (n - 1);
      const pts = [];
      const vertical = (o.dir || 'up') === 'up' || o.dir === 'down';
      for (let i = 0; i < n; i++) {
        const q = ease.inOutQuart(clamp((p - i * each) / dur)) * 100;
        const a = (i / n) * 100, b = ((i + 1) / n) * 100 + 0.05;
        if (vertical) pts.push(`${a}% 100%`, `${a}% ${100 - q}%`, `${b}% ${100 - q}%`, `${b}% 100%`);
        else pts.push(`0% ${a}%`, `${q}% ${a}%`, `${q}% ${b}%`, `0% ${b}%`);
      }
      const poly = vertical ? `polygon(0% 100%, ${pts.join(',')}, 100% 100%)` : `polygon(0% 0%, ${pts.join(',')}, 0% 100%)`;
      set(B, { clip: poly, z: 2 });
      set(A, { bright: 1 - p * 0.3 });
    },

    /* sweep: colour panels cross the frame, covering the cut (1–3 layered panels) */
    sweep(p, A, B, o) {
      const ov = getOverlay();
      const colors = o.colors || [o.color || '#111'];
      const d = o.dir || 'up';
      const [vx, vy] = dirVec[d];
      const stag = o.stagger ?? 0.09;
      colors.forEach((c, i) => {
        const el = ov.children[i];
        const lp = clamp((p - i * stag) / (1 - stag * (colors.length - 1)));
        // travel from +1 (off) → 0 (covering) → -1 (off), using whip
        const pos = 1 - 2 * ease.inOutQuart(lp);
        el.style.display = lp > 0 && lp < 1 ? 'block' : 'none';
        el.style.background = c;
        const skew = o.skew ?? -6;
        el.style.transform = `translate(${(-vx * pos * 120).toFixed(2)}%, ${(-vy * pos * 120).toFixed(2)}%) skew${vx ? 'X' : 'Y'}(${skew}deg)`;
      });
      const mid = 0.5 + stag * (colors.length - 1) * 0.5;
      set(A, { opacity: p < mid ? 1 : 0 });
      set(B, { opacity: p < mid ? 0 : 1, z: 2, scale: p < mid ? 1.04 : mix(1.04, 1, ease.outCubic(clamp((p - mid) / (1 - mid)))) });
    },

    /* stack: A shrinks into a card and lifts away, B slides up as a card and unfolds full-frame */
    stack(p, A, B, o) {
      const q = ease.snap(p), r = o.radius ?? 56;
      set(A, { scale: mix(1, 0.86, ease.inOutCubic(p)), y: -q * 140, bright: 1 - q * 0.45, clip: `inset(0 round ${(ease.outCubic(p) * r).toFixed(1)}px)` });
      const b = ease.snap(clamp((p - 0.12) / 0.88));
      set(B, { y: (1 - b) * H() * 0.9, scale: mix(0.86, 1, ease.inOutCubic(clamp((p - 0.45) / 0.55))), clip: `inset(0 round ${((1 - clamp((p - 0.6) / 0.4)) * r).toFixed(1)}px)`, z: 2 });
    },

    /* dissolve: soft blur cross-fade (calm, luxury, time passing) */
    dissolve(p, A, B, o) {
      const q = ease.inOutCubic(p), bl = o.blur ?? 10;
      set(A, { opacity: 1 - q, blur: q * bl });
      set(B, { opacity: q, blur: (1 - q) * bl, z: 2 });
    },

    /* dip: to a colour and back (end-cards, chapter breaks) */
    dip(p, A, B, o) {
      const ov = getOverlay(), el = ov.children[0];
      el.style.display = 'block'; el.style.transform = 'none'; el.style.background = o.color || '#000';
      el.style.opacity = (1 - Math.abs(p * 2 - 1)).toFixed(3);
      set(A, { opacity: p < 0.5 ? 1 : 0 });
      set(B, { opacity: p < 0.5 ? 0 : 1, z: 2 });
    },
  };
  MM.TX = TX;

  /* ---------- the edit driver ---------- */
  MM.edit = function (t, scenes, cuts = []) {
    const n = scenes.length;
    // hide overlay panels by default each frame
    if (overlay) for (const c of overlay.children) c.style.display = 'none';
    const win = cuts.map((c, i) => {
      if (!c || i >= n - 1) return null;
      const at = c.at ?? scenes[i].end;
      const dur = c.type === 'cut' ? 0 : c.dur ?? 0.5;
      return { at, dur, a: at - dur / 2, b: at + dur / 2, c };
    });
    for (let i = 0; i < n; i++) {
      const s = scenes[i];
      const inW = win[i - 1], outW = win[i];
      const from = inW ? inW.a : s.start;
      const to = outW ? outW.b : s.end;
      const on = t >= from && t < (outW ? (outW.dur ? to : outW.at) : to + 1e9);
      set(s.el, { vis: on });
      if (on) set(s.el, NORMAL);
      s.el.style.zIndex = '';
    }
    MM.txActive = false;
    win.forEach((w, i) => {
      if (!w || !w.dur) return;
      if (t < w.a || t >= w.b) return;
      MM.txActive = true;
      const p = (t - w.a) / w.dur;
      const fn = TX[w.c.type] || TX.dissolve;
      fn(p, scenes[i].el, scenes[i + 1].el, w.c, { t, at: w.at, dur: w.dur });
    });
  };
})(typeof window !== 'undefined' ? window : globalThis);
