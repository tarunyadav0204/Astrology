import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  Animated,
  Alert,
  StyleSheet,
  Linking,
  Platform,
} from 'react-native';
import { chatAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

/** Same listing as web chat + AstroRoshni homepage CTA. */
const ANDROID_PACKAGE_NAME = 'com.astroroshni.mobile';
const GOOGLE_PLAY_LISTING_URL =
  `https://play.google.com/store/apps/details?id=${ANDROID_PACKAGE_NAME}&showAllReviews=true&pcampaignid=web_share`;

function FeedbackPlayStoreRow({ colors, t }) {
  const openPlay = async () => {
    if (Platform.OS === 'android') {
      try {
        await Linking.openURL(`market://details?id=${ANDROID_PACKAGE_NAME}`);
        return;
      } catch (_) {
        // Fall back to web listing below.
      }
    }
    try {
      await Linking.openURL(GOOGLE_PLAY_LISTING_URL);
    } catch (_) {
      Alert.alert(t('premiumUi.chat.playStoreError'), t('premiumUi.chat.playStoreSearch'));
    }
  };
  return (
    <>
      <View style={styles.playDivider} />
      <TouchableOpacity
        style={[
          styles.playLinkButton,
          {
            borderColor: colors.cardBorder,
            backgroundColor: colors.surfaceMuted,
          },
        ]}
        onPress={openPlay}
        activeOpacity={0.85}
        accessibilityRole="link"
        accessibilityLabel={t('premiumUi.chat.rateOnPlay')}
      >
        <View style={styles.playIconBadge}>
          <Text style={styles.playIconText}>▶</Text>
        </View>
        <Text style={[styles.playLinkLabel, { color: colors.text }]}>
          {t('premiumUi.chat.rateOnPlay')}
        </Text>
      </TouchableOpacity>
      <Text style={[styles.playHint, { color: colors.textSecondary || '#6b7280' }]}>
        {t('premiumUi.chat.ratingHelps')}
      </Text>
    </>
  );
}

const FEEDBACK_REASON_KEYS = { helpful: 'helpful', unclear: 'unclear', wrong_personal_detail: 'wrongPersonalDetail', contradicts_earlier_answer: 'contradictsEarlierAnswer' };

export default function FeedbackComponent({ message, onFeedbackSubmitted }) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const [feedback, setFeedback] = useState({ reason: null, rating: 0, comment: '', submitted: false });
  const [submitting, setSubmitting] = useState(false);
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const eligible =
    message.role === 'assistant' &&
    !message.isTyping &&
    Boolean(message.messageId) &&
    message.message_type === 'answer';

  useEffect(() => {
    // Show feedback only for 'answer' type messages from assistant
    if (!eligible || dismissed) return undefined;
    const timer = setTimeout(() => {
      setVisible(true);
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }).start();
    }, 3000);
    return () => clearTimeout(timer);
  }, [eligible, dismissed, fadeAnim]);

  const submitFeedback = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await chatAPI.submitFeedback({
        message_id: Number(message.messageId),
        rating: feedback.rating,
        reason: feedback.reason,
        comment: feedback.comment.trim() || null,
      });

      setFeedback(prev => ({ ...prev, submitted: true }));
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted(message.messageId, feedback.rating);
      }
      setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }).start(() => {
          setVisible(false);
          setDismissed(true);
        });
      }, feedback.rating >= 4 ? 12000 : 2200);
    } catch (error) {
      const detail = error?.response?.data?.detail || error?.message || 'Failed to submit feedback';
      if (__DEV__) console.warn('[Feedback] submit failed:', detail);
      Alert.alert('Error', detail);
    } finally { setSubmitting(false); }
  };


  const handleSkip = () => {
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start(() => {
      setVisible(false);
      setDismissed(true);
    });
  };

  // Reserve space as soon as the answer is shown so the delayed reveal does not
  // grow the FlatList row mid-read (that shifts scroll through long answers).
  if (!eligible || dismissed) return null;

  return (
    <Animated.View
      style={[
        styles.container,
        {
          opacity: visible ? fadeAnim : 0,
          minHeight: 58,
          backgroundColor: colors.surface,
          borderColor: colors.cardBorder,
        },
      ]}
      pointerEvents={visible ? 'auto' : 'none'}
    >
      {feedback.submitted ? (
        <>
          <Text style={[styles.thanksText, { color: colors.primary }]}>{t('premiumUi.chat.feedbackThanks')} 🙏</Text>
          {feedback.rating >= 4 && (
            <FeedbackPlayStoreRow colors={colors} t={t} />
          )}
        </>
      ) : (
        <>
          <View style={styles.ratingRow}>
            <View style={styles.ratingPrompt}>
              <Text style={[styles.eyebrow, { color: colors.primary }]}>{t('premiumUi.chat.answerFeedback')}</Text>
              <Text style={[styles.title, { color: colors.text }]}>{t('premiumUi.chat.wasUseful')}</Text>
            </View>
            <TouchableOpacity
              onPress={handleSkip}
              style={styles.dismissButton}
              hitSlop={8}
              accessibilityRole="button"
              accessibilityLabel={t('premiumUi.chat.dismissFeedback')}
            >
              <Ionicons name="close" size={17} color={colors.textTertiary} />
            </TouchableOpacity>
          </View>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            <TouchableOpacity disabled={submitting} accessibilityRole="button" accessibilityState={{ selected: feedback.reason === 'helpful' }} onPress={() => setFeedback(prev => ({ ...prev, reason: 'helpful', rating: 5 }))} style={{ padding: 10, borderWidth: 1, borderRadius: 16, borderColor: feedback.reason === 'helpful' ? colors.primary : colors.cardBorder }}><Text style={{ color: colors.text }}>{t('premiumUi.chat.feedbackReasons.helpful')}</Text></TouchableOpacity>
            <TouchableOpacity disabled={submitting} accessibilityRole="button" accessibilityState={{ selected: feedback.reason === 'unclear' }} onPress={() => setFeedback(prev => ({ ...prev, reason: 'unclear', rating: 2 }))} style={{ padding: 10, borderWidth: 1, borderRadius: 16, borderColor: feedback.reason === 'unclear' ? colors.primary : colors.cardBorder }}><Text style={{ color: colors.text }}>{t('premiumUi.chat.feedbackReasons.unclear')}</Text></TouchableOpacity>
            <TouchableOpacity disabled={submitting} accessibilityRole="button" accessibilityState={{ selected: feedback.reason === 'wrong_personal_detail' }} onPress={() => setFeedback(prev => ({ ...prev, reason: 'wrong_personal_detail', rating: 1 }))} style={{ padding: 10, borderWidth: 1, borderRadius: 16, borderColor: feedback.reason === 'wrong_personal_detail' ? colors.primary : colors.cardBorder }}><Text style={{ color: colors.text }}>{t('premiumUi.chat.feedbackReasons.wrongPersonalDetail')}</Text></TouchableOpacity>
            <TouchableOpacity disabled={submitting} accessibilityRole="button" accessibilityState={{ selected: feedback.reason === 'contradicts_earlier_answer' }} onPress={() => setFeedback(prev => ({ ...prev, reason: 'contradicts_earlier_answer', rating: 1 }))} style={{ padding: 10, borderWidth: 1, borderRadius: 16, borderColor: feedback.reason === 'contradicts_earlier_answer' ? colors.primary : colors.cardBorder }}><Text style={{ color: colors.text }}>{t('premiumUi.chat.feedbackReasons.contradictsEarlierAnswer')}</Text></TouchableOpacity>
          </View>
          {feedback.rating > 0 && (
            <>
              <TextInput
                style={[styles.commentInput, {
                  color: colors.text,
                  borderColor: colors.cardBorder,
                  backgroundColor: colors.surfaceMuted,
                }]}
                placeholder={t(`premiumUi.chat.feedbackPrompts.${FEEDBACK_REASON_KEYS[feedback.reason]}`)}
                accessibilityLabel={t(`premiumUi.chat.feedbackPrompts.${FEEDBACK_REASON_KEYS[feedback.reason]}`)}
                placeholderTextColor={colors.textTertiary}
                multiline
                value={feedback.comment}
                onChangeText={(text) => setFeedback(prev => ({ ...prev, comment: text }))}
              />
              <View style={styles.buttonsContainer}>
                <TouchableOpacity style={[styles.submitButton, { backgroundColor: colors.primary }]} disabled={submitting} onPress={submitFeedback}>
                  <Text style={[styles.submitButtonText, { color: colors.onPrimary }]}>{t('premiumUi.chat.sendFeedback')}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.skipButton, { borderColor: colors.cardBorder }]} onPress={handleSkip}>
                  <Text style={[styles.skipButtonText, { color: colors.textSecondary }]}>{t('common.cancel')}</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </>
      )}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 18,
    borderWidth: 1,
    marginHorizontal: 12,
  },
  ratingRow: {
    minHeight: 38,
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingPrompt: {
    flex: 1,
    paddingRight: 8,
  },
  eyebrow: {
    fontSize: 9,
    lineHeight: 12,
    fontWeight: '800',
    letterSpacing: 1.2,
    marginBottom: 1,
  },
  title: {
    fontSize: 14,
    lineHeight: 18,
    fontWeight: '700',
  },
  starsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  starButton: {
    paddingHorizontal: 3,
    paddingVertical: 5,
  },
  dismissButton: {
    paddingLeft: 7,
    paddingVertical: 7,
  },
  commentInput: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 11,
    marginTop: 10,
    minHeight: 68,
    textAlignVertical: 'top',
    fontSize: 14,
  },
  buttonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  submitButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
    flex: 1,
    marginRight: 8,
  },
  submitButtonText: {
    fontWeight: '800',
    textAlign: 'center',
  },
  skipButton: {
    backgroundColor: 'transparent',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
  },
  skipButtonText: {
    textAlign: 'center',
  },
  thanksText: {
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '600',
    marginBottom: 4,
  },
  playDivider: {
    height: 1,
    marginTop: 14,
    marginBottom: 12,
    backgroundColor: 'rgba(249, 115, 22, 0.22)',
  },
  playLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    maxWidth: 320,
  },
  playIconBadge: {
    width: 20,
    height: 20,
    marginRight: 8,
    borderRadius: 4,
    backgroundColor: '#01875f',
    alignItems: 'center',
    justifyContent: 'center',
  },
  playIconText: {
    color: '#fff',
    fontSize: 9,
    fontWeight: '700',
    marginLeft: 1,
  },
  playLinkLabel: {
    fontSize: 13,
    fontWeight: '600',
    flexShrink: 1,
  },
  playHint: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 15,
    paddingHorizontal: 8,
  },
});
