import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

import { chatAPI } from '../services/api';
import { useTheme } from '../context/ThemeContext';

const SUBJECTS = [
  ['spouse', 'Spouse / partner'],
  ['mother', 'Mother'],
  ['father', 'Father'],
  ['child', 'Child'],
  ['younger_sibling', 'Younger sibling'],
  ['elder_sibling', 'Elder sibling'],
];

const WORK_OPTIONS = [
  ['employed', 'Working'], ['self_employed', 'Business'], ['homemaker', 'Homemaker'],
  ['student', 'Studying'], ['retired', 'Retired'], ['unemployed', 'Not working'], ['unknown', 'Not sure'],
];
const LOCATION_OPTIONS = [
  ['with_native', 'Lives with you'], ['same_city', 'Same city'],
  ['elsewhere_india', 'Elsewhere in India'], ['abroad', 'Abroad'], ['unknown', 'Not sure'],
];
const EMPTY = {
  life_status: 'living', age_years: '', employment_state: 'unknown',
  location_context: 'unknown', relationship_status: 'unknown', enabled: true,
};

function ChoiceRow({ options, value, onChange, colors, t, namespace }) {
  return (
    <View style={styles.choiceRow}>
      {options.map(([key, label]) => (
        <TouchableOpacity
          key={key}
          onPress={() => onChange(key)}
          style={[
            styles.choice,
            { borderColor: value === key ? colors.primary : colors.cardBorder, backgroundColor: value === key ? colors.selectionSurface : colors.surface },
          ]}
        >
          <Text style={[styles.choiceText, { color: value === key ? colors.primary : colors.textSecondary }]}>{t(`${namespace}.${key}`, label)}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

export default function RelativeProfilesPanel({ birthChartId, compact = false, onSaved }) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);
  const [form, setForm] = useState(EMPTY);

  const byKey = useMemo(() => Object.fromEntries(profiles.map((row) => [row.subject_key, row])), [profiles]);

  useEffect(() => {
    let active = true;
    if (!birthChartId) return undefined;
    setLoading(true);
    chatAPI.getRelativeProfiles(birthChartId)
      .then((response) => { if (active) setProfiles(response?.data?.profiles || []); })
      .catch(() => {})
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [birthChartId]);

  const openProfile = (subjectKey) => {
    const existing = byKey[subjectKey];
    setForm(existing ? { ...EMPTY, ...existing, age_years: existing.age_years == null ? '' : String(existing.age_years) } : EMPTY);
    setSelectedKey(subjectKey);
  };

  const save = async () => {
    if (!selectedKey || !birthChartId || saving) return;
    setSaving(true);
    try {
      const payload = {
        ...form,
        birth_chart_id: Number(birthChartId),
        age_years: form.age_years === '' ? null : Number(form.age_years),
        display_label: SUBJECTS.find(([key]) => key === selectedKey)?.[1] || null,
      };
      const response = await chatAPI.saveRelativeProfile(selectedKey, payload);
      const saved = response?.data?.profile;
      if (saved) setProfiles((previous) => [...previous.filter((row) => row.subject_key !== selectedKey), saved]);
      setSelectedKey(null);
      onSaved?.(saved);
    } catch (error) {
      Alert.alert(
        t('relativeProfiles.saveErrorTitle', 'Could not save person'),
        error?.response?.data?.detail || t('relativeProfiles.saveError', 'Please check your connection and try again.')
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <View style={[styles.panel, compact && styles.panelCompact, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      <View style={styles.headingRow}>
        <View style={[styles.icon, { backgroundColor: colors.surface }]}><Ionicons name="people-outline" size={18} color={colors.primary} /></View>
        <View style={styles.headingCopy}>
          <Text style={[styles.title, { color: colors.text }]}>{t('relativeProfiles.title', 'People around you')}</Text>
          <Text style={[styles.hint, { color: colors.textSecondary }]}>
            {t('relativeProfiles.hint', 'Add a person so their age and daily life can shape realistic family predictions.')}
          </Text>
        </View>
        {loading ? <ActivityIndicator size="small" color={colors.primary} /> : null}
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabs}>
        {SUBJECTS.map(([key, fallback]) => {
          const profile = byKey[key];
          const active = profile?.enabled && profile?.life_status !== 'deceased';
          return (
            <TouchableOpacity key={key} onPress={() => openProfile(key)} style={[styles.tab, { borderColor: active ? colors.primary : colors.cardBorder, backgroundColor: active ? colors.selectionSurface : colors.surface }]}>
              <Ionicons name={active ? 'checkmark-circle' : 'add-circle-outline'} size={16} color={active ? colors.primary : colors.textTertiary} />
              <Text style={[styles.tabText, { color: active ? colors.primary : colors.textSecondary }]}>{t(`relativeProfiles.subjects.${key}`, fallback)}</Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
      <Text style={[styles.scope, { color: colors.textTertiary }]}>
        {t('relativeProfiles.scope', 'Without their own linked birth chart, these are family developments seen through your chart—not a complete personal forecast for them.')}
      </Text>

      <Modal visible={!!selectedKey} transparent animationType="slide" onRequestClose={() => setSelectedKey(null)}>
        <View style={styles.overlay}>
          <View style={[styles.sheet, { backgroundColor: colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
            <View style={styles.modalHeader}>
              <View style={styles.headingCopy}>
                <Text style={[styles.modalTitle, { color: colors.text }]}>{t(`relativeProfiles.subjects.${selectedKey}`, SUBJECTS.find(([key]) => key === selectedKey)?.[1] || 'Relative')}</Text>
                <Text style={[styles.hint, { color: colors.textSecondary }]}>{t('relativeProfiles.setupHint', 'A few details help us avoid unrealistic wording.')}</Text>
              </View>
              <TouchableOpacity onPress={() => setSelectedKey(null)}><Ionicons name="close" size={25} color={colors.text} /></TouchableOpacity>
            </View>

            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={[styles.label, { color: colors.text }]}>{t('relativeProfiles.lifeStatus', 'Is this person living?')}</Text>
              <ChoiceRow t={t} namespace="relativeProfiles.lifeOptions" colors={colors} value={form.life_status} onChange={(value) => setForm((old) => ({ ...old, life_status: value, enabled: value !== 'deceased' }))} options={[["living", "Yes"], ["deceased", "No"], ["unknown", "Prefer not to say"]]} />

              {form.life_status !== 'deceased' ? (
                <>
                  <Text style={[styles.label, { color: colors.text }]}>{t('relativeProfiles.age', 'Approximate age (optional)')}</Text>
                  <TextInput
                    value={form.age_years}
                    onChangeText={(value) => setForm((old) => ({ ...old, age_years: value.replace(/[^0-9]/g, '').slice(0, 3) }))}
                    keyboardType="number-pad"
                    placeholder={t('relativeProfiles.agePlaceholder', 'For example, 62')}
                    placeholderTextColor={colors.textTertiary}
                    style={[styles.input, { color: colors.text, backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
                  />
                  <Text style={[styles.label, { color: colors.text }]}>{t('relativeProfiles.work', 'What best describes their daily life?')}</Text>
                  <ChoiceRow t={t} namespace="relativeProfiles.workOptions" colors={colors} value={form.employment_state} onChange={(value) => setForm((old) => ({ ...old, employment_state: value }))} options={WORK_OPTIONS} />
                  <Text style={[styles.label, { color: colors.text }]}>{t('relativeProfiles.location', 'Where do they live?')}</Text>
                  <ChoiceRow t={t} namespace="relativeProfiles.locationOptions" colors={colors} value={form.location_context} onChange={(value) => setForm((old) => ({ ...old, location_context: value }))} options={LOCATION_OPTIONS} />
                </>
              ) : null}
            </ScrollView>

            <TouchableOpacity disabled={saving} onPress={save} style={[styles.save, { backgroundColor: colors.primary }]}>
              {saving ? <ActivityIndicator color={colors.onPrimary || '#fff'} /> : <Text style={[styles.saveText, { color: colors.onPrimary || '#fff' }]}>{t('relativeProfiles.save', 'Save person')}</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  panel: { marginHorizontal: 18, marginVertical: 12, padding: 16, borderWidth: 1, borderRadius: 20 },
  panelCompact: { marginHorizontal: 0 }, headingRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  icon: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  headingCopy: { flex: 1, minWidth: 0 }, title: { fontSize: 18, fontWeight: '800' }, hint: { fontSize: 13, lineHeight: 18, marginTop: 3 },
  tabs: { gap: 8, paddingTop: 14, paddingBottom: 8 }, tab: { flexDirection: 'row', gap: 6, alignItems: 'center', borderWidth: 1, borderRadius: 18, paddingHorizontal: 12, paddingVertical: 9 },
  tabText: { fontSize: 13, fontWeight: '700' }, scope: { fontSize: 11, lineHeight: 16, marginTop: 4 },
  overlay: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.48)' },
  sheet: { maxHeight: '88%', padding: 20, paddingBottom: 30, borderTopLeftRadius: 26, borderTopRightRadius: 26, borderWidth: 1 },
  modalHeader: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12 }, modalTitle: { fontSize: 22, fontWeight: '800' },
  label: { marginTop: 16, marginBottom: 9, fontSize: 14, fontWeight: '800' }, choiceRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { borderWidth: 1, borderRadius: 16, paddingHorizontal: 11, paddingVertical: 8 }, choiceText: { fontSize: 12, fontWeight: '700' },
  input: { borderWidth: 1, borderRadius: 14, paddingHorizontal: 14, paddingVertical: 12, fontSize: 15 },
  save: { marginTop: 22, minHeight: 50, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }, saveText: { fontSize: 16, fontWeight: '800' },
});
