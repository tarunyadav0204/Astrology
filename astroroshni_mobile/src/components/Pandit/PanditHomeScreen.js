import React, { useEffect } from 'react';
import { View, ActivityIndicator, StatusBar } from 'react-native';
import { useTheme } from '../../context/ThemeContext';
import { useAuthGate } from '../../auth/AuthGateContext';
import { openPanditMode } from './openPanditMode';

/**
 * Deep-link entry only: /mobile/pandit (and aliases).
 * Turns on pandit mode (white theme) and returns to main Home with same tabs.
 * Auth resume after "I am a Pandit" goes to Home + activatePandit — not here.
 */
export default function PanditHomeScreen({ navigation }) {
  const { colors, enterPanditMode } = useTheme();
  const { requireAuthForPaid } = useAuthGate();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ok = await openPanditMode({
        navigation,
        requireAuthForPaid,
        enterPanditMode,
      });
      if (cancelled) return;
      if (!ok) {
        // Practice setup navigates itself; auth cancel → go Home
        const state = navigation.getState?.();
        const current = state?.routes?.[state.index || 0]?.name;
        if (current === 'PanditHome') {
          if (navigation.canGoBack()) navigation.goBack();
          else navigation.navigate('Home');
        }
      }
    })();
    return () => { cancelled = true; };
  }, [enterPanditMode, navigation, requireAuthForPaid]);

  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} />
      <ActivityIndicator color={colors.primary} />
    </View>
  );
}
