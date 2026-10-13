/* motion-montage · stage.js
 * DOM layer: fast style setter, scenes, camera + parallax, motion blur,
 * footage frames, word timeline, sound cues, grain, and the QC probe.
 * Requires motion.js loaded first.
 */
(function (root) {
  const MM = root.MM;
  const { clamp, mix } = MM;

  /* ---------- selectors ---------- */
  MM.$ = (s, r = document) => r.querySelector(s);
  MM.$$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  /* ---------- set(): one call, all transforms, no layout thrash ----------
   * props: x y (px) | xp yp (% of own size) | scale sx sy | rot rx ry (deg) | persp
   *        opacity | blur (px) | mb [x,y] directional motion blur px | bright | sat
   *        clip (css clip-path string) | origin | z (z-index) | vis (bool)
   *        any other key is written straight to style (e.g. color, background)
   */
  let mbId = 0;
  let svgDefs = null;
  function mbFilter(el, bx, by) {
    if (!svgDefs) {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('width', '0'); svg.setAttribute('height', '0');
      svg.style.position = 'absolute';
      svgDefs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
      svg.appendChild(svgDefs); document.body.appendChild(svg);
    }
    if (!el.__mb) {
      const id = 'mm-mb-' + mbId++;
      const f = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
      f.setAttribute('id', id);
      f.setAttribute('x', '-50%'); f.setAttribute('y', '-50%');
      f.setAttribute('width', '200%'); f.setAttribute('height', '200%');
      f.setAttribute('color-interpolation-filters', 'sRGB');
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
      f.appendChild(g); svgDefs.appendChild(f);
      el.__mb = { id, g };
    }
    el.__mb.g.setAttribute('stdDeviation', `${Math.abs(bx).toFixed(2)} ${Math.abs(by).toFixed(2)}`);
    return `url(#${el.__mb.id})`;
  }

  function set(el, p) {
    if (!el) return;
    if (Array.isArray(el) || el instanceof NodeList) { for (const e of el) set(e, p); return; }
    const s = el.style;
    const T = [];
    if (p.persp) T.push(`perspective(${p.persp}px)`);
    if (p.x != null || p.y != null) T.push(`translate3d(${(p.x || 0).toFixed(2)}px,${(p.y || 0).toFixed(2)}px,0)`);
    if (p.xp != null || p.yp != null) T.push(`translate(${(p.xp || 0).toFixed(3)}%,${(p.yp || 0).toFixed(3)}%)`);
    if (p.rx) T.push(`rotateX(${p.rx.toFixed(3)}deg)`);
    if (p.ry) T.push(`rotateY(${p.ry.toFixed(3)}deg)`);
    if (p.rot) T.push(`rotate(${p.rot.toFixed(3)}deg)`);
    if (p.scale != null) T.push(`scale(${p.scale.toFixed(4)})`);
    if (p.sx != null || p.sy != null) T.push(`scale(${(p.sx ?? 1).toFixed(4)},${(p.sy ?? 1).toFixed(4)})`);
    const tr = T.join(' ');
    if (T.length || p.resetT) if (el.__tr !== tr) { s.transform = tr; el.__tr = tr; }

    const F = [];
    if (p.mb && (Math.abs(p.mb[0]) > 0.3 || Math.abs(p.mb[1]) > 0.3)) F.push(mbFilter(el, p.mb[0], p.mb[1]));
    if (p.blur > 0.05) F.push(`blur(${p.blur.toFixed(2)}px)`);
    if (p.bright != null) F.push(`brightness(${p.bright.toFixed(3)})`);
    if (p.sat != null) F.push(`saturate(${p.sat.toFixed(3)})`);
    if ('blur' in p || 'mb' in p || 'bright' in p || 'sat' in p) {
      const f = F.join(' ') || 'none';
      if (el.__f !== f) { s.filter = f; el.__f = f; }
    }
    if (p.opacity != null) { const o = clamp(p.opacity).toFixed(4); if (el.__o !== o) { s.opacity = o; el.__o = o; } }
    if (p.clip != null && el.__c !== p.clip) { s.clipPath = p.clip; el.__c = p.clip; }
    if (p.origin) s.transformOrigin = p.origin;
    if (p.z != null) s.zIndex = p.z;
    if (p.vis != null) { const d = p.vis ? '' : 'none'; if (el.__d !== d) { s.display = d; el.__d = d; } }
    for (const k in p) {
      if (!(k in SKIP)) s[k] = p[k];
    }
  }
  const SKIP = { x: 1, y: 1, xp: 1, yp: 1, rx: 1, ry: 1, rot: 1, scale: 1, sx: 1, sy: 1, persp: 1, mb: 1, blur: 1, bright: 1, sat: 1, opacity: 1, clip: 1, origin: 1, z: 1, vis: 1, resetT: 1 };
  MM.set = set;

  /* ---------- scenes ----------
   * MM.scene(el, start, end, {pre, post}) → returns local time info and toggles display.
   * pre/post keep the scene alive around its cut for transitions & overlaps.
   */
  MM.scene = function (el, t, start, end, { pre = 0.8, post = 0.8 } = {}) {
    const on = t >= start - pre && t < end + post;
    set(el, { vis: on });
    return { on, local: t - start, dur: end - start, p: clamp((t - start) / (end - start)) };
  };

  /* ---------- camera with parallax ----------
   * Children with data-depth="d" move d× the camera (0 = locked UI, 1 = scene plane, 1.3 = foreground).
   * cam: {x, y, zoom, rot}. Zoom is applied around frame centre.
   */
  MM.camera = function (sceneEl, cam) {
    const { x = 0, y = 0, zoom = 1, rot = 0 } = cam;
    for (const L of sceneEl.querySelectorAll('[data-depth]')) {
      const d = parseFloat(L.dataset.depth);
      const z = 1 + (zoom - 1) * d;
      set(L, { x: -x * d, y: -y * d, rot: rot * d, scale: z, origin: '50% 50%' });
    }
  };
  // a slow "breathing" handheld drift — subtle by design (amplitude in px)
  MM.handheld = (seed, t, amp = 6, speed = 0.3) => ({
    x: MM.drift(seed, t, speed) * amp,
    y: MM.drift(seed + 3, t, speed) * amp,
    rot: MM.drift(seed + 7, t, speed * 0.7) * amp * 0.03,
  });

  /* ---------- motion blur from velocity ----------
   * Give it the position function and t; returns [bx, by] px for set({mb}).
   * shutter 0.5 = 180° shutter (film standard). fps = render fps.
   */
  MM.blurFrom = function (fx, fy, t, { fps = 60, shutter = 0.5, max = 60, k = 0.45 } = {}) {
    const vx = fx ? MM.vel(fx, t) : 0;
    const vy = fy ? MM.vel(fy, t) : 0;
    const per = shutter / fps;
    return [clamp(vx * per * k, -max, max), clamp(vy * per * k, -max, max)];
  };

  /* ---------- footage: image-sequence playback with speed ramps ----------
   * Pre-extract clips: ffmpeg -i clip.mp4 -vf fps=60,scale=1080:-2 clips/name/%05d.jpg
   * MM.footage(imgEl, {dir:'clips/name', fps:60, frames:N, ext:'jpg'}, srcTime)
   * Returns a promise; render() must `return MM.flush()` so the renderer waits for decode.
   */
  const pending = [];
  MM.footage = function (img, clip, srcT) {
    const n = clamp(Math.floor(srcT * clip.fps) + 1, 1, clip.frames);
    const src = `${clip.dir}/${String(n).padStart(5, '0')}.${clip.ext || 'jpg'}`;
    if (img.__src !== src) {
      img.__src = src;
      img.src = src;
      pending.push(img.decode().catch(() => {}));
    }
  };
  MM.flush = function () { const p = Promise.all(pending.splice(0)); return p; };

  /* ---------- word timeline (from transcribe + align) ----------
   * MM.loadTimeline(json) — {words:[{w,s,e}], lines:[{text,s,e}], markers:{name:t}}
   * MM.at('motion')      → start time of first occurrence of that word
   * MM.at('motion', 2)   → second occurrence
   * MM.at('#hook')       → a named marker
   */
  MM.TL = { words: [], lines: [], markers: {} };
  MM.loadTimeline = (tl) => { MM.TL = Object.assign({ words: [], lines: [], markers: {} }, tl); return MM.TL; };
  const norm = (s) => s.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
  MM.at = function (key, nth = 1, which = 's') {
    if (key[0] === '#') return MM.TL.markers[key.slice(1)];
    const k = norm(key);
    let c = 0;
    for (const w of MM.TL.words) if (norm(w.w) === k && ++c === nth) return w[which];
    console.warn('[mm] word not found:', key, nth);
    return NaN;
  };
  MM.endOf = (key, nth = 1) => MM.at(key, nth, 'e');

  /* ---------- sound cues (declared once, exported for the mixer) ----------
   * MM.cue(t, 'whoosh', {gain:-6}) — types: whoosh pop swish click boom riser shimmer tick hit
   */
  MM.cues = [];
  MM.cue = (t, type, opt = {}) => { if (isFinite(t)) MM.cues.push(Object.assign({ t: +t.toFixed(3), type }, opt)); };
  root.getCues = () => MM.cues.slice().sort((a, b) => a.t - b.t);

  /* ---------- grain (fixed or per-frame seeded) ---------- */
  MM.grain = function (canvas, frameSeed = 0, alpha = 22) {
    const ctx = canvas.getContext('2d');
    const { width: w, height: h } = canvas;
    const img = ctx.createImageData(w, h);
    let s = 1234567 + frameSeed * 7919;
    for (let i = 0; i < img.data.length; i += 4) {
      s = (s * 16807) % 2147483647;
      const v = (s & 255);
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
      img.data[i + 3] = alpha;
    }
    ctx.putImageData(img, 0, 0);
  };

  /* ---------- QC probe ----------
   * Called by the renderer at sample times. Flags:
   *  - text outside the frame or outside the safe area
   *  - two visible text blocks overlapping
   * Mark text blocks with class "qc" (or data-qc). Safe area set by MM.SAFE.
   */
  MM.SAFE = { top: 200, bottom: 1700, left: 60, right: 1020, W: 1080, H: 1920, tol: 12 };
  function visibleOpacity(el) {
    let o = 1;
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden') return 0;
      o *= parseFloat(cs.opacity);
      // still in motion (blurred) → not a settled layout, skip
      const m = /blur\(([\d.]+)px\)/.exec(cs.filter);
      if (m && parseFloat(m[1]) > 1) return 0;
    }
    return o;
  }
  // bounds of the actual glyphs, not the (possibly full-width) box
  function inkRect(el) {
    // split text: only count words whose inner span is actually visible inside its mask
    const masks = el.querySelectorAll('.mm-m');
    if (masks.length) {
      let L = 1e9, T = 1e9, R = -1e9, B = -1e9, any = false;
      for (const m of masks) {
        const i = m.firstElementChild; if (!i) continue;
        const a = m.getBoundingClientRect(), b = i.getBoundingClientRect();
        const iy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (iy < a.height * 0.5 || parseFloat(getComputedStyle(i).opacity) < 0.5) continue;
        any = true; L = Math.min(L, a.left); T = Math.min(T, a.top); R = Math.max(R, a.right); B = Math.max(B, a.bottom);
      }
      return any ? { left: L, top: T, right: R, bottom: B, width: R - L, height: B - T } : { left: 0, top: 0, right: 0, bottom: 0, width: 0, height: 0 };
    }
    const r = document.createRange();
    r.selectNodeContents(el);
    const b = r.getBoundingClientRect();
    return b.width > 0 ? b : el.getBoundingClientRect();
  }
  MM.qcProbe = function (t) {
    const S = MM.SAFE, issues = [];
    const boxes = [];
    if (MM.txActive) return issues; // layout is judged on settled frames, not mid-transition
    for (const el of document.querySelectorAll('.qc,[data-qc]')) {
      if (visibleOpacity(el) < 0.6) continue;
      const r = inkRect(el);
      if (r.width < 2 || r.height < 2) continue;
      const name = el.dataset.qc || (el.textContent || '').trim().slice(0, 28);
      if (r.left < -1 || r.right > S.W + 1 || r.top < -1 || r.bottom > S.H + 1)
        issues.push({ t, kind: 'OFF-FRAME', name, box: [r.left, r.top, r.right, r.bottom].map(Math.round) });
      else if (!el.hasAttribute('data-qc-nosafe') && (r.left < S.left - S.tol || r.right > S.right + S.tol || r.top < S.top - S.tol || r.bottom > S.bottom + S.tol))
        issues.push({ t, kind: 'UNSAFE', name, box: [r.left, r.top, r.right, r.bottom].map(Math.round) });
      boxes.push({ name, r, el });
    }
    for (let i = 0; i < boxes.length; i++)
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i], b = boxes[j];
        if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
        const ix = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
        const iy = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
        // tight leading is deliberate: only flag when glyph boxes overlap > 45% of the smaller height
        if (ix > 8 && iy > 0.45 * Math.min(a.r.height, b.r.height)) issues.push({ t, kind: 'OVERLAP', name: `${a.name} × ${b.name}` });
      }
    return issues;
  };
})(typeof window !== 'undefined' ? window : globalThis);
