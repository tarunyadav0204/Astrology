import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import sharp from '../../astroroshni_mobile/node_modules/sharp/lib/index.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const work = path.join(here, 'build');
const output = path.join(here, 'astroroshni-business-reading-demo.mp4');
const ffmpeg = '/private/tmp/astroroshni-video-prototype/node_modules/ffmpeg-static/ffmpeg';

fs.mkdirSync(work, { recursive: true });

const scenes = [
  {
    eyebrow: 'A QUESTION WITH WEIGHT',
    title: ['Can I build', 'an astrology', 'business?'],
    body: 'A personal reading, transformed into an AstroRoshni Story.',
    kind: 'question',
  },
  {
    eyebrow: 'THE SHORT ANSWER',
    title: ['Yes — with', 'structure.'],
    body: 'The potential is real. The outcome depends on how clearly you shape it.',
    kind: 'answer',
  },
  {
    eyebrow: 'YOUR NATURAL EDGE',
    title: ['Insight.', 'Communication.', 'Trust.'],
    body: 'Your advantage is translating complex patterns into guidance people can use.',
    kind: 'pillars',
  },
  {
    eyebrow: 'THE CHART EVIDENCE',
    title: ['Voice becomes', 'value.'],
    body: 'The 2nd house speaks to voice and resources. The 10th brings the focus to vocation and reputation.',
    kind: 'chart',
  },
  {
    eyebrow: 'THE REAL TEST',
    title: ['Potential is not', 'a business model.'],
    body: 'Consistent delivery and calm daily operations will matter more than quick expansion.',
    kind: 'tension',
  },
  {
    eyebrow: 'YOUR PATH FORWARD',
    title: ['Focus.', 'Prove.', 'Grow.'],
    body: 'Begin with one clear promise. Build proof through outcomes. Expand what people return for.',
    kind: 'timeline',
  },
  {
    eyebrow: 'YOUR CHART. YOUR CHOICES.',
    title: ['Make your way', 'of seeing', 'useful.'],
    body: 'See the pattern. Choose the path.',
    kind: 'final',
  },
];

const escapeXml = (value) => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;');

function wrapWords(value, maxChars = 48) {
  const lines = [];
  let current = '';
  for (const word of String(value).split(/\s+/)) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

function stars(seed) {
  let x = seed >>> 0;
  const random = () => {
    x = (1664525 * x + 1013904223) >>> 0;
    return x / 4294967296;
  };
  return Array.from({ length: 72 }, () => {
    const cx = Math.round(random() * 1080);
    const cy = Math.round(random() * 1920);
    const r = (0.7 + random() * 2.2).toFixed(1);
    const opacity = (0.16 + random() * 0.55).toFixed(2);
    return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="#ffe8bd" opacity="${opacity}"/>`;
  }).join('');
}

function chartArt() {
  return `
    <g transform="translate(540 540)" opacity=".92">
      <circle r="250" fill="none" stroke="url(#gold)" stroke-width="3"/>
      <circle r="205" fill="#2b1045" fill-opacity=".3" stroke="#f8cb79" stroke-opacity=".42" stroke-width="2"/>
      <path d="M0-205 L205 0 L0 205 L-205 0 Z M0-205 L0 205 M-205 0 L205 0 M-102.5-102.5 L102.5 102.5 M102.5-102.5 L-102.5 102.5" fill="none" stroke="#f8d89b" stroke-width="2.5" stroke-opacity=".75"/>
      <circle cx="-155" cy="-65" r="24" fill="#ffca72"/><circle cx="-155" cy="-65" r="8" fill="#fff4d0"/>
      <circle cx="138" cy="74" r="19" fill="#f47948"/><circle cx="138" cy="74" r="6" fill="#ffe2b1"/>
      <circle cx="58" cy="-146" r="14" fill="#e7c8ff"/>
      <text x="-155" y="-112" text-anchor="middle" class="mini">2ND HOUSE</text>
      <text x="138" y="122" text-anchor="middle" class="mini">10TH HOUSE</text>
    </g>`;
}

function decorativeArt(kind) {
  if (kind === 'chart') return chartArt();
  if (kind === 'pillars') return `
    <g transform="translate(110 470)">
      ${['INSIGHT', 'VOICE', 'TRUST'].map((label, i) => `
        <g transform="translate(${i * 292} 0)">
          <circle cx="115" cy="115" r="94" fill="#fff7eb" fill-opacity=".08" stroke="#ffd489" stroke-opacity=".64" stroke-width="2"/>
          <circle cx="115" cy="115" r="58" fill="#ffb05d" fill-opacity=".13"/>
          <text x="115" y="125" text-anchor="middle" class="pill">${label}</text>
        </g>`).join('')}
      <path d="M230 115 H292 M522 115 H584" stroke="#ffd489" stroke-width="2" stroke-dasharray="8 12" opacity=".62"/>
    </g>`;
  if (kind === 'timeline') return `
    <g transform="translate(120 520)">
      <path d="M70 100 H770" stroke="#f6cb80" stroke-width="4" opacity=".5"/>
      ${['FOCUS', 'PROVE', 'GROW'].map((label, i) => `
        <g transform="translate(${i * 350} 0)">
          <circle cx="70" cy="100" r="43" fill="#46165f" stroke="#ffd58d" stroke-width="4"/>
          <circle cx="70" cy="100" r="12" fill="#ffad5b"/>
          <text x="70" y="183" text-anchor="middle" class="step">${label}</text>
          <text x="70" y="222" text-anchor="middle" class="stepNo">0${i + 1}</text>
        </g>`).join('')}
    </g>`;
  if (kind === 'tension') return `
    <g transform="translate(540 585)">
      <circle r="205" fill="#2c0d42" fill-opacity=".28" stroke="#ffc877" stroke-opacity=".42" stroke-width="2"/>
      <path d="M0-145 L0 145 M-145 0 L145 0" stroke="#ffd79a" stroke-opacity=".68" stroke-width="3"/>
      <text x="-78" y="-25" text-anchor="middle" class="scale">VISION</text>
      <text x="78" y="35" text-anchor="middle" class="scale">SYSTEM</text>
      <circle cx="0" cy="0" r="22" fill="#ffb257"/>
    </g>`;
  return `
    <g transform="translate(540 525)">
      <circle r="210" fill="none" stroke="#ffd38a" stroke-opacity=".38" stroke-width="2"/>
      <circle r="145" fill="none" stroke="#ffd38a" stroke-opacity=".25" stroke-width="2"/>
      <ellipse rx="280" ry="95" fill="none" stroke="#ffb25c" stroke-opacity=".44" stroke-width="3" transform="rotate(-18)"/>
      <circle cx="-245" cy="72" r="22" fill="#ffbd68"/>
      <circle r="76" fill="url(#sun)"/>
      <path d="M-28 3 L-6 25 L36-26" fill="none" stroke="#fff7e8" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" opacity="${kind === 'answer' ? 1 : 0}"/>
    </g>`;
}

function makeSvg(scene, index) {
  const titleStart = scene.title.length === 3 ? 1015 : 1070;
  const titleSize = scene.title.some((line) => line.length > 16) ? 82 : 96;
  const title = scene.title.map((line, i) => `<text x="82" y="${titleStart + i * 108}" class="title" font-size="${titleSize}">${escapeXml(line)}</text>`).join('');
  const bodyStart = titleStart + scene.title.length * 108 + 48;
  const body = wrapWords(scene.body).map((line, i) => `<text x="82" y="${bodyStart + i * 48}" class="body">${escapeXml(line)}</text>`).join('');
  return `
  <svg width="1080" height="1920" viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2=".78" y2="1"><stop stop-color="#25083f"/><stop offset=".49" stop-color="#64205e"/><stop offset="1" stop-color="#ee7438"/></linearGradient>
      <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff0b7"/><stop offset=".5" stop-color="#f4b95f"/><stop offset="1" stop-color="#fff1c2"/></linearGradient>
      <radialGradient id="sun"><stop stop-color="#fff8da"/><stop offset=".3" stop-color="#ffd886"/><stop offset="1" stop-color="#f18445" stop-opacity=".15"/></radialGradient>
      <radialGradient id="glow"><stop stop-color="#ffbd68" stop-opacity=".38"/><stop offset="1" stop-color="#ff9850" stop-opacity="0"/></radialGradient>
      <filter id="blur"><feGaussianBlur stdDeviation="32"/></filter>
      <style>
        .brand { fill:#fff8ec; font: 700 31px Helvetica,Arial,sans-serif; letter-spacing:8px }
        .eyebrow { fill:#ffd897; font:700 24px Helvetica,Arial,sans-serif; letter-spacing:7px }
        .title { fill:#fffaf2; font-family:Georgia,'Times New Roman',serif; font-weight:500 }
        .body { fill:#f9e9df; font:400 33px Helvetica,Arial,sans-serif }
        .mini { fill:#ffe2ad; font:700 18px Helvetica,Arial,sans-serif; letter-spacing:3px }
        .pill { fill:#fff5e5; font:700 18px Helvetica,Arial,sans-serif; letter-spacing:2px }
        .step { fill:#fff6e8; font:700 22px Helvetica,Arial,sans-serif; letter-spacing:3px }
        .stepNo { fill:#ffc878; font:500 17px Helvetica,Arial,sans-serif; letter-spacing:3px }
        .scale { fill:#fff0df; font:700 19px Helvetica,Arial,sans-serif; letter-spacing:2px }
      </style>
    </defs>
    <rect width="1080" height="1920" fill="url(#bg)"/>
    <circle cx="1050" cy="90" r="410" fill="url(#glow)" filter="url(#blur)"/>
    <circle cx="80" cy="1810" r="430" fill="#ff9c51" opacity=".14" filter="url(#blur)"/>
    ${stars(9103 + index * 97)}
    <g opacity=".34"><path d="M760-30 A360 360 0 0 0 1110 330" fill="none" stroke="#ffd797" stroke-width="2"/><path d="M825-25 A285 285 0 0 0 1110 255" fill="none" stroke="#ffd797" stroke-width="2"/></g>
    <g transform="translate(80 74)"><circle cx="31" cy="31" r="31" fill="none" stroke="#ffd483" stroke-width="2"/><text x="31" y="42" text-anchor="middle" fill="#fff7e7" font-family="Helvetica" font-size="26" font-weight="800">AR</text><text x="85" y="42" class="brand">ASTROROSHNI</text></g>
    ${decorativeArt(scene.kind)}
    <text x="82" y="930" class="eyebrow">${escapeXml(scene.eyebrow)}</text>
    ${title}
    ${body}
    <line x1="82" y1="1780" x2="998" y2="1780" stroke="#ffe0a8" stroke-opacity=".34"/>
    <text x="82" y="1834" fill="#f7ddcf" font-family="Helvetica" font-size="22" letter-spacing="2">CONCEPT DEMO · BASED ON A SAMPLE CHAT ANSWER</text>
    <text x="998" y="1834" text-anchor="end" fill="#ffd18a" font-family="Helvetica" font-size="22">0${index + 1} / 07</text>
  </svg>`;
}

for (let i = 0; i < scenes.length; i += 1) {
  const svg = Buffer.from(makeSvg(scenes[i], i));
  await sharp(svg).png().toFile(path.join(work, `scene-${i}.png`));
}

const narration = `Can you build an astrology business? Your chart suggests genuine potential — but not because of one lucky placement. Your strength is the combination of insight, communication, and trust. The second house highlights voice and value. Your professional pattern rewards turning complex observations into guidance people can actually use. But potential is not a business model. Reputation, consistent delivery, and calm daily operations will matter more than quick expansion. Begin with one clear promise. Build proof through real outcomes. Then grow what people return for. Your chart does not ask you to imitate another astrologer. It asks you to make your way of seeing unmistakably useful. AstroRoshni. See the pattern. Choose the path.`;
const voiceAiff = path.join(work, 'narration.aiff');
if (!fs.existsSync(voiceAiff) || fs.statSync(voiceAiff).size < 5000) {
  execFileSync('/usr/bin/say', ['-v', 'Rishi', '-r', '164', '-o', voiceAiff, narration]);
}

const probe = execFileSync('/usr/bin/afinfo', [voiceAiff], { encoding: 'utf8' });
const durationMatch = probe.match(/estimated duration:\s*([0-9.]+)\s*sec/i);
if (!durationMatch || Number(durationMatch[1]) <= 0) {
  throw new Error('Narration could not be generated. Run the renderer with access to the macOS speech service.');
}
const narrationDuration = Number(durationMatch[1]);
const totalDuration = narrationDuration + 1.8;
const sceneDuration = totalDuration / scenes.length;
const fps = 30;

const args = ['-y'];
for (let i = 0; i < scenes.length; i += 1) {
  args.push('-loop', '1', '-t', String(sceneDuration + 0.15), '-i', path.join(work, `scene-${i}.png`));
}
args.push('-i', voiceAiff);
args.push('-f', 'lavfi', '-t', String(totalDuration), '-i', 'sine=frequency=110:sample_rate=48000');
args.push('-f', 'lavfi', '-t', String(totalDuration), '-i', 'sine=frequency=220:sample_rate=48000');

const filters = [];
for (let i = 0; i < scenes.length; i += 1) {
  const zoom = i % 2 === 0 ? `min(zoom+0.00035,1.045)` : `if(lte(zoom,1.0),1.045,max(1.0,zoom-0.00035))`;
  filters.push(`[${i}:v]scale=1140:2027,crop=1080:1920,zoompan=z='${zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${Math.ceil((sceneDuration + 0.15) * fps)}:s=1080x1920:fps=${fps},format=yuv420p[v${i}]`);
}
let previous = 'v0';
let elapsed = sceneDuration;
for (let i = 1; i < scenes.length; i += 1) {
  const out = `x${i}`;
  filters.push(`[${previous}][v${i}]xfade=transition=${i % 3 === 0 ? 'circleopen' : 'fade'}:duration=0.7:offset=${(elapsed - 0.7).toFixed(3)}[${out}]`);
  previous = out;
  elapsed += sceneDuration - 0.7;
}
filters.push(`[${previous}]setsar=1,format=yuv420p[video]`);
const narrationInput = scenes.length;
const toneOne = scenes.length + 1;
const toneTwo = scenes.length + 2;
filters.push(`[${toneOne}:a]volume=0.018[t1]`);
filters.push(`[${toneTwo}:a]volume=0.010[t2]`);
filters.push(`[t1][t2]amix=inputs=2,afade=t=in:st=0:d=2,afade=t=out:st=${Math.max(0, totalDuration - 3).toFixed(2)}:d=3[bed]`);
filters.push(`[${narrationInput}:a]volume=1.0,adelay=650|650[voice]`);
filters.push(`[voice][bed]amix=inputs=2:duration=longest:weights='1 1'[audio]`);

args.push('-filter_complex', filters.join(';'));
args.push('-map', '[video]', '-map', '[audio]', '-t', String(totalDuration), '-r', String(fps), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', output);
execFileSync(ffmpeg, args, { stdio: 'inherit' });

console.log(`Rendered ${output}`);
