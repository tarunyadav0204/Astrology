import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  Animated,
  Alert,
  StyleSheet,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';

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
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/chat/feedback/submit')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message_id: String(message.messageId),
          rating: feedback.rating,
          comment: feedback.comment.trim() || null
        })
      });

      if (response.ok) {
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
        }, 2000);
      } else {
        Alert.alert('Error', 'Failed to submit feedback');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to submit feedback');
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
        <Text style={[styles.thanksText, { color: colors.primary }]}>Thanks for your feedback! 🙏</Text>
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
  },
});