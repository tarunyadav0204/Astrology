import React, { useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { typographyTokens } from '../../theme/tokens';
import { useTranslation } from 'react-i18next';

const YogaAccordion = ({ title, data = [] }) => {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);

  return (
    <View style={[styles.container, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      <TouchableOpacity onPress={() => setExpanded((value) => !value)} style={styles.header} accessibilityRole="button" accessibilityState={{ expanded }}>
        <View style={[styles.icon, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
          <Ionicons name="sparkles-outline" size={18} color={colors.selectionText} />
        </View>
        <View style={styles.titleWrap}>
          <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
          <Text style={[styles.count, { color: colors.textSecondary }]}>{t('premiumUi.yogas.combinationsFound', { count: data.length })}</Text>
        </View>
        <Ionicons name={expanded ? 'remove' : 'add'} size={20} color={colors.primaryStrong} />
      </TouchableOpacity>
      {expanded ? (
        <View style={[styles.content, { borderTopColor: colors.cardBorder }]}>
          {data.length > 0 ? data.map((yoga, index) => (
            <View key={`${yoga.name}-${index}`} style={[styles.yogaItem, index < data.length - 1 && { borderBottomColor: colors.cardBorder, borderBottomWidth: StyleSheet.hairlineWidth }]}>
              <Text style={[styles.yogaName, { color: colors.text }]}>{yoga.name}</Text>
              {yoga.description ? <Text style={[styles.yogaDescription, { color: colors.textSecondary }]}>{yoga.description}</Text> : null}
            </View>
          )) : <Text style={[styles.empty, { color: colors.textSecondary }]}>{t('premiumUi.yogas.noCategory')}</Text>}
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { borderRadius: 20, borderWidth: 1, overflow: 'hidden', marginBottom: 12 },
  header: { minHeight: 72, paddingHorizontal: 14, paddingVertical: 12, flexDirection: 'row', alignItems: 'center', gap: 12 },
  icon: { width: 42, height: 42, borderRadius: 14, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  titleWrap: { flex: 1 },
  title: { ...typographyTokens.sectionTitle, fontSize: 17 },
  count: { fontSize: 12, marginTop: 3 },
  content: { borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: 16 },
  yogaItem: { paddingVertical: 15 },
  yogaName: { ...typographyTokens.sectionTitle, fontSize: 16, marginBottom: 5 },
  yogaDescription: { fontSize: 13, lineHeight: 19 },
  empty: { paddingVertical: 18, fontSize: 13 },
});

export default YogaAccordion;
