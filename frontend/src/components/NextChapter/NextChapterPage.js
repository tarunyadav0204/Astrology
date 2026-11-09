import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ThemeButton, ThemeModal } from '../Theme';
import ReelStudioModal from '../Chat/ReelStudioModal';
import CreditsModal from '../Credits/CreditsModal';
import BirthFormModal from '../BirthForm/BirthFormModal';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import { useAstrology } from '../../context/AstrologyContext';
import copy from './copy.json';
import './NextChapter.css';

const stages = ['queued', 'mapping', 'exploring', 'writing', 'reviewing'];
const planetHi = {Sun:'सूर्य',Moon:'चंद्र',Mars:'मंगल',Mercury:'बुध',Jupiter:'गुरु',Venus:'शुक्र',Saturn:'शनि',Rahu:'राहु',Ketu:'केतु'};
async function request(path, body) {
  const response = await fetch(`/api${path}`, { method: body ? 'POST' : 'GET', cache:'no-store', signal:AbortSignal.timeout(20000), headers: {Authorization:`Bearer ${localStorage.getItem('token')}`, 'Content-Type':'application/json'}, ...(body ? {body:JSON.stringify(body)} : {}) });
  const data = await response.json();
  if (!response.ok) throw Object.assign(new Error('request_failed'), {status:response.status});
  return data;
}
export default function NextChapterPage({user,onLogout,onAdminClick}) {
  const {birthData} = useAstrology();
  const navigate = useNavigate();
  const [selection,setSelection] = useState('current');
  const [periodPreview,setPeriodPreview] = useState(null);
  const periodFor = value => String(periodPreview?.chart) === String(chart) ? periodPreview?.spine?.[value + '_antardasha'] : null;
  const [language,setLanguage] = useState(() => localStorage.getItem('nextChapterLanguage') === 'hi' ? 'hi' : 'en');
  const [addChart,setAddChart] = useState(false), [loading,setLoading] = useState(true);
  const [chart,setChart] = useState(''), [history,setHistory] = useState([]);
  const [connectionLost,setConnectionLost] = useState(false);
  const [quote,setQuote] = useState(null), [job,setJob] = useState(null), [phase,setPhase] = useState(-1);
  const [error,setError] = useState(''), [busy,setBusy] = useState(false), [confirm,setConfirm] = useState(false), [buy,setBuy] = useState(false), [refresh,setRefresh] = useState(0);
  const lock = useRef(false), quoteSequence = useRef(0);
  const t = (key,args={}) => Object.entries(args).reduce((s,[k,v])=>s.replace(`{{${k}}}`,v), (copy[language] || copy.en)[key]);
  const [loadError,setLoadError] = useState(false), [quoteError,setQuoteError] = useState(false);
  const [reelSource,setReelSource]=useState(null),[reelBusy,setReelBusy]=useState(false),[reelError,setReelError]=useState(false);
  const reelLock=useRef(false),activeChapter=useRef(null);
  activeChapter.current=job?.id;
  useEffect(()=>{setReelSource(null);setReelError(false);},[job?.id]);
  const openReel=async()=>{
    if(reelLock.current||!job?.report)return;
    const chapterId=job.id;
    reelLock.current=true;setReelBusy(true);setReelError(false);
    try{const source=await request(`/next-chapter/jobs/${chapterId}/reel-source`,{});if(activeChapter.current===chapterId)setReelSource(source.message_id);}
    catch{if(activeChapter.current===chapterId)setReelError(true);}
    finally{reelLock.current=false;setReelBusy(false);}
  };
  const hasJob = Boolean(job);
  const visibleError = hasJob ? (job.report && connectionLost ? 'connectionLost' : '') : error || (loadError || quoteError ? 'previewError' : '');
  const planet = name => language==='hi' ? planetHi[name] || name : name;
  const dates = p => p ? `${new Date(p.start_at).toLocaleDateString(language==='hi'?'hi-IN':'en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:job?.spine?.timezone || quote?.spine?.timezone || periodPreview?.spine?.timezone})} — ${new Date(p.end_at).toLocaleDateString(language==='hi'?'hi-IN':'en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:job?.spine?.timezone || quote?.spine?.timezone || periodPreview?.spine?.timezone})}` : '';
  useEffect(() => {
    if (hasJob) return;
    let active = true;
    setLoadError(false); setLoading(true);
    Promise.all([request('/birth-charts'),request('/next-chapter/jobs')]).then(([c,h]) => {
      if (!active) return;
      const rows=c.charts || [];
      const id=birthData?.id || birthData?.birth_chart_id || birthData?._id;
      const selected=rows.find(r=>String(r.id)===String(id)) || (!id&&birthData&&rows.find(r=>r.name===birthData.name&&String(r.date).slice(0,10)===String(birthData.date).slice(0,10)&&String(r.time).slice(0,5)===String(birthData.time).slice(0,5)));
      setChart(String(selected?.id || id || ''));setHistory(h.chapters);setLoadError(false);
    }).catch(()=>active&&setLoadError(true)).finally(()=>active&&setLoading(false));
    return()=>{active=false;};
  },[refresh,birthData,hasJob]);
  useEffect(()=>{setJob(null);setConfirm(false);},[birthData]);
  useEffect(() => {
    const requestId = ++quoteSequence.current;
    setQuoteError(false);
    if (hasJob) return;
    setQuote(null);
    if (!chart) return;
    request('/next-chapter/quote',{birth_chart_id:Number(chart),language,selection}).then(q => {
      if (requestId !== quoteSequence.current) return;
      setQuote(q); setPeriodPreview({chart,spine:q.spine}); setQuoteError(false);
    }).catch(() => { if (requestId === quoteSequence.current) setQuoteError(true); });
    return () => { quoteSequence.current++; };
  }, [chart,language,selection,refresh,hasJob]);

  useEffect(() => {
    if (!job?.id || ['completed','failed'].includes(job.status)) return;
    let active=true,pending=false,timer;
    const poll=async()=>{
      if(!active||pending)return;
      clearTimeout(timer);pending=true;
      let terminal=false;
      try {
        const latest=await request(`/next-chapter/jobs/${job.id}`);
        terminal=['completed','failed'].includes(latest.status);
        if(active){setConnectionLost(false);setError('');setJob(previous=>previous?.id===latest.id&&!['completed','failed'].includes(previous.status)?latest:previous);}
      } catch (_) {if(active)setConnectionLost(true);}
      finally {pending=false;if(active&&!terminal)timer=setTimeout(poll,4000);}
    };
    poll();
    const onVisible=()=>{if(document.visibilityState==='visible')poll();};
    document.addEventListener('visibilitychange',onVisible);
    return()=>{active=false;clearTimeout(timer);document.removeEventListener('visibilitychange',onVisible);};
  },[job?.id,job?.status]);
  const open = async id => {setBusy(true);setError('');window.scrollTo({top:0,behavior:'instant'});try{const j=await request(`/next-chapter/jobs/${id}`);setConnectionLost(false);setError('');setLanguage(j.language);setJob(j);setPhase(-1);window.scrollTo({top:0,behavior:'instant'});}catch{setError('error');setConnectionLost(true);}finally{setBusy(false);}};
  const purchase = async()=>{if(lock.current || !quote)return;lock.current=true;setConfirm(false);setBusy(true);setError('');setConnectionLost(false);setJob({id:null,status:'queued',stage:'queued',progress_percent:0,native_name:quote.native_name,spine:quote.spine});window.scrollTo({top:0,behavior:'instant'});try{const j=await request('/next-chapter/jobs',{quote_id:quote.quote_id});setJob(previous=>({...previous,id:j.id}));await open(j.id);setRefresh(v=>v+1);}catch(e){setJob(null);setError(e.status===409?'changed':'error');if(e.status===402)setBuy(true);setRefresh(v=>v+1);}finally{setBusy(false);lock.current=false;}};
  const report=job?.report, period=phase>=0?report?.periods[phase]:null;
  const cards = period?.manifestations || report?.antardasha_events || [];
  return <><ModernNavigationHeader user={user} onLogout={onLogout} onAdminClick={onAdminClick}/><main className="nc-page"><div className="nc-shell">
    {busy&&!job&&<p role="status">{t('loading')}</p>}<header className="nc-top"><ThemeButton variant="ghost" onClick={()=>job?(setJob(null),setRefresh(v=>v+1)):navigate('/profile')}>{t('back')}</ThemeButton><span>{t('eyebrow')}</span><select aria-label={t('language')} value={language} onChange={e=>{setLanguage(e.target.value);localStorage.setItem('nextChapterLanguage',e.target.value);setJob(null);}}><option value="en">{t('en')}</option><option value="hi">{t('hi')}</option></select></header>
    {visibleError&&<div role="alert" className="nc-error">{t(visibleError)} <ThemeButton variant="secondary" onClick={()=>{setError('');setRefresh(v=>v+1);if(job?.id)open(job.id);}}>{t('retry')}</ThemeButton></div>}
    {!job ? <><section className="nc-hero"><div className="nc-orbit" aria-hidden="true">✦</div><p className="nc-eyebrow">{t('title')}</p><h1>{t('hero')}</h1><p className="nc-lead">{t('intro')}</p>
      <div className="nc-chapter-choice" role="group" aria-label={t('chooseChapter')}>{['current','next'].map(value=><button key={value} type="button" aria-pressed={selection===value} disabled={busy} onClick={()=>{if(selection===value)return;setQuote(null);setConfirm(false);setError('');setSelection(value);}}><strong>{t(value+'Chapter')}</strong><span>{t(value+'ChapterBody')}</span>{periodFor(value)&&<span><strong>{planet(periodFor(value).planet)}</strong><br/>{dates(periodFor(value))}</span>}</button>)}</div>
      {quote ? <div className="nc-offer"><span className="nc-eyebrow">{quote.native_name}</span><h2>{planet(quote.spine.mahadasha.planet)} · {planet(quote.spine.antardasha.planet)}</h2><p>{dates(quote.spine.antardasha)}</p><div className="nc-mini-timeline" aria-hidden="true">{quote.spine.pratyantardashas.map(p=><span key={p.id}>{planet(p.planet)}</span>)}</div><ThemeButton disabled={busy||(!quote.saved_job_id&&quote.credit_cost===null)} onClick={()=>quote.saved_job_id?open(quote.saved_job_id):quote.credits<quote.credit_cost?setBuy(true):setConfirm(true)}>{quote.saved_job_id?t('open'):t('create')}</ThemeButton><p>{quote.saved_job_id?t('privacy'):quote.credit_cost===null?t('unavailable'):t('cost',{count:quote.credit_cost})}</p></div>:<div role="status"><p>{loading||chart?t('loading'):t('noCharts')}</p>{!loading&&!chart&&<ThemeButton variant="secondary" onClick={()=>setAddChart(true)}>{t('addChart')}</ThemeButton>}</div>}
    </section><section className="nc-included"><h2>{t('included')}</h2><p>{t('includedBody')}</p><div>{['overview','possibilities','timeline'].map((key,i)=><article key={key}><span className="nc-index">{String(i+1).padStart(2,'0')}</span><h3>{t(key)}</h3></article>)}</div></section><section><h2>{t('saved')}</h2>{!history.length&&<p>{t('empty')}</p>}<div className="nc-library">{history.map(h=><button key={h.id} className="nc-saved" disabled={busy} onClick={()=>open(h.id)}><span>{h.native_name} · {t(h.language)}</span><strong>{planet(h.spine.mahadasha.planet)} · {planet(h.spine.antardasha.planet)}</strong><span>{dates(h.spine.antardasha)}</span><span>{t(h.status==='completed'?'open':h.status==='failed'?'failed':'resume')} →</span></button>)}</div></section></> : !report ? <section className="nc-progress" aria-live="polite"><div className="nc-orbit" aria-hidden="true">✦</div><p className="nc-eyebrow">{job.native_name}</p><h1>{t(job.status==='failed'?'failed':job.stage)}</h1>{job.status==='failed'?<><p>{job.refunded?t('refunded'):t('error')}</p><ThemeButton onClick={()=>{setJob(null);setRefresh(v=>v+1);}}>{t('retry')}</ThemeButton></>:<>{connectionLost?<div role="alert"><p>{t('connectionLost')}</p><ThemeButton onClick={()=>open(job.id)}>{t('refresh')}</ThemeButton></div>:<><strong className="nc-percentage">{job.progress_percent ?? 0}%</strong><progress aria-label={t(job.stage)} max={100} value={job.progress_percent ?? 0}/><p>{t('progressNote')}</p></>}<div className="nc-steps">{stages.map((s,i)=><span key={s} className={i<=stages.indexOf(job.stage)?'active':''}>{t(s)}</span>)}</div><p className="nc-lead">{t('wait')}</p></>}</section> : <>
      <section className="nc-reading-hero"><p className="nc-eyebrow">{job.native_name} · {t('title')}</p><h1>{report.title}</h1><p>{dates(job.spine.antardasha)}</p><p className="nc-lead">{report.overview}</p></section>
      <section className="nc-event"><h2>{t('reelTitle')}</h2><p>{t('reelBody')}</p><ThemeButton disabled={reelBusy} onClick={openReel}>{t(reelBusy?'loading':'reelTitle')}</ThemeButton>{reelError&&<p role="alert">{t('error')}</p>}</section>
      <nav className="nc-tabs" aria-label={t('timeline')}><button aria-pressed={phase===-1} onClick={()=>setPhase(-1)}>{t('all')}</button>{job.spine.pratyantardashas.map((p,i)=><button key={p.id} aria-pressed={phase===i} onClick={()=>setPhase(i)}>{planet(p.planet)}<small>{t('phase',{number:i+1})}</small></button>)}</nav>
      <section className="nc-reading" key={phase}>{period?<><p className="nc-eyebrow">{t('phase',{number:phase+1})} · {dates(job.spine.pratyantardashas[phase])}</p><h2>{period.summary}</h2><p>{period.what_changes}</p><aside><h3>{t('timing')}</h3><p>{period.timing_explanation}</p></aside></>:<><h2>{t('overview')}</h2><p>{report.mahadasha_context}</p><p>{report.antardasha_themes}</p></>}
        <h2>{t('possibilities')}</h2>{cards.map((c,i)=><article className="nc-event" key={i}><span className="nc-index">{String(i+1).padStart(2,'0')}</span><h3>{c.theme}</h3>{c.circumstances&&<p>{c.circumstances}</p>}<ul>{c.possibilities.map((s,k)=><li key={k}>{s}</li>)}</ul>{c.timing&&<p className="nc-timing">{c.timing}</p>}<details><summary>{t('why')}</summary><p>{c.why}</p>{c.practical_guidance&&<><h3>{t('guidance')}</h3><p>{c.practical_guidance}</p></>}{c.timing_windows?.length>0&&<><h3>{t('timing')}</h3><ul>{c.timing_windows.map((w,k)=><li key={k}>{dates(w)}{w.transiting_planet&&<> · {planet(w.transiting_planet)} → {planet(w.natal_planet)}</>}</li>)}</ul></>}</details></article>)}
        <details className="nc-evidence"><summary>{t('evidence')}</summary>{period&&<p>{period.conditions_and_cautions}</p>}{(period?.transit_story || report.antardasha_transits || []).map((r,i)=><p key={i}>{r.explanation}</p>)}</details>{phase===-1&&report.closing&&<aside><h3>{t('guidance')}</h3><p>{report.closing}</p></aside>}<p className="nc-note">{t('note')}</p>
      </section></>}
    {report&&reelSource&&<ReelStudioModal key={reelSource} messageId={reelSource} initialLanguage={job.language} onClose={()=>setReelSource(null)}/>}
    <ThemeModal isOpen={confirm} onClose={()=>setConfirm(false)} title={t('confirm')} closeLabel={t('cancel')}><p>{t('confirmBody')}</p><h2>{t('cost',{count:quote?.credit_cost})}</h2><p>{t('balance',{count:quote?.credits})}</p><ThemeButton onClick={purchase} disabled={busy}>{t('create')}</ThemeButton><ThemeButton variant="ghost" onClick={()=>setConfirm(false)}>{t('cancel')}</ThemeButton></ThemeModal>
    <BirthFormModal isOpen={addChart} onClose={()=>setAddChart(false)} onSubmit={()=>setRefresh(v=>v+1)} title={t('addChart')} />
    <CreditsModal isOpen={buy} onClose={()=>{setBuy(false);setRefresh(v=>v+1);}} />
  </div></main></>;
}
