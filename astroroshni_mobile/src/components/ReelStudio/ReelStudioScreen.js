import React, { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, Platform, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { ScrollView as GestureScrollView, RefreshControl as GestureRefreshControl } from 'react-native-gesture-handler';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { layoutTokens as space, typographyTokens as type } from '../../theme/tokens';
import api, { chatAPI } from '../../services/api';
import { storage } from '../../services/storage';
import { getEndpoint } from '../../utils/constants';
import { goBackOrHome } from '../../navigation/navHelpers';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import MessageBubble from '../Chat/MessageBubble';
import ReelArtwork from '../ReelArtwork';
import ReelPlayerModal from '../ReelPlayerModal';

// Android nested rows need native gesture arbitration with the vertical page.
const StudioScrollView = Platform.OS === 'android' ? GestureScrollView : ScrollView;
const StudioRefreshControl = Platform.OS === 'android' ? GestureRefreshControl : RefreshControl;

const topics = [
  {id:'know_me',group:'relationships',icon:'heart-outline'},
  {id:'love_me',group:'relationships',icon:'rose-outline'},
  {id:'real_me',group:'identity',icon:'layers-outline'},
  {id:'superpower',group:'identity',icon:'sparkles-outline'},
  {id:'career',group:'careerGroup',icon:'compass-outline'},
  {id:'next_chapter',group:'future',icon:'moon-outline'},
];
const get = path => api.get(getEndpoint(path), {suppressGlobalError:true}).then(r=>r.data);
export default function ReelStudioScreen({navigation}) {
  const {t:i18t,i18n}=useTranslation(), {colors}=useTheme();
  const t=(key,args)=>i18t(`reelStudio.${key}`,args);
  const [native,setNative]=useState(null),[chartId,setChartId]=useState(null),[catalog,setCatalog]=useState(null);
  const [history,setHistory]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState(false),[filter,setFilter]=useState('all');
  const [source,setSource]=useState(null),[launch,setLaunch]=useState(0),[busy,setBusy]=useState(null),[player,setPlayer]=useState(null);
  const lock=useRef(false), sequence=useRef(0);
  const language=i18n.language?.startsWith('hi')?'hi':'en';
  const refreshHistory=useCallback(()=>chatAPI.getReelHistory().then(r=>setHistory(r.data.reels||[])).catch(()=>setError(true)),[]);
  const load=useCallback(async()=>{
    const version=++sequence.current;
    setLoading(true);setError(false);
    try {
      const [chosen,charts,pricing,reels]=await Promise.all([storage.getBirthDetails(),get('/birth-charts'),get('/reel-studio/catalog'),chatAPI.getReelHistory()]);
      if(version!==sequence.current)return;
      const id=chosen?.id||chosen?.birth_chart_id||chosen?._id;
      const owned=(charts.charts||[]).find(r=>String(r.id)===String(id)) || (!id&&chosen&&(charts.charts||[]).find(r=>r.name===chosen.name&&String(r.date).slice(0,10)===String(chosen.date).slice(0,10)&&String(r.time).slice(0,5)===String(chosen.time).slice(0,5)));
      setNative(chosen);setChartId(owned?.id||null);setCatalog(pricing);setHistory(reels.data.reels||[]);
    }catch{if(version===sequence.current){setError(true);setCatalog(null);}}
    finally{if(version===sequence.current)setLoading(false);}
  },[]);
  useFocusEffect(useCallback(()=>{load();return()=>{sequence.current++;};},[load]));
  const selectNative=()=>navigation.navigate('SelectNative',{returnTo:'ReelStudio'});
  const openTopic=async id=>{
    if(lock.current)return;
    if(!chartId){selectNative();return;}
    if(id==='next_chapter'){navigation.navigate('NextChapter');return;}
    const version=sequence.current;
    lock.current=true;setBusy(id);setError(false);
    try{
      const {data}=await api.post(getEndpoint('/reel-studio/sources'),{birth_chart_id:chartId,topic:id},{suppressGlobalError:true});
      if(version!==sequence.current)return;
      setSource({messageId:data.message_id,role:'assistant',content:t(id)});setLaunch(v=>v+1);
    }catch{setError(true);}
    finally{lock.current=false;setBusy(null);}
  };
  const price=id=>!catalog?t('loading'):id==='next_chapter'?t('chapterPrice',{report:catalog.chapter_credit_cost,reel:catalog.pricing.credit_cost}):t('from',{count:catalog.pricing.credit_cost});
  const renderTopic=(topic,featured=false)=><Pressable key={topic.id} accessibilityRole="button" accessibilityLabel={`${t(topic.id)}. ${price(topic.id)}`} disabled={!!busy||!catalog} onPress={()=>openTopic(topic.id)} style={({pressed})=>[s.topic,{backgroundColor:featured?colors.headerSurface:colors.surfaceRaised,borderColor:featured?colors.accent:colors.cardBorder,opacity:pressed?0.85:1}]}>
    <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={s.art}>
      <View style={[s.orbit,{borderColor:colors.accent}]}><Ionicons name={topic.icon} size={28} color={colors.accent}/></View>
      <View style={[s.orbitSmall,{borderColor:colors.accent}]} />
    </View>
    <View style={s.cardCopy}>{featured&&<Text style={[s.eyebrow,s.cardEyebrow,{color:colors.accent}]}>{t('featured')}</Text>}<Text style={[s.eyebrow,s.cardEyebrow,{color:featured?colors.accent:colors.primary}]}>{t(topic.group)}</Text><Text style={[s.cardTitle,{color:featured?colors.textInverse:colors.text}]}>{t(topic.id)}</Text><Text style={[s.body,{color:featured?colors.textInverseMuted:colors.textSecondary}]}>{t(`${topic.id}Hook`)}</Text>
      {topic.id==='next_chapter'&&<Text style={[s.meta,{color:colors.textSecondary}]}>{t('chapterNote')}</Text>}
      <View style={[s.cardFooter,{borderColor:featured?colors.cosmicLine:colors.cardBorder}]}><Text style={[s.price,{color:featured?colors.accent:colors.primary}]}>{price(topic.id)}</Text>{busy===topic.id?<ActivityIndicator color={featured?colors.accent:colors.primary}/>:<Ionicons name="arrow-forward" size={22} color={featured?colors.accent:colors.primary}/>}</View>
    </View>
  </Pressable>;
  const ready=history.filter(r=>r.status==='completed');
  return <View style={[s.page,{backgroundColor:colors.background}]}>
    <SafeAreaView edges={['top']} style={{backgroundColor:colors.headerSurface}}><View style={s.header}>
      <Pressable accessibilityRole="button" accessibilityLabel={t('back')} onPress={()=>goBackOrHome(navigation)} style={s.icon}><Ionicons name="arrow-back" size={22} color={colors.textInverse}/></Pressable>
      <View style={s.flex}><Text style={[s.headerTitle,{color:colors.textInverse}]}>{t('title')}</Text><NativeSelectorChip birthData={native} onPress={selectNative} showIcon={false} textStyle={{color:colors.textInverseMuted}} iconColor={colors.accent} style={{alignSelf:'flex-start',backgroundColor:colors.cosmicRaised,borderColor:colors.cosmicLine}}/></View>
      <Pressable accessibilityRole="button" accessibilityLabel={t('refresh')} onPress={load} style={s.icon}><Ionicons name="refresh-outline" size={22} color={colors.textInverse}/></Pressable>
    </View></SafeAreaView>
    <StudioScrollView nestedScrollEnabled directionalLockEnabled contentContainerStyle={s.content} refreshControl={<StudioRefreshControl refreshing={loading} onRefresh={load} tintColor={colors.primary}/>}>
      <Text style={[s.eyebrow,{color:colors.primary}]}>{t('title')}</Text><Text style={[s.hero,{color:colors.text}]}>{t('hero')}</Text><Text style={[s.body,{color:colors.textSecondary}]}>{t('intro')}</Text>
      {error&&<Pressable accessibilityRole="button" onPress={load} style={[s.notice,{backgroundColor:colors.surfaceMuted}]}><Text style={[s.body,{color:colors.text}]}>{t('error')}</Text><Text style={[s.price,{color:colors.primary}]}>{t('retry')}</Text></Pressable>}
      {!loading&&!chartId&&<Pressable accessibilityRole="button" onPress={selectNative} style={[s.notice,{backgroundColor:colors.accentSoft}]}><Text style={[s.price,{color:colors.primary}]}>{t('choose')} →</Text></Pressable>}
      {renderTopic(topics[0],true)}
      <Text style={[s.section,{color:colors.text}]}>{t('topics')}</Text>
      <StudioScrollView horizontal nestedScrollEnabled directionalLockEnabled style={s.horizontalScroll} showsHorizontalScrollIndicator={false} contentContainerStyle={s.filters}>{['all','relationships','identity','careerGroup','future'].map(group=><Pressable key={group} accessibilityRole="button" accessibilityState={{selected:filter===group}} onPress={()=>setFilter(group)} style={[s.chip,{backgroundColor:filter===group?colors.primary:colors.surfaceRaised,borderColor:colors.cardBorder}]}><Text style={[s.label,{color:filter===group?colors.onPrimary:colors.text}]}>{t(group)}</Text></Pressable>)}</StudioScrollView>
      {topics.filter(item=>filter==='all'||item.group===filter).map(item=>renderTopic(item))}
      <View style={s.sectionRow}><Text style={[s.section,s.flex,{color:colors.text}]}>{t('saved')}</Text><Pressable accessibilityRole="button" onPress={()=>navigation.navigate('ReelHistory')} style={s.icon}><Text style={[s.label,{color:colors.primary}]}>{t('history')}</Text></Pressable></View>
      {!history.length&&<Text style={[s.body,{color:colors.textSecondary}]}>{t('empty')}</Text>}
      <StudioScrollView horizontal nestedScrollEnabled directionalLockEnabled style={s.horizontalScroll} showsHorizontalScrollIndicator={false} contentContainerStyle={s.filters}>{history.slice(0,8).map(item=><Pressable key={item.job_id} accessibilityRole="button" accessibilityLabel={item.question||t('play')} disabled={!!busy} onPress={()=>item.status==='completed'?setPlayer(item.job_id):(setSource({messageId:item.message_id,role:'assistant',content:item.question||t('title')}),setLaunch(v=>v+1))} style={[s.saved,{backgroundColor:colors.surfaceRaised,borderColor:colors.cardBorder}]}><View style={s.cover}><ReelArtwork jobId={item.status==='completed'?item.job_id:null} style={StyleSheet.absoluteFill}/><View style={[s.play,{backgroundColor:colors.primary}]}><Ionicons name={item.status==='completed'?'play':'time-outline'} color={colors.onPrimary} size={20}/></View></View><Text numberOfLines={2} style={[s.label,s.savedCopy,{color:colors.text}]}>{item.question||t('title')}</Text><Text style={[s.meta,s.savedCopy,{color:colors.textSecondary}]}>{t(item.status==='completed'?'play':item.status==='failed'?'failed':'inProgress')}</Text></Pressable>)}</StudioScrollView>
    </StudioScrollView>
    {source&&<MessageBubble key={source.messageId} reelOnly message={source} language={language} reelAutoLaunchMessageId={source.messageId} reelAutoLaunchKey={launch} reelAutoLaunchLang={language} onReelCompleted={refreshHistory}/>}
    {player&&<ReelPlayerModal jobId={player} reels={ready} reelIds={ready.map(r=>r.job_id)} onSwipeToReel={setPlayer} onClose={()=>setPlayer(null)} allowRecreate={false}/>}
  </View>;
}
const s=StyleSheet.create({
  page:{flex:1},flex:{flex:1},header:{flexDirection:'row',alignItems:'center',paddingHorizontal:space.space3,paddingVertical:space.space3,gap:space.space2},headerTitle:{...type.sectionTitle},icon:{minHeight:space.touchTarget,minWidth:space.touchTarget,alignItems:'center',justifyContent:'center'},
  content:{padding:space.space5,gap:space.space4,paddingBottom:space.space7,maxWidth:space.contentMaxWidth*1.6,width:'100%',alignSelf:'center'},eyebrow:{...type.eyebrow},hero:{...type.title},body:{...type.bodyMd},meta:{...type.label},section:{...type.sectionTitle},label:{...type.label},price:{...type.label,flexShrink:1},
  topic:{borderRadius:space.radiusLg,borderWidth:1,overflow:'hidden'},art:{position:'absolute',right:-space.space4,top:-space.space5,width:space.space7*3,height:space.space7*3,alignItems:'center',justifyContent:'center',opacity:0.18},orbit:{width:space.space7*1.5,height:space.space7*1.5,borderRadius:space.radiusPill,borderWidth:1,alignItems:'center',justifyContent:'center',transform:[{rotate:'-12deg'}]},orbitSmall:{position:'absolute',width:space.space7*3,height:space.space7*3,borderWidth:1,borderRadius:space.radiusPill},cardEyebrow:{paddingRight:space.space7},cardCopy:{padding:space.space5,gap:space.space3},cardTitle:{...type.sectionTitle},cardFooter:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',gap:space.space3,borderTopWidth:1,paddingTop:space.space4,marginTop:space.space2},
  horizontalScroll:{flexGrow:0,flexShrink:0,width:'100%'},
  filters:{gap:space.space3},chip:{borderWidth:1,borderRadius:space.radiusPill,paddingHorizontal:space.space4,paddingVertical:space.space3,minHeight:space.touchTarget,justifyContent:'center'},notice:{borderRadius:space.radiusMd,padding:space.space4,gap:space.space2},sectionRow:{flexDirection:'row',alignItems:'center',gap:space.space3},saved:{width:180,borderWidth:1,borderRadius:space.radiusMd,overflow:'hidden',paddingBottom:space.space3},cover:{aspectRatio:9/12},play:{position:'absolute',bottom:space.space3,right:space.space3,borderRadius:space.radiusPill,padding:space.space3},savedCopy:{marginHorizontal:space.space3,marginTop:space.space2},
});
