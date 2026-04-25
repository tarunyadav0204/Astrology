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

/** Same listing as web chat + AstroRoshni homepage CTA. */
const ANDROID_PACKAGE_NAME = 'com.astroroshni.mobile';
const GOOGLE_PLAY_LISTING_URL =
  `https://play.google.com/store/apps/details?id=${ANDROID_PACKAGE_NAME}&showAllReviews=true&pcampaignid=web_share`;

function FeedbackPlayStoreRow({ colors, theme }) {
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
      Alert.alert('Could not open Play Store', 'Please search for AstroRoshni in the Play Store.');
    }
  };
  return (
    <>
      <View style={styles.playDivider} />
      <TouchableOpacity
        style={[
          styles.playLinkButton,
          {
            borderColor: theme === 'dark' ? 'rgba(96, 165, 250, 0.45)' : 'rgba(15, 71, 160, 0.25)',
            backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.06)' : 'rgba(255, 255, 255, 0.85)',
          },
        ]}
        onPress={openPlay}
        activeOpacity={0.85}
        accessibilityRole="link"
        accessibilityLabel="Leave a rating on Google Play"
      >
        <View style={styles.playIconBadge}>
          <Text style={styles.playIconText}>▶</Text>
        </View>
        <Text style={[styles.playLinkLabel, { color: theme === 'dark' ? '#93c5fd' : '#0f47a0' }]}>
          Leave a rating on Google Play
        </Text>
      </TouchableOpacity>
      <Text style={[styles.playHint, { color: colors.textSecondary || '#6b7280' }]}>
        Helps others discover the app
      </Text>
    </>
  );
}

export default function FeedbackComponent({ message, onFeedbackSubmitted }) {
  const { theme, colors } = useTheme();
  const [feedback, setFeedback] = useState({ rating: 0, comment: '', submitted: false });
  const [visible, setVisible] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Show feedback only for 'answer' type messages from assistant
    if (message.role === 'assistant' && 
        !message.isTyping && 
        message.messageId && 
        message.message_type === 'answer') {
      const timer = setTimeout(() => {
        setVisible(true);
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 500,
          useNativeDriver: true,
        }).start();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message.isTyping, message.message_type]);

  const submitFeedback = async () => {
    try {
      await chatAPI.submitFeedback({
        message_id: Number(message.messageId),
        rating: feedback.rating,
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
        });
      }, feedback.rating >= 4 ? 12000 : 2200);
    } catch (error) {
      const detail = error?.response?.data?.detail || error?.message || 'Failed to submit feedback';
      if (__DEV__) console.warn('[Feedback] submit failed:', detail);
      Alert.alert('Error', detail);
    }
  };

  const handleStarPress = (rating) => {
    setFeedback(prev => ({ ...prev, rating }));
  };

  const handleSkip = () => {
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start(() => {
      setVisible(false);
    });
  };

  if (!visible) return null;

  return (
    <Animated.View style={[styles.container, { 
      opacity: fadeAnim,
      backgroundColor: theme === 'dark' ? 'rgba(249, 115, 22, 0.05)' : 'rgba(249, 115, 22, 0.1)',
      borderColor: theme === 'dark' ? 'rgba(249, 115, 22, 0.2)' : 'rgba(249, 115, 22, 0.3)'
    }]}>
      {feedback.submitted ? (
        <>
          <Text style={[styles.thanksText, { color: colors.primary }]}>Thanks for your feedback! 🙏</Text>
          {feedback.rating >= 4 && (
            <FeedbackPlayStoreRow colors={colors} theme={theme} />
          )}
        </>
      ) : (
        <>
          <Text style={[styles.title, { color: colors.text }]}>How was this answer?</Text>
          <View style={styles.starsContainer}>
            {[1, 2, 3, 4, 5].map((star) => (
              <TouchableOpacity
                key={star}
                onPress={() => handleStarPress(star)}
                style={styles.starButton}
              >
                <Text style={[
                  styles.starIcon,
                  { color: star <= feedback.rating ? '#FFD700' : '#999' }
                ]}>★</Text>
              </TouchableOpacity>
            ))}
          </View>
          {feedback.rating > 0 && (
            <>
              <TextInput
                style={[styles.commentInput, { 
                  color: colors.text,
                  borderColor: theme === 'dark' ? '#E0E0E0' : 'rgba(249, 115, 22, 0.3)',
                  backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(249, 115, 22, 0.05)'
                }]}
                placeholder="Tell us more (optional)"
                placeholderTextColor={theme === 'dark' ? '#999' : 'rgba(0, 0, 0, 0.4)'}
                multiline
                value={feedback.comment}
                onChangeText={(text) => setFeedback(prev => ({ ...prev, comment: text }))}
              />
              <View style={styles.buttonsContainer}>
                <TouchableOpacity style={styles.submitButton} onPress={submitFeedback}>
                  <Text style={styles.submitButtonText}>Submit</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
                  <Text style={[styles.skipButtonText, { color: colors.text }]}>Skip</Text>
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
    marginTop: 8,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginHorizontal: 16,
  },
  title: {
    fontSize: 13,
    marginBottom: 8,
    textAlign: 'center',
  },
  starsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 8,
  },
  starButton: {
    padding: 4,
  },
  starIcon: {
    fontSize: 20,
  },
  commentInput: {
    borderWidth: 1,
    borderRadius: 6,
    padding: 8,
    marginTop: 8,
    minHeight: 60,
    textAlignVertical: 'top',
    fontSize: 14,
  },
  buttonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  submitButton: {
    backgroundColor: '#ff6b35',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    flex: 1,
    marginRight: 8,
  },
  submitButtonText: {
    color: 'white',
    fontWeight: '600',
    textAlign: 'center',
  },
  skipButton: {
    backgroundColor: 'transparent',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(249, 115, 22, 0.3)',
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
