# Engine API (`engine/lib/*.js`)

Classic scripts load in this order: `motion.js`, `stage.js`, `text.js`, `transitions.js`. Everything is on `window.MM`.
**Determinism contract:** no CSS animations or transitions, no `setTimeout`/`requestAnimationFrame`, no `Math.random()` and no `Date`.
`render(t)` must give the same frame for the same `t`, in any order (the renderer jumps around in parallel).

## Composition contract
```js
window.COMP = { W:1080, H:1920, fps:60, duration:16 };
window.setup = async () => { /* fit + split text, build DOM, MM.cue(...) */ };
window.render = (t) => { MM.edit(t, S, CUTS); /* scenes */ return MM.flush(); };
```
Structure: `#frame > section.scene > .layer[data-depth] > content`. Transitions act on `.scene`, the camera on `.layer`.

## motion.js: maths
| API | What |
|---|---|
| `ease.{snap, glide, whip, exit, emphasized, anticipate, outExpo, outQuart, inOutCubic, outBack(t,s)…}` | easing functions |
| `bezier(x1,y1,x2,y2)` | custom curve, with the same maths as CSS and AE |
| `spring({stiffness,damping,mass})(t)` · `spring.pop/land/soft` | closed-form damped spring |
| `prog(t,start,dur,ease)` | eased 0..1 |
| `inOut(t,start,end,inDur,outDur)` | `{in,out,v}` envelope |
| `kf(t,[[time,value,easeIn],…])` | keyframes (numbers or arrays) |
| `stagger(i,n,each,from)` | `from`: start / end / center / edges / random |
| `drift(seed,t,speed)` · `noise(seed,t)` | seeded smooth noise |
| `vel(f,t)` | derivative of any f(t) |
| `ramp(t,[[outT,srcT],…])` | time remap for speed ramps |

## stage.js: DOM
| API | What |
|---|---|
| `set(el,{x,y,xp,yp,scale,sx,sy,rot,rx,ry,persp,opacity,blur,mb:[x,y],bright,sat,clip,origin,z,vis})` | the only style writer you need (cached) |
| `scene(el,t,start,end)` | manual visibility (MM.edit already does this) |
| `camera(sceneEl,{x,y,zoom,rot})` | moves `[data-depth]` layers, with parallax = depth |
| `handheld(seed,t,amp,speed)` | subtle drift for `camera()` |
| `blurFrom(fx,fy,t,{shutter,k})` | velocity → `mb` directional blur |
| `footage(img,{dir,fps,frames,ext},srcT)` + `return MM.flush()` | image-sequence playback |
| `loadTimeline(tl)` · `at(word,nth)` · `endOf(word,nth)` · `at('#marker')` | the voice clock |
| `cue(t,type,{gain,pitch,dur})` · `getCues()` | sound cues for `sound.py sfx` |
| `grain(canvas,seed,alpha)` | static film grain |
| `SAFE` · `qcProbe(t)` | safe area + layout probe. Tag text blocks `.qc` or `data-qc="name"` |

## text.js: type
`split(el,'words'|'chars')`, `fit(el,width)`, `rise`, `exit`, `pop`, `onWords`, `track`, `cascade`, `weight`,
`highlight(hl,t,start,{dir})`, `strike(word,t,start)`, `underline`, `count`, `type`, `swap`, `captions(box,t,{hideWhen})`.
Markup helpers: `<span class="hl"><i class="hl-bg"></i>word</span>` and `<span style="position:relative;display:inline-block">word<i class="strike"></i></span>`.

## transitions.js: the edit
`MM.edit(t, scenes, cuts)` with `scenes=[{el,start,end}]` and `cuts=[{type,dur,at?,…}]`.
Types: `cut, panel, wipe, push, whip, zoom, iris, slats, sweep, stack, dissolve, dip` (see `transitions.md`).
Add your own: `MM.TX.myType = (p, A, B, opts, {t,at,dur}) => { set(A,{…}); set(B,{…, z:2}); }`.

## render.mjs
`--comp --out --fps --workers --shutter --stills a,b --every s --qc --from --to --quality --crf`.
Set `MM_CHROMIUM=/path/to/chrome` to use a system Chromium.

## Performance
- Speed at 1080×1920: about 3 frames/s per core. A 30 s film at 60 fps with `--shutter 2` is about 3,600 captures, so roughly 10 min on 2 cores or 3 min on 8.
- Use `--from/--to` to re-render a fixed section, and `--stills` for iteration. Only do full renders at gates.
- Keep the DOM light: hide scenes outside their window (`MM.edit` does), and avoid huge box-shadows on moving elements.
