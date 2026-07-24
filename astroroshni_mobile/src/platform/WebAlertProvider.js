import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../context/ThemeContext';

const STORE_KEY = '__ASTROROSHNI_WEB_ALERT_STORE__';
const PATCH_KEY = '__ASTROROSHNI_WEB_ALERT_PATCHED__';

function createWebAlertStore() {
  let nextId = 1;
  let queue = [];
  const listeners = new Set();

  const notify = () => {
    const current = queue[0] || null;
    listeners.forEach((listener) => {
      try {
        listener(current);
      } catch (_) {
        /* A broken subscriber must not prevent alert delivery elsewhere. */
      }
    });
  };

  return {
    enqueue(title, message, buttons, options) {
      const normalizedButtons =
        Array.isArray(buttons) && buttons.length
          ? buttons
              .filter((button) => button && typeof button === 'object')
              .map((button) => ({
                text: String(button.text || 'OK'),
                style: button.style || 'default',
                onPress: typeof button.onPress === 'function' ? button.onPress : null,
              }))
          : [{ text: 'OK', style: 'default', onPress: null }];

      queue.push({
        id: nextId++,
        title: title == null ? '' : String(title),
        message: message == null ? '' : String(message),
        buttons: normalizedButtons.length
          ? normalizedButtons
          : [{ text: 'OK', style: 'default', onPress: null }],
        onDismiss: typeof options?.onDismiss === 'function' ? options.onDismiss : null,
      });
      notify();
    },
    dismiss(id, { invokeDismiss = false } = {}) {
      const current = queue[0];
      if (!current || current.id !== id) {
        queue = queue.filter((item) => item.id !== id);
        notify();
        return;
      }
      queue.shift();
      notify();
      if (invokeDismiss && current.onDismiss) {
        try {
          current.onDismiss();
        } catch (_) {
          /* Match native Alert: dismissal callback failures do not crash the UI. */
        }
      }
    },
    peek() {
      return queue[0] || null;
    },
    subscribe(listener) {
      listeners.add(listener);
      listener(queue[0] || null);
      return () => listeners.delete(listener);
    },
  };
}

function getWebAlertStore() {
  if (Platform.OS !== 'web') return null;
  if (!globalThis[STORE_KEY]) {
    globalThis[STORE_KEY] = createWebAlertStore();
  }
  return globalThis[STORE_KEY];
}

const webAlertStore = getWebAlertStore();

// react-native-web intentionally implements Alert.alert as a no-op. Patch the
// shared Alert object once so every existing Alert.alert call reaches this UI.
if (Platform.OS === 'web' && webAlertStore && !globalThis[PATCH_KEY]) {
  globalThis[PATCH_KEY] = true;
  Alert.alert = (title, message, buttons, options) => {
    webAlertStore.enqueue(title, message, buttons, options);
  };
}

function alertPresentation(alert) {
  const title = String(alert?.title || '').toLowerCase();
  const hasDestructiveButton = alert?.buttons?.some((button) => button.style === 'destructive');
  if (hasDestructiveButton || /delete|remove|warning|insufficient/.test(title)) {
    return { icon: 'warning', accent: '#f59e0b', glow: 'rgba(245, 158, 11, 0.16)' };
  }
  if (/error|failed|failure|unable|could not|invalid/.test(title)) {
    return { icon: 'alert-circle', accent: '#ef4444', glow: 'rgba(239, 68, 68, 0.16)' };
  }
  if (/success|complete|copied|saved|downloaded|verified|deleted/.test(title)) {
    return { icon: 'checkmark-circle', accent: '#22c55e', glow: 'rgba(34, 197, 94, 0.16)' };
  }
  return { icon: 'information-circle', accent: '#f97316', glow: 'rgba(249, 115, 22, 0.16)' };
}

export default function WebAlertProvider({ children }) {
  const { theme, colors } = useTheme();
  const [current, setCurrent] = useState(() => webAlertStore?.peek() || null);

  useEffect(() => {
    if (!webAlertStore) return undefined;
    return webAlertStore.subscribe(setCurrent);
  }, []);

  const presentation = useMemo(() => alertPresentation(current), [current]);

  if (Platform.OS !== 'web') {
    return children;
  }

  const pressButton = (button) => {
    if (!current) return;
    const alertId = current.id;
    webAlertStore.dismiss(alertId);
    if (button?.onPress) {
      try {
        const result = button.onPress();
        if (result && typeof result.catch === 'function') {
          result.catch((error) => console.error('[WebAlert] Button action failed:', error));
        }
      } catch (error) {
        console.error('[WebAlert] Button action failed:', error);
      }
    }
  };

  const buttons = current?.buttons || [];
  const dismiss = () => {
    if (!current) return;
    const cancelButton =
      buttons.find((button) => button.style === 'cancel') ||
      buttons.find((button) =>
        /^(cancel|close|dismiss|not now|stay|go back|later|no)$/i.test(
          String(button.text || '').trim()
        )
      );
    if (cancelButton) {
      pressButton(cancelButton);
      return;
    }
    if (buttons.length === 1) {
      pressButton(buttons[0]);
      return;
    }
    webAlertStore.dismiss(current.id, { invokeDismiss: true });
  };

  const totalLabelLength = buttons.reduce((sum, button) => sum + String(button.text || '').length, 0);
  const stackButtons = buttons.length > 2 || totalLabelLength > 28;
  const defaultButtonIndexes = buttons
    .map((button, index) => (button.style !== 'cancel' && button.style !== 'destructive' ? index : -1))
    .filter((index) => index >= 0);
  const primaryButtonIndex =
    defaultButtonIndexes.length > 0
      ? defaultButtonIndexes[defaultButtonIndexes.length - 1]
      : -1;
  const isDark = theme === 'dark';
  const modalGradient = isDark
    ? [
        colors.gradientStart || '#1a0033',
        colors.gradientMid || '#2d1b4e',
        colors.gradientEnd || '#4a2c6d',
      ]
    : [colors.cardBackground || '#ffffff', colors.backgroundSecondary || '#fff7ed'];

  return (
    <>
      {children}
      <Modal
        visible={current != null}
        transparent
        animationType="fade"
        onRequestClose={dismiss}
        statusBarTranslucent
      >
        <View style={styles.overlay}>
          <View style={styles.cardShadow}>
            <LinearGradient
              colors={modalGradient}
              style={[styles.card, { borderColor: colors.cardBorder }]}
            >
              <TouchableOpacity
                style={[styles.closeButton, { backgroundColor: colors.backgroundSecondary }]}
                activeOpacity={0.8}
                onPress={dismiss}
                accessibilityRole="button"
                accessibilityLabel="Close"
              >
                <Ionicons name="close" size={22} color={colors.textSecondary} />
              </TouchableOpacity>

              <View
                style={[
                  styles.iconHalo,
                  {
                    backgroundColor: presentation.glow,
                    borderColor: presentation.accent,
                  },
                ]}
              >
                <Ionicons name={presentation.icon} size={38} color={presentation.accent} />
              </View>

              <Text style={[styles.title, { color: colors.text }]}>
                {current?.title || 'AstroRoshni'}
              </Text>
              {!!current?.message && (
                <ScrollView
                  style={styles.messageScroll}
                  contentContainerStyle={styles.messageScrollContent}
                  showsVerticalScrollIndicator={false}
                >
                  <Text style={[styles.message, { color: colors.textSecondary }]}>
                    {current.message}
                  </Text>
                </ScrollView>
              )}

              <View style={[styles.buttonRow, stackButtons && styles.buttonRowStacked]}>
                {buttons.map((button, index) => {
                  const destructive = button.style === 'destructive';
                  const cancel = button.style === 'cancel';
                  const primary = !cancel && index === primaryButtonIndex;
                  if (primary && !destructive) {
                    return (
                      <TouchableOpacity
                        key={`${current.id}-${index}`}
                        style={[styles.button, stackButtons && styles.stackedButton]}
                        activeOpacity={0.88}
                        onPress={() => pressButton(button)}
                      >
                        <LinearGradient
                          colors={['#f97316', '#ea580c']}
                          style={styles.primaryGradient}
                        >
                          <Text style={styles.primaryButtonText}>{button.text}</Text>
                        </LinearGradient>
                      </TouchableOpacity>
                    );
                  }
                  return (
                    <TouchableOpacity
                      key={`${current.id}-${index}`}
                      style={[
                        styles.button,
                        styles.outlineButton,
                        stackButtons && styles.stackedButton,
                        {
                          borderColor: destructive ? '#ef4444' : colors.cardBorder,
                          backgroundColor: destructive
                            ? 'rgba(239, 68, 68, 0.1)'
                            : colors.backgroundSecondary,
                        },
                      ]}
                      activeOpacity={0.82}
                      onPress={() => pressButton(button)}
                    >
                      <Text
                        style={[
                          styles.outlineButtonText,
                          { color: destructive ? '#ef4444' : colors.textSecondary },
                        ]}
                      >
                        {button.text}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </LinearGradient>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
  },
  cardShadow: {
    width: '100%',
    maxWidth: 390,
    borderRadius: 26,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 18 },
    shadowOpacity: 0.35,
    shadowRadius: 28,
  },
  card: {
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 26,
    paddingHorizontal: 22,
    paddingTop: 26,
    paddingBottom: 20,
    overflow: 'hidden',
  },
  closeButton: {
    position: 'absolute',
    top: 13,
    right: 13,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
  },
  iconHalo: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: {
    maxWidth: '88%',
    fontSize: 21,
    lineHeight: 27,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 9,
  },
  messageScroll: {
    width: '100%',
    maxHeight: 260,
    marginBottom: 20,
  },
  messageScrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  message: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
  },
  buttonRow: {
    flexDirection: 'row',
    width: '100%',
    gap: 10,
  },
  buttonRowStacked: {
    flexDirection: 'column',
  },
  button: {
    flex: 1,
    minHeight: 50,
    borderRadius: 15,
    overflow: 'hidden',
  },
  stackedButton: {
    flex: 0,
    width: '100%',
  },
  outlineButton: {
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  outlineButtonText: {
    fontSize: 15,
    fontWeight: '700',
    textAlign: 'center',
  },
  primaryGradient: {
    minHeight: 50,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '800',
    textAlign: 'center',
  },
});
