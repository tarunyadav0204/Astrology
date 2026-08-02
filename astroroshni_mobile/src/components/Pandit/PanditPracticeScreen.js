import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { panditAPI } from '../../services/api';
import { useCredits } from '../../credits/CreditContext';
import { trackAstrologyEvent } from '../../utils/analytics';
import { LANGUAGE_OPTIONS, PUJA_TYPE_OPTIONS } from './panditConstants';

// Theme is global: openPanditMode enters white pandit shell before this screen.

function Chip({ label, selected, onPress, colors }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[
        styles.chip,
        {
          backgroundColor: selected ? 'rgba(234, 88, 12, 0.12)' : colors.backgroundSecondary,
          borderColor: selected ? colors.primary : colors.cardBorder,
        },
      ]}
    >
      <Text style={[styles.chipText, { color: selected ? colors.primary : colors.text }]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

export default function PanditPracticeScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors, enterPanditMode } = useTheme();
  const { fetchBalance } = useCredits();
  const initial = route?.params?.profile || null;
  const isJoin = route?.params?.mode !== 'edit';

  const [displayName, setDisplayName] = useState(initial?.display_name || '');
  const [city, setCity] = useState(initial?.city || '');
  const [pincode, setPincode] = useState(initial?.pincode || '');
  const [tagline, setTagline] = useState(initial?.tagline || '');
  const [phone, setPhone] = useState(initial?.phone || '');
  const [email, setEmail] = useState(initial?.email || '');
  const [website, setWebsite] = useState(initial?.website || '');
  const [address, setAddress] = useState(initial?.address || '');
  const [languages, setLanguages] = useState(
    Array.isArray(initial?.languages) && initial.languages.length
      ? initial.languages
      : ['hindi', 'english']
  );
  const [pujaTypes, setPujaTypes] = useState(
    Array.isArray(initial?.puja_types) ? initial.puja_types : []
  );
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await panditAPI.getMeta();
        const types = res?.data?.allowed_puja_types;
        if (!cancelled && Array.isArray(types) && types.length && !pujaTypes.length) {
          // keep empty until user picks
        }
      } catch (_) {
        /* optional */
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const canSubmit = useMemo(() => {
    const pin = String(pincode || '').replace(/\D/g, '');
    return Boolean(displayName.trim() && city.trim() && pin.length >= 6 && pujaTypes.length > 0);
  }, [displayName, city, pincode, pujaTypes]);

  const toggle = (list, setList, id) => {
    setList((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const onSave = async () => {
    if (!canSubmit) {
      Alert.alert(
        'Incomplete',
        'Add practice name, city, 6-digit pincode, and at least one puja type.'
      );
      return;
    }
    setSaving(true);
    try {
      const payload = {
        display_name: displayName.trim(),
        city: city.trim(),
        pincode: String(pincode).replace(/\D/g, '').slice(0, 10),
        languages,
        puja_types: pujaTypes,
        tagline: tagline.trim(),
        phone: phone.trim(),
        email: email.trim(),
        website: website.trim(),
        address: address.trim(),
      };
      if (isJoin) {
        await panditAPI.join(payload);
        trackAstrologyEvent.panditJoined({
          pincode: payload.pincode,
          city: payload.city,
          puja_types_count: payload.puja_types?.length || 0,
        });
        await fetchBalance();
        // Idempotent if openPanditMode already entered white theme.
        await enterPanditMode();
        Alert.alert(
          'Pandit mode on',
          'Free desk is ready. Home now shows kundli & muhurat tools with a white theme.'
        );
        navigation.reset({
          index: 0,
          routes: [{ name: 'Home' }],
        });
        return;
      }
      await panditAPI.updateProfile(payload);
      await fetchBalance();
      Alert.alert('Saved', 'Practice details updated.');
      if (navigation.canGoBack()) navigation.goBack();
      else navigation.navigate('Home');
    } catch (error) {
      const detail = error?.response?.data?.detail;
      const message = typeof detail === 'string'
        ? detail
        : detail?.message || error?.message || 'Could not save practice profile.';
      Alert.alert('Error', message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => (navigation.canGoBack() ? navigation.goBack() : navigation.navigate('Home'))}
            style={styles.backBtn}
          >
            <Ionicons name="arrow-back" size={22} color={colors.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.text }]}>
            {isJoin
              ? t('panditPractice.setupTitle', 'Set up practice')
              : t('panditPractice.detailsTitle', 'Practice details')}
          </Text>
          <View style={{ width: 36 }} />
        </View>

        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
            <Text style={[styles.lead, { color: colors.textSecondary }]}>
              {t(
                'panditPractice.lead',
                'Free for pandits. Used on kundli PDFs and later to match puja requests near you.',
              )}
            </Text>

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.practiceName', 'Practice name *')}
            </Text>
            <TextInput
              value={displayName}
              onChangeText={setDisplayName}
              placeholder="Pandit Sharma Jyotish"
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.city', 'City *')}
            </Text>
            <TextInput
              value={city}
              onChangeText={setCity}
              placeholder="Varanasi"
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.pincode', 'Pincode *')}
            </Text>
            <TextInput
              value={pincode}
              onChangeText={setPincode}
              placeholder="221001"
              keyboardType="number-pad"
              maxLength={10}
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.pujaTypes', 'Puja types you perform *')}
            </Text>
            <View style={styles.chipRow}>
              {PUJA_TYPE_OPTIONS.map((opt) => (
                <Chip
                  key={opt.id}
                  label={opt.label}
                  selected={pujaTypes.includes(opt.id)}
                  onPress={() => toggle(pujaTypes, setPujaTypes, opt.id)}
                  colors={colors}
                />
              ))}
            </View>

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.languages', 'Languages')}
            </Text>
            <View style={styles.chipRow}>
              {LANGUAGE_OPTIONS.map((opt) => (
                <Chip
                  key={opt.id}
                  label={opt.label}
                  selected={languages.includes(opt.id)}
                  onPress={() => toggle(languages, setLanguages, opt.id)}
                  colors={colors}
                />
              ))}
            </View>

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.tagline', 'Tagline')}
            </Text>
            <TextInput
              value={tagline}
              onChangeText={setTagline}
              placeholder="Vedic guidance you can trust"
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.phoneOnPdf', 'Phone on PDF')}
            </Text>
            <TextInput
              value={phone}
              onChangeText={setPhone}
              placeholder="+91 …"
              keyboardType="phone-pad"
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.email', 'Email')}
            </Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              keyboardType="email-address"
              autoCapitalize="none"
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.website', 'Website')}
            </Text>
            <TextInput
              value={website}
              onChangeText={setWebsite}
              placeholder="https://…"
              autoCapitalize="none"
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <Text style={[styles.label, { color: colors.textSecondary }]}>
              {t('panditPractice.address', 'Address')}
            </Text>
            <TextInput
              value={address}
              onChangeText={setAddress}
              placeholder="Area, landmark"
              placeholderTextColor={colors.textTertiary}
              style={[styles.input, { color: colors.text, borderColor: colors.cardBorder, backgroundColor: colors.backgroundSecondary }]}
            />

            <TouchableOpacity
              style={[styles.cta, { backgroundColor: canSubmit ? colors.primary : colors.backgroundTertiary }]}
              onPress={onSave}
              disabled={saving || !canSubmit}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.ctaText}>
                  {isJoin
                    ? t('panditPractice.activateCta', 'Activate Free Desk')
                    : t('panditPractice.saveCta', 'Save practice')}
                </Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(0,0,0,0.08)',
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0,0,0,0.04)',
  },
  headerTitle: { flex: 1, textAlign: 'center', fontSize: 17, fontWeight: '600' },
  scroll: { padding: 20, paddingBottom: 40 },
  lead: { fontSize: 14, lineHeight: 22, marginBottom: 18 },
  label: { fontSize: 12, fontWeight: '600', marginBottom: 6, marginTop: 12 },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
  },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipText: { fontSize: 13, fontWeight: '500' },
  cta: {
    marginTop: 28,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
  },
  ctaText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
