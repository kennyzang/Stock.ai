// Render a code-drawn page (window.render(t), window.DUR, window.READY) to PNG stills or an MP4.
//   node render.mjs page.html still 1.5 out.png
//   node render.mjs page.html video out.mp4 [fps]
import { createRequire } from 'module';
import { spawn } from 'child_process';
import path from 'path';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');
const [page_, mode, a, b, c] = process.argv.slice(2);
const W = 1080, H = 1920;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(2); });
await page.goto('file://' + path.resolve(page_));
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
const shot = async t => { await page.evaluate(t => window.render(t), t); return page.screenshot({ type: 'png' }); };
if (mode === 'still') {
  const fs = await import('fs');
  fs.writeFileSync(b, await shot(parseFloat(a)));
} else {
  const fps = parseInt(b || '30'), dur = await page.evaluate(() => window.DUR);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', '-movflags', '+faststart', a], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) { const buf = await page.evaluate(t => { window.render(t); return null; }, i / fps).then(() => page.screenshot({ type: 'jpeg', quality: 92 })); ff.stdin.write(buf); }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close();
