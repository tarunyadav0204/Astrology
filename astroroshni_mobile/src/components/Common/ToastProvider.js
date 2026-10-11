import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';

const ToastContext = createContext(() => {});
export const useToast = () => useContext(ToastContext);

export default function ToastProvider({ children }) {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const [message, setMessage] = useState('');
  const timer = useRef(null);
  const showToast = useCallback((text) => {
    clearTimeout(timer.current);
    setMessage(text);
    timer.current = setTimeout(() => setMessage(''), 2500);
  }, []);
  useEffect(() => () => clearTimeout(timer.current), []);
  return (
    <ToastContext.Provider value={showToast}>
      <View style={styles.container}>
        {children}
        {message ? (
          <View pointerEvents="none" style={[styles.overlay, { top: insets.top + 76 }]}>
            <View accessibilityRole="alert" accessibilityLiveRegion="polite" style={[styles.toast, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
              <Ionicons name="bookmark-outline" size={18} color={colors.primary} />
              <Text style={[styles.message, { color: colors.text }]}>{message}</Text>
            </View>
          </View>
        ) : null}
      </View>
    </ToastContext.Provider>
  );
}
const styles = StyleSheet.create({
  container: { flex: 1, minHeight: 0 },
  overlay: { position: 'absolute', left: 16, right: 16, alignItems: 'center', zIndex: 1000, elevation: 20 },
  toast: { maxWidth: 420, flexDirection: 'row', alignItems: 'center', gap: 9, paddingHorizontal: 16, paddingVertical: 12, borderRadius: 16, borderWidth: 1, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.16, shadowRadius: 10, elevation: 12 },
  message: { flexShrink: 1, fontSize: 14, fontWeight: '600', lineHeight: 20 },
});
