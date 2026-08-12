import React, { useCallback } from 'react';
import { Platform, StatusBar } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';

export default function FocusedStatusBar({ backgroundColor, barStyle = 'light-content' }) {
  useFocusEffect(
    useCallback(() => {
      StatusBar.setBarStyle(barStyle, true);
      if (Platform.OS === 'android') {
        StatusBar.setTranslucent(false);
        StatusBar.setBackgroundColor(backgroundColor, true);
      }
    }, [backgroundColor, barStyle])
  );

  return <StatusBar barStyle={barStyle} backgroundColor={backgroundColor} translucent={false} />;
}
