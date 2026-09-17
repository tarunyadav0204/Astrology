import React from 'react';
import {
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { typographyTokens } from '../../theme/tokens';

/**
 * Credit conversion sheet: buy credits, or tap Live / Talk to Tara
 * when the current balance already covers those modes.
 */
export default function ChatCreditChoiceModal({
  visible,
  onClose,
  onBuyCredits,
  cost,
  credits,
  modeName,
  buyLabel,
  liveOption = null,
  speechOption = null,
  onSelectMode,
}) {
  const { colors, getCardElevation } = useTheme();
  const { t } = useTranslation();

  if (!visible) return null;

  const linkStyle = [styles.link, { color: colors.primary }];
  const bodyColor = { color: colors.textSecondary };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable style={[styles.overlay, { backgroundColor: colors.overlay }]} onPress={onClose}>
        <Pressable style={styles.outer} onPress={(e) => e.stopPropagation()}>
          <View style={[styles.modalContainer, {
            backgroundColor: colors.surfaceRaised,
            borderColor: colors.cardBorder,
            elevation: getCardElevation(4),
          }]}>
            <View style={[styles.modalAccentLine, { backgroundColor: colors.accent }]} />
            <View style={styles.modalContent}>
              <TouchableOpacity
                style={[styles.closeButton, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                onPress={onClose}
                accessibilityRole="button"
                accessibilityLabel={t('creditConfirmation.cancel')}
              >
                <Ionicons name="close" size={18} color={colors.textSecondary} />
              </TouchableOpacity>
              <View style={[styles.iconRow, { backgroundColor: colors.accentSoft }]}>
                <Ionicons name="wallet-outline" size={25} color={colors.onAccent || colors.text} />
              </View>
              <Text style={[styles.eyebrow, { color: colors.accent }]}>{t('creditConfirmation.eyebrow')}</Text>
              <Text style={[styles.modalTitle, { color: colors.text }]}>
                {t('chat.creditChoice.title', 'Not enough credits')}
              </Text>
              <Text style={[
                styles.modalText,
                !(liveOption || speechOption) && styles.useLine,
                bodyColor,
              ]}>
                {t('chat.creditChoice.needLine', {
                  mode: modeName,
                  cost,
                  balance: credits,
                  defaultValue: `You need ${cost} credits for ${modeName} and you have ${credits}.`,
                })}
              </Text>
              {liveOption || speechOption ? (
                <Text style={[styles.modalText, styles.useLine, bodyColor]}>
                  {t('chat.creditChoice.canUsePrefix', 'You can use ')}
                  {liveOption ? (
                    <Text
                      style={linkStyle}
                      onPress={() => onSelectMode?.('instant')}
                      accessibilityRole="link"
                      accessibilityLabel={t('chat.modeIntro.instant.name', 'Live')}
                    >
                      {t('chat.modeIntro.instant.name', 'Live')}
                    </Text>
                  ) : null}
                  {liveOption ? ` (${liveOption.rate})` : null}
                  {liveOption && speechOption
                    ? t('chat.creditChoice.orWrapped', ' or ')
                    : null}
                  {speechOption ? (
                    <Text
                      style={linkStyle}
                      onPress={() => onSelectMode?.('speech')}
                      accessibilityRole="link"
                      accessibilityLabel={t('chat.speechChatCta', 'Talk To Tara')}
                    >
                      {t('chat.speechChatCta', 'Talk To Tara')}
                    </Text>
                  ) : null}
                  {speechOption ? ` (${speechOption.rate})` : null}
                  {t('chat.creditChoice.canUseSuffix', '.')}
                </Text>
              ) : null}

              <TouchableOpacity
                style={[styles.modalConfirmButton, { backgroundColor: colors.primaryStrong }]}
                onPress={onBuyCredits}
                accessibilityRole="button"
                accessibilityLabel={buyLabel}
              >
                <View style={styles.modalConfirmGradient}>
                  <Text style={[styles.modalConfirmText, { color: colors.onPrimary }]}>{buyLabel}</Text>
                  <Ionicons name="arrow-forward" size={17} color={colors.onPrimary} />
                </View>
              </TouchableOpacity>
            </View>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  outer: {
    width: '88%',
    maxWidth: 410,
  },
  modalContainer: {
    borderRadius: 28,
    overflow: 'hidden',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 18 },
    shadowOpacity: 0.28,
    shadowRadius: 30,
  },
  modalAccentLine: { height: 4, width: '100%' },
  modalContent: {
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 22,
    alignItems: 'center',
  },
  iconRow: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  closeButton: {
    position: 'absolute',
    right: 16,
    top: 16,
    width: 34,
    height: 34,
    borderRadius: 17,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
  },
  eyebrow: {
    ...typographyTokens.eyebrow,
    fontSize: 9,
    marginBottom: 8,
  },
  modalTitle: {
    ...typographyTokens.display,
    fontSize: 26,
    lineHeight: 30,
    marginBottom: 10,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 8,
    maxWidth: 320,
  },
  useLine: {
    marginBottom: 22,
  },
  link: {
    fontSize: 15,
    fontWeight: '800',
    textDecorationLine: 'underline',
  },
  modalConfirmButton: {
    width: '100%',
    borderRadius: 12,
    overflow: 'hidden',
    alignItems: 'center',
    marginTop: 8,
  },
  modalConfirmGradient: {
    paddingVertical: 13,
    paddingHorizontal: 20,
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
  },
  modalConfirmText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
