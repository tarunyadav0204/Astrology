import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Animated,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import { useCredits } from '../../credits/CreditContext';
import { storage } from '../../services/storage';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { cleanupStorage } from '../../services/storageCleanup';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';

export default function AnalysisDetailScreen({ route, navigation }) {
  const { analysisType, title, cost } = route.params;
  const { credits, fetchBalance } = useCredits();
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [birthData, setBirthData] = useState(null);
  const [fadeAnim] = useState(new Animated.Value(0));
  const [expandedItems, setExpandedItems] = useState({});
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);

  useEffect(() => {
    checkBirthData();
    cleanupStorage();
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 600,
      useNativeDriver: true,
    }).start();
  }, []);

  useEffect(() => {
    if (birthData) {
      loadStoredAnalysis();
    }
  }, [birthData]);

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      console.log('Analysis screen focused, checking for stored data...');
      if (birthData) {
        loadStoredAnalysis();
      }
    });
    
    return unsubscribe;
  }, [navigation, birthData]);

  const checkBirthData = async () => {
    try {
      const savedBirthData = await storage.getBirthDetails();
      if (savedBirthData && savedBirthData.name) {
        setBirthData(savedBirthData);
      } else {
        Alert.alert('Birth Data Required', 'Please complete your birth details first.', [
          { text: 'OK', onPress: () => navigation.navigate('BirthForm') }
        ]);
      }
    } catch (error) {
      console.error('Error checking birth data:', error);
      navigation.navigate('BirthForm');
    }
  };

  const startAnalysis = async () => {
    if (!birthData) {
      Alert.alert('Error', 'Birth data not available');
      return;
    }

    if (credits < cost) {
      Alert.alert('Insufficient Credits', `You need ${cost} credits for this analysis.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' }
      ]);
      return;
    }

    setLoading(true);
    
    const loadingMessages = [
      '🔮 Analyzing your birth chart...',
      '⭐ Consulting the cosmic energies...',
      '📊 Calculating planetary positions...',
      '🌟 Interpreting astrological patterns...',
      '✨ Preparing your personalized insights...',
      '🌙 Reading lunar influences...',
      '☀️ Examining solar aspects...',
      '♃ Studying Jupiter blessings...',
      '♀ Analyzing Venus placements...',
      '♂ Checking Mars energy...',
      '☿ Decoding Mercury messages...',
      '♄ Understanding Saturn lessons...',
      '🐉 Exploring Rahu-Ketu axis...',
      '🏠 Examining house strengths...',
      '🔄 Calculating dasha periods...',
      '🎯 Identifying key yogas...',
      '🌊 Flowing through nakshatras...',
      '⚖️ Balancing planetary forces...',
      '🎭 Unveiling karmic patterns...',
      '🗝️ Unlocking hidden potentials...'
    ];
    
    let messageIndex = 0;
    setLoadingMessage(loadingMessages[0]);
    
    const messageInterval = setInterval(() => {
      messageIndex = (messageIndex + 1) % loadingMessages.length;
      setLoadingMessage(loadingMessages[messageIndex]);
    }, 3000);
    
    try {
      const fixedBirthData = { ...birthData };
      
      if (fixedBirthData.date && fixedBirthData.date.includes('T')) {
        fixedBirthData.date = fixedBirthData.date.split('T')[0];
      }
      
      if (fixedBirthData.time && fixedBirthData.time.includes('T')) {
        const timeDate = new Date(fixedBirthData.time);
        fixedBirthData.time = timeDate.toTimeString().slice(0, 5);
      }

      const requestBody = {
        ...fixedBirthData,
        language: 'english',
        response_style: 'detailed'
      };

      const token = await AsyncStorage.getItem('authToken');
      const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      };

      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/${analysisType}/analyze`)}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status}`);
      }

      const responseText = await response.text();
      console.log('Raw response text length:', responseText.length);
      console.log('Raw response preview:', responseText.substring(0, 500));
      
      const lines = responseText.split('\n').filter(line => line.trim());
      console.log('Filtered lines count:', lines.length);
      let fullContent = '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (data === '[DONE]') break;
          if (data && data.length > 0) {
            try {
              const parsed = JSON.parse(data);
              if (parsed.status === 'chunk') {
                fullContent += parsed.response || '';
              } else if (parsed.status === 'complete') {
                // Handle nested response structure
                if (parsed.data && parsed.data[`${analysisType}_analysis`]) {
                  const analysisData = parsed.data[`${analysisType}_analysis`];
                  if (analysisData.json_response && typeof analysisData.json_response === 'object') {
                    console.log('Setting analysis result from nested response');
                    setAnalysisResult(analysisData.json_response);
                    await saveAnalysis(analysisData.json_response);
                    fetchBalance();
                    return;
                  } else if (analysisData.raw_response) {
                    console.log('Using raw_response, json_response was null');
                    fullContent = analysisData.raw_response;
                  } else {
                    fullContent = '';
                  }
                } else {
                  fullContent = parsed.response || '';
                }
                break;
              } else if (parsed.content) {
                fullContent += parsed.content;
              }
            } catch (parseError) {
              console.warn('Parse error:', parseError);
            }
          }
        }
      }

      if (fullContent && typeof fullContent === 'string' && fullContent.trim()) {
        try {
          console.log('Processing fullContent, length:', fullContent.length);
          console.log('Content preview:', fullContent.substring(0, 500));
          
          let cleanContent = fullContent.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
          
          // Remove markdown code blocks if present
          cleanContent = cleanContent.replace(/```json\s*/g, '').replace(/```\s*$/g, '');
          
          // Try to extract JSON from the content
          const jsonMatch = cleanContent.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            console.log('Found JSON match, parsing...');
            console.log('JSON to parse:', jsonMatch[0].substring(0, 200) + '...');
            const analysisData = JSON.parse(jsonMatch[0]);
            console.log('Setting analysis result from JSON match');
            setAnalysisResult(analysisData);
            await saveAnalysis(analysisData);
            fetchBalance();
          } else {
            // If no JSON found, create a simple structure from HTML content
            console.log('No JSON found, creating simple structure from HTML');
            const htmlContent = cleanContent.replace(/<[^>]*>/g, '').trim();
            const simpleResult = {
              quick_answer: htmlContent.substring(0, 500) + (htmlContent.length > 500 ? '...' : ''),
              detailed_analysis: [{
                question: 'Health Analysis',
                answer: htmlContent
              }]
            };
            setAnalysisResult(simpleResult);
            await saveAnalysis(simpleResult);
            fetchBalance();
          }
        } catch (jsonError) {
          console.error('JSON parse error:', jsonError);
          console.log('Failed content:', fullContent.substring(0, 1000));
          Alert.alert('Error', 'Failed to parse analysis results');
        }
      } else {
        throw new Error('Empty response received');
      }

    } catch (error) {
      console.error('Analysis error:', error);
      console.log('Full response text:', responseText);
      console.log('Response lines:', lines);
      console.log('Full content:', fullContent);
      
      let errorMessage = 'Analysis failed. Please try again.';
      
      if (error.message?.includes('Network')) {
        errorMessage = 'Network error. Please check your connection.';
      } else if (error.message?.includes('timeout')) {
        errorMessage = 'Request timed out. Please try again.';
      } else if (error.message?.includes('storage')) {
        errorMessage = 'Storage error. Please restart the app.';
      } else if (error.message?.includes('Empty response')) {
        errorMessage = 'Server returned empty response. Please try again.';
      }
      
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
      setLoadingMessage('');
      clearInterval(messageInterval);
    }
  };

  const toggleExpanded = (index) => {
    setExpandedItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const formatTextWithBold = (text) => {
    if (!text) return null;
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        return <Text key={index} style={styles.boldYellowText}>{part}</Text>;
      }
      return part;
    });
  };

  const loadStoredAnalysis = async () => {
    try {
      if (!birthData?.name) {
        console.log('No birth data name available');
        return;
      }
      const key = `analysis_${analysisType}_${birthData.name}`;
      console.log('Loading stored analysis with key:', key);
      
      // Debug: List all keys
      const allKeys = await AsyncStorage.getAllKeys();
      console.log('All AsyncStorage keys:', allKeys);
      const analysisKeys = allKeys.filter(k => k.startsWith('analysis_'));
      console.log('Analysis keys found:', analysisKeys);
      
      const stored = await AsyncStorage.getItem(key);
      if (stored) {
        const parsedData = JSON.parse(stored);
        console.log('Found stored analysis:', parsedData);
        setAnalysisResult(parsedData);
      } else {
        console.log('No stored analysis found for key:', key);
      }
    } catch (error) {
      console.error('Error loading stored analysis:', error);
    }
  };

  const saveAnalysis = async (data) => {
    try {
      if (!birthData?.name) {
        console.log('Cannot save: no birth data name');
        return;
      }
      const key = `analysis_${analysisType}_${birthData.name}`;
      console.log('Saving analysis with key:', key);
      console.log('Data to save:', JSON.stringify(data).substring(0, 200) + '...');
      
      await AsyncStorage.setItem(key, JSON.stringify(data));
      
      // Verify save
      const saved = await AsyncStorage.getItem(key);
      if (saved) {
        console.log('Analysis saved and verified successfully');
      } else {
        console.error('Save verification failed');
      }
    } catch (error) {
      console.error('Failed to save analysis:', error);
    }
  };

  const regenerateAnalysis = () => {
    setShowRegenerateModal(true);
  };

  const confirmRegenerate = () => {
    setShowRegenerateModal(false);
    setAnalysisResult(null);
    startAnalysis();
  };

  const downloadPDF = async () => {
    try {
      Alert.alert(
        'Download PDF',
        `Generate ${title} report for ${birthData.name}?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Generate', onPress: generatePDF }
        ]
      );
    } catch (error) {
      console.error('PDF download error:', error);
      Alert.alert('Error', 'Failed to download PDF. Please try again.');
    }
  };

  const generatePDF = async () => {
    try {
      const htmlContent = `
        <html>
          <head>
            <style>
              body { font-family: 'Arial', sans-serif; margin: 40px; color: #333; line-height: 1.6; }
              .header { text-align: center; margin-bottom: 40px; border-bottom: 3px solid #ff6b35; padding-bottom: 20px; }
              .title { font-size: 28px; font-weight: bold; color: #4a2c6d; margin-bottom: 10px; }
              .subtitle { font-size: 16px; color: #666; margin: 5px 0; }
              .section { margin-bottom: 30px; }
              .section-title { font-size: 20px; font-weight: bold; color: #ff6b35; margin-bottom: 15px; border-left: 4px solid #ff6b35; padding-left: 15px; }
              .quick-answer { background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 20px; border-radius: 10px; border-left: 5px solid #4a2c6d; }
              .question { font-weight: bold; font-size: 16px; color: #4a2c6d; margin: 20px 0 10px 0; }
              .answer { margin-bottom: 15px; text-align: justify; }
              .key-points { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }
              .key-point { margin: 8px 0; padding-left: 20px; position: relative; }
              .key-point:before { content: '•'; color: #ff6b35; font-weight: bold; position: absolute; left: 0; }
              .final-thoughts { background: linear-gradient(135deg, #fff3e0, #ffe0b2); padding: 20px; border-radius: 10px; border: 2px solid #ff6b35; }
              .bold { font-weight: bold; color: #4a2c6d; }
              .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }
            </style>
          </head>
          <body>
            <div class="header">
              <div class="title">${title} Analysis</div>
              <div class="subtitle">Personalized Report for ${birthData.name}</div>
              <div class="subtitle">Generated on ${new Date().toLocaleDateString()}</div>
            </div>
            
            <div class="section">
              <div class="section-title">✨ Quick Insights</div>
              <div class="quick-answer">${analysisResult.quick_answer?.replace(/<[^>]*>/g, '').replace(/\*\*(.*?)\*\*/g, '<span class="bold">$1</span>') || 'No quick answer available'}</div>
            </div>
            
            ${analysisResult.detailed_analysis ? `
              <div class="section">
                <div class="section-title">📊 Detailed Analysis</div>
                ${analysisResult.detailed_analysis.map(item => `
                  <div class="question">${item.question}</div>
                  <div class="answer">${item.answer?.replace(/\*\*(.*?)\*\*/g, '<span class="bold">$1</span>') || ''}</div>
                  ${item.key_points ? `
                    <div class="key-points">
                      <strong>Key Points:</strong>
                      ${item.key_points.map(point => `<div class="key-point">${point}</div>`).join('')}
                    </div>
                  ` : ''}
                `).join('')}
              </div>
            ` : ''}
            
            ${analysisResult.final_thoughts ? `
              <div class="section">
                <div class="section-title">🌟 Final Thoughts</div>
                <div class="final-thoughts">${analysisResult.final_thoughts.replace(/\*\*(.*?)\*\*/g, '<span class="bold">$1</span>')}</div>
              </div>
            ` : ''}
            
            <div class="footer">
              This analysis is based on Vedic astrology principles and is for guidance purposes.
            </div>
          </body>
        </html>
      `;

      const { uri } = await Print.printToFileAsync({ html: htmlContent });
      await Sharing.shareAsync(uri);
    } catch (error) {
      console.error('PDF generation error:', error);
      Alert.alert('Error', 'Failed to generate PDF. Please try again.');
    }
  };

  const getAnalysisIcon = () => {
    switch (analysisType) {
      case 'wealth': return '💰';
      case 'health': return '🏥';
      case 'marriage': return '💕';
      case 'education': return '🎓';
      default: return '🔮';
    }
  };

  const getAnalysisGradient = () => {
    switch (analysisType) {
      case 'wealth': return ['#FFD700', '#FF8C00'];
      case 'health': return ['#32CD32', '#228B22'];
      case 'marriage': return ['#FF69B4', '#DC143C'];
      case 'education': return ['#4169E1', '#1E90FF'];
      default: return ['#ff6b35', '#ff8c5a'];
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradientBg}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity 
              style={styles.backButton}
              onPress={() => navigation.goBack()}
            >
              <Ionicons name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>{title}</Text>
            <View style={styles.headerRight}>
              {analysisResult && (
                <TouchableOpacity 
                  style={styles.regenerateButton}
                  onPress={regenerateAnalysis}
                >
                  <Ionicons name="refresh" size={20} color={COLORS.white} />
                </TouchableOpacity>
              )}
              {analysisResult && (
                <TouchableOpacity 
                  style={styles.pdfButton}
                  onPress={downloadPDF}
                >
                  <Ionicons name="download" size={20} color={COLORS.white} />
                </TouchableOpacity>
              )}
              <TouchableOpacity 
                style={styles.creditButton}
                onPress={() => navigation.navigate('Credits')}
              >
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.creditGradient}
                >
                  <Text style={styles.creditText}>💳 {credits}</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </View>

          <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
            {!analysisResult ? (
              <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
                <View style={styles.previewSection}>
                  <View style={styles.analysisIcon}>
                    <LinearGradient
                      colors={getAnalysisGradient()}
                      style={styles.iconGradient}
                    >
                      <Text style={styles.iconText}>{getAnalysisIcon()}</Text>
                    </LinearGradient>
                  </View>
                  <Text style={styles.analysisTitle}>{title}</Text>
                  <Text style={styles.analysisDescription}>
                    Get comprehensive insights into your {analysisType} prospects with detailed astrological analysis
                  </Text>
                  
                  {/* Debug buttons */}
                  <TouchableOpacity
                    style={styles.debugButton}
                    onPress={async () => {
                      const allKeys = await AsyncStorage.getAllKeys();
                      const analysisKeys = allKeys.filter(k => k.startsWith('analysis_'));
                      Alert.alert('Debug Info', `Birth data: ${birthData?.name}\nAnalysis keys: ${analysisKeys.join(', ')}\nExpected key: analysis_${analysisType}_${birthData?.name}`);
                    }}
                  >
                    <Text style={styles.debugText}>Debug Storage</Text>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={[styles.debugButton, { backgroundColor: 'rgba(0, 255, 0, 0.3)' }]}
                    onPress={async () => {
                      const testData = { test: 'data', timestamp: Date.now() };
                      const key = `analysis_${analysisType}_${birthData?.name}`;
                      console.log('Test save key:', key);
                      try {
                        await AsyncStorage.setItem(key, JSON.stringify(testData));
                        console.log('Test data saved');
                        const retrieved = await AsyncStorage.getItem(key);
                        console.log('Test data retrieved:', retrieved);
                        
                        // Check all keys after save
                        const allKeys = await AsyncStorage.getAllKeys();
                        const analysisKeys = allKeys.filter(k => k.startsWith('analysis_'));
                        console.log('All keys after test save:', allKeys);
                        console.log('Analysis keys after test save:', analysisKeys);
                        
                        Alert.alert('Test Save', retrieved ? `Success: ${retrieved}` : 'Failed: Could not retrieve data');
                      } catch (error) {
                        console.error('Test save error:', error);
                        Alert.alert('Test Save Error', error.message);
                      }
                    }}
                  >
                    <Text style={styles.debugText}>Test Save</Text>
                  </TouchableOpacity>
                </View>

                <TouchableOpacity
                  style={styles.startButton}
                  onPress={startAnalysis}
                  disabled={loading || credits < cost}
                >
                  <LinearGradient
                    colors={loading ? ['#666', '#888'] : getAnalysisGradient()}
                    style={styles.startGradient}
                  >
                    <Text style={styles.startButtonText}>
                      {loading ? loadingMessage : `Start Analysis (${cost} credits)`}
                    </Text>
                    {loading && <Text style={styles.loadingIcon}>⏳</Text>}
                  </LinearGradient>
                </TouchableOpacity>

                {credits < cost && (
                  <TouchableOpacity 
                    style={styles.lowCreditBanner}
                    onPress={() => navigation.navigate('Credits')}
                  >
                    <Text style={styles.lowCreditText}>💳 Get more credits to continue</Text>
                  </TouchableOpacity>
                )}
              </ScrollView>
            ) : (
              <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
                <View style={styles.quickAnswerSection}>
                  <LinearGradient
                    colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
                    style={styles.quickAnswerCard}
                  >
                    <Text style={styles.quickAnswerTitle}>✨ Quick Insights</Text>
                    <Text style={styles.quickAnswerText}>{formatTextWithBold(analysisResult.quick_answer)}</Text>
                  </LinearGradient>
                </View>

                {analysisResult.detailed_analysis && (
                  <View style={styles.detailedSection}>
                    <Text style={styles.sectionTitle}>📋 Detailed Analysis</Text>
                    {analysisResult.detailed_analysis.map((item, index) => (
                      <View key={index} style={styles.analysisItem}>
                        <TouchableOpacity
                          style={styles.analysisHeader}
                          onPress={() => toggleExpanded(index)}
                        >
                          <LinearGradient
                            colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                            style={styles.analysisHeaderGradient}
                          >
                            <Text style={styles.questionText}>{item.question}</Text>
                            <Ionicons 
                              name={expandedItems[index] ? "chevron-up" : "chevron-down"} 
                              size={20} 
                              color="rgba(255, 255, 255, 0.8)" 
                            />
                          </LinearGradient>
                        </TouchableOpacity>
                        
                        {expandedItems[index] && (
                          <View style={styles.answerSection}>
                            <Text style={styles.answerText}>{formatTextWithBold(item.answer)}</Text>
                            {item.key_points && item.key_points.length > 0 && (
                              <View style={styles.keyPointsSection}>
                                <Text style={styles.keyPointsTitle}>Key Points:</Text>
                                {item.key_points.map((point, pointIndex) => (
                                  <Text key={pointIndex} style={styles.keyPoint}>• {point}</Text>
                                ))}
                              </View>
                            )}
                            {item.astrological_basis && (
                              <View style={styles.basisSection}>
                                <Text style={styles.basisTitle}>Astrological Basis:</Text>
                                <Text style={styles.basisText}>{item.astrological_basis}</Text>
                              </View>
                            )}
                          </View>
                        )}
                      </View>
                    ))}
                  </View>
                )}

                {analysisResult.final_thoughts && (
                  <View style={styles.finalSection}>
                    <LinearGradient
                      colors={getAnalysisGradient()}
                      style={styles.finalCard}
                    >
                      <Text style={styles.finalTitle}>🌟 Final Thoughts</Text>
                      <Text style={styles.finalText}>{formatTextWithBold(analysisResult.final_thoughts)}</Text>
                    </LinearGradient>
                  </View>
                )}

                {analysisResult.follow_up_questions && (
                  <View style={styles.followUpSection}>
                    <Text style={styles.sectionTitle}>💭 Explore Further</Text>
                    {analysisResult.follow_up_questions.map((question, index) => (
                      <TouchableOpacity
                        key={index}
                        style={styles.followUpButton}
                        onPress={() => navigation.navigate('Chat')}
                      >
                        <LinearGradient
                          colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                          style={styles.followUpGradient}
                        >
                          <Text style={styles.followUpText}>{question}</Text>
                          <Ionicons name="arrow-forward" size={16} color="rgba(255, 255, 255, 0.8)" />
                        </LinearGradient>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </ScrollView>
            )}
          </Animated.View>

          {/* Regenerate Modal */}
          {showRegenerateModal && (
            <View style={styles.modalOverlay}>
              <View style={styles.modalContainer}>
                <LinearGradient
                  colors={['rgba(26, 0, 51, 0.95)', 'rgba(77, 44, 109, 0.95)']}
                  style={styles.modalContent}
                >
                  <Text style={styles.modalTitle}>🔄 Regenerate Analysis</Text>
                  <Text style={styles.modalText}>
                    This will create a fresh {title.toLowerCase()} analysis with new insights.
                  </Text>
                  <View style={styles.modalCreditInfo}>
                    <Text style={styles.modalCreditText}>💳 Credits to be charged: {cost}</Text>
                    <Text style={styles.modalBalanceText}>Current balance: {credits}</Text>
                  </View>
                  <View style={styles.modalButtons}>
                    <TouchableOpacity
                      style={styles.modalCancelButton}
                      onPress={() => setShowRegenerateModal(false)}
                    >
                      <Text style={styles.modalCancelText}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.modalConfirmButton}
                      onPress={confirmRegenerate}
                    >
                      <LinearGradient
                        colors={getAnalysisGradient()}
                        style={styles.modalConfirmGradient}
                      >
                        <Text style={styles.modalConfirmText}>Regenerate</Text>
                      </LinearGradient>
                    </TouchableOpacity>
                  </View>
                </LinearGradient>
              </View>
            </View>
          )}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradientBg: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
  },
  creditButton: { borderRadius: 18, overflow: 'hidden' },
  creditGradient: { paddingHorizontal: 14, paddingVertical: 8 },
  creditText: { color: COLORS.white, fontSize: 14, fontWeight: '700' },
  content: { flex: 1 },
  scrollView: { flex: 1 },
  scrollContent: { paddingBottom: 30 },
  previewSection: {
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 20,
  },
  analysisIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 20,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6,
    shadowRadius: 16,
    elevation: 10,
  },
  iconGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  iconText: { fontSize: 40 },
  analysisTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 12,
  },
  analysisDescription: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 24,
  },
  startButton: {
    marginHorizontal: 20,
    marginVertical: 20,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
  startGradient: {
    paddingVertical: 18,
    paddingHorizontal: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  startButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
    marginRight: 8,
    textAlign: 'center',
    flex: 1,
  },
  loadingIcon: { fontSize: 18 },
  lowCreditBanner: {
    marginHorizontal: 20,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  lowCreditText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  quickAnswerSection: { paddingHorizontal: 20, paddingVertical: 20 },
  quickAnswerCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  quickAnswerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  quickAnswerText: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 22,
  },
  detailedSection: { paddingHorizontal: 20 },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 16,
  },
  analysisItem: { marginBottom: 12, borderRadius: 12, overflow: 'hidden' },
  analysisHeader: { borderRadius: 12, overflow: 'hidden' },
  analysisHeaderGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  questionText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
    marginRight: 12,
  },
  answerSection: { backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: 16 },
  answerText: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 22,
    marginBottom: 12,
  },
  keyPointsSection: { marginBottom: 12 },
  keyPointsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 8,
  },
  keyPoint: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 20,
    marginBottom: 4,
  },
  basisSection: { marginTop: 8 },
  basisTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 6,
  },
  basisText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 18,
    fontStyle: 'italic',
  },
  finalSection: { paddingHorizontal: 20, paddingVertical: 20 },
  finalCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  finalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
  },
  finalText: { fontSize: 15, color: COLORS.white, lineHeight: 22 },
  followUpSection: { paddingHorizontal: 20, paddingBottom: 20 },
  followUpButton: { marginBottom: 8, borderRadius: 12, overflow: 'hidden' },
  followUpGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  followUpText: {
    flex: 1,
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginRight: 12,
  },
  boldYellowText: {
    fontWeight: 'bold',
    color: '#FFD700',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  regenerateButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pdfButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  debugButton: {
    marginTop: 20,
    padding: 10,
    backgroundColor: 'rgba(255, 0, 0, 0.3)',
    borderRadius: 8,
  },
  debugText: {
    color: COLORS.white,
    fontSize: 12,
    textAlign: 'center',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContainer: {
    marginHorizontal: 20,
    borderRadius: 16,
    overflow: 'hidden',
  },
  modalContent: {
    padding: 24,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 12,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 20,
  },
  modalCreditInfo: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
    width: '100%',
  },
  modalCreditText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 4,
  },
  modalBalanceText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  modalCancelButton: {
    flex: 0.8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  modalCancelText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
  modalConfirmButton: {
    flex: 1.2,
    borderRadius: 12,
    overflow: 'hidden',
  },
  modalConfirmGradient: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  modalConfirmText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    numberOfLines: 1,
  },
});