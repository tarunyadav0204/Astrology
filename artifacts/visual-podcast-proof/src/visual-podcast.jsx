import React, {useMemo} from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const GOLD = '#FFD78D';
const CREAM = '#FFF9EF';
const INK = '#26072F';
const HOUSE_CENTERS = {
  1: [540, 415], 2: [330, 318], 3: [205, 438], 4: [330, 635],
  5: [205, 835], 6: [330, 952], 7: [540, 850], 8: [750, 952],
  9: [875, 835], 10: [750, 635], 11: [875, 438], 12: [750, 318],
};
const PLANET_SHORT = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju', Venus: 'Ve',
  Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke', Uranus: 'Ur', Neptune: 'Ne', Pluto: 'Pl',
};

const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));

function Stars({frame}) {
  const stars = useMemo(() => Array.from({length: 92}, (_, index) => ({
    left: (index * 47.37) % 100,
    top: (index * 31.83) % 100,
    size: 1 + (index % 4),
    phase: (index * 13) % 90,
  })), []);
  return <AbsoluteFill>{stars.map((star, index) => {
    const opacity = 0.16 + 0.5 * ((Math.sin((frame + star.phase) / 19) + 1) / 2);
    return <div key={index} style={{position:'absolute',left:`${star.left}%`,top:`${star.top}%`,width:star.size,height:star.size,borderRadius:'50%',background:CREAM,opacity,boxShadow:`0 0 ${star.size * 4}px ${GOLD}`}} />;
  })}</AbsoluteFill>;
}

function AmbientWorld({frame}) {
  const rotate = frame * 0.035;
  return <AbsoluteFill style={{overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,background:'linear-gradient(155deg,#210634 0%,#511754 48%,#A53C53 72%,#F27B39 100%)'}} />
    <div style={{position:'absolute',width:900,height:900,right:-360,top:-300,borderRadius:'50%',background:'radial-gradient(circle,rgba(255,199,107,.26),rgba(255,130,69,.02) 62%,transparent 70%)',filter:'blur(10px)'}} />
    <div style={{position:'absolute',width:760,height:760,left:-390,bottom:-320,borderRadius:'50%',background:'radial-gradient(circle,rgba(251,138,62,.28),transparent 68%)',filter:'blur(18px)'}} />
    <Stars frame={frame} />
    <div style={{position:'absolute',width:980,height:420,left:50,top:250,border:`2px solid rgba(255,215,141,.24)`,borderRadius:'50%',transform:`rotate(${rotate}deg)`}} />
    <div style={{position:'absolute',width:1180,height:610,left:-50,top:130,border:`1px solid rgba(255,215,141,.15)`,borderRadius:'50%',transform:`rotate(${-18 + rotate * .45}deg)`}} />
  </AbsoluteFill>;
}

function Brand() {
  return <div style={{position:'absolute',top:82,left:72,right:72,display:'flex',alignItems:'center',zIndex:20}}>
    <div style={{width:54,height:54,borderRadius:'50%',border:`2px solid ${GOLD}`,display:'grid',placeItems:'center',fontFamily:'Arial',fontWeight:800,fontSize:20,color:CREAM}}>AR</div>
    <div style={{marginLeft:18,color:CREAM,fontFamily:'Arial',fontSize:20,fontWeight:800,letterSpacing:7}}>ASTROROSHNI</div>
    <div style={{marginLeft:'auto',padding:'10px 18px',borderRadius:28,background:'rgba(31,2,44,.38)',border:'1px solid rgba(255,215,141,.22)',color:'#FBEBDD',fontFamily:'Arial',fontSize:13,fontWeight:700,letterSpacing:2}}>VISUAL PODCAST</div>
  </div>;
}

function HostPresence({speaker, frame}) {
  const pulse = 1 + Math.sin(frame / 5) * 0.035;
  const host = (name, side, colors, active) => <div style={{position:'absolute',top:178,[side]:72,display:'flex',alignItems:'center',gap:14,opacity:active ? 1 : .38,transition:'opacity .2s'}}>
    {side === 'right' && <div style={{textAlign:'right'}}><div style={{fontFamily:'Arial',fontSize:17,fontWeight:800,color:CREAM,letterSpacing:2}}>{name}</div><div style={{fontFamily:'Arial',fontSize:11,color:GOLD,letterSpacing:2,marginTop:4}}>{active ? 'SPEAKING' : 'LISTENING'}</div></div>}
    <div style={{width:62,height:62,borderRadius:'50%',background:`radial-gradient(circle at 35% 30%,${colors[0]},${colors[1]} 45%,rgba(38,7,47,.2) 70%)`,boxShadow:active ? `0 0 45px ${colors[0]},0 0 90px ${colors[1]}` : 'none',transform:`scale(${active ? pulse : 1})`,border:'1px solid rgba(255,255,255,.38)'}} />
    {side === 'left' && <div><div style={{fontFamily:'Arial',fontSize:17,fontWeight:800,color:CREAM,letterSpacing:2}}>{name}</div><div style={{fontFamily:'Arial',fontSize:11,color:GOLD,letterSpacing:2,marginTop:4}}>{active ? 'SPEAKING' : 'LISTENING'}</div></div>}
  </div>;
  return <>{host('ANANYA','left',['#FFF1BF','#C74187'],speaker === 'ananya')}{host('ARJUN','right',['#DCCBFF','#5847C7'],speaker === 'arjun')}</>;
}

function NatalChart({chart, highlightedHouses = [], highlightedPlanets = [], reveal = 1, frame = 0}) {
  const ascSign = Math.floor(Number(chart?.ascendant || 0) / 30) + 1;
  const planetsByHouse = {};
  for (const planet of chart?.planets || []) {
    const house = Number(planet.house || 0);
    if (!planetsByHouse[house]) planetsByHouse[house] = [];
    planetsByHouse[house].push(planet);
  }
  const isHouseHot = (house) => highlightedHouses.map(Number).includes(house);
  const orbit = frame * .06;
  return <div style={{position:'relative',width:920,height:920,margin:'0 auto',filter:'drop-shadow(0 28px 60px rgba(24,0,35,.42))',opacity:reveal,transform:`scale(${.82 + reveal * .18})`}}>
    <svg viewBox="0 0 1080 1080" width="100%" height="100%">
      <defs><filter id="chartGlow"><feGaussianBlur stdDeviation="9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
      <rect x="110" y="110" width="860" height="860" rx="20" fill="rgba(38,7,47,.38)" stroke={GOLD} strokeWidth="3" opacity=".95" />
      <path d="M110 110 L970 970 M970 110 L110 970 M540 110 L970 540 L540 970 L110 540 Z" fill="none" stroke={GOLD} strokeWidth="2.6" opacity=".72" />
      {Object.entries(HOUSE_CENTERS).map(([houseRaw,[x,y]]) => {
        const house = Number(houseRaw);
        const hot = isHouseHot(house);
        const sign = ((ascSign + house - 2) % 12) + 1;
        return <g key={house} filter={hot ? 'url(#chartGlow)' : undefined}>
          {hot && <circle cx={x} cy={y} r="92" fill="rgba(255,172,82,.18)" stroke="#FFB15A" strokeWidth="3" />}
          <text x={x} y={y - 44} textAnchor="middle" fill={hot ? '#FFCF7D' : 'rgba(255,232,192,.52)'} fontFamily="Arial" fontSize="22" fontWeight="800">{sign}</text>
          {(planetsByHouse[house] || []).map((planet,index) => {
            const hotPlanet = highlightedPlanets.map(p => String(p).toLowerCase()).includes(String(planet.name).toLowerCase());
            return <text key={planet.name} x={x} y={y + index * 31 - 2} textAnchor="middle" fill={hotPlanet ? '#FFF7D9' : '#F8E6D6'} fontFamily="Arial" fontSize={hotPlanet ? 28 : 22} fontWeight={hotPlanet ? 900 : 600}>{PLANET_SHORT[planet.name] || String(planet.name).slice(0,2)}{planet.retrograde ? 'ᴿ' : ''}</text>;
          })}
        </g>;
      })}
      <circle cx="540" cy="540" r="28" fill="#FFB25B" opacity=".88" />
      <circle cx="540" cy="540" r="130" fill="none" stroke="rgba(255,215,141,.28)" strokeWidth="2" strokeDasharray="8 16" transform={`rotate(${orbit} 540 540)`} />
    </svg>
  </div>;
}

function Timeline({scene, progress}) {
  const dates = scene.dates?.length ? scene.dates : ['NOW','TRANSITION','NEXT CHAPTER'];
  return <div style={{width:900,margin:'70px auto 0'}}>
    <div style={{height:4,background:'rgba(255,215,141,.28)',position:'relative'}}>
      <div style={{height:'100%',width:`${clamp(progress) * 100}%`,background:`linear-gradient(90deg,${GOLD},#FF9451)`,boxShadow:`0 0 28px ${GOLD}`}} />
      {dates.slice(0,3).map((date,index) => <div key={date} style={{position:'absolute',left:`${index * 50}%`,top:-22,transform:'translateX(-50%)',width:220,textAlign:'center'}}>
        <div style={{width:46,height:46,borderRadius:'50%',background:index / 2 <= progress ? '#FFAE57' : '#4C1558',border:`3px solid ${GOLD}`,margin:'0 auto',boxShadow:index / 2 <= progress ? `0 0 35px ${GOLD}` : 'none'}} />
        <div style={{fontFamily:'Arial',fontSize:17,fontWeight:800,letterSpacing:2,color:CREAM,marginTop:22}}>{date}</div>
      </div>)}
    </div>
  </div>;
}

function RemedyPath({progress}) {
  const steps = ['CLEAR THE OLD','RESTORE VISIBILITY','ENTER STRATEGICALLY'];
  return <div style={{display:'flex',gap:20,width:940,margin:'55px auto 0'}}>{steps.map((step,index) => {
    const active = progress > index / steps.length;
    return <div key={step} style={{flex:1,minHeight:190,borderRadius:30,padding:'30px 24px',background:active ? 'linear-gradient(145deg,rgba(255,201,112,.22),rgba(85,21,87,.55))' : 'rgba(42,6,54,.32)',border:`1px solid ${active ? GOLD : 'rgba(255,255,255,.15)'}`,boxShadow:active ? '0 24px 60px rgba(42,5,49,.35)' : 'none',transform:`translateY(${active ? 0 : 24}px)`,opacity:active ? 1 : .48}}>
      <div style={{fontFamily:'Georgia',fontSize:44,color:GOLD}}>0{index + 1}</div><div style={{fontFamily:'Arial',fontSize:20,fontWeight:800,letterSpacing:2,color:CREAM,marginTop:34,lineHeight:1.3}}>{step}</div>
    </div>;
  })}</div>;
}

function SceneBody({scene, chart, sceneProgress, frame}) {
  const type = scene.type || 'takeaway';
  if (['natal_chart','house_focus','planet_focus'].includes(type)) {
    return <NatalChart chart={chart} highlightedHouses={scene.houses || []} highlightedPlanets={scene.planets || []} reveal={clamp(sceneProgress * 2)} frame={frame} />;
  }
  if (['dasha_timeline','date_window'].includes(type)) return <Timeline scene={scene} progress={sceneProgress} />;
  if (['remedy','action_steps'].includes(type)) return <RemedyPath progress={sceneProgress} />;
  return <div style={{width:650,height:650,margin:'50px auto 0',position:'relative',display:'grid',placeItems:'center'}}>
    <div style={{position:'absolute',width:520,height:520,borderRadius:'50%',border:`2px solid rgba(255,215,141,.36)`,transform:`rotate(${frame * .08}deg)`}} />
    <div style={{position:'absolute',width:390,height:390,borderRadius:'50%',border:'1px solid rgba(255,215,141,.2)'}} />
    <div style={{width:170,height:170,borderRadius:'50%',background:'radial-gradient(circle at 35% 30%,#FFF2BC,#FFB45A 35%,rgba(255,120,58,.12) 72%)',boxShadow:'0 0 90px rgba(255,185,91,.72)'}} />
    <div style={{position:'absolute',width:640,height:220,borderRadius:'50%',border:`3px solid rgba(255,181,88,.55)`,transform:`rotate(${-12 + frame * .04}deg)`}} />
  </div>;
}

function Caption({turn, frame, fps}) {
  if (!turn?.text) return null;
  const startFrame = Number(turn.start || 0) * fps;
  const endFrame = Math.max(startFrame + 1, Number(turn.end || turn.start + 4) * fps);
  const words = String(turn.text).split(/\s+/);
  const reveal = Math.floor(interpolate(frame,[startFrame,endFrame],[0,words.length],{extrapolateLeft:'clamp',extrapolateRight:'clamp'}));
  const from = Math.max(0,reveal - 13);
  return <div style={{position:'absolute',left:92,right:92,bottom:115,padding:'24px 34px',borderRadius:26,background:'rgba(28,3,38,.68)',backdropFilter:'blur(14px)',border:'1px solid rgba(255,215,141,.22)',fontFamily:'Arial',fontSize:28,lineHeight:1.35,color:CREAM,textAlign:'center',boxShadow:'0 20px 60px rgba(17,0,27,.28)'}}>
    {words.slice(from,from + 13).map((word,index) => <span key={`${from}-${index}`} style={{color:from + index < reveal ? CREAM : 'rgba(255,249,239,.3)',fontWeight:from + index === reveal - 1 ? 800 : 500}}>{word}{' '}</span>)}
  </div>;
}

export const VisualPodcast = ({durationSeconds,scenes,turns,chart,episodeTitle}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;
  const activeScene = scenes.find((scene) => seconds >= Number(scene.start || 0) && seconds < Number(scene.end || durationSeconds)) || scenes[scenes.length - 1] || {start:0,end:durationSeconds,type:'opening',headline:episodeTitle,supporting:'A personal AstroRoshni visual podcast',houses:[],planets:[],dates:[]};
  const activeTurn = turns.find((turn) => seconds >= Number(turn.start || 0) && seconds < Number(turn.end || 0));
  const sceneDuration = Math.max(.1, Number(activeScene.end || durationSeconds) - Number(activeScene.start || 0));
  const sceneProgress = clamp((seconds - Number(activeScene.start || 0)) / sceneDuration);
  const entrance = spring({frame:Math.max(0,frame - Number(activeScene.start || 0) * fps),fps,config:{damping:18,mass:.8,stiffness:90}});
  const exit = interpolate(sceneProgress,[.82,1],[1,0],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.quad)});
  const speaker = activeTurn?.speaker || (Math.floor(seconds / 7) % 2 ? 'arjun' : 'ananya');

  return <AbsoluteFill style={{background:INK}}>
    <Audio src={staticFile('episode.mp3')} />
    <AmbientWorld frame={frame} />
    <Brand />
    <HostPresence speaker={speaker} frame={frame} />
    <div style={{position:'absolute',left:0,right:0,top:292,bottom:245,opacity:exit,transform:`translateY(${(1 - entrance) * 55}px) scale(${.97 + entrance * .03})`}}>
      <SceneBody scene={activeScene} chart={chart} sceneProgress={sceneProgress} frame={frame} />
      <div style={{position:'absolute',left:82,right:82,bottom:10}}>
        <div style={{fontFamily:'Arial',fontSize:18,fontWeight:800,letterSpacing:6,color:GOLD,textTransform:'uppercase'}}>{String(activeScene.type || 'insight').replaceAll('_',' ')}</div>
        <div style={{fontFamily:'Georgia',fontSize:72,lineHeight:1.02,color:CREAM,marginTop:18,maxWidth:920,textShadow:'0 10px 40px rgba(24,0,32,.45)'}}>{activeScene.headline || episodeTitle}</div>
        {activeScene.supporting && <div style={{fontFamily:'Arial',fontSize:27,lineHeight:1.35,color:'#F8E5DB',marginTop:18,maxWidth:870}}>{activeScene.supporting}</div>}
      </div>
    </div>
    <Caption turn={activeTurn} frame={frame} fps={fps} />
    <div style={{position:'absolute',left:72,right:72,bottom:62,height:3,background:'rgba(255,255,255,.16)'}}><div style={{height:'100%',width:`${clamp(seconds / durationSeconds) * 100}%`,background:`linear-gradient(90deg,${GOLD},#FF8D4A)`,boxShadow:`0 0 16px ${GOLD}`}} /></div>
  </AbsoluteFill>;
};

