import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BirthFormModal from '../BirthForm/BirthFormModal';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import { ThemeButton } from '../Theme';
import { useAstrology } from '../../context/AstrologyContext';
import ReelStudioModal from '../Chat/ReelStudioModal';
import ReelPlayer from '../Chat/ReelPlayer';
import copy from './copy.json';
import { studioLanguage } from './locale';
import './ReelStudio.css';

const topics=[['know_me','relationships','heart'],['love_me','relationships','heart'],['real_me','identity','layers'],['superpower','identity','star'],['career','careerGroup','compass'],['next_chapter','future','moon']];
const paths={heart:'M12 21 3 12C-3 5 6-2 12 5c6-7 15 0 9 7Z',layers:'m12 3 10 6-10 6L2 9Zm-10 11 10 6 10-6M2 19l10 6 10-6',star:'m12 2 3 7 8 1-6 5 2 8-7-4-7 4 2-8-6-5 8-1Z',compass:'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm4 6-3 5-5 3 3-5Z',moon:'M21 14A9 9 0 0 1 10 3 9 9 0 1 0 21 14Z'};
const Icon=({name})=><svg viewBox="0 0 26 28" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.2"><path d={paths[name]}/></svg>;
const auth=()=>({Authorization:`Bearer ${localStorage.getItem('token')||''}`});
async function request(path,body){const r=await fetch(`/api${path}`,{method:body?'POST':'GET',headers:{...auth(),'Content-Type':'application/json'},cache:'no-store',...(body?{body:JSON.stringify(body)}:{})});if(!r.ok)throw new Error('request_failed');return r.json();}
function Artwork({id}){
  const [url,setUrl]=useState(null);
  useEffect(()=>{if(!id)return;let active=true,objectUrl;const controller=new AbortController();fetch(`/api/reel-studio/jobs/${id}/thumbnail`,{headers:auth(),signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('thumbnail');return r.blob();}).then(blob=>{if(active){objectUrl=URL.createObjectURL(blob);setUrl(objectUrl);}}).catch(()=>{});return()=>{active=false;controller.abort();if(objectUrl)URL.revokeObjectURL(objectUrl);};},[id]);
  return url?<img src={url} alt=""/>:<Icon name="star"/>;
}
export default function ReelStudioPage({user,onLogout,onAdminClick}){
  const {birthData,setBirthData}=useAstrology(),navigate=useNavigate();
  const language=studioLanguage();
  const t=(key,args={})=>Object.entries(args).reduce((text,[k,v])=>text.replace(`{{${k}}}`,v),(copy[language]||copy.en)[key]);
  const [catalog,setCatalog]=useState(null),[charts,setCharts]=useState([]),[history,setHistory]=useState([]),[error,setError]=useState(false),[loading,setLoading]=useState(true);
  const [addChart,setAddChart]=useState(false);
  const [filter,setFilter]=useState('all'),[busy,setBusy]=useState(null),[source,setSource]=useState(null),[player,setPlayer]=useState(null);
  const lock=useRef(false), sequence=useRef(0);
  const refreshHistory=useCallback(()=>request('/reel-studio/history').then(r=>setHistory(r.reels||[])).catch(()=>setError(true)),[]);
  const load=useCallback(async()=>{const version=++sequence.current;setLoading(true);setError(false);try{const [c,b,h]=await Promise.all([request('/reel-studio/catalog'),request('/birth-charts'),request('/reel-studio/history')]);if(version===sequence.current){setCatalog(c);setCharts(b.charts||[]);setHistory(h.reels||[]);}}catch{if(version===sequence.current){setError(true);setCatalog(null);}}finally{if(version===sequence.current)setLoading(false);}},[]);
  useEffect(()=>{load();return()=>{sequence.current++;};},[load]);
  const id=birthData?.id||birthData?.birth_chart_id||birthData?._id;
  const chart=charts.find(c=>String(c.id)===String(id))||(!id&&birthData&&charts.find(c=>c.name===birthData.name&&String(c.date).slice(0,10)===String(birthData.date).slice(0,10)&&String(c.time).slice(0,5)===String(birthData.time).slice(0,5)));
  const open=async topic=>{
    if(lock.current)return;
    if(!chart){setAddChart(true);return;}
    if(topic==='next_chapter'){navigate('/next-chapter');return;}
    lock.current=true;setBusy(topic);setError(false);
    try{const data=await request('/reel-studio/sources',{birth_chart_id:chart.id,topic});setSource(data.message_id);}catch{setError(true);}finally{setBusy(null);lock.current=false;}
  };
  const price=topic=>!catalog?t('loading'):topic==='next_chapter'?t('chapterPrice',{report:catalog.chapter_credit_cost,reel:catalog.pricing.credit_cost}):t('from',{count:catalog.pricing.credit_cost});
  const card=([topic,group,icon],featured=false)=><button key={topic} className={`rs-card${featured?' rs-card--featured':''}`} disabled={!catalog||!!busy} onClick={()=>open(topic)}><div className="rs-art"><div className="rs-orbit"><Icon name={icon}/></div><span className="rs-spark" aria-hidden="true">✦</span>{featured&&<span className="rs-eyebrow rs-art-label">{t('featured')}</span>}</div><div className="rs-card-copy"><span className="rs-eyebrow">{t(group)}</span><h2>{t(topic)}</h2><p>{t(`${topic}Hook`)}</p>{topic==='next_chapter'&&<small>{t('chapterNote')}</small>}<div className="rs-card-footer"><strong>{busy===topic?t('loading'):price(topic)}</strong><span aria-hidden="true">↗</span></div></div></button>;
  return <><ModernNavigationHeader user={user} onLogout={onLogout} onAdminClick={onAdminClick}/><main className="rs-page"><div className="rs-shell">
    <header className="rs-toolbar"><ThemeButton variant="ghost" onClick={()=>navigate('/profile')}>{t('back')}</ThemeButton><label><span className="rs-sr-only">{t('choose')}</span><select id="studio-native" value={chart?.id||''} onChange={e=>{const selected=charts.find(c=>String(c.id)===e.target.value);if(selected)setBirthData(selected);}}><option value="" disabled>{t('choose')}</option>{charts.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><ThemeButton variant="ghost" onClick={load}>{t('refresh')}</ThemeButton></header>
    <section className="rs-hero"><div><p className="rs-eyebrow">{t('title')}</p><h1>{t('hero')}</h1><p className="rs-intro">{t('intro')}</p>{!loading&&!chart&&<ThemeButton onClick={()=>setAddChart(true)}>{t('choose')}</ThemeButton>}</div>{card(topics[0],true)}</section>
    {error&&<div role="alert" className="rs-notice"><p>{t('error')}</p><ThemeButton onClick={load}>{t('retry')}</ThemeButton></div>}
    <section><h2 className="rs-section-title">{t('topics')}</h2><nav className="rs-filters" aria-label={t('topics')}>{['all','relationships','identity','careerGroup','future'].map(group=><button key={group} aria-pressed={group===filter} onClick={()=>setFilter(group)}>{t(group)}</button>)}</nav><div className="rs-grid">{topics.filter(item=>filter==='all'||item[1]===filter).map(item=>card(item))}</div></section>
    <section className="rs-library"><h2 className="rs-section-title">{t('saved')}</h2>{loading?<p role="status">{t('loading')}</p>:!history.length?<p>{t('empty')}</p>:<div className="rs-saved-grid">{history.map(item=><button key={item.job_id} className="rs-saved" onClick={()=>item.status==='completed'?setPlayer(item.job_id):setSource(item.message_id)}><div className="rs-cover"><Artwork id={item.status==='completed'?item.job_id:null}/><span className="rs-play" aria-hidden="true">{item.status==='completed'?'▷':'◷'}</span></div><strong>{item.question||t('title')}</strong><small>{t(item.status==='completed'?'play':item.status==='failed'?'failed':'inProgress')}</small></button>)}</div>}</section>
    <BirthFormModal isOpen={addChart} onClose={()=>setAddChart(false)} title={t('choose')} onChartPick={value=>{setBirthData(value);load();}} onSubmit={value=>{setBirthData(value);load();}}/>
    {source&&<ReelStudioModal key={source} messageId={source} initialLanguage={language==='hi'?'hi':'en'} onClose={()=>{setSource(null);refreshHistory();}}/>}
    {player&&<ReelPlayer jobId={player} onClose={()=>setPlayer(null)}/>}
  </div></main></>;
}
