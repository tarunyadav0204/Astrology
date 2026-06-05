import React from 'react';
import {
  Dimensions,
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';

const { width } = Dimensions.get('window');

const VARIANT_CONFIG = {
  success: {
    icon: 'checkmark-circle',
    accent: '#4CAF50',
    glow: 'rgba(76, 175, 80, 0.18)',
  },
  error: {
    icon: 'alert-circle',
    accent: '#EF4444',
    glow: 'rgba(239, 68, 68, 0.16)',
  },
  warning: {
    icon: 'warning',
    accent: '#F59E0B',
    glow: 'rgba(245, 158, 11, 0.16)',
  },
  info: {
    icon: 'sparkles',
    accent: '#ff6b35',
    glow: 'rgba(255, 107, 53, 0.16)',
  },
};

export default function AppAlertModal({
  visible,
  title,
  message,
  variant = 'info',
  icon,
  primaryText = 'OK',
  secondaryText,
  onPrimaryPress,
  onSecondaryPress,
  onRequestClose,
}) {
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const config = VARIANT_CONFIG[variant] || VARIANT_CONFIG.info;
  const accent = config.accent;
  const modalGradient = isDark
    ? [colors.gradientStart || '#1a0033', colors.gradientMid || '#2d1b4e', colors.gradientEnd || '#4a2c6d']
    : [colors.cardBackground || '#ffffff', colors.backgroundSecondary || '#fff7ed'];

  const handleClose = onRequestClose || onPrimaryPress || (() => {});

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
      statusBarTranslucent
    >
      <View style={styles.overlay}>
        <View style={styles.cardShadow}>
          <LinearGradient colors={modalGradient} style={[styles.card, { borderColor: colors.cardBorder }]}>
            <View style={[styles.iconHalo, { backgroundColor: config.glow, borderColor: accent }]}>
              <Ionicons name={icon || config.icon} size={42} color={accent} />
            </View>

            <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
            {!!message && (
              <Text style={[styles.message, { color: colors.textSecondary }]}>{message}</Text>
            )}

            <View style={styles.buttonRow}>
              {!!secondaryText && (
                <TouchableOpacity
                  style={[styles.secondaryButton, { borderColor: colors.cardBorder }]}
                  activeOpacity={0.85}
                  onPress={onSecondaryPress || handleClose}
                >
                  <Text style={[styles.secondaryText, { color: colors.textSecondary }]}>{secondaryText}</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity style={styles.primaryButton} activeOpacity={0.9} onPress={onPrimaryPress || handleClose}>
                <LinearGradient colors={[accent, '#ff8c5a']} style={styles.primaryGradient}>
                  <Text style={styles.primaryText}>{primaryText}</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </LinearGradient>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: 'rgba(0, 0, 0, 0.68)',
  },
  cardShadow: {
    width: Math.min(width - 48, 360),
    borderRadius: 28,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 18 },
    shadowOpacity: 0.35,
    shadowRadius: 28,
    elevation: 18,
  },
  card: {
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 28,
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 22,
    overflow: 'hidden',
  },
  iconHalo: {
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 10,
  },
  message: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 24,
  },
  buttonRow: {
    flexDirection: 'row',
    width: '100%',
    gap: 12,
  },
  secondaryButton: {
    flex: 1,
    minHeight: 52,
    borderWidth: 1,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 14,
  },
  secondaryText: {
    fontSize: 16,
    fontWeight: '700',
  },
  primaryButton: {
    flex: 1,
    minHeight: 52,
    borderRadius: 16,
    overflow: 'hidden',
  },
  primaryGradient: {
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 18,
  },
  primaryText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '800',
  },
});
