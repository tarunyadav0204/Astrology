import React, { useEffect, useState } from 'react';
import {
  Animated,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  useWindowDimensions,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

export default function AuthKeyboardScreen({
  emoji,
  title,
  subtitle,
  onBack,
  children,
  action,
  footer,
  headerExtra,
  keyboardVerticalOffset = 0,
}) {
  const { height: windowHeight } = useWindowDimensions();
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const [keyboardMetrics, setKeyboardMetrics] = useState({ height: 0, screenY: 0 });

  useEffect(() => {
    const syncKeyboardMetrics = () => {
      if (typeof Keyboard.metrics !== 'function') return;
      const metrics = Keyboard.metrics();
      const height = Number(metrics?.height || 0);
      const keyboardTop = Number(metrics?.screenY || 0);
      if (height > 0 || keyboardTop > 0) {
        setKeyboardVisible(true);
        setKeyboardMetrics({ height, screenY: keyboardTop });
      }
    };
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvent, (event) => {
      const height = Number(event?.endCoordinates?.height || 0);
      const keyboardTop = Number(event?.endCoordinates?.screenY || 0);
      setKeyboardVisible(true);
      setKeyboardMetrics({ height, screenY: keyboardTop });
    });
    const hideSub = Keyboard.addListener(hideEvent, () => {
      setKeyboardVisible(false);
      setKeyboardMetrics({ height: 0, screenY: 0 });
    });
    const timers = [
      setTimeout(syncKeyboardMetrics, 80),
      setTimeout(syncKeyboardMetrics, 300),
      setTimeout(syncKeyboardMetrics, 700),
    ];
    return () => {
      showSub?.remove();
      hideSub?.remove();
      timers.forEach(clearTimeout);
    };
  }, []);

  const keyboardOverlap = (() => {
    if (Platform.OS !== 'android' || !keyboardVisible) return 0;
    const keyboardTop = Number(keyboardMetrics.screenY || 0);
    const keyboardHeight = Number(keyboardMetrics.height || 0);
    const overlap = windowHeight > 0 && keyboardTop > 0
      ? Math.max(0, windowHeight - keyboardTop)
      : keyboardHeight;
    return Math.max(0, overlap - (Platform.OS === 'ios' ? keyboardVerticalOffset : 0));
  })();

  const actionBottom =
    Platform.OS === 'android' && keyboardVisible
      ? Math.max(24, keyboardOverlap + 24)
      : 16;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={keyboardVerticalOffset}
    >
      <View style={styles.frame}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Ionicons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>

        <View style={[styles.header, keyboardVisible && styles.headerCompact]}>
          <Text style={[styles.emoji, keyboardVisible && styles.emojiCompact]}>{emoji}</Text>
          <Text style={[styles.title, keyboardVisible && styles.titleCompact]}>{title}</Text>
          <Text
            style={[styles.subtitle, keyboardVisible && styles.subtitleCompact]}
            numberOfLines={keyboardVisible ? 1 : 3}
          >
            {subtitle}
          </Text>
          {!keyboardVisible && headerExtra}
        </View>

        <ScrollView
          style={styles.bodyScroll}
          contentContainerStyle={[
            styles.bodyContent,
            keyboardVisible && styles.bodyContentKeyboard,
          ]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {children}
          {!keyboardVisible && (
            <>
              <Animated.View style={styles.actionContainer}>
                {action}
              </Animated.View>
              {footer ? <View style={styles.footer}>{footer}</View> : null}
            </>
          )}
        </ScrollView>

        {keyboardVisible && (
          <Animated.View
            style={[
              styles.actionContainer,
              styles.actionContainerKeyboard,
              { bottom: actionBottom },
            ]}
          >
            {action}
          </Animated.View>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  frame: {
    flex: 1,
    paddingHorizontal: 20,
  },
  backButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 10,
  },
  header: {
    alignItems: 'center',
    marginBottom: 18,
  },
  headerCompact: {
    marginBottom: 8,
  },
  emoji: {
    fontSize: 52,
    marginBottom: 14,
  },
  emojiCompact: {
    fontSize: 28,
    marginBottom: 6,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 12,
    textAlign: 'center',
  },
  titleCompact: {
    fontSize: 21,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 22,
  },
  subtitleCompact: {
    fontSize: 13,
    lineHeight: 18,
    maxWidth: '100%',
  },
  bodyScroll: {
    flex: 1,
    minHeight: 0,
    ...(Platform.OS === 'web' ? { overflow: 'auto' } : null),
  },
  bodyContent: {
    flexGrow: 1,
    // On web, vertical centering + flexGrow can clip tall content; keep top-aligned.
    justifyContent: Platform.OS === 'web' ? 'flex-start' : 'center',
    paddingTop: 10,
    paddingBottom: 14,
  },
  bodyContentKeyboard: {
    justifyContent: 'flex-start',
    paddingTop: 6,
    paddingBottom: 120,
  },
  footer: {
    alignItems: 'center',
    paddingTop: 2,
    paddingBottom: 2,
  },
  actionContainer: {
    paddingTop: 14,
    paddingBottom: 10,
  },
  actionContainerKeyboard: {
    position: 'absolute',
    left: 20,
    right: 20,
    paddingTop: 8,
    paddingBottom: 0,
  },
});
