import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const readJson = (name, fallback) => {
  const target = path.join(here, name);
  return fs.existsSync(target) ? JSON.parse(fs.readFileSync(target, 'utf8')) : fallback;
};

const fallbackScenes = [
  {start:0,end:8,type:'opening',headline:'One chapter is closing.',supporting:'But your career story is not standing still.',houses:[],planets:[],dates:[]},
  {start:8,end:23,type:'natal_chart',headline:'The transition is visible.',supporting:'Mercury connects endings with profession.',houses:[10,12],planets:['Mercury'],dates:[]},
  {start:23,end:38,type:'house_focus',headline:'Visibility needs attention.',supporting:'Strong work can still go unseen during this cycle.',houses:[10],planets:['Mercury','Sun'],dates:[]},
  {start:38,end:52,type:'planet_focus',headline:'Protect your inner rhythm.',supporting:'The Moon carries both career direction and emotional load.',houses:[6,10],planets:['Moon'],dates:[]},
  {start:52,end:68,type:'dasha_timeline',headline:'The larger promise remains.',supporting:'Work with the active period instead of fighting it.',houses:[],planets:['Venus','Mercury'],dates:['NOW','OCT 2027','DEC 2028']},
  {start:68,end:82,type:'remedy',headline:'Shift from labour to visibility.',supporting:'Clear the old role, strengthen visibility, enter strategically.',houses:[],planets:[],dates:[]},
  {start:82,end:90,type:'closing',headline:'Your next role needs to see you.',supporting:'Close cleanly. Reposition deliberately.',houses:[],planets:[],dates:[]},
];

const transcript = readJson('transcript.json', {});
const chart = readJson('chart-data.json', {planets:[]});
const durationSeconds = 90;
const scenes = (transcript.scenes || fallbackScenes)
  .filter((scene) => Number(scene.start || 0) < durationSeconds)
  .map((scene, index, all) => ({
    ...scene,
    start: Math.max(0, Number(scene.start || 0)),
    end: Math.min(durationSeconds, Number(scene.end || all[index + 1]?.start || durationSeconds)),
  }));
const turns = (transcript.turns || []).filter((turn) => Number(turn.start || 0) < durationSeconds);
const inputProps = {
  durationSeconds,
  scenes,
  turns,
  chart,
  episodeTitle: transcript.title || 'Your Career Transition',
};

const serveUrl = await bundle({entryPoint:path.join(here,'src','index.jsx'),webpackOverride:(config)=>config});
const composition = await selectComposition({serveUrl,id:'AstroRoshniVisualPodcast',inputProps});
const output = path.join(here,'astroroshni-visual-podcast-proof.mp4');
await renderMedia({
  composition,
  serveUrl,
  codec:'h264',
  outputLocation:output,
  inputProps,
  crf:18,
  pixelFormat:'yuv420p',
  audioBitrate:'192k',
  chromiumOptions:{enableMultiProcessOnLinux:true},
});
console.log(output);
