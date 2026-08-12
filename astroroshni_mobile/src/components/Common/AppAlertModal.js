import React from 'react';
import {
  Dimensions,
  Modal,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { typographyTokens } from '../../theme/tokens';
import { useTranslation } from 'react-i18next';

const { width } = Dimensions.get('window');

const VARIANT_CONFIG = {
  success: {
    icon: 'checkmark',
    colorToken: 'success',
  },
  error: {
    icon: 'alert-circle',
    colorToken: 'error',
  },
  warning: {
    icon: 'warning',
    colorToken: 'warning',
  },
  info: {
    icon: 'sparkles',
    colorToken: 'primary',
  },
};

export default function AppAlertModal({
  visible,
  title,
  message,
  variant = 'info',
  icon,
  primaryText,
  secondaryText,
  onPrimaryPress,
  onSecondaryPress,
  onRequestClose,
  stackButtons = false,
  showCloseButton = false,
}) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const resolvedPrimaryText = primaryText || t('common.ok', 'OK');
  const config = VARIANT_CONFIG[variant] || VARIANT_CONFIG.info;
  const accent = colors[config.colorToken] || colors.primary;
  const modalGradient = [colors.surfaceRaised, colors.backgroundSecondary];

  const handleClose = onRequestClose || onPrimaryPress || (() => {});

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
      statusBarTranslucent
    >
      <View style={[styles.overlay, { backgroundColor: colors.overlay }]}>
        <View style={styles.cardShadow}>
          <LinearGradient colors={modalGradient} style={[styles.card, { borderColor: colors.cardBorder }]}>
            <View style={[styles.topRule, { backgroundColor: colors.accent }]} />
            <View style={[styles.orbit, styles.orbitLarge, { borderColor: colors.strokeMuted }]} />
            <View style={[styles.orbit, styles.orbitSmall, { borderColor: colors.strokeMuted }]} />
            {showCloseButton && (
              <TouchableOpacity
                style={[styles.closeButton, { backgroundColor: colors.backgroundSecondary }]}
                activeOpacity={0.8}
                onPress={handleClose}
                accessibilityRole="button"
                accessibilityLabel={t('premiumUi.common.close')}
              >
                <Ionicons name="close" size={22} color={colors.textSecondary} />
              </TouchableOpacity>
            )}
            <View style={[styles.iconHalo, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
              <Ionicons name={icon || config.icon} size={28} color={accent} />
            </View>

            <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
            {!!message && (
              <Text style={[styles.message, { color: colors.textSecondary }]}>{message}</Text>
            )}

            <View style={[styles.buttonRow, stackButtons && styles.buttonRowStacked]}>
              {!!secondaryText && (
                <TouchableOpacity
                  style={[
                    styles.secondaryButton,
                    stackButtons && styles.stackedButton,
                    { borderColor: colors.cardBorder, backgroundColor: colors.surfaceMuted },
                  ]}
                  activeOpacity={0.85}
                  onPress={onSecondaryPress || handleClose}
                >
                  <Text style={[styles.secondaryText, { color: colors.textSecondary }]}>{secondaryText}</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity
                style={[styles.primaryButton, stackButtons && styles.stackedButton, { backgroundColor: colors.primary }]}
                activeOpacity={0.9}
                onPress={onPrimaryPress || handleClose}
              >
                <LinearGradient colors={[colors.primary, colors.primaryStrong]} style={styles.primaryGradient}>
                <Text style={[styles.primaryText, { color: colors.onPrimary }]}>{resolvedPrimaryText}</Text>
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
    ...(Platform.OS === 'web'
      ? {
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          left: 0,
          zIndex: 2147483647,
        }
      : null),
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
    paddingTop: 30,
    paddingBottom: 24,
    overflow: 'hidden',
  },
  topRule: {
    position: 'absolute',
    top: 0,
    left: 32,
    right: 32,
    height: 3,
    borderBottomLeftRadius: 3,
    borderBottomRightRadius: 3,
  },
  orbit: {
    position: 'absolute',
    borderWidth: 1,
    borderRadius: 999,
  },
  orbitLarge: {
    width: 150,
    height: 150,
    top: -88,
    right: -42,
  },
  orbitSmall: {
    width: 96,
    height: 96,
    top: -58,
    right: -15,
  },
  closeButton: {
    position: 'absolute',
    top: 14,
    right: 14,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  iconHalo: {
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  title: {
    ...typographyTokens.display,
    fontSize: 29,
    lineHeight: 34,
    textAlign: 'center',
    marginBottom: 10,
  },
  message: {
    fontSize: 15,
    lineHeight: 23,
    textAlign: 'center',
    marginBottom: 24,
  },
  buttonRow: {
    flexDirection: 'row',
    width: '100%',
    gap: 12,
  },
  buttonRowStacked: {
    flexDirection: 'column',
  },
  stackedButton: {
    flex: 0,
    width: '100%',
  },
  secondaryButton: {
    flex: 1,
    minHeight: 52,
    borderWidth: 1,
    borderRadius: 18,
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
    borderRadius: 18,
    overflow: 'hidden',
  },
  primaryGradient: {
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 18,
    borderRadius: 18,
  },
  primaryText: {
    fontSize: 16,
    fontWeight: '800',
  },
});
