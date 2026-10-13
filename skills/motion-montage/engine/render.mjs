#!/usr/bin/env node
/* motion-montage · render.mjs
 * Deterministic frame renderer: HTML composition → frames → MP4 (silent) + cues.json
 *
 *  node render.mjs --comp project/composition.html --out project/out [options]
 *
 *  --fps 60            output frame rate
 *  --workers 4         parallel pages (≈ CPU cores)
 *  --shutter 1         >1 = true motion blur: renders N sub-frames per frame and blends them
 *                      (2 = cheap & good, 4 = film-like; costs N× render time)
 *  --stills 0.5,2.1    render only these times → stills/*.png + contact-sheet.png  (preview gate)
 *  --every 1.0         stills every N seconds (alternative to --stills)
 *  --qc                run the layout probe every 0.1 s → qc.json (off-frame / unsafe / overlap)
 *  --from 0 --to 12    render a range only (seconds)
 *  --quality 92        JPEG quality for frames
 *  --crf 16            x264 quality
 *
 * Composition contract (see templates/):
 *   window.COMP = { W:1080, H:1920, fps:60, duration:38.0 }
 *   window.setup?() async — runs once (split text, load timeline, declare cues)
 *   window.render(t)  — pure function of t (seconds). May return a Promise (footage decode).
 *   window.getCues?() — sound cues for the mixer
 */
import { chromium } from 'playwright';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => {
    if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
    return acc;
  }, [])
);
if (!args.comp) { console.error('usage: node render.mjs --comp composition.html --out outdir [--stills t1,t2 | --every 1] [--qc] [--shutter 2]'); process.exit(1); }

const comp = path.resolve(args.comp);
const out = path.resolve(args.out || path.join(path.dirname(comp), 'out'));
const workers = +(args.workers || 4);
const shutter = Math.max(1, +(args.shutter || 1));
const quality = +(args.quality || 92);
const crf = +(args.crf || 16);
fs.mkdirSync(out, { recursive: true });

const launchOpts = { args: ['--allow-file-access-from-files', '--font-render-hinting=none', '--force-color-profile=srgb'] };
if (process.env.MM_CHROMIUM) launchOpts.executablePath = process.env.MM_CHROMIUM;
const browser = await chromium.launch(launchOpts);

async function openPage() {
  const page = await browser.newPage();
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) console.log(`[page ${m.type()}]`, m.text()); });
  page.on('pageerror', (e) => console.log('[page error]', e.message));
  await page.goto(pathToFileURL(comp).href);
  const C = await page.evaluate(async () => {
    await document.fonts.ready;
    if (window.setup) await window.setup();
    await document.fonts.ready;
    return window.COMP;
  });
  await page.setViewportSize({ width: C.W, height: C.H });
  return { page, C };
}

const first = await openPage();
const C = first.C;
const fps = +(args.fps || C.fps || 60);
const t0 = +(args.from || 0);
const t1 = +(args.to || C.duration);

async function shoot(page, t, file, type = 'jpeg') {
  await page.evaluate(async (tt) => { await window.render(tt); }, t);
  await page.screenshot({ path: file, type, ...(type === 'jpeg' ? { quality } : {}) });
}

/* ---------- stills mode: the preview gate ---------- */
if (args.stills || args.every) {
  const times = args.stills
    ? String(args.stills).split(',').map(Number)
    : Array.from({ length: Math.floor((t1 - t0) / +args.every) + 1 }, (_, i) => +(t0 + i * +args.every).toFixed(2));
  const dir = path.join(out, 'stills'); fs.mkdirSync(dir, { recursive: true });
  const files = [];
  for (const t of times) {
    const f = path.join(dir, `t${t.toFixed(2).padStart(6, '0')}.png`);
    await shoot(first.page, t, f, 'png'); files.push({ t, f });
  }
  // contact sheet, built in the browser (no extra deps)
  const cols = Math.min(6, files.length), cw = 300, ch = Math.round(cw * C.H / C.W);
  const html = `<html><body style="margin:0;background:#0d0d0f;font:600 15px system-ui;color:#ddd">
    <div style="display:grid;grid-template-columns:repeat(${cols},${cw}px);gap:10px;padding:12px">
    ${files.map(({ t, f }) => `<div><img src="${pathToFileURL(f).href}" style="width:${cw}px;height:${ch}px;display:block;border-radius:6px">
    <div style="padding:4px 2px">${t.toFixed(2)}s</div></div>`).join('')}</div></body></html>`;
  const sheetHtml = path.join(dir, 'sheet.html'); fs.writeFileSync(sheetHtml, html);
  const sp = await browser.newPage();
  await sp.setViewportSize({ width: cols * (cw + 10) + 14, height: 400 });
  await sp.goto(pathToFileURL(sheetHtml).href); await sp.waitForTimeout(150);
  await sp.screenshot({ path: path.join(out, 'contact-sheet.png'), fullPage: true });
  console.log(`stills: ${files.length} → ${dir}\ncontact sheet → ${path.join(out, 'contact-sheet.png')}`);
  await browser.close(); process.exit(0);
}

/* ---------- QC probe ---------- */
if (args.qc) {
  const issues = [];
  for (let t = t0; t <= t1; t += 0.1) {
    await first.page.evaluate(async (tt) => { await window.render(tt); }, t);
    const r = await first.page.evaluate((tt) => (window.MM && MM.qcProbe ? MM.qcProbe(tt) : []), +t.toFixed(2));
    issues.push(...r);
  }
  // collapse consecutive identical issues into ranges
  const ranges = [];
  for (const i of issues) {
    const last = ranges.find((r) => r.kind === i.kind && r.name === i.name && Math.abs(r.to - i.t) < 0.11);
    if (last) last.to = i.t; else ranges.push({ kind: i.kind, name: i.name, from: i.t, to: i.t, box: i.box });
  }
  fs.writeFileSync(path.join(out, 'qc.json'), JSON.stringify(ranges, null, 2));
  console.log(ranges.length ? `QC: ${ranges.length} layout issue(s) → qc.json` : 'QC: layout clean ✓');
  for (const r of ranges) console.log(`  ${r.kind.padEnd(9)} ${r.from.toFixed(2)}–${r.to.toFixed(2)}s  ${r.name}`);
  await browser.close(); process.exit(0);
}

/* ---------- full render ---------- */
const frames = path.join(out, 'frames');
fs.rmSync(frames, { recursive: true, force: true }); fs.mkdirSync(frames, { recursive: true });
const sub = shutter;                          // sub-frames per output frame
const total = Math.round((t1 - t0) * fps) * sub;
const pages = [first];
for (let i = 1; i < workers; i++) pages.push(await openPage());
let done = 0; const started = Date.now();
await Promise.all(pages.map(async ({ page }, w) => {
  for (let k = w; k < total; k += workers) {
    // sub-frames spread across a 180° shutter (half the frame interval), centred on the frame time
    const fi = Math.floor(k / sub), si = k % sub;
    const off = sub > 1 ? ((si + 0.5) / sub - 0.5) * (0.5 / fps) : 0;
    const t = t0 + fi / fps + off;
    await shoot(page, Math.max(0, t), path.join(frames, `${String(k).padStart(6, '0')}.jpg`));
    if (++done % 120 === 0) {
      const el = (Date.now() - started) / 1000;
      process.stdout.write(`\r  ${done}/${total} frames  ${(done / el).toFixed(1)} fps  eta ${((total - done) / (done / el)).toFixed(0)}s   `);
    }
  }
}));
console.log(`\n  rendered ${total} frames in ${((Date.now() - started) / 1000).toFixed(1)}s`);

const cues = await first.page.evaluate(() => (window.getCues ? window.getCues() : []));
fs.writeFileSync(path.join(out, 'cues.json'), JSON.stringify({ fps, duration: t1 - t0, cues }, null, 2));
await browser.close();

const vf = sub > 1 ? `tmix=frames=${sub}:weights=${Array(sub).fill(1).join(' ')},framestep=${sub},` : '';
const enc = spawnSync('ffmpeg', ['-y', '-v', 'error', '-framerate', String(fps * sub), '-i', path.join(frames, '%06d.jpg'),
  '-vf', `${vf}format=yuv420p`, '-r', String(fps), '-c:v', 'libx264', '-preset', 'slow', '-crf', String(crf),
  '-movflags', '+faststart', path.join(out, 'video-silent.mp4')], { stdio: 'inherit' });
if (enc.status !== 0) process.exit(enc.status);
console.log(`video → ${path.join(out, 'video-silent.mp4')}\ncues  → ${path.join(out, 'cues.json')} (${cues.length})`);
