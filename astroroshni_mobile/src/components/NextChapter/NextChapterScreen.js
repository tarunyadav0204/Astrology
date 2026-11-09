import React, { useEffect, useRef, useState } from 'react';
import { AppState, ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { layoutTokens, typographyTokens } from '../../theme/tokens';
import api from '../../services/api';
import { getEndpoint } from '../../utils/constants';
import MessageBubble from '../Chat/MessageBubble';
import ConfirmCreditsModal from '../ConfirmCreditsModal';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { storage } from '../../services/storage';
import { goBackOrHome } from '../../navigation/navHelpers';

const stages = ['queued','mapping','exploring','writing','reviewing'];
const hindiPlanets = {Sun:'सूर्य',Moon:'चंद्र',Mars:'मंगल',Mercury:'बुध',Jupiter:'गुरु',Venus:'शुक्र',Saturn:'शनि',Rahu:'राहु',Ketu:'केतु'};
const get = path => api.get(getEndpoint(path),{suppressGlobalError:true,timeout:15000,headers:{'Cache-Control':'no-cache'}}).then(r=>r.data);
const post = (path,body) => api.post(getEndpoint(path),body,{suppressGlobalError:true}).then(r=>r.data);

export default function NextChapterScreen({navigation,route}) {
  const {t:i18t,i18n}=useTranslation(), {colors}=useTheme();
  const t=(key,args)=>i18t(`nextChapter.${key}`,args);
  const [selection,setSelection] = useState('current');
  const [periodPreview,setPeriodPreview] = useState(null);
  const periodFor = value => String(periodPreview?.chart) === String(chart) ? periodPreview?.spine?.[value + '_antardasha'] : null;
  const [language,setLanguage]=useState(['hi','hindi'].includes(i18n.language)?'hi':'en');
  const [native,setNative]=useState(null),[chart,setChart]=useState(null),[history,setHistory]=useState([]);
  const [quote,setQuote]=useState(null),[job,setJob]=useState(null),[phase,setPhase]=useState(-1),[expanded,setExpanded]=useState({});
  const [error,setError]=useState(''),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState(false),[revision,setRevision]=useState(0),[loading,setLoading]=useState(true);
  const sequence=useRef(0), lock=useRef(false), scroll=useRef(null);
  const [connectionLost,setConnectionLost]=useState(false);
  const [regenerateError,setRegenerateError] = useState(false);
  const [loadError,setLoadError] = useState(false), [quoteError,setQuoteError] = useState(false);
  const [reelSource,setReelSource]=useState(null),[reelLaunch,setReelLaunch]=useState(0),[reelBusy,setReelBusy]=useState(false),[reelError,setReelError]=useState(false);
  const reelLock=useRef(false), activeChapter=useRef(null);
  activeChapter.current=job?.id;
  useEffect(()=>{setRegenerateError(false);setConfirm(false);setReelSource(null);setReelLaunch(0);setReelError(false);},[job?.id]);
  const openReel=async()=>{
    if(reelLock.current||!job?.report)return;
    const chapterId=job.id;
    reelLock.current=true;setReelBusy(true);setReelError(false);
    try{
      const source=await post(`/next-chapter/jobs/${chapterId}/reel-source`,{});
      if(activeChapter.current!==chapterId)return;
      setReelSource({messageId:source.message_id,role:'assistant',content:job.report.overview||job.report.title});
      setReelLaunch(v=>v+1);
    }catch{if(activeChapter.current===chapterId)setReelError(true);}
    finally{reelLock.current=false;setReelBusy(false);}
  };
  const hasJob = Boolean(job);
  const visibleError = regenerateError ? 'error' : hasJob ? (job.report && connectionLost ? 'connectionLost' : '') : error || (loadError || quoteError ? 'previewError' : '');
  const planet=name=>language==='hi'?hindiPlanets[name]||name:name;
  const dates=p=>p?`${new Date(p.start_at).toLocaleDateString(language==='hi'?'hi-IN':'en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:job?.spine?.timezone||quote?.spine?.timezone || periodPreview?.spine?.timezone})} — ${new Date(p.end_at).toLocaleDateString(language==='hi'?'hi-IN':'en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:job?.spine?.timezone||quote?.spine?.timezone || periodPreview?.spine?.timezone})}`:'';
  useEffect(() => {
    if (hasJob) return;
    let active = true;
    setLoadError(false); setLoading(true);
    Promise.all([get('/birth-charts'), get('/next-chapter/jobs'), storage.getBirthDetails()])
      .then(([c,h,selected]) => {
        if (!active) return;
        const chosen = selected || route.params?.birthData;
        const id = chosen?.id || chosen?.birth_chart_id || chosen?._id;
        const owned = c.charts.find(r => String(r.id) === String(id)) ||
          (!id && chosen && c.charts.find(r => r.name === chosen.name && String(r.date).slice(0,10) === String(chosen.date).slice(0,10) && String(r.time).slice(0,5) === String(chosen.time).slice(0,5)));
        const next = owned || (id ? chosen : null);
        setNative(next); setChart(next?.id || next?.birth_chart_id || next?._id || null);
        setHistory(h.chapters);setLoadError(false);
      }).catch(() => active && setLoadError(true)).finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [revision, route.params?.birthData, hasJob]);
  useEffect(() => {
    const requestId = ++sequence.current;
    setQuoteError(false);
    if (hasJob) return;
    setQuote(null);
    if (!chart) return;
    post('/next-chapter/quote',{birth_chart_id:Number(chart),language,selection}).then(q => {
      if (requestId !== sequence.current) return;
      setQuote(q); setPeriodPreview({chart,spine:q.spine}); setQuoteError(false);
    }).catch(() => { if (requestId === sequence.current) setQuoteError(true); });
    return () => { sequence.current++; };
  }, [chart,language,selection,revision,hasJob]);

  useEffect(() => {
    if (!job?.id || ['completed','failed'].includes(job.status)) return;
    let active = true, pending = false, timer;
    const poll = async () => {
      if (!active || pending) return;
      clearTimeout(timer); pending = true;
      let terminal = false;
      try {
        const latest = await get(`/next-chapter/jobs/${job.id}`);
        terminal = ['completed','failed'].includes(latest.status);
        if (active) {
          setConnectionLost(false);setError('');
          setJob(previous => previous?.id === latest.id && !['completed','failed'].includes(previous.status) ? latest : previous);
          if (terminal) scroll.current?.scrollTo({y:0,animated:false});
        }
      } catch (_) { if (active) setConnectionLost(true); }
      finally { pending = false; if (active && !terminal) timer = setTimeout(poll, 4000); }
    };
    poll();
    const sub = AppState.addEventListener('change', state => { if (state === 'active') poll(); });
    const focus = navigation.addListener('focus', poll);
    return () => { active = false; clearTimeout(timer); sub.remove(); focus(); };
  }, [job?.id, job?.status, navigation]);
  useEffect(()=>navigation.addListener('focus',()=>setRevision(v=>v+1)),[navigation]);
  const open=async id=>{setBusy(true);setError('');setConnectionLost(false);scroll.current?.scrollTo({y:0,animated:false});try{const j=await get(`/next-chapter/jobs/${id}`);setConnectionLost(false);setError('');setJob(j);setLanguage(j.language);setPhase(-1);setExpanded({});scroll.current?.scrollTo({y:0,animated:false});}catch{setError('error');setConnectionLost(true);}finally{setBusy(false);}};
  const regenerate=async()=>{
    if(lock.current||busy||!job?.id)return;
    lock.current=true;const sourceId=job.id;setBusy(true);setRegenerateError(false);
    try {
      const q=await post(`/next-chapter/jobs/${sourceId}/regeneration-quote`,{});
      if(activeChapter.current!==sourceId)return;
      if(q.saved_job_id){await open(q.saved_job_id);return;}
      setQuote(q);
      if(q.credits<q.credit_cost)navigation.navigate('Credits');else setConfirm(true);
    } catch {setRegenerateError(true);} finally {lock.current=false;setBusy(false);}
  };
  const purchase=async()=>{if(lock.current||!quote)return;lock.current=true;const previousJob=job;setConfirm(false);setBusy(true);setError('');setConnectionLost(false);setJob({id:null,status:'queued',stage:'queued',progress_percent:0,native_name:quote.native_name,spine:quote.spine});scroll.current?.scrollTo({y:0,animated:false});try{const j=await post('/next-chapter/jobs',{quote_id:quote.quote_id});setJob(previous=>({...previous,id:j.id}));await open(j.id);setRevision(v=>v+1);}catch(e){setJob(quote.regenerated_from?previousJob:null);if(quote.regenerated_from)setRegenerateError(true);setError(e.response?.status===409?'changed':'error');if(e.response?.status===402)navigation.navigate('Credits');setRevision(v=>v+1);}finally{setBusy(false);lock.current=false;}};
  const toggle=key=>setExpanded(v=>({...v,[key]:!v[key]}));
  const body=text=><Text style={[s.body,{color:colors.textSecondary}]}>{text}</Text>;
  const heading=text=><Text accessibilityRole="header" style={[s.heading,{color:colors.text}]}>{text}</Text>;
  const button=(label,onPress,secondary=false,disabled=false)=><TouchableOpacity accessibilityRole="button" accessibilityState={{disabled}} disabled={disabled} onPress={onPress} style={[s.button,{backgroundColor:secondary?colors.surfaceMuted:colors.primaryStrong,borderColor:colors.cardBorder,opacity:disabled ? 0.5 : 1}]}><Text style={[s.buttonText,{color:secondary?colors.text:colors.onPrimary}]}>{label}</Text><Ionicons name="arrow-forward" size={18} color={secondary?colors.text:colors.onPrimary}/></TouchableOpacity>;
  const card={...s.card,backgroundColor:colors.surfaceRaised,borderColor:colors.cardBorder};
  const report=job?.report,period=phase>=0?report?.periods[phase]:null;
  const events=period?.manifestations||report?.antardasha_events||[];
  const percent = job?.progress_percent ?? 0;
  const selectNative = () => { setJob(null); setConfirm(false); navigation.navigate('SelectNative', {returnTo:'NextChapter'}); };
  return <View style={[s.page,{backgroundColor:colors.background}]}>
    <View style={{backgroundColor:colors.headerSurface}}><SafeAreaView edges={['top']}>
      <View style={[s.header,{borderColor:colors.cosmicLine}]}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel={t('back')} onPress={()=>job?(setJob(null),setRevision(v=>v+1)):goBackOrHome(navigation)} style={[s.icon,{backgroundColor:colors.cosmicRaised,borderColor:colors.cosmicLine}]}><Ionicons name="arrow-back" size={21} color={colors.textInverse}/></TouchableOpacity>
        <View style={s.headerCopy}><Text style={[s.headerText,{color:colors.textInverse}]}>{t('title')}</Text>
          <NativeSelectorChip birthData={job?{name:job.native_name}:native} onPress={selectNative} showIcon={false} style={{alignSelf:'flex-start',backgroundColor:colors.cosmicRaised,borderColor:colors.cosmicLine}} textStyle={{color:colors.textInverseMuted}} iconColor={colors.accent}/>
        </View>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel={t(job?.report?'regenerate':'refresh')} disabled={busy} onPress={()=>job?.report?regenerate():(setRevision(v=>v+1),job?.id&&open(job.id))} style={s.icon}><>{busy?<ActivityIndicator color={colors.textInverse}/>:<Ionicons name="refresh-outline" size={21} color={colors.textInverse}/>}</></TouchableOpacity>
      </View>
    </SafeAreaView></View>
    <ScrollView ref={scroll} contentContainerStyle={s.content}>
      {!!visibleError&&<View accessibilityRole="alert" style={card}>{body(t(visibleError))}{button(t('retry'),()=>{if(regenerateError){regenerate();return;}setError('');setRevision(v=>v+1);if(job?.id)open(job.id);},true)}</View>}
      {busy&&!job&&<ActivityIndicator color={colors.primary} accessibilityLabel={t('loading')}/>}
      {!job?<><View style={s.hero}><View style={[s.emblem,{borderColor:colors.accent,backgroundColor:colors.accentSoft}]}><Ionicons name="sparkles-outline" size={34} color={colors.onAccent}/></View><Text style={[s.eyebrow,{color:colors.primary}]}>{t('eyebrow')}</Text><Text accessibilityRole="header" style={[s.title,{color:colors.text}]}>{t('hero')}</Text>{body(t('intro'))}</View>
        <View style={s.formSection}>{heading(t('chooseChapter'))}<View style={s.chapterChoices}>{['current','next'].map(value=><TouchableOpacity key={value} accessibilityRole="button" accessibilityState={{selected:selection===value,disabled:busy}} disabled={busy} onPress={()=>{if(selection===value)return;setQuote(null);setConfirm(false);setError('');setSelection(value);}} style={[s.card,s.choiceCard,{backgroundColor:selection===value?colors.selectionSurface:colors.surfaceRaised,borderColor:selection===value?colors.selectionBorder:colors.cardBorder}]}><View style={s.choiceHeader}><Text style={[s.label,{color:selection===value?colors.selectionText:colors.text}]}>{t(value+'Chapter')}</Text><Ionicons name={selection===value?'radio-button-on':'radio-button-off'} size={22} color={selection===value?colors.selectionText:colors.primary}/></View><Text style={[s.body,{color:selection===value?colors.selectionTextMuted:colors.textSecondary}]}>{t(value+'ChapterBody')}</Text>{periodFor(value)&&<View style={s.periodMeta}><Text style={[s.label,{color:selection===value?colors.selectionText:colors.text}]}>{planet(periodFor(value).planet)}</Text><Text style={[s.body,{color:selection===value?colors.selectionTextMuted:colors.textSecondary}]}>{dates(periodFor(value))}</Text></View>}</TouchableOpacity>)}</View></View>
        <View style={s.formSection}>{heading(t('language'))}<View style={s.chips}>{['en','hi'].map(l=><TouchableOpacity key={l} accessibilityRole="button" accessibilityState={{selected:l===language}} onPress={()=>setLanguage(l)} style={[s.chip,{backgroundColor:l===language?colors.primaryStrong:colors.surface,borderColor:colors.cardBorder}]}><Text style={[s.label,{color:l===language?colors.onPrimary:colors.text}]}>{t(l)}</Text></TouchableOpacity>)}</View></View>
        {quote?<View style={card}><Text style={[s.eyebrow,{color:colors.primary}]}>{quote.native_name}</Text>{heading(`${planet(quote.spine.mahadasha.planet)} · ${planet(quote.spine.antardasha.planet)}`)}{body(dates(quote.spine.antardasha))}<View style={[s.rule,{backgroundColor:colors.cardBorder}]}/>{body(t('includedBody'))}{button(quote.saved_job_id?t('open'):t('create'),()=>quote.saved_job_id?open(quote.saved_job_id):quote.credits<quote.credit_cost?navigation.navigate('Credits'):setConfirm(true),false,busy)}{body(quote.saved_job_id?t('privacy'):t('cost',{count:quote.credit_cost}))}</View>:<View style={card}>{body(loading||chart?t('loading'):t('noCharts'))}{!loading&&!chart&&button(t('chart'),selectNative)}</View>}
        {heading(t('saved'))}{!history.length&&body(t('empty'))}{history.map(h=><TouchableOpacity key={h.id} accessibilityRole="button" disabled={busy} accessibilityState={{disabled:busy}} onPress={()=>open(h.id)} style={card}><Text style={[s.eyebrow,{color:colors.primary}]}>{h.native_name} · {t(h.language)}</Text>{heading(`${planet(h.spine.mahadasha.planet)} · ${planet(h.spine.antardasha.planet)}`)}{body(dates(h.spine.antardasha))}<Text style={[s.label,{color:colors.primary}]}>{t(h.status==='completed'?'open':h.status==='failed'?'failed':'resume')}</Text></TouchableOpacity>)}</>:!report?<View style={s.hero}><View style={[s.emblem,{borderColor:colors.accent,backgroundColor:colors.accentSoft}]}><Ionicons name={job.status==='failed'?'alert-outline':'sparkles-outline'} size={34} color={colors.onAccent}/></View>{heading(t(job.status==='failed'?'failed':job.stage))}{job.status==='failed'?<>{body(t(job.refunded?'refunded':'error'))}{button(t('retry'),()=>{setJob(null);setRevision(v=>v+1);})}</>:<>{connectionLost?<View style={card}>{body(t('connectionLost'))}{button(t('refresh'),()=>open(job.id),true)}</View>:<View accessibilityRole="progressbar" accessibilityValue={{min:0,max:100,now:percent}} style={s.progressPanel}><Text style={[s.percentage,{color:colors.primary}]}>{percent}%</Text><ActivityIndicator color={colors.primary} accessibilityLabel={t(job.stage)}/><View style={[s.progressTrack,{backgroundColor:colors.surfaceMuted}]}><View style={[s.progressFill,{backgroundColor:colors.primary,width:`${percent}%`}]}/></View>{body(t('progressNote'))}</View>}{stages.map((stage,i)=><View key={stage} style={[s.step,{borderColor:i<=stages.indexOf(job.stage)?colors.primary:colors.cardBorder}]}><Ionicons name={i<stages.indexOf(job.stage)?'checkmark-circle':'ellipse-outline'} size={20} color={colors.primary}/>{body(t(stage))}</View>)}{body(t('wait'))}</>}</View>:<>
          <Text style={[s.eyebrow,{color:colors.primary}]}>{job.native_name}</Text><Text style={[s.title,{color:colors.text}]}>{report.title}</Text>{body(dates(job.spine.antardasha))}{body(report.overview)}<View style={card}>{heading(t('reelTitle'))}{body(t('reelBody'))}{button(t(reelBusy?'loading':'reelTitle'),openReel,false,reelBusy)}{reelError&&body(t('error'))}</View>{heading(t('timeline'))}
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.chips}>{[{planet:null},...job.spine.pratyantardashas].map((p,i)=><TouchableOpacity key={i} accessibilityRole="button" accessibilityState={{selected:phase===i-1}} onPress={()=>{setPhase(i-1);setExpanded({});}} style={[s.chip,{backgroundColor:phase===i-1?colors.primaryStrong:colors.surface,borderColor:colors.cardBorder}]}><Text style={[s.label,{color:phase===i-1?colors.onPrimary:colors.text}]}>{i?planet(p.planet):t('all')}</Text></TouchableOpacity>)}</ScrollView>
          {period?<View style={card}>{body(dates(job.spine.pratyantardashas[phase]))}{heading(period.summary)}{body(period.what_changes)}{heading(t('timing'))}{body(period.timing_explanation)}</View>:<View style={card}>{heading(t('overview'))}{body(report.mahadasha_context)}{body(report.antardasha_themes)}</View>}
          {heading(t('possibilities'))}{events.map((e,i)=><View style={card} key={`${phase}-${i}`}><Text style={[s.index,{color:colors.primary}]}>{String(i+1).padStart(2,'0')}</Text>{heading(e.theme)}{!!e.circumstances&&body(e.circumstances)}{e.possibilities.map((p,k)=><View style={s.event} key={k}><View style={[s.dot,{backgroundColor:colors.accent}]}/>{body(p)}</View>)}{!!e.timing&&body(e.timing)}<TouchableOpacity accessibilityRole="button" accessibilityState={{expanded:!!expanded[i]}} onPress={()=>toggle(i)} style={s.expand}><Text style={[s.label,{color:colors.primary}]}>{t('why')}</Text><Ionicons name={expanded[i]?'chevron-up':'chevron-down'} color={colors.primary} size={18}/></TouchableOpacity>{expanded[i]&&<>{body(e.why)}{!!e.practical_guidance&&<>{heading(t('guidance'))}{body(e.practical_guidance)}</>}{e.timing_windows?.length>0&&<>{heading(t('timing'))}{e.timing_windows.map((w,k)=><View key={k}>{body(dates(w))}{w.transiting_planet&&body(`${planet(w.transiting_planet)} → ${planet(w.natal_planet)}`)}</View>)}</>}</>}</View>)}
          <View style={card}><TouchableOpacity accessibilityRole="button" accessibilityState={{expanded:!!expanded.evidence}} style={s.expand} onPress={()=>toggle('evidence')}><Text style={[s.label,{color:colors.primary}]}>{t('evidence')}</Text><Ionicons name={expanded.evidence?'chevron-up':'chevron-down'} size={18} color={colors.primary}/></TouchableOpacity>{expanded.evidence&&<>{period&&body(period.conditions_and_cautions)}{(period?.transit_story||report.antardasha_transits||[]).map((e,i)=><View key={i}>{body(e.explanation)}</View>)}</>}</View>{phase===-1&&report.closing&&<View style={card}>{heading(t('guidance'))}{body(report.closing)}</View>}{body(t('note'))}
        </>}
    </ScrollView>
    {report&&reelSource&&<MessageBubble key={reelSource.messageId} reelOnly message={reelSource} language={job.language} reelAutoLaunchMessageId={reelSource.messageId} reelAutoLaunchKey={reelLaunch} reelAutoLaunchLang={job.language}/>}
    <ConfirmCreditsModal visible={confirm} onClose={()=>setConfirm(false)} onConfirm={purchase} title={t(quote?.regenerated_from?'regenerate':'confirm')} description={t(quote?.regenerated_from?'regenerateBody':'confirmBody')} cost={quote?.credit_cost} credits={quote?.credits} confirmLabel={t(quote?.regenerated_from?'regenerate':'create')} iconName="sparkles-outline"/>
  </View>;
}
const s = StyleSheet.create({
  formSection: {gap:layoutTokens.space3},
  choiceCard: {padding:layoutTokens.space4,gap:layoutTokens.space2},
  choiceHeader: {flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:layoutTokens.space3},
  periodMeta: {gap:layoutTokens.space1,marginTop:layoutTokens.space1},
  chapterChoices: {gap:layoutTokens.space3},
  page: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, paddingHorizontal: layoutTokens.space3 },
  headerText: { ...typographyTokens.sectionTitle },
  headerCopy: {flex:1,gap:layoutTokens.space2,paddingVertical:layoutTokens.space3},
  progressPanel: {gap:layoutTokens.space3},
  percentage: {...typographyTokens.title,textAlign:'center'},
  progressTrack: {height:layoutTokens.space2,borderRadius:layoutTokens.radiusPill,overflow:'hidden'},
  progressFill: {height:'100%',borderRadius:layoutTokens.radiusPill},
  icon: { padding: layoutTokens.space4, minHeight: layoutTokens.touchTarget },
  content: { padding: layoutTokens.space4, paddingBottom: layoutTokens.space7, maxWidth: layoutTokens.contentMaxWidth * 1.6, width: '100%', alignSelf: 'center', gap: layoutTokens.space4 },
  hero: { paddingTop: layoutTokens.space3, paddingBottom: layoutTokens.space4, gap: layoutTokens.space3 },
  emblem: { width: layoutTokens.space7 + layoutTokens.space4, height: layoutTokens.space7 + layoutTokens.space4, borderRadius: layoutTokens.radiusPill, borderWidth: 1, alignItems: 'center', justifyContent: 'center', alignSelf: 'center', marginBottom: layoutTokens.space1 },
  eyebrow: { ...typographyTokens.eyebrow },
  title: { ...typographyTokens.title },
  heading: { ...typographyTokens.sectionTitle, marginVertical: 0 },
  body: { ...typographyTokens.bodyMd, flexShrink: 1, marginVertical: 0 },
  label: { ...typographyTokens.label, flexShrink: 1 },
  card: { borderWidth: 1, borderRadius: layoutTokens.radiusLg, padding: layoutTokens.space5, gap: layoutTokens.space2 },
  button: { minHeight: layoutTokens.touchTarget, borderWidth: 1, borderRadius: layoutTokens.radiusMd, padding: layoutTokens.space4, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: layoutTokens.space3, marginVertical: layoutTokens.space3 },
  buttonText: { ...typographyTokens.label, flexShrink: 1 },
  chips: { flexDirection: 'row', gap: layoutTokens.space3, paddingVertical: layoutTokens.space2 },
  chip: { paddingHorizontal: layoutTokens.space4, paddingVertical: layoutTokens.space3, minHeight: layoutTokens.touchTarget, justifyContent: 'center', borderWidth: 1, borderRadius: layoutTokens.radiusPill },
  rule: { height: 1, marginVertical: layoutTokens.space3 },
  step: { flexDirection: 'row', alignItems: 'center', gap: layoutTokens.space3, borderLeftWidth: 2, paddingLeft: layoutTokens.space4 },
  expand: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: layoutTokens.space3, minHeight: layoutTokens.touchTarget },
  event: { flexDirection: 'row', gap: layoutTokens.space3, alignItems: 'flex-start' },
  dot: { width: layoutTokens.space1, height: layoutTokens.space1, borderRadius: layoutTokens.radiusPill, marginTop: layoutTokens.space4 },
  index: { ...typographyTokens.sectionTitle },
});
