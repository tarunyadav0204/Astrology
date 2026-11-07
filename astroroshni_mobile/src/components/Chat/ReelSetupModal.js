import React, { useEffect, useRef, useState } from 'react';
import { Modal, View, Text, Pressable, ScrollView, Switch, ActivityIndicator, StyleSheet } from 'react-native';
import { useTranslation } from 'react-i18next';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { chatAPI } from '../../services/api';

export default function ReelSetupModal({ visible, initialLanguage = 'en', initialDuration = 90, recreating, colors, onClose, onCreate, onBuyCredits }) {
  const { t } = useTranslation();
  const [language, setLanguage] = useState(initialLanguage);
  const [duration, setDuration] = useState(initialDuration);
  const [presenter, setPresenter] = useState(false);
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const languageTouched = useRef(false);
  const submitted = useRef(false);
  useEffect(() => {
    if (!visible) return;
    let active = true;
    submitted.current = false; languageTouched.current = false;
    setLanguage(initialLanguage); setDuration(initialDuration); setPresenter(false);
    AsyncStorage.getItem('reelLanguage').then((saved) => {
      if (active && !languageTouched.current && ['en', 'hi'].includes(saved)) setLanguage(saved);
    }).catch(() => {});
    return () => { active = false; };
  }, [visible, initialLanguage, initialDuration]);
  useEffect(() => {
    if (!visible) return;
    let active = true;
    setQuote(null); setError(false);
    chatAPI.getReelPricing(duration, presenter).then(({ data }) => {
      if (active && Number.isFinite(data?.credit_cost) && Number.isFinite(data?.credits) && (!presenter || data.presenter_enabled === true)) setQuote({ ...data, duration, presenter });
      else if (active) setError(true);
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [visible, duration, presenter, retry]);
  // Prevent a stale quote from authorising the previous selection even before the effect runs.
  const ready = quote && quote.duration === duration && quote.presenter === presenter;
  const insufficient = ready && quote.credits < quote.credit_cost;
  const choose = (lang) => { languageTouched.current = true; setLanguage(lang); };
  const create = () => {
    if (!ready || submitted.current) return;
    if (insufficient) { onBuyCredits(); return; }
    submitted.current = true;
    AsyncStorage.setItem('reelLanguage', language).catch(() => {});
    onCreate({ language, durationSeconds: duration, presenterEnabled: presenter, confirmedCreditCost: quote.credit_cost });
  };
  const option = (label, selected, onPress) => <Pressable accessibilityRole="radio" accessibilityState={{ checked: selected }} aria-checked={selected} onPress={onPress} style={[styles.option, { borderColor: selected ? colors.primary : colors.cardBorder, backgroundColor: selected ? colors.accentSoft : colors.surface }]}><Text style={[styles.optionText, { color: selected ? colors.primary : colors.text }]}>{label}</Text></Pressable>;
  return <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
    <View style={styles.overlay}><View style={[styles.sheet, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={[styles.title, { color: colors.text }]}>{t(recreating ? 'reelSetup.recreate' : 'reelSetup.title')}</Text>
        <Text style={[styles.label, { color: colors.textSecondary }]}>{t('reelSetup.language')}</Text>
        <View style={styles.row}>{option(t('chat.podcastLanguage.english'), language === 'en', () => choose('en'))}{option(t('chat.podcastLanguage.hindi'), language === 'hi', () => choose('hi'))}</View>
        <Text style={[styles.label, { color: colors.textSecondary }]}>{t('reelSetup.length')}</Text>
        <View style={styles.row}>{option(t('reelSetup.short'), duration === 90, () => setDuration(90))}{option(t('reelSetup.deep'), duration === 180, () => setDuration(180))}</View>
        <View style={[styles.presenter, { borderColor: colors.cardBorder }]}>
          <View style={styles.flex}><Text style={[styles.optionText, { color: colors.text }]}>{t('reelSetup.presenter')}</Text><Text style={[styles.body, { color: colors.textSecondary }]}>{t('reelSetup.presenterDetail')}</Text>{ready && Number.isFinite(quote.presenter_addon_cost) && <Text style={{ color: colors.primary }}>{t('reelSetup.extra', { count: quote.presenter_addon_cost })}</Text>}</View>
          <Switch accessibilityLabel={t('reelSetup.presenter')} value={presenter} onValueChange={setPresenter} trackColor={{ true: colors.primary }} thumbColor={colors.surfaceRaised} />
        </View>
        <View style={[styles.summary, { backgroundColor: colors.accentSoft }]}>
          {ready ? <><Text style={[styles.price, { color: colors.primary }]}>{t('reelSetup.total', { count: quote.credit_cost })}</Text><Text style={{ color: colors.textSecondary }}>{t('reelSetup.balance', { count: quote.credits })}</Text></> : error ? <Pressable onPress={() => setRetry((value) => value + 1)}><Text style={{ color: colors.primary }}>{t('reelSetup.retry')}</Text></Pressable> : <ActivityIndicator color={colors.primary} />}
        </View>
        <Text style={[styles.note, { color: colors.textSecondary }]}>{t('reelSetup.note')}</Text>
        <Pressable accessibilityRole="button" disabled={!ready} onPress={create} style={[styles.create, { backgroundColor: colors.primary, opacity: ready ? 1 : 0.5 }]}><Text style={[styles.createText, { color: colors.onPrimary || '#fff' }]}>{insufficient ? t('credits.buyCredits') : t('reelSetup.create')}</Text></Pressable>
        <Pressable accessibilityRole="button" onPress={onClose} style={styles.cancel}><Text style={{ color: colors.textSecondary }}>{t('common.cancel')}</Text></Pressable>
      </ScrollView>
    </View></View>
  </Modal>;
}
const styles = StyleSheet.create({
  overlay: { flex: 1, justifyContent: 'flex-end', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)' },
  sheet: { width: '100%', maxWidth: 560, maxHeight: '92%', borderTopLeftRadius: 28, borderTopRightRadius: 28, borderWidth: 1 },
  content: { padding: 24, paddingBottom: 32 }, title: { fontSize: 27, fontWeight: '700', marginBottom: 10 },
  label: { marginTop: 16, marginBottom: 8, fontSize: 13, fontWeight: '600' }, row: { flexDirection: 'row', gap: 10 },
  option: { flex: 1, padding: 14, borderRadius: 14, borderWidth: 1, justifyContent: 'center' }, optionText: { fontSize: 15, fontWeight: '700' },
  presenter: { flexDirection: 'row', alignItems: 'center', gap: 12, borderTopWidth: 1, marginTop: 22, paddingTop: 18 }, flex: { flex: 1 }, body: { fontSize: 13, lineHeight: 19, marginVertical: 5 },
  summary: { marginTop: 20, padding: 16, borderRadius: 14, gap: 5 }, price: { fontSize: 21, fontWeight: '700' },
  note: { fontSize: 12, lineHeight: 18, marginVertical: 13 }, create: { padding: 17, borderRadius: 16, alignItems: 'center' }, createText: { fontSize: 16, fontWeight: '700' }, cancel: { paddingTop: 18, paddingBottom: 6, alignItems: 'center' },
});
