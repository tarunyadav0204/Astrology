import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Image, ScrollView, StyleSheet, Switch, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useFocusEffect } from '@react-navigation/native';
import { storage } from '../../services/storage';
import { nakshatraBlueprintAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import ConfirmCreditsModal from '../ConfirmCreditsModal';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { exportHtmlAsPdf, PDF_PRINT_STYLES, sharePDFOnWhatsApp, userFacingPdfExportError } from '../../utils/pdfGenerator';

const LIFE_AREA_TITLES = {
  identity: 'Identity', mind: 'Mind & emotions', family: 'Family & wealth', home: 'Home & roots',
  creativity: 'Creativity & children', work: 'Work & wellbeing', partnership: 'Partnership',
  transformation: 'Transformation', dharma: 'Dharma & learning', career: 'Career & purpose',
  gains: 'Gains & community', spirituality: 'Spirituality & rest',
};

const escapeHtml = (value) => String(value || '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));

export default function NakshatraBlueprintScreen({ navigation }) {
  const { colors } = useTheme();
  const { credits, fetchBalance } = useCredits();
  const [birthData, setBirthData] = useState(null);
  const [blueprint, setBlueprint] = useState(null);
  const [pricing, setPricing] = useState(null);
  const [includeImages, setIncludeImages] = useState(false);
  const [accuracy, setAccuracy] = useState(15);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [showCreditConfirmation, setShowCreditConfirmation] = useState(false);
  const [forceRegenerate, setForceRegenerate] = useState(false);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [checkingCache, setCheckingCache] = useState(false);

  const payload = useCallback(() => ({
    birth_data: birthData,
    language: 'english',
    include_images: includeImages,
    birth_time_accuracy_minutes: accuracy,
    force_regenerate: false,
  }), [birthData, includeImages, accuracy]);

  const load = useCallback(async () => {
    const native = await storage.getBirthDetails();
    setBirthData(native);
    setBlueprint(null);
    setForceRegenerate(false);
    if (!native?.date || native?.latitude == null || native?.longitude == null) {
      setLoading(false);
      return;
    }
    try {
      const [price, existing] = await Promise.all([
        nakshatraBlueprintAPI.getPricing(),
        nakshatraBlueprintAPI.findLatestExisting({
          birth_data: native,
          language: 'english',
          include_images: false,
          birth_time_accuracy_minutes: 15,
          force_regenerate: false,
        }),
      ]);
      setPricing(price.data);
      if (existing.data?.exists) {
        setIncludeImages(Boolean(existing.data?.payload?.include_images));
        setAccuracy(existing.data?.payload?.precision?.declared_accuracy_minutes ?? 15);
        setBlueprint(existing.data.payload);
      }
    } catch (_) {
      // The generate action shows the user-facing failure if the service is unavailable.
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  useEffect(() => {
    if (!generating) {
      setGenerationProgress(0);
      return undefined;
    }
    const startedAt = Date.now();
    const startProgress = 5;
    const targetProgress = 90;
    const rampDurationMs = 40_000;
    setGenerationProgress(startProgress);
    const progressTimer = setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const progress = startProgress + ((targetProgress - startProgress) * Math.min(elapsed / rampDurationMs, 1));
      setGenerationProgress(Math.round(progress));
    }, 500);
    return () => clearInterval(progressTimer);
  }, [generating]);

  const generate = async () => {
    if (!birthData) {
      navigation.navigate('BirthForm');
      return;
    }
    if (forceRegenerate) {
      setShowCreditConfirmation(true);
      return;
    }
    setCheckingCache(true);
    try {
      const existing = await nakshatraBlueprintAPI.findExisting(payload());
      if (existing.data?.exists) {
        setBlueprint(existing.data.payload);
        return;
      }
      setShowCreditConfirmation(true);
    } catch (_) {
      // The generation endpoint performs the same cache check, so this only
      // affects the pre-confirmation convenience path.
      setShowCreditConfirmation(true);
    } finally {
      setCheckingCache(false);
    }
  };

  const regenerate = () => {
    // Return to the configuration state first so the user can choose whether
    // this fresh reading includes the four illustration chapters.
    setIncludeImages(Boolean(blueprint?.include_images));
    setBlueprint(null);
    setForceRegenerate(true);
    setGenerationProgress(0);
  };

  const confirmGenerate = async () => {
    setShowCreditConfirmation(false);
    setGenerating(true);
    try {
      const response = await nakshatraBlueprintAPI.generate({ ...payload(), force_regenerate: forceRegenerate });
      setBlueprint(response.data?.payload || null);
      fetchBalance?.();
    } catch (error) {
      Alert.alert('Could not generate Blueprint', error?.response?.data?.detail || 'Please try again. No credits were used if generation did not complete.');
    } finally { setGenerating(false); }
  };

  const generatePdf = async () => {
    if (!blueprint) return;
    setGeneratingPdf(true);
    try {
      const planetSections = (blueprint.reading?.planet_readings || []).map((item) => `<section><h2>${escapeHtml(item.planet)}</h2><p>${escapeHtml(item.signature || item.behaviour)}</p></section>`).join('');
      const lifeSections = (blueprint.reading?.life_areas || []).map((item) => `<section><h2>${escapeHtml(item.title || LIFE_AREA_TITLES[item.key] || item.key)}</h2><p>${escapeHtml(item.reading)}</p></section>`).join('');
      const html = `<!doctype html><html><head><meta charset="utf-8"><style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#20142d;line-height:1.65;padding:26px;background:#fff}.cover{padding:34px 24px;text-align:center;border:2px solid #c79b45;border-radius:22px;background:linear-gradient(145deg,#25133f,#63306d);color:#fff}.eyebrow{color:#f9d88b;font-size:11px;font-weight:800;letter-spacing:1.5px}.cover h1{font-family:Georgia,serif;font-size:36px;margin:14px 0 8px}.cover p{color:#f1e9f2;margin:0}section{margin-top:26px;padding:20px;border:1px solid #eadfea;border-radius:16px;break-inside:avoid}h2{font-family:Georgia,serif;font-size:24px;margin:0 0 10px;color:#542060}h3{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#9a6b23;margin:18px 0 3px}p{margin:0 0 10px}.page-title{font-family:Georgia,serif;font-size:28px;margin:34px 0 0}</style>${PDF_PRINT_STYLES}</head><body><div class="cover"><div class="eyebrow">YOUR STELLAR SIGNATURE</div><h1>Nakshatra Blueprint</h1><p>${escapeHtml(blueprint.native_name || birthData?.name || 'Your natal reading')}</p></div><section><h2>${escapeHtml(blueprint.reading?.headline)}</h2><p>${escapeHtml(blueprint.reading?.opening)}</p></section><div class="page-title">Every graha</div>${planetSections}<div class="page-title">Life areas</div>${lifeSections}</body></html>`;
      const pdfUri = await exportHtmlAsPdf(html, { timeoutMs: 60000 });
      await sharePDFOnWhatsApp(pdfUri, { dialogTitle: 'Share Nakshatra Blueprint PDF' });
    } catch (error) {
      Alert.alert('PDF error', userFacingPdfExportError(error));
    } finally { setGeneratingPdf(false); }
  };

  const reading = blueprint?.reading || {};
  const visualsByKey = (blueprint?.visual_slots || []).reduce((result, visual) => ({ ...result, [visual?.key]: visual }), {});
  const textCost = Number(pricing?.text_cost || 0);
  const illustratedCost = Number(pricing?.illustrated_cost || 0);
  const illustrationAddonCost = Math.max(0, illustratedCost - textCost);
  const generationStatus = generationProgress < 28
    ? 'Preparing your natal chart…'
    : generationProgress < 58
      ? 'Mapping nakshatras, padas and grahas…'
      : generationProgress < 82
        ? 'Writing your life-area chapters…'
        : generationProgress < 90
          ? 'Adding the final synthesis…'
          : 'Painting your celestial chapter images…';
  const renderVisual = (key) => {
    const visual = visualsByKey[key];
    if (!visual?.url || visual.status !== 'ready') return null;
    return <View key={key} style={[styles.visualCard, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}><Image source={{ uri: visual.url }} accessibilityLabel={visual.alt_text} style={styles.visualImage} /><Text style={[styles.visualCaption, { color: colors.textSecondary }]}>{key.replace(/_/g, ' ')}</Text></View>;
  };
  return <View style={[styles.page, { backgroundColor: colors.background }]}><SafeAreaView style={styles.safe}>
    <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}><TouchableOpacity style={styles.headerButton} onPress={() => navigation.goBack()}><Ionicons name="arrow-back" size={21} color={colors.textInverse} /></TouchableOpacity><View style={styles.headerCopy}><Text style={[styles.headerTitle, { color: colors.textInverse }]}>Nakshatra Blueprint</Text><NativeSelectorChip birthData={birthData} onPress={() => navigation.navigate('SelectNative', { returnTo: 'NakshatraBlueprint' })} showIcon={false} style={[styles.headerNativeChip, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} textStyle={{ color: colors.textInverseMuted }} iconColor={colors.accent} /></View><View style={styles.headerActions}>{blueprint ? <><TouchableOpacity style={[styles.headerButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} onPress={generatePdf} disabled={generatingPdf} accessibilityLabel="Generate PDF">{generatingPdf ? <ActivityIndicator size="small" color={colors.accent} /> : <Ionicons name="document-text-outline" size={19} color={colors.textInverse} />}</TouchableOpacity><TouchableOpacity style={[styles.headerButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} onPress={regenerate} accessibilityLabel="Regenerate Blueprint"><Ionicons name="refresh-outline" size={19} color={colors.textInverse} /></TouchableOpacity></> : null}</View></View>
    <ScrollView contentContainerStyle={styles.content}>
      <View style={[styles.hero, { backgroundColor: colors.surfaceInverse }]}><Text style={[styles.kicker, { color: colors.accent }]}>YOUR STELLAR SIGNATURE</Text><Text style={[styles.title, { color: colors.textInverse }]}>Nakshatra Blueprint</Text><Text style={[styles.subtitle, { color: colors.textInverseMuted }]}>A complete behavioural reading of every graha, every life area, and the finer pada layer.</Text></View>
      {loading ? <ActivityIndicator color={colors.primary} /> : !birthData ? <TouchableOpacity onPress={() => navigation.navigate('BirthForm')}><Text style={[styles.action, { color: colors.onPrimary, backgroundColor: colors.primary }]}>Add birth details</Text></TouchableOpacity> : !blueprint ? <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}><Text style={[styles.cardTitle, { color: colors.text }]}>{forceRegenerate ? 'Regenerate your Blueprint' : 'Choose your Blueprint'}</Text><Text style={[styles.copy, { color: colors.textSecondary }]}>{forceRegenerate ? 'Choose the edition for this fresh reading. It will be charged again at the displayed price.' : 'Pada-level detail depends on precise birth time.'}</Text><View style={[styles.illustrationOption, { borderColor: includeImages ? colors.primary : colors.cardBorder, backgroundColor: includeImages ? colors.accentSoft : colors.surfaceMuted }]}><View style={styles.illustrationOptionCopy}><Text style={[styles.illustrationOptionTitle, { color: colors.text }]}>Illustrated Blueprint</Text><Text style={[styles.illustrationOptionBody, { color: colors.textSecondary }]}>Adds four celestial life-scene artworks to the written reading.</Text><Text style={[styles.illustrationOptionPrice, { color: colors.primary }]}>{illustrationAddonCost > 0 ? `+${illustrationAddonCost} credits · ${illustratedCost} credits total` : illustratedCost > 0 ? `${illustratedCost} credits total` : 'Price loads from Credits Management'}</Text></View><Switch value={includeImages} onValueChange={setIncludeImages} accessibilityLabel="Add illustrations to Nakshatra Blueprint" /></View><Text style={[styles.copy, { color: colors.textSecondary }]}>Time accuracy</Text><View style={styles.choices}>{[0,15,60].map(v => <TouchableOpacity key={v} onPress={() => setAccuracy(v)}><Text style={[styles.chip, { color: accuracy === v ? colors.onPrimary : colors.text, backgroundColor: accuracy === v ? colors.primary : colors.surfaceMuted }]}>{v === 0 ? 'Exact' : `±${v} min`}</Text></TouchableOpacity>)}</View>{generating ? <View style={[styles.progressCard, { backgroundColor: colors.accentSoft, borderColor: colors.primary }]}><View style={styles.progressHeader}><Text style={[styles.progressTitle, { color: colors.text }]}>{forceRegenerate ? 'Regenerating your Blueprint' : 'Creating your Blueprint'}</Text><Text style={[styles.progressPercent, { color: colors.primary }]}>{generationProgress}%</Text></View><Text style={[styles.progressStatus, { color: colors.textSecondary }]}>{generationStatus}</Text><View style={[styles.progressTrack, { backgroundColor: colors.surfaceMuted }]}><View style={[styles.progressFill, { backgroundColor: colors.primary, width: `${generationProgress}%` }]} /></View><Text style={[styles.progressNote, { color: colors.textSecondary }]}>This can take a minute. Please keep this screen open.</Text></View> : <TouchableOpacity disabled={checkingCache} onPress={generate}><Text style={[styles.action, { color: colors.onPrimary, backgroundColor: colors.primary }]}>{checkingCache ? 'Checking your saved Blueprint…' : `${forceRegenerate ? 'Regenerate' : 'Generate'} ${includeImages ? 'Illustrated ' : ''}Blueprint · ${includeImages ? illustratedCost || '—' : textCost || '—'} credits`}</Text></TouchableOpacity>}</View> : <>
        <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}><Text style={[styles.headline, { color: colors.text }]}>{reading.headline}</Text><Text style={[styles.copy, { color: colors.textSecondary }]}>{reading.opening}</Text><Text style={[styles.precision, { color: colors.primary }]}>{blueprint.precision?.message}</Text></View>
        <Text style={[styles.section, { color: colors.text }]}>Your life areas</Text>{(reading.life_areas || []).map((item) => <React.Fragment key={item.key}><View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}><Text style={[styles.cardTitle, { color: colors.text }]}>{item.title || LIFE_AREA_TITLES[item.key] || item.key}</Text><Text style={[styles.copy, { color: colors.textSecondary }]}>{item.reading}</Text>{item.alignment ? <View style={[styles.alignmentBox, { backgroundColor: colors.accentSoft, borderColor: colors.selectionBorder || colors.cardBorder }]}><Text style={[styles.alignmentLabel, { color: colors.onAccent || colors.text }]}>ALIGN WITH THIS ENERGY</Text><Text style={[styles.alignmentText, { color: colors.onAccent || colors.text }]}>{item.alignment}</Text></View> : null}</View>{item.key === 'identity' ? renderVisual('identity_foundation') : null}{item.key === 'mind' ? renderVisual('inner_nature') : null}{item.key === 'home' ? renderVisual('relationships_and_home') : null}{item.key === 'career' ? renderVisual('vocation_and_abundance') : null}</React.Fragment>)}
        <Text style={[styles.section, { color: colors.text }]}>Planetary Nakshatra signatures</Text><Text style={[styles.remediesIntro, { color: colors.textSecondary }]}>A concise reference for the instinct each graha brings to your life.</Text>{(reading.planet_readings || []).map((item) => <View key={item.planet} style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}><Text style={[styles.cardTitle, { color: colors.text }]}>{item.planet}</Text><Text style={[styles.copy, { color: colors.textSecondary }]}>{item.signature || item.behaviour}</Text></View>)}
        {(reading.nakshatra_remedies || []).length ? <><Text style={[styles.section, { color: colors.text }]}>Nakshatra remedies</Text><Text style={[styles.remediesIntro, { color: colors.textSecondary }]}>Gentle practices to consciously work with the Nakshatra energies active in your chart.</Text>{reading.nakshatra_remedies.map((remedy, index) => <View key={`${remedy.nakshatra}-${index}`} style={[styles.remedyCard, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}><Text style={[styles.remedyNakshatra, { color: colors.primary }]}>{remedy.nakshatra}</Text>{remedy.life_area ? <View style={[styles.remedyArea, { backgroundColor: colors.accentSoft }]}><Text style={[styles.remedyAreaText, { color: colors.primary }]}>Supports: {remedy.life_area}</Text></View> : null}<Text style={[styles.remedyPractice, { color: colors.text }]}>{remedy.practice}</Text><Text style={[styles.remedyPurpose, { color: colors.textSecondary }]}>{remedy.purpose}</Text></View>)}</> : null}
      </>}
    </ScrollView>
    <ConfirmCreditsModal
      visible={showCreditConfirmation}
      onClose={() => setShowCreditConfirmation(false)}
      onConfirm={confirmGenerate}
      title={forceRegenerate ? 'Regenerate Nakshatra Blueprint?' : (includeImages ? 'Generate Illustrated Blueprint?' : 'Generate Nakshatra Blueprint?')}
      description={forceRegenerate
        ? `This creates a new ${includeImages ? 'illustrated ' : ''}reading and charges the full configured price again. Credits are deducted only after it is generated successfully.`
        : (includeImages ? 'Your complete written Blueprint, with celestial artwork in selected chapters. Credits are deducted only after it is generated successfully.' : 'Your complete written reading of every graha, nakshatra, pada and life area. Credits are deducted only after it is generated successfully.')}
      cost={includeImages ? illustratedCost : textCost}
      credits={credits}
      confirmLabel={forceRegenerate ? 'Regenerate' : 'Generate Blueprint'}
      iconName="sparkles-outline"
    />
  </SafeAreaView></View>;
}

const styles = StyleSheet.create({ page:{flex:1}, safe:{flex:1}, header:{minHeight:70,flexDirection:'row',alignItems:'center',paddingHorizontal:10,borderBottomWidth:StyleSheet.hairlineWidth},headerButton:{width:40,height:40,borderRadius:14,borderWidth:1,alignItems:'center',justifyContent:'center'},headerCopy:{flex:1,alignItems:'center',justifyContent:'center',gap:3,minWidth:0},headerTitle:{fontSize:16,fontWeight:'800'},headerNativeChip:{minHeight:26,paddingVertical:1,paddingHorizontal:9,borderRadius:13,maxWidth:160,elevation:0,shadowOpacity:0},headerActions:{width:88,flexDirection:'row',justifyContent:'flex-end',gap:6},content:{padding:16,gap:14,paddingBottom:42},hero:{padding:24,borderRadius:24,gap:8},kicker:{fontWeight:'900',fontSize:11,letterSpacing:1.4},title:{fontSize:29,fontWeight:'900'},subtitle:{fontSize:14,lineHeight:20},card:{padding:18,borderRadius:18,borderWidth:1,gap:8},cardTitle:{fontSize:18,fontWeight:'800'},headline:{fontSize:24,fontWeight:'900'},copy:{fontSize:14,lineHeight:21},precision:{fontSize:13,lineHeight:19,fontWeight:'700',marginTop:6},alignmentBox:{borderWidth:1,borderRadius:12,padding:12,marginTop:6,gap:4},alignmentLabel:{fontSize:10,fontWeight:'900',letterSpacing:.9},alignmentText:{fontSize:13,lineHeight:19,fontWeight:'600'},remediesIntro:{fontSize:13,lineHeight:19,marginTop:-7},remedyCard:{padding:16,borderRadius:16,borderWidth:1,gap:6},remedyNakshatra:{fontSize:11,fontWeight:'900',letterSpacing:1,textTransform:'uppercase'},remedyArea:{alignSelf:'flex-start',borderRadius:999,paddingHorizontal:9,paddingVertical:4},remedyAreaText:{fontSize:11,fontWeight:'800'},remedyPractice:{fontSize:16,lineHeight:22,fontWeight:'800'},remedyPurpose:{fontSize:13,lineHeight:19},row:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',marginVertical:4},illustrationOption:{flexDirection:'row',alignItems:'center',gap:12,borderWidth:1,borderRadius:14,padding:13,marginTop:3},illustrationOptionCopy:{flex:1,minWidth:0,gap:3},illustrationOptionTitle:{fontSize:15,fontWeight:'800'},illustrationOptionBody:{fontSize:12,lineHeight:17},illustrationOptionPrice:{fontSize:12,lineHeight:17,fontWeight:'800',marginTop:2},choices:{flexDirection:'row',gap:8},chip:{paddingHorizontal:11,paddingVertical:8,borderRadius:16,fontWeight:'700'},progressCard:{borderWidth:1,borderRadius:14,padding:14,marginTop:10,gap:8},progressHeader:{flexDirection:'row',alignItems:'center',justifyContent:'space-between'},progressTitle:{fontSize:15,fontWeight:'800'},progressPercent:{fontSize:14,fontWeight:'900'},progressStatus:{fontSize:13,lineHeight:18},progressTrack:{height:8,borderRadius:999,overflow:'hidden',marginTop:2},progressFill:{height:'100%',borderRadius:999},progressNote:{fontSize:11,lineHeight:16},visualCard:{borderWidth:1,borderRadius:18,overflow:'hidden'},visualImage:{width:'100%',aspectRatio:1},visualCaption:{fontSize:11,fontWeight:'800',letterSpacing:1,textTransform:'uppercase',paddingHorizontal:13,paddingVertical:10},action:{textAlign:'center',overflow:'hidden',padding:14,borderRadius:14,fontWeight:'900',marginTop:10},section:{fontSize:20,fontWeight:'900',marginTop:8},label:{fontSize:12,textTransform:'uppercase',fontWeight:'900',marginTop:5} });
