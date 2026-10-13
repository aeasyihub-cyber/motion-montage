/* motion-montage · text.js
 * Kinetic typography primitives. Split once at setup, animate every frame.
 * Every function is pure in t: call it every frame with the same arguments.
 */
(function (root) {
  const MM = root.MM;
  const { clamp, mix, prog, ease, set, spring } = MM;
  const T = (MM.text = {});

  /* ---------- split ----------
   * MM.text.split(el, 'words'|'chars') → array of inner spans, each inside an overflow mask.
   * Keeps highlight spans (<span class="hl">) intact as single units.
   * For RTL/Arabic ALWAYS split by words, never chars (letters must stay joined).
   */
  T.split = function (el, mode = 'words', { mask = true } = {}) {
    if (el.__split) return el.__split;
    const out = [];
    const wrap = (node) => {
      const outer = document.createElement('span');
      outer.className = 'mm-m';
      outer.style.display = 'inline-block';
      outer.style.verticalAlign = 'top';
      if (mask) { outer.style.overflow = 'hidden'; outer.style.paddingBottom = '0.12em'; outer.style.marginBottom = '-0.12em'; }
      const inner = document.createElement('span');
      inner.className = 'mm-i';
      inner.style.display = 'inline-block';
      inner.style.willChange = 'transform';
      outer.appendChild(inner);
      return [outer, inner];
    };
    const walk = (node, parent) => {
      for (const ch of Array.from(node.childNodes)) {
        if (ch.nodeType === 3) {
          const parts = ch.textContent.split(/(\s+)/);
          const frag = document.createDocumentFragment();
          for (const part of parts) {
            if (!part) continue;
            if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); continue; }
            if (mode === 'chars') {
              const word = document.createElement('span');
              word.style.display = 'inline-block'; word.style.whiteSpace = 'nowrap';
              for (const c of Array.from(part)) {
                const [o, i] = wrap(); i.textContent = c; word.appendChild(o); out.push(i);
              }
              frag.appendChild(word);
            } else {
              const [o, i] = wrap(); i.textContent = part; frag.appendChild(o); out.push(i);
            }
          }
          ch.replaceWith(frag);
        } else if (ch.nodeType === 1) {
          if (ch.matches('.hl,.keep,[data-keep]')) {
            const [o, i] = wrap(); ch.replaceWith(o); i.appendChild(ch); out.push(i);
          } else walk(ch, ch);
        }
      }
    };
    walk(el, el);
    el.__split = out;
    return out;
  };

  /* ---------- rise: the editor's line/word reveal (masked) ----------
   * items rise from `from`% of their height to 0, staggered.
   * opts: each, dur, from (110), ease, blur (px at start), rot (deg at start)
   */
  T.rise = function (items, t, start, o = {}) {
    const { each = 0.06, dur = 0.5, from = 110, e = ease.snap, blur = 0, rot = 0, order = 'start' } = o;
    const n = items.length;
    items.forEach((it, i) => {
      const p = prog(t, start + MM.stagger(i, n, each, order), dur, e);
      set(it, { yp: (1 - p) * from, rot: (1 - p) * rot, blur: (1 - p) * blur, opacity: p > 0 ? 1 : 0 });
    });
  };

  /* ---------- exit: leave upward, accelerating, with blur ---------- */
  T.exit = function (items, t, start, o = {}) {
    const { each = 0.03, dur = 0.3, to = -110, e = ease.exit, blur = 6 } = o;
    const n = items.length;
    items.forEach((it, i) => {
      const p = prog(t, start + MM.stagger(i, n, each), dur, e);
      if (p <= 0) return;
      set(it, { yp: p * to, blur: p * blur, opacity: 1 - p * 0.6 });
    });
  };

  /* ---------- pop: words scale in on a spring (for punchy hooks) ---------- */
  T.pop = function (items, t, start, o = {}) {
    const { each = 0.07, sp = spring.pop, from = 0.4, times = null } = o;
    items.forEach((it, i) => {
      const t0 = times ? times[i] : start + i * each;
      const lt = t - t0;
      const s = lt <= 0 ? 0 : sp(lt);
      set(it, { scale: lt <= 0 ? from : mix(from, 1, s), opacity: lt <= 0 ? 0 : clamp(lt / 0.06), origin: '50% 80%' });
    });
  };

  /* ---------- onWords: reveal each word EXACTLY when it is spoken ----------
   * times = array of start times (from MM.at). Style: 'rise' | 'pop' | 'fade'
   */
  T.onWords = function (items, t, times, style = 'rise', o = {}) {
    items.forEach((it, i) => {
      const t0 = times[i] ?? times[times.length - 1];
      if (style === 'pop') {
        const lt = t - t0;
        set(it, { scale: lt <= 0 ? 0.5 : mix(0.5, 1, spring.pop(lt)), opacity: lt <= 0 ? 0 : clamp(lt / 0.05), origin: '50% 85%' });
      } else if (style === 'fade') {
        const p = prog(t, t0, 0.18, ease.outCubic);
        set(it, { opacity: mix(o.dim ?? 0, 1, p), y: (1 - p) * 10 });
      } else {
        const p = prog(t, t0 - 0.04, o.dur ?? 0.36, ease.snap);
        set(it, { yp: (1 - p) * 105, opacity: p > 0 ? 1 : 0 });
      }
    });
  };

  /* ---------- track: letter-spacing collapse (luxury / cinematic titles) ---------- */
  T.track = function (el, t, start, o = {}) {
    const { dur = 1.2, from = 0.6, to = 0.02, blur = 10, e = ease.snap } = o;
    const p = prog(t, start, dur, e);
    el.style.letterSpacing = mix(from, to, p).toFixed(4) + 'em';
    set(el, { blur: (1 - p) * blur, opacity: clamp(p * 1.6) });
  };

  /* ---------- cascade: per-character drop with rotation (Latin only) ---------- */
  T.cascade = function (chars, t, start, o = {}) {
    const { each = 0.025, dur = 0.55, dist = 120, rot = 12, sp = null, order = 'start' } = o;
    const n = chars.length;
    chars.forEach((c, i) => {
      const t0 = start + MM.stagger(i, n, each, order);
      const p = sp ? (t < t0 ? 0 : sp(t - t0)) : prog(t, t0, dur, ease.snap);
      set(c, { yp: (1 - p) * dist, rot: (1 - p) * rot, opacity: p > 0 ? 1 : 0 });
    });
  };

  /* ---------- weight: variable-font weight morph (needs a variable font) ---------- */
  T.weight = function (el, t, keys) {
    el.style.fontVariationSettings = `"wght" ${MM.kf(t, keys).toFixed(1)}`;
  };

  /* ---------- highlight: marker block behind ONE word ----------
   * markup: <span class="hl"><i class="hl-bg"></i>word</span>
   * dir: 'ltr' grows from left, 'rtl' from right (Arabic).
   */
  T.highlight = function (hlEl, t, start, o = {}) {
    const { dur = 0.32, dir = 'ltr', e = ease.inOutQuart, out = null } = o;
    const bg = hlEl.querySelector('.hl-bg');
    let p = prog(t, start, dur, e);
    let origin = dir === 'rtl' ? '100% 50%' : '0% 50%';
    if (out != null && t > out) { p = 1 - prog(t, out, dur * 0.8, ease.inOutQuart); origin = dir === 'rtl' ? '0% 50%' : '100% 50%'; }
    set(bg, { sx: p, sy: 1, origin });
    hlEl.classList.toggle('on', p > 0.5);
  };

  /* ---------- strike: a line drawn through a word, then the word dims ---------- */
  T.strike = function (wordEl, t, start, o = {}) {
    const { dur = 0.28, dir = 'ltr', dimTo = 0.45 } = o;
    const line = wordEl.querySelector('.strike');
    const p = prog(t, start, dur, ease.inOutCubic);
    set(line, { sx: p, sy: 1, origin: dir === 'rtl' ? '100% 50%' : '0% 50%' });
    const d = prog(t, start + dur * 0.6, 0.25, ease.outCubic);
    wordEl.style.opacity = mix(1, dimTo, d).toFixed(3);
  };

  /* ---------- underline draw ---------- */
  T.underline = (lineEl, t, start, o = {}) => T.strike(lineEl.parentElement, t, start, Object.assign({ dimTo: 1 }, o));

  /* ---------- counter: numbers roll to a value ---------- */
  T.count = function (el, t, start, dur, from, to, fmt = (v) => Math.round(v).toLocaleString('en-US')) {
    el.textContent = fmt(mix(from, to, prog(t, start, dur, ease.outExpo)));
  };

  /* ---------- type: typewriter for prompt boxes / documents only ---------- */
  T.type = function (el, full, t, start, cps = 28, cursor = null) {
    const n = clamp(Math.floor((t - start) * cps), 0, full.length);
    el.textContent = full.slice(0, n);
    if (cursor) cursor.style.opacity = (n < full.length || Math.floor(t * 2.2) % 2 === 0) ? 1 : 0;
    return n;
  };

  /* ---------- fit: size text so a line fills an exact width (fill the frame!) ----------
   * Call in setup AFTER fonts load. el must be display:inline-block or have white-space:nowrap.
   */
  T.fit = function (el, width, { max = 600, min = 20 } = {}) {
    el.style.whiteSpace = 'nowrap';
    el.style.display = 'inline-block';
    let size = 100;
    el.style.fontSize = size + 'px';
    const w = el.getBoundingClientRect().width || 1;
    size = clamp((size * width) / w, min, max);
    el.style.fontSize = size.toFixed(2) + 'px';
    return size;
  };

  /* ---------- captions: sentence block + active word, driven by the timeline ----------
   * MM.text.captions(boxEl, t, {keyWords:Set, hideWhen:(t)=>bool, rtl:false})
   * Rebuilds DOM only when the line changes. Active word gets .on, emphasised words .key
   * Rule: hide captions while the same words are already big on screen (no duplicates).
   */
  T.captions = function (box, t, o = {}) {
    const TL = MM.TL;
    const li = TL.lines.findIndex((L, i) => L.s != null && t >= L.s - 0.05 && (i === TL.lines.length - 1 || t < (TL.lines[i + 1].s ?? 1e9) - 0.05));
    const hide = li < 0 || (o.hideWhen && o.hideWhen(t, li));
    if (box.__li !== li) {
      box.__li = li;
      box.innerHTML = '';
      if (li >= 0) {
        for (const w of TL.words.filter((w) => w.line === li)) {
          const s = document.createElement('span');
          s.className = 'cw' + (w.emph ? ' key' : '');
          s.textContent = w.w;
          s.__w = w;
          box.appendChild(s);
          box.appendChild(document.createTextNode(' '));
        }
      }
    }
    if (li < 0) { set(box, { opacity: 0 }); return; }
    const L = TL.lines[li];
    const p = prog(t, L.s - 0.05, 0.18, ease.outCubic);
    set(box, { opacity: hide ? 0 : p, y: (1 - p) * 16 });
    for (const s of box.children) {
      const w = s.__w;
      s.classList.toggle('said', t >= w.s);
      s.classList.toggle('on', t >= w.s && t < w.e + 0.08);
      if (s.classList.contains('key')) {
        const k = t - w.s;
        set(s, { scale: k < 0 ? 1 : 1 + 0.12 * Math.sin(clamp(k / 0.18) * Math.PI) });
      }
    }
  };

  /* ---------- swap: replace word A with word B in place (vertical roll) ---------- */
  T.swap = function (aEl, bEl, t, at, o = {}) {
    const { dur = 0.4, e = ease.whip } = o;
    const p = prog(t, at, dur, e);
    set(aEl, { yp: -p * 110, blur: Math.sin(p * Math.PI) * 4 });
    set(bEl, { yp: (1 - p) * 110, blur: Math.sin(p * Math.PI) * 4 });
  };
})(typeof window !== 'undefined' ? window : globalThis);
