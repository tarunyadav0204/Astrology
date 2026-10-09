import React from 'react';
import { View, Text } from 'react-native';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import PlaceSearchField from '../PlaceSearchField';
export default function PrashnaSetup({ onSelect }) {
  const { t } = useTranslation(); const { colors } = useTheme();
  return <View><Text style={{ color: colors.text, marginVertical: 12 }}>{t('premiumUi.chat.prashna.description', 'Start with Parashari. KP and Tajika are available when useful. The question chart is fixed when you send your question.')}</Text>
    <Text style={{ color: colors.text, marginBottom: 12 }}>{t('premiumUi.chat.prashna.chooseCity', 'Choose the city where you are asking the question.')}</Text>
    <PlaceSearchField onSelect={onSelect} placeholder={t('premiumUi.chat.prashna.cityPlaceholder', 'Search your current city')} />
  </View>;
}
