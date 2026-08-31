import React, { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, Alert, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { useTranslation } from 'react-i18next';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import api, { creditAPI } from '../../services/api';
import { getEndpoint } from '../../utils/constants';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import AppAlertModal from '../Common/AppAlertModal';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useAuthGate } from '../../auth/AuthGateContext';

const TABS = [['pillars', 'Pillars + Safety'], ['dossier', 'Maraka Dossier'], ['timeline', 'Time-Windows']];
const SUBJECTS = [['self', 'Native'], ['mother', 'Mother'], ['father', 'Father']];
const monthYear = (value) => {
  const [year, month] = String(value).split('-').map(Number);
  return `${new Date(year, month - 1).toLocaleString('en', { month: 'short' })} ${year}`;
};

export default function LongevityScreen({ navigation }) {
  useAnalytics('LongevityScreen');
  const { t } = useTranslation();
  const { colors } = useTheme();
  const { requireAuthForPaid } = useAuthGate();
  const [birthData, setBirthData] = useState(null);
  const [result, setResult] = useState(null);
  const [tab, setTab] = useState('pillars');
  const [subject, setSubject] = useState('self');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [checkingLicense, setCheckingLicense] = useState(false);
  const [showLicenseModal, setShowLicenseModal] = useState(false);
  const [licensePrice, setLicensePrice] = useState('₹100/month');
  const checkingLicenseRef = useRef(false);

  const calculate = useCallback(async () => {
    if (checkingLicenseRef.current) return;
    const authenticated = await requireAuthForPaid({
      feature: 'Longevity Inspector',
      message: 'Sign in to access this professional Ayurdaya workspace.',
      resume: { resumeRoute: 'Longevity', resumeParams: {} },
    });
    if (!authenticated) {
      setLoading(false);
      return;
    }

    checkingLicenseRef.current = true;
    setCheckingLicense(true);
    try {
      const { data } = await creditAPI.getEntitlements();
      if (!data?.is_astrologer_licensed) {
        try {
          const catalog = Platform.OS === 'android'
            ? await creditAPI.getSubscriptionPlans()
            : await creditAPI.getRazorpaySubscriptionPlans();
          const plans = catalog?.data?.plans || [];
          const plan = plans.find((item) =>
            item.subscription_family === 'astrologer'
            || item.entitlement_key === 'astrologer_tools'
            || item.google_play_product_id === 'astrologer_license_monthly'
            || item.product_id === 'astrologer_license_monthly'
          );
          const livePrice = plan?.formatted_price || plan?.amount_display;
          setLicensePrice(livePrice ? `${livePrice}/month` : '₹100/month');
        } catch (_) {
          setLicensePrice('₹100/month');
        }
        setShowLicenseModal(true);
        setLoading(false);
        return;
      }
    } catch (licenseError) {
      if (licenseError?.response?.status === 403) {
        setShowLicenseModal(true);
      } else {
        Alert.alert('Could not check access', 'Please check your connection and try again.');
      }
      setLoading(false);
      return;
    } finally {
      checkingLicenseRef.current = false;
      setCheckingLicense(false);
    }

    const birth = await storage.getBirthDetails();
    if (!birth?.name) {
      navigation.replace('BirthProfileIntro', { returnTo: 'Longevity' });
      return;
    }
    setBirthData(birth);
    setLoading(true);
    setError('');
    try {
      const response = await api.post(getEndpoint('/longevity/calculate'), {
        birth_data: birth,
        horizon_years: 12,
        subject,
      });
      setResult(response.data?.result);
    } catch (requestError) {
      const detail = requestError?.response?.data?.detail;
      if (requestError?.response?.status === 403 && detail?.code === 'ASTROLOGER_LICENSE_REQUIRED') {
        setResult(null);
        setShowLicenseModal(true);
      } else {
        setError(typeof detail === 'string' ? detail : detail?.message || 'Unable to complete the longevity calculation.');
      }
    } finally {
      setLoading(false);
    }
  }, [navigation, requireAuthForPaid, subject]);

  useFocusEffect(useCallback(() => { calculate(); }, [calculate]));

  const cardStyle = [styles.card, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }];
  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]}>
      <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity style={styles.headerButton} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { color: colors.textInverse }]}>Longevity Inspector</Text>
          {birthData && (
            <NativeSelectorChip
              birthData={birthData}
              showIcon={false}
              onPress={() => navigation.navigate('SelectNative', { returnTo: 'Longevity' })}
              style={[
                styles.headerNativeChip,
                {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  borderColor: colors.cosmicLine || colors.cardBorder,
                },
              ]}
              textStyle={{ color: colors.textInverse }}
              iconColor={colors.textInverseMuted || colors.textInverse}
            />
          )}
        </View>
        <TouchableOpacity style={styles.headerButton} onPress={calculate}>
          {checkingLicense
            ? <ActivityIndicator size="small" color={colors.textInverse} />
            : <Ionicons name="refresh" size={20} color={colors.textInverse} />}
        </TouchableOpacity>
      </View>

      {birthData && <View style={[styles.subjectWrap, { backgroundColor: colors.surfaceRaised, borderBottomColor: colors.cardBorder }]}> 
        <Text style={[styles.subjectHint, { color: colors.textSecondary }]}>Derived from this native chart</Text>
        <View style={[styles.subjectSwitch, { backgroundColor: colors.surface }]}> 
          {SUBJECTS.map(([id, label]) => <TouchableOpacity key={id} accessibilityRole="button" accessibilityState={{ selected: subject === id }} onPress={() => { setSubject(id); setTab('pillars'); }} style={[styles.subjectButton, subject === id && { backgroundColor: colors.primary }]}><Text style={[styles.subjectButtonText, { color: subject === id ? colors.onPrimary : colors.textSecondary }]}>{label}</Text></TouchableOpacity>)}
        </View>
      </View>}

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.centerText, { color: colors.textSecondary }]}>Calculating D3, D9, Shadbala, Ashtakavarga and dashas…</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Calculator unavailable</Text>
          <Text style={[styles.centerText, { color: colors.textSecondary }]}>{error}</Text>
          <TouchableOpacity style={[styles.retry, { backgroundColor: colors.primary }]} onPress={calculate}><Text style={styles.retryText}>Try again</Text></TouchableOpacity>
        </View>
      ) : result ? (
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <View style={[styles.verdict, { backgroundColor: colors.cosmicSurface || colors.headerSurface, borderColor: colors.cosmicLine || colors.cardBorder }]}> 
            <Text style={[styles.verdictEyebrow, { color: colors.accent || colors.textInverse }]}>{subject === 'self' ? 'CALCULATED LIFESPAN COMPARTMENT' : `DERIVED ${result.subject.label.toUpperCase()} VITALITY SUPPORT`}</Text>
            <Text style={[styles.verdictTitle, { color: colors.textInverse }]}>{result.verdict.compartment.label}</Text>
            <Text style={[styles.verdictRange, { color: colors.textInverse }]}>{subject === 'self' ? `${result.verdict.compartment.range} years · baseline ${result.verdict.compartment.baseline_window.join('–')}` : result.verdict.compartment.interpretation}</Text>
            {result.verdict.compartment.age_validation?.reconciled && <Text style={[styles.verdictRange, { color: colors.textInverse }]}>Age reconciliation · {result.verdict.compartment.age_validation.reason}</Text>}
            <View style={[styles.verdictMetrics, { borderTopColor: colors.cardBorder }]}>
              <View style={styles.metric}><Text style={[styles.metricLabel, { color: colors.textInverse }]}>{result.subject.label} vector</Text><Text style={[styles.metricValue, { color: colors.textInverse }]}>{result.verdict.primary_threat.planet} · {result.verdict.primary_threat.score}</Text></View>
              <View style={styles.metric}><Text style={[styles.metricLabel, { color: colors.textInverse }]}>Current {result.subject.label.toLowerCase()} vulnerability</Text><Text style={[styles.metricValue, { color: colors.textInverse }]}>{result.verdict.current_vulnerability.label} · {result.verdict.current_vulnerability.score}</Text></View>
            </View>
          </View>

          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabs}>
            {TABS.map(([id, label]) => (
              <TouchableOpacity key={id} onPress={() => setTab(id)} style={[styles.tab, { backgroundColor: tab === id ? colors.accentSoft : colors.surfaceRaised, borderColor: tab === id ? colors.primary : colors.cardBorder }]}>
                <Text style={{ color: tab === id ? colors.primary : colors.textSecondary, fontWeight: '800' }}>{label}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {tab === 'pillars' && result.pillars.map((pillar, index) => (
            <View style={cardStyle} key={pillar.id}>
              <Text style={[styles.eyebrow, { color: colors.primary }]}>0{index + 1} · {pillar.title}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{pillar.verdict}</Text>
              <Text style={[styles.body, { color: colors.textSecondary }]}>{pillar.detail}</Text>
              {pillar.pairs?.map((pair) => (
                <View style={[styles.pairRow, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]} key={pair.label}>
                  <View style={styles.grow}><Text style={[styles.rowTitle, { color: colors.text }]}>{pair.label}</Text><Text style={[styles.small, { color: colors.textSecondary }]}>{pair.left.sign} ({pair.left.nature}) + {pair.right.sign} ({pair.right.nature})</Text></View>
                  <Text style={[styles.rowScore, { color: colors.primary }]}>{pair.verdict}</Text>
                </View>
              ))}
              {pillar.metrics && Object.entries(pillar.metrics).filter(([, value]) => value !== null && typeof value !== 'object').map(([key, value]) => (
                <View style={[styles.pairRow, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]} key={key}>
                  <Text style={[styles.small, styles.grow, { color: colors.textSecondary }]}>{key.replaceAll('_', ' ')}</Text>
                  <Text style={[styles.rowScore, { color: colors.primary }]}>{String(value)}</Text>
                </View>
              ))}
              {pillar.modifications?.rules?.map((rule) => (
                <View style={[styles.pairRow, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]} key={rule.id}>
                  <View style={styles.grow}>
                    <Text style={[styles.rowTitle, { color: colors.text }]}>{rule.effect === 'vriddhi' ? 'Kakshya Vriddhi' : 'Kakshya Hrasa'}</Text>
                    <Text style={[styles.small, { color: colors.textSecondary }]}>{rule.evidence}</Text>
                    <Text style={[styles.reason, { color: colors.textSecondary }]}>Requirement: {rule.requirement}</Text>
                    <Text style={[styles.reason, { color: colors.textSecondary }]}>{rule.status_explanation}</Text>
                    {rule.calculated_effect && <Text style={[styles.reason, { color: colors.textSecondary }]}>Calculated effect: {rule.calculated_effect}</Text>}
                    {rule.final_verdict_effect && <Text style={[styles.reason, { color: colors.textSecondary }]}>Final verdict: {rule.final_verdict_effect}</Text>}
                  </View>
                  <Text style={[styles.rowScore, { color: rule.applied && rule.used_in_final_verdict !== false ? colors.primary : colors.textSecondary }]}>{rule.applied ? rule.used_in_final_verdict === false ? 'APPLIED · EXCLUDED' : 'APPLIED' : 'NOT APPLIED'}</Text>
                </View>
              ))}
            </View>
          ))}

          {tab === 'pillars' && result.safeguards && (
            <View style={cardStyle}>
              <Text style={[styles.eyebrow, { color: colors.primary }]}>04 · CLASSICAL SOURCE AUDIT</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{result.safeguards.title || 'BPHS early-life cancellation audit'}</Text>
              <Text style={[styles.body, { color: colors.textSecondary }]}>{result.safeguards.summary}</Text>
              {result.safeguards.interpretation && <Text style={[styles.reason, { color: colors.textSecondary }]}>{result.safeguards.interpretation}</Text>}
              {result.safeguards.rules.map((rule) => <View style={[styles.pairRow, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]} key={rule.id}>
                <View style={styles.grow}>
                  <Text style={[styles.rowTitle, { color: colors.text }]}>{rule.label || rule.id.replaceAll('_', ' ')}</Text>
                  <Text style={[styles.small, { color: colors.textSecondary }]}>{rule.requirement || rule.evidence}</Text>
                  {rule.condition_checks?.map((check) => <Text style={[styles.reason, { color: colors.textSecondary }]} key={check.label}>{check.passed ? '✓ Passed' : '✗ Failed'} · {check.label}. {check.detail}</Text>)}
                </View>
                <Text style={[styles.rowScore, { color: rule.applied ? colors.primary : colors.textSecondary }]}>{rule.status === 'partially_satisfied' ? 'PARTIAL' : rule.applied ? 'FULL' : 'NOT MET'}</Text>
              </View>)}
              {result.safeguards.classification_policy && <Text style={[styles.reason, { color: colors.textSecondary }]}>{result.safeguards.classification_policy}</Text>}
            </View>
          )}

          {tab === 'dossier' && (
            <>
              <View style={cardStyle}>
                <Text style={[styles.eyebrow, { color: colors.primary }]}>MRITYU STHANA STRENGTH</Text>
                <Text style={[styles.sectionTitle, { color: colors.text }]}>Ranked crisis grahas</Text>
                {result.maraka_dossier.ranked_planets.map((planet, index) => (
                  <View style={[styles.rankRow, { borderTopColor: colors.cardBorder }]} key={planet.planet}>
                    <Text style={[styles.rank, { backgroundColor: colors.primary, color: colors.onPrimary }]}>#{index + 1}</Text>
                    <View style={styles.grow}><Text style={[styles.rowTitle, { color: colors.text }]}>{planet.planet}</Text><Text style={[styles.small, { color: colors.textSecondary }]}>{planet.sign} · {subject === 'self' ? `H${planet.house}` : `derived H${planet.house} · native H${planet.native_house}`} · {planet.longitude}</Text><Text style={[styles.reason, { color: colors.textSecondary }]}>{planet.factors.join(' · ')}</Text></View>
                    <Text style={[styles.bigScore, { color: colors.primary }]}>{planet.score}</Text>
                  </View>
                ))}
              </View>
              <View style={cardStyle}>
                <Text style={[styles.eyebrow, { color: colors.primary }]}>SENSITIVE COORDINATES</Text>
                {Object.entries(result.maraka_dossier.sensitive_points).map(([key, point]) => (
                  <View style={[styles.pointRow, { borderTopColor: colors.cardBorder }]} key={key}>
                    <Text style={[styles.pointLabel, { color: colors.textSecondary }]}>{key.replaceAll('_', ' ')}</Text>
                    <Text style={[styles.rowTitle, { color: colors.text }]}>{point.planet || point.lord} {point.sign ? `· ${point.sign}` : ''}</Text>
                  </View>
                ))}
              </View>
            </>
          )}

          {tab === 'timeline' && (
            <View style={cardStyle}>
              <Text style={[styles.eyebrow, { color: colors.primary }]}>VIMSHOTTARI × SHOOLA × TRANSIT</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Next 12 years</Text>
              {result.crisis_windows.map((window) => (
                <View style={[styles.windowRow, { borderTopColor: colors.cardBorder }]} key={`${window.start_date}-${window.antardasha}`}>
                  <View style={[styles.dot, { backgroundColor: window.level === 'critical' ? colors.error : ['moderate', 'transformative'].includes(window.level) ? colors.warning : colors.success }]} />
                    <View style={styles.grow}><Text style={[styles.rowTitle, { color: colors.text }]}>{monthYear(window.start_date)} — {monthYear(window.end_date)}</Text><Text style={[styles.small, { color: colors.textSecondary }]}>{window.mahadasha}–{window.antardasha} · {window.label}</Text><Text style={[styles.small, { color: colors.textSecondary }]}>{window.khanda_boundary?.status === 'not_applicable' ? 'Parent Khanda not calculated from the child’s age' : `Convergence ${window.convergence?.confirmed_systems || 0}/3 · Khanda ${window.khanda_boundary?.status}`}</Text><Text style={[styles.reason, { color: colors.textSecondary }]}>{window.reasons.join(' · ')}</Text></View>
                  <Text style={[styles.bigScore, { color: colors.primary }]}>{window.convergence?.confirmed_systems || 0}/3</Text>
                </View>
              ))}
            </View>
          )}

          <View style={[styles.disclaimer, { backgroundColor: colors.accentSoft, borderLeftColor: colors.warning }]}>
            <Text style={[styles.disclaimerTitle, { color: colors.text }]}>Vigilance, not a fate verdict</Text>
            <Text style={[styles.small, { color: colors.textSecondary }]}>{result.disclaimer}</Text>
          </View>
        </ScrollView>
      ) : null}

      <AppAlertModal
        visible={showLicenseModal}
        variant="info"
        icon="school-outline"
        title={t('premiumUi.chart.licenseRequired')}
        message={`Longevity Inspector is a professional calculation workspace. An active Astrologer License (${licensePrice}) is required.`}
        primaryText={t('premiumUi.chart.viewPlan')}
        secondaryText={t('common.notNow')}
        onPrimaryPress={() => {
          setShowLicenseModal(false);
          navigation.navigate('Credits', {
            focusSubscriptionFamily: 'astrologer',
            returnTo: 'Longevity',
          });
        }}
        onSecondaryPress={() => {
          setShowLicenseModal(false);
          navigation.goBack();
        }}
        onRequestClose={() => {
          setShowLicenseModal(false);
          navigation.goBack();
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen:{flex:1},header:{height:72,flexDirection:'row',alignItems:'center',borderBottomWidth:1,paddingHorizontal:12},headerButton:{width:42,height:42,alignItems:'center',justifyContent:'center'},headerCenter:{flex:1,alignItems:'center',justifyContent:'center',gap:4},headerTitle:{fontSize:17,fontWeight:'900'},headerNativeChip:{minHeight:28,paddingVertical:2,paddingHorizontal:11,borderRadius:14,elevation:0,shadowOpacity:0,maxWidth:180},subjectWrap:{paddingHorizontal:14,paddingVertical:11,borderBottomWidth:1},subjectHint:{fontSize:10,fontWeight:'700',marginBottom:7,textTransform:'uppercase',letterSpacing:.5},subjectSwitch:{flexDirection:'row',padding:3,borderRadius:12},subjectButton:{flex:1,alignItems:'center',paddingVertical:8,borderRadius:9},subjectButtonText:{fontSize:12,fontWeight:'900'},center:{flex:1,alignItems:'center',justifyContent:'center',padding:30,gap:14},centerText:{textAlign:'center',fontSize:13,lineHeight:19},retry:{paddingVertical:11,paddingHorizontal:22,borderRadius:22},retryText:{color:'#fff',fontWeight:'800'},content:{padding:14,paddingBottom:50},verdict:{borderWidth:1,borderRadius:22,padding:23},verdictEyebrow:{color:'#d4b477',fontSize:10,fontWeight:'900',letterSpacing:1.2},verdictTitle:{color:'#fff',fontFamily:'Georgia',fontSize:40,fontWeight:'700',marginTop:7},verdictRange:{color:'#c8dad0',fontSize:13},verdictMetrics:{flexDirection:'row',gap:12,borderTopWidth:1,borderTopColor:'rgba(255,255,255,.16)',paddingTop:17,marginTop:22},metric:{flex:1},metricLabel:{color:'#b6c8be',fontSize:9,textTransform:'uppercase'},metricValue:{color:'#fff',fontSize:12,fontWeight:'800',marginTop:4},tabs:{gap:8,paddingVertical:15},tab:{borderWidth:1,borderRadius:22,paddingVertical:9,paddingHorizontal:14},card:{borderWidth:1,borderRadius:18,padding:17,marginBottom:12},eyebrow:{fontSize:10,fontWeight:'900',letterSpacing:1},sectionTitle:{fontFamily:'Georgia',fontSize:24,fontWeight:'700',marginVertical:6},body:{fontSize:13,lineHeight:19},pairRow:{flexDirection:'row',alignItems:'center',borderWidth:1,borderRadius:12,padding:11,marginTop:8,gap:8},grow:{flex:1},rowTitle:{fontSize:14,fontWeight:'800'},small:{fontSize:11,lineHeight:16},rowScore:{fontSize:11,fontWeight:'900'},rankRow:{flexDirection:'row',alignItems:'flex-start',gap:9,borderTopWidth:1,paddingVertical:12},rank:{fontSize:9,fontWeight:'900',paddingVertical:5,paddingHorizontal:6,borderRadius:10,overflow:'hidden'},reason:{fontSize:10,lineHeight:14,marginTop:4},bigScore:{fontSize:18,fontWeight:'900'},pointRow:{borderTopWidth:1,paddingVertical:11,gap:3},pointLabel:{fontSize:9,textTransform:'uppercase',letterSpacing:.7},windowRow:{flexDirection:'row',alignItems:'flex-start',gap:9,borderTopWidth:1,paddingVertical:13},dot:{width:9,height:9,borderRadius:5,marginTop:5},disclaimer:{borderLeftWidth:3,borderRadius:10,padding:13},disclaimerTitle:{fontSize:13,fontWeight:'900',marginBottom:4}
});
