import React, { useCallback, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { panditAPI } from '../../services/api';

function ActionCard({ icon, title, subtitle, onPress, colors }) {
  return (
    <TouchableOpacity
      style={[styles.card, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}
      onPress={onPress}
      activeOpacity={0.85}
    >
      <View style={[styles.iconWrap, { backgroundColor: 'rgba(24, 24, 27, 0.06)' }]}>
        <Ionicons name={icon} size={22} color={colors.primary} />
      </View>
      <View style={styles.cardBody}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>{title}</Text>
        <Text style={[styles.cardSub, { color: colors.textSecondary }]}>{subtitle}</Text>
      </View>
      <Ionicons name="chevron-forward" size={18} color={colors.textTertiary} />
    </TouchableOpacity>
  );
}

/** Pandit tools on the main Home scroll (same tabs/menu chrome). */
export default function PanditHomePanel({ navigation, showExit = true }) {
  const { t } = useTranslation();
  const { colors, exitPanditMode } = useTheme();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      (async () => {
        setLoading(true);
        try {
          const res = await panditAPI.getMe();
          if (cancelled) return;
          const data = res?.data || {};
          if (!data.desk_ready) {
            navigation.navigate('PanditPractice', {
              mode: 'join',
              profile: data.profile || null,
            });
            return;
          }
          setProfile(data.profile || null);
        } catch (_) {
          /* keep last profile */
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
      return () => { cancelled = true; };
    }, [navigation])
  );

  return (
    <View style={styles.wrap}>
      <View style={[styles.badge, { backgroundColor: 'rgba(22, 163, 74, 0.1)', borderColor: 'rgba(22, 163, 74, 0.25)' }]}>
        <Ionicons name="checkmark-circle" size={16} color="#16A34A" />
        <Text style={styles.badgeText}>
          {profile?.display_name
            ? t('home.pandit.badgeWithName', {
                name: profile.display_name,
                defaultValue: 'Pandit mode · Free desk · {{name}}',
              })
            : t('home.pandit.badge', 'Pandit mode · Free desk')}
        </Text>
      </View>

      <Text style={[styles.sectionLabel, { color: colors.textSecondary }]}>
        {t('home.pandit.clientTools', 'Client tools')}
      </Text>

      {loading ? (
        <ActivityIndicator color={colors.primary} style={{ marginVertical: 24 }} />
      ) : (
        <>
          <ActionCard
            icon="person-add-outline"
            title={t('home.pandit.addNative', 'Add new client chart')}
            subtitle={t('home.pandit.addNativeSub', 'Enter birth details to create a chart for your client')}
            colors={colors}
            onPress={() => navigation.navigate('BirthForm', { returnTo: 'Home' })}
          />
          <ActionCard
            icon="document-text-outline"
            title={t('home.pandit.makeKundli', 'Make Kundli')}
            subtitle={t('home.pandit.makeKundliSub', 'Branded Janam Kundli PDF for your client')}
            colors={colors}
            onPress={() => navigation.navigate('ReportsStudio', { reportType: 'janam_kundli' })}
          />
          <ActionCard
            icon="calendar-outline"
            title={t('home.pandit.findMuhurat', 'Find Muhurat')}
            subtitle={t('home.pandit.findMuhuratSub', 'Auspicious timings with reasons to share')}
            colors={colors}
            onPress={() => navigation.navigate('MuhuratHub')}
          />
          <ActionCard
            icon="sunny-outline"
            title={t('home.pandit.todaysPanchang', "Today's Panchang")}
            subtitle={t('home.pandit.todaysPanchangSub', 'Tithi, Choghadiya, Rahu Kaal for the day')}
            colors={colors}
            onPress={() => navigation.navigate('DailyPanchang')}
          />
          <ActionCard
            icon="business-outline"
            title={t('home.pandit.practiceDetails', 'Practice details')}
            subtitle={`${profile?.city || t('home.pandit.cityFallback', 'City')} · ${profile?.pincode || t('home.pandit.pincodeFallback', 'Pincode')}`}
            colors={colors}
            onPress={() => navigation.navigate('PanditPractice', { mode: 'edit', profile })}
          />
        </>
      )}

      {showExit ? (
        <TouchableOpacity
          style={styles.exitBtn}
          onPress={async () => {
            await exitPanditMode();
          }}
        >
          <Text style={[styles.exitText, { color: colors.primary }]}>
            {t('home.pandit.switchPersonal', 'Switch to personal app')}
          </Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { paddingHorizontal: 16, paddingBottom: 24 },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 16,
  },
  badgeText: { flex: 1, color: '#166534', fontSize: 13, fontWeight: '600' },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.4,
    marginBottom: 10,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 16,
    padding: 14,
    marginBottom: 10,
    gap: 12,
  },
  iconWrap: {
    width: 42,
    height: 42,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: { flex: 1, minWidth: 0 },
  cardTitle: { fontSize: 16, fontWeight: '800' },
  cardSub: { fontSize: 12, marginTop: 2 },
  exitBtn: { marginTop: 8, alignItems: 'center', paddingVertical: 14 },
  exitText: { fontSize: 15, fontWeight: '700' },
});
