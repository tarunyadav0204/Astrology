import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  Alert,
  Animated,
  Platform,
  Linking,
  Share,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as Speech from 'expo-speech';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { COLORS, API_BASE_URL, getEndpoint } from '../utils/constants';
import { useCredits } from '../credits/CreditContext';
import { storage } from '../services/storage';
import { useAnalytics } from '../hooks/useAnalytics';
import { trackAstrologyEvent } from '../utils/analytics';

const { width } = Dimensions.get('window');

export default function EventScreen({ route, navigation }) {
  useAnalytics('EventScreen');
  const { eventType, title, icon, color, description, cost } = route.params;
  const { credits, fetchBalance } = useCredits();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(0));
  const [birthData, setBirthData] = useState(null);

  useFocusEffect(
    useCallback(() => {
      if (fetchBalance) {
        fetchBalance().catch(err => console.log('Credit fetch error:', err));
      }
    }, [fetchBalance])
  );

  useEffect(() => {
    loadBirthData();
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 600,
      useNativeDriver: true,
    }).start();

    return () => {
      Speech.stop();
    };
  }, []);

  const loadBirthData = async () => {
    try {
      const savedData = await storage.getBirthDetails();
      if (savedData) {
        setBirthData(savedData);
      }
    } catch (error) {
      console.error('Error loading birth data:', error);
    }
  };

  const startAnalysis = async () => {
    if (credits < cost) {
      Alert.alert('Insufficient Credits', `You need ${cost} credits for this analysis.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' }
      ]);
      return;
    }

    setLoading(true);
    try {
      // Track event analysis request
      trackAstrologyEvent.analysisRequested(`event_${eventType}`);
      
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/analyze/event')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: eventType,
          ...birthData,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setAnalysis(data);
        fetchBalance();
      } else {
        throw new Error(data.message || 'Analysis failed');
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const speak = async () => {
    if (isSpeaking) {
      Speech.stop();
      setIsSpeaking(false);
      return;
    }

    if (!analysis) return;

    setIsSpeaking(true);
    const textToSpeak = `${analysis.summary}. ${analysis.details}`;
    Speech.speak(textToSpeak, {
      onDone: () => setIsSpeaking(false),
      onError: () => setIsSpeaking(false),
    });
  };

  const generatePDF = async () => {
    if (!analysis) return;

    try {
      // Track PDF generation
      trackAstrologyEvent.pdfGenerated(`event_${eventType}`);
      
      const htmlContent = `
        <html>
          <head>
            <style>
              body { font-family: 'Helvetica', sans-serif; padding: 40px; color: #333; }
              .header { text-align: center; border-bottom: 2px solid ${color}; padding-bottom: 20px; }
              .title { color: ${color}; font-size: 24px; margin-bottom: 10px; }
              .section { margin-top: 30px; }
              .section-title { font-weight: bold; color: ${color}; font-size: 18px; margin-bottom: 10px; }
              .content { line-height: 1.6; font-size: 14px; }
              .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #666; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1 class="title">${title} Analysis</h1>
              <p>For ${birthData.name}</p>
            </div>
            <div class="section">
              <div class="section-title">Summary</div>
              <div class="content">${analysis.summary}</div>
            </div>
            <div class="section">
              <div class="section-title">Detailed Insights</div>
              <div class="content">${analysis.details}</div>
            </div>
            <div class="section">
              <div class="section-title">Recommendations</div>
              <div class="content">${analysis.recommendations}</div>
            </div>
            <div class="footer">
              Generated by AstroRoshni - Your Personal Vedic Guide
            </div>
          </body>
        </html>
      `;

      const { uri } = await Print.printToFileAsync({ html: htmlContent });
      await Sharing.shareAsync(uri);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate PDF');
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <LinearGradient colors={['#1a0033', '#2d1b4e']} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>{title}</Text>
            <TouchableOpacity 
              style={styles.creditBadge}
              onPress={() => navigation.navigate('Credits')}
            >
              <Text style={styles.creditText}>💳 {credits}</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            <View style={styles.introCard}>
              <View style={[styles.iconContainer, { backgroundColor: color + '20' }]}>
                <Text style={styles.mainIcon}>{icon}</Text>
              </View>
              <Text style={styles.description}>{description}</Text>
            </View>

            {!analysis ? (
              <View style={styles.actionSection}>
                <TouchableOpacity 
                  style={styles.startButton}
                  onPress={startAnalysis}
                  disabled={loading}
                >
                  <LinearGradient
                    colors={[color, color + 'CC']}
                    style={styles.buttonGradient}
                  >
                    {loading ? (
                      <ActivityIndicator color={COLORS.white} />
                    ) : (
                      <Text style={styles.buttonText}>Start Analysis ({cost} credits)</Text>
                    )}
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            ) : (
              <Animated.View style={[styles.resultsContainer, { opacity: fadeAnim }]}>
                <View style={styles.resultCard}>
                  <View style={styles.resultHeader}>
                    <Text style={styles.resultTitle}>✨ Cosmic Summary</Text>
                    <View style={styles.resultActions}>
                      <TouchableOpacity onPress={speak} style={styles.actionIcon}>
                        <Ionicons 
                          name={isSpeaking ? "stop-circle" : "volume-high"} 
                          size={24} 
                          color={color} 
                        />
                      </TouchableOpacity>
                      <TouchableOpacity onPress={generatePDF} style={styles.actionIcon}>
                        <Ionicons name="download-outline" size={24} color={color} />
                      </TouchableOpacity>
                    </View>
                  </View>
                  <Text style={styles.summaryText}>{analysis.summary}</Text>
                </View>

                <View style={styles.resultCard}>
                  <Text style={styles.resultTitle}>📊 Detailed Analysis</Text>
                  <Text style={styles.detailsText}>{analysis.details}</Text>
                </View>

                <View style={[styles.resultCard, styles.recommendationCard]}>
                  <Text style={styles.resultTitle}>🌟 Recommendations</Text>
                  <Text style={styles.recommendationText}>{analysis.recommendations}</Text>
                </View>
              </Animated.View>
            )}
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  creditBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  creditText: {
    color: COLORS.white,
    fontWeight: '700',
    fontSize: 14,
  },
  content: { flex: 1, paddingHorizontal: 20 },
  introCard: {
    alignItems: 'center',
    padding: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 25,
    marginTop: 20,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  mainIcon: { fontSize: 40 },
  description: {
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    fontSize: 16,
    lineHeight: 24,
  },
  actionSection: { marginTop: 40 },
  startButton: { borderRadius: 15, overflow: 'hidden' },
  buttonGradient: {
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: '700',
  },
  resultsContainer: { marginTop: 20, paddingBottom: 40 },
  resultCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 20,
    padding: 20,
    marginBottom: 15,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 10,
  },
  resultActions: { flexDirection: 'row' },
  actionIcon: { marginLeft: 15 },
  summaryText: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 16,
    lineHeight: 24,
  },
  detailsText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 15,
    lineHeight: 22,
  },
  recommendationCard: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  recommendationText: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },
});
