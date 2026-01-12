import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Dimensions,
  TouchableOpacity,
  Animated,
  Alert,
  Modal,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { API_BASE_URL, getEndpoint, COLORS } from '../../utils/constants';
import { useFocusEffect } from '@react-navigation/native';
import { storage } from '../../services/storage';
import { useCredits } from '../../credits/CreditContext';

const { width, height } = Dimensions.get('window');

const KarmaAnalysisScreen = ({ route, navigation }) => {
  const { chartId } = route.params || {};
  const { credits, fetchBalance } = useCredits();
  const [karmaCost, setKarmaCost] = useState(25);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);
  const [fadeAnim] = useState(new Animated.Value(0));
  const [nativeName, setNativeName] = useState('Native');
  const [selectedChartId, setSelectedChartId] = useState(chartId);
  const [showStartModal, setShowStartModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [generatingPDF, setGeneratingPDF] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const [progressTimer, setProgressTimer] = useState(null);

  useFocusEffect(
    useCallback(() => {
      loadBirthData();
      fetchKarmaCost();
    }, [])
  );

  const fetchKarmaCost = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/credits/settings/karma-cost')}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setKarmaCost(data.cost || 25);
      }
    } catch (err) {
      console.error('Error fetching karma cost:', err);
    }
  };

  const loadBirthData = async () => {
    try {
      console.log('[KarmaAnalysis] Loading birth data...');
      const birthDetails = await storage.getBirthDetails();
      console.log('[KarmaAnalysis] Birth details:', birthDetails);
      
      if (birthDetails?.name) {
        setNativeName(birthDetails.name);
      }
      if (birthDetails?.id) {
        console.log('[KarmaAnalysis] Setting selectedChartId to:', birthDetails.id);
        setSelectedChartId(birthDetails.id);
        // Reset analysis if chart changed
        if (birthDetails.id !== selectedChartId && selectedChartId) {
          console.log('[KarmaAnalysis] Chart changed, resetting analysis');
          setAnalysis(null);
          setError(null);
        }
      }
    } catch (err) {
      console.error('[KarmaAnalysis] Error loading birth data:', err);
    }
  };

  useEffect(() => {
    if (selectedChartId && !loading) {
      checkExistingAnalysis();
    }
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: true,
    }).start();
    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [selectedChartId]);

  const checkExistingAnalysis = async () => {
    try {
      if (!selectedChartId) return;
      
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint(`/karma-analysis/status?chart_id=${selectedChartId}`)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'complete' && data.data) {
          setAnalysis(data.data);
          await saveAnalysis(data.data);
        } else if (data.status === 'pending' || data.status === 'processing') {
          startProgressBar();
          startPolling();
          return;
        }
      }
      setLoading(false);
    } catch (err) {
      console.error('Error checking existing analysis:', err);
      setLoading(false);
    }
  };

  const saveAnalysis = async (data) => {
    try {
      if (!selectedChartId) return;
      await AsyncStorage.setItem(`karma_analysis_${selectedChartId}`, JSON.stringify(data));
    } catch (error) {
      console.error('Error saving analysis:', error);
    }
  };

  const handleStartAnalysis = () => {
    if (credits < karmaCost) {
      Alert.alert('Insufficient Credits', `You need ${karmaCost} credits for karma analysis.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' }
      ]);
      return;
    }
    setShowStartModal(true);
  };

  const confirmStartAnalysis = async () => {
    setShowStartModal(false);
    setLoading(true);
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
    startProgressBar();
    await initiateAnalysis(false);
  };

  const handleRegenerate = () => {
    if (credits < karmaCost) {
      Alert.alert('Insufficient Credits', `You need ${karmaCost} credits for karma analysis.`, [
        { text: 'Get Credits', onPress: () => navigation.navigate('Credits') },
        { text: 'Cancel', style: 'cancel' }
      ]);
      return;
    }
    setShowRegenerateModal(true);
  };

  const confirmRegenerate = async () => {
    setShowRegenerateModal(false);
    try {
      if (selectedChartId) {
        await AsyncStorage.removeItem(`karma_analysis_${selectedChartId}`);
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
    setAnalysis(null);
    setLoading(true);
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
    startProgressBar();
    setTimeout(() => initiateAnalysis(true), 100);
  };

  const initiateAnalysis = async (forceRegenerate = false) => {
    if (!selectedChartId) return;
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/karma-analysis')}${forceRegenerate ? '?force_regenerate=true' : ''}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ chart_id: String(selectedChartId) })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to initiate analysis');
      }
      
      const data = await response.json();
      
      if (data.status === 'complete') {
        stopProgressBar();
        setAnalysis(data.data);
        await saveAnalysis(data.data);
        await fetchBalance();
        setLoading(false);
      } else if (data.status === 'pending') {
        startPolling();
      } else {
        throw new Error('Unexpected response status');
      }
    } catch (err) {
      stopProgressBar();
      setError(err.message);
      setLoading(false);
    }
  };

  const startProgressBar = () => {
    setProgress(0);
    setShowProgress(true);
    const duration = 60000; // 60 seconds
    const steps = 600; // Update every 100ms
    let currentStep = 0;
    
    const timer = setInterval(() => {
      currentStep++;
      setProgress((currentStep / steps) * 100);
      
      if (currentStep >= steps) {
        clearInterval(timer);
        setShowProgress(false);
      }
    }, duration / steps);
    
    setProgressTimer(timer);
  };

  const stopProgressBar = () => {
    if (progressTimer) {
      clearInterval(progressTimer);
      setProgressTimer(null);
    }
    setShowProgress(false);
    setProgress(0);
  };

  const startPolling = () => {
    const interval = setInterval(async () => {
      try {
        const token = await AsyncStorage.getItem('authToken');
        const response = await fetch(`${API_BASE_URL}${getEndpoint(`/karma-analysis/status?chart_id=${selectedChartId}`)}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        
        if (data.status === 'complete') {
          stopProgressBar();
          setAnalysis(data.data);
          await saveAnalysis(data.data);
          await fetchBalance();
          setLoading(false);
          clearInterval(interval);
          setPollingInterval(null);
        } else if (data.status === 'error') {
          stopProgressBar();
          setError(data.error);
          setLoading(false);
          clearInterval(interval);
          setPollingInterval(null);
        }
      } catch (err) {
        console.error('[KarmaAnalysis] Polling error:', err);
        stopProgressBar();
        setError(err.message);
        setLoading(false);
        clearInterval(interval);
        setPollingInterval(null);
      }
    }, 2000);
    
    setPollingInterval(interval);
  };

  const generateKarmaPDF = async () => {
    if (!analysis) return;
    
    try {
      setGeneratingPDF(true);
      console.log('[PDF] Starting generation...');
      
      const sections = analysis.sections || {};
      let contentHTML = '';
      
      Object.entries(sections).forEach(([title, content]) => {
        // Format content with bold and italic
        let formattedContent = content
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
          .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic
          .replace(/\n/g, '<br>');
        
        contentHTML += `
          <div class="karma-section">
            <h2 class="section-title">🕉️ ${title}</h2>
            <div class="section-content">${formattedContent}</div>
          </div>
        `;
      });
      
      const html = `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
              * { margin: 0; padding: 0; box-sizing: border-box; }
              body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: white;
                padding: 20px;
                color: #1a1a1a;
                line-height: 1.6;
              }
              .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.1);
                border: 2px solid #FFD700;
              }
              .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #FFD700;
              }
              .logo { font-size: 48px; margin-bottom: 10px; }
              .title {
                font-size: 32px;
                font-weight: 700;
                color: #1a0033;
                margin-bottom: 5px;
                letter-spacing: 1px;
              }
              .subtitle {
                font-size: 16px;
                color: #4a0080;
                font-style: italic;
              }
              .native-name {
                font-size: 18px;
                color: #1a0033;
                margin-top: 10px;
                font-weight: 600;
              }
              .timestamp {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
              }
              .karma-section {
                background: #fef7f0;
                border-radius: 16px;
                padding: 20px;
                margin: 20px 0;
                border: 2px solid #FFD700;
              }
              .section-title {
                font-size: 20px;
                font-weight: 700;
                color: #1a0033;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
              }
              .section-content {
                font-size: 15px;
                line-height: 1.8;
                color: #1a1a1a;
                text-align: justify;
              }
              strong {
                font-weight: 700;
                color: #1a0033;
              }
              em {
                font-style: italic;
                color: #4a0080;
              }
              .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #FFD700;
                text-align: center;
                color: #666;
                font-size: 12px;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <div class="logo">🕉️</div>
                <div class="title">Past Life Karma Analysis</div>
                <div class="subtitle">Your Soul's Eternal Journey</div>
                <div class="native-name">${nativeName}</div>
                <div class="timestamp">${new Date().toLocaleString()}</div>
              </div>
              ${contentHTML}
              <div class="footer">
                ✨ Analyzed by AstroRoshni<br>
                Artificial Intelligence • Vedic Astrology
              </div>
            </div>
          </body>
        </html>
      `;
      
      console.log('[PDF] HTML generated, calling printToFileAsync...');
      const { uri } = await Promise.race([
        Print.printToFileAsync({ html }),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('PDF generation timeout after 30s')), 30000)
        )
      ]);
      
      console.log('[PDF] Generated successfully:', uri);
      console.log('[PDF] Sharing...');
      
      await Sharing.shareAsync(uri, {
        mimeType: 'application/pdf',
        dialogTitle: 'Share Karma Analysis',
        UTI: 'com.adobe.pdf',
      });
      
      console.log('[PDF] Share completed');
      setGeneratingPDF(false);
    } catch (error) {
      console.error('[PDF] Error:', error);
      setGeneratingPDF(false);
      Alert.alert('Error', `Failed to generate PDF: ${error.message}`);
    }
  };

  if (loading) {
    return (
      <LinearGradient colors={['#1a0033', '#2d004d', '#4a0080']} style={styles.container}>
        <View style={styles.topBar}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backIconButton}>
            <Text style={styles.backIcon}>←</Text>
          </TouchableOpacity>
          <View style={styles.nameChip}>
            <Text style={styles.nameChipText}>{nativeName}</Text>
          </View>
          <View style={styles.regenerateButton} />
        </View>
        <Animated.View style={[styles.loadingContainer, { opacity: fadeAnim }]}>
          <View style={styles.cosmicLoader}>
            <Text style={styles.omSymbol}>🕉️</Text>
          </View>
          <ActivityIndicator size="large" color="#FFD700" style={styles.spinner} />
          <Text style={styles.loadingTitle}>Accessing Akashic Records</Text>
          <Text style={styles.loadingSubtitle}>
            {showProgress ? 'Analyzing your soul\'s journey through time...' : 'This is taking longer than usual...'}
          </Text>
          {showProgress && (
            <View style={styles.progressBarContainer}>
              <View style={styles.progressBarBackground}>
                <View style={[styles.progressBarFill, { width: `${progress}%` }]} />
              </View>
              <Text style={styles.progressText}>{Math.round(progress)}%</Text>
            </View>
          )}
          <View style={styles.dotsContainer}>
            <View style={[styles.dot, styles.dot1]} />
            <View style={[styles.dot, styles.dot2]} />
            <View style={[styles.dot, styles.dot3]} />
          </View>
        </Animated.View>
      </LinearGradient>
    );
  }

  if (error) {
    return (
      <LinearGradient colors={['#1a0033', '#2d004d', '#4a0080']} style={styles.container}>
        <View style={styles.topBar}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backIconButton}>
            <Text style={styles.backIcon}>←</Text>
          </TouchableOpacity>
          <View style={styles.nameChip}>
            <Text style={styles.nameChipText}>{nativeName}</Text>
          </View>
          <View style={styles.regenerateButton} />
        </View>
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorTitle}>Unable to Access Records</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={initiateAnalysis}>
            <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.retryGradient}>
              <Text style={styles.retryText}>Try Again</Text>
            </LinearGradient>
          </TouchableOpacity>
          <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
            <Text style={styles.backText}>← Go Back</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    );
  }

  if (!analysis && !loading && !error) {
    return (
      <LinearGradient colors={['#1a0033', '#2d004d', '#4a0080']} style={styles.container}>
        <View style={styles.topBar}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backIconButton}>
            <Text style={styles.backIcon}>←</Text>
          </TouchableOpacity>
          <View style={styles.nameChip}>
            <Text style={styles.nameChipText}>{nativeName}</Text>
          </View>
          <View style={styles.regenerateButton} />
        </View>
        <View style={styles.startContainer}>
          <Text style={styles.omSymbol}>🕉️</Text>
          <Text style={styles.startTitle}>Past Life Karma Analysis</Text>
          <Text style={styles.startSubtitle}>Discover your soul's eternal journey</Text>
          <TouchableOpacity style={styles.startButton} onPress={handleStartAnalysis}>
            <LinearGradient colors={['#FFD700', '#FFA500']} style={styles.startGradient}>
              <Text style={styles.startButtonText}>Start Analysis</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
        <CreditModal
          visible={showStartModal}
          onClose={() => setShowStartModal(false)}
          onConfirm={confirmStartAnalysis}
          credits={credits}
          cost={karmaCost}
          title="Start Karma Analysis"
        />
      </LinearGradient>
    );
  }

  const sections = analysis?.sections || {};
  const sectionKeys = Object.keys(sections);

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1a0033', '#2d004d', '#4a0080', '#1a0033']} style={styles.backgroundGradient}>
        <View style={styles.topBar}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backIconButton}>
            <Text style={styles.backIcon}>←</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.navigate('SelectNative', { returnTo: 'KarmaAnalysis' })} style={styles.nameChip}>
            <Text style={styles.nameChipText}>{nativeName}</Text>
            <Text style={styles.nameChipIcon}>▼</Text>
          </TouchableOpacity>
          <View style={styles.topBarActions}>
            <TouchableOpacity onPress={generateKarmaPDF} style={styles.shareButton} disabled={generatingPDF}>
              <Text style={styles.shareIcon}>{generatingPDF ? '⏳' : '📤'}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={handleRegenerate} style={styles.regenerateButton}>
              <Text style={styles.regenerateIcon}>↻</Text>
            </TouchableOpacity>
          </View>
        </View>
        <CreditModal
          visible={showRegenerateModal}
          onClose={() => setShowRegenerateModal(false)}
          onConfirm={confirmRegenerate}
          credits={credits}
          cost={karmaCost}
          title="Regenerate Karma Analysis"
        />
        <ScrollView 
          showsVerticalScrollIndicator={false} 
          contentContainerStyle={styles.scrollContent}
          bounces={true}
        >
          <Animated.View style={{ opacity: fadeAnim }}>
            <View style={styles.headerContainer}>
              <View style={styles.headerGlow}>
                <Text style={styles.omHeader}>🕉️</Text>
                <Text style={styles.title}>Past Life Karma</Text>
                <Text style={styles.subtitle}>Your Soul's Eternal Journey</Text>
                <View style={styles.divider} />
              </View>
            </View>

            {sectionKeys.map((key, index) => (
              <KarmaCard key={index} title={key} content={sections[key]} index={index} />
            ))}

            <View style={styles.footerContainer}>
              <View style={styles.footerGradient}>
                <Text style={styles.footerIcon}>✨</Text>
                <Text style={styles.footerText}>Analyzed by AstroRoshni</Text>
                <Text style={styles.footerSubtext}>Artificial Intelligence</Text>
              </View>
            </View>
          </Animated.View>
        </ScrollView>
      </LinearGradient>
    </View>
  );
};

const CreditModal = ({ visible, onClose, onConfirm, credits, cost, title }) => (
  <Modal visible={visible} transparent animationType="fade">
    <View style={styles.modalOverlay}>
      <View style={styles.modalContent}>
        <Text style={styles.modalTitle}>{title}</Text>
        <Text style={styles.modalText}>This will use {cost} credits</Text>
        <Text style={styles.modalBalance}>Your balance: {credits} credits</Text>
        <View style={styles.modalButtons}>
          <TouchableOpacity style={styles.modalButton} onPress={onClose}>
            <Text style={styles.modalButtonText}>Cancel</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.modalButton, styles.modalButtonPrimary]} onPress={onConfirm}>
            <Text style={[styles.modalButtonText, styles.modalButtonTextPrimary]}>Confirm</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  </Modal>
);

const KarmaCard = ({ title, content, index }) => {
  const [expanded, setExpanded] = useState(true);
  const icons = ['🕉️', '🌟', '🎯', '⚖️', '💎', '🔱', '👪', '🦋', '🙏', '⏳', '🕉️'];
  
  const isIntroduction = title === 'Introduction';
  const cardStyle = isIntroduction 
    ? { backgroundColor: 'rgba(218, 165, 32, 0.9)', borderColor: 'rgba(218, 165, 32, 1)' }
    : { backgroundColor: 'rgba(255, 255, 255, 0.15)', borderColor: 'rgba(255, 255, 255, 0.3)' };

  const formatContent = (text) => {
    // Clean up text first
    const cleanText = text.trim();
    
    // Split by markdown patterns while preserving them
    const parts = [];
    let lastIndex = 0;
    
    // Match **bold** and *italic* patterns (non-greedy, must have closing tag)
    const regex = /\*\*(.+?)\*\*|\*([^*]+?)\*/g;
    let match;
    
    while ((match = regex.exec(cleanText)) !== null) {
      // Add text before match
      if (match.index > lastIndex) {
        parts.push({ text: cleanText.slice(lastIndex, match.index), style: 'normal' });
      }
      
      // Add matched text with style
      if (match[1]) {
        // Bold (**text**)
        parts.push({ text: match[1], style: 'bold' });
      } else if (match[2]) {
        // Italic (*text*)
        parts.push({ text: match[2], style: 'italic' });
      }
      
      lastIndex = regex.lastIndex;
    }
    
    // Add remaining text
    if (lastIndex < cleanText.length) {
      parts.push({ text: cleanText.slice(lastIndex), style: 'normal' });
    }
    
    // Clean up standalone asterisks in normal text parts only
    return parts.map(part => {
      if (part.style === 'normal') {
        // Replace asterisks with space, then clean up multiple spaces
        return { ...part, text: part.text.replace(/\*/g, ' ').replace(/\s+/g, ' ') };
      }
      return part;
    });
  };

  const renderFormattedText = (text) => {
    // Split by single or double newlines to get paragraphs
    const paragraphs = text.split(/\n+/).filter(p => p.trim().length > 0);
    
    return (
      <View>
        {paragraphs.map((para, paraIndex) => {
          const parts = formatContent(para);
          return (
            <Text key={paraIndex} style={[styles.cardContent, paraIndex > 0 && styles.paragraphSpacing]}>
              {parts.map((part, index) => (
                <Text
                  key={index}
                  style={[
                    styles.cardContent,
                    part.style === 'bold' && (isIntroduction ? styles.introBoldText : styles.boldText),
                    part.style === 'italic' && (isIntroduction ? styles.introItalicText : styles.italicText),
                  ]}
                >
                  {index === 0 ? part.text.trimStart() : part.text}
                </Text>
              ))}
            </Text>
          );
        })}
      </View>
    );
  };

  return (
    <View style={styles.cardWrapper}>
      <View style={[styles.glassCard, cardStyle]}>
        <TouchableOpacity 
          style={styles.cardHeader}
          onPress={() => setExpanded(!expanded)}
          activeOpacity={0.8}
        >
          <View style={[styles.iconCircle, isIntroduction && styles.introIconCircle]}>
            <Text style={styles.cardIcon}>{icons[index % icons.length]}</Text>
          </View>
          <Text style={styles.cardTitle}>{title}</Text>
          <Text style={styles.expandIcon}>{expanded ? '▼' : '▶'}</Text>
        </TouchableOpacity>
        {expanded && (
          <View style={styles.cardContentContainer}>
            <View style={styles.contentDivider} />
            {renderFormattedText(content)}
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a0033',
  },
  backgroundGradient: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 40,
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 10,
  },
  backIconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  backIcon: {
    fontSize: 24,
    color: '#FFD700',
  },
  nameChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.4)',
    maxWidth: '50%',
  },
  nameChipText: {
    color: '#FFD700',
    fontSize: 14,
    fontWeight: '600',
    marginRight: 6,
  },
  nameChipIcon: {
    color: '#FFD700',
    fontSize: 10,
  },
  topBarActions: {
    flexDirection: 'row',
    gap: 10,
  },
  shareButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 215, 0, 0.5)',
  },
  shareIcon: {
    fontSize: 20,
    color: '#FFD700',
  },
  regenerateButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 215, 0, 0.5)',
  },
  regenerateIcon: {
    fontSize: 24,
    color: '#FFD700',
    fontWeight: 'bold',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  cosmicLoader: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
    borderWidth: 2,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  omSymbol: {
    fontSize: 60,
  },
  spinner: {
    marginVertical: 20,
  },
  loadingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
    marginTop: 20,
    textAlign: 'center',
  },
  loadingSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 10,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  progressBarContainer: {
    width: width * 0.7,
    marginTop: 20,
    alignItems: 'center',
  },
  progressBarBackground: {
    width: '100%',
    height: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#FFD700',
    borderRadius: 4,
  },
  progressText: {
    color: '#FFD700',
    fontSize: 14,
    marginTop: 8,
    fontWeight: '600',
  },
  dotsContainer: {
    flexDirection: 'row',
    marginTop: 30,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#FFD700',
    marginHorizontal: 5,
  },
  headerContainer: {
    marginBottom: 30,
  },
  headerGlow: {
    borderRadius: 16,
    padding: 30,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 0.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  omHeader: {
    fontSize: 50,
    marginBottom: 15,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 8,
    textAlign: 'center',
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  divider: {
    width: 100,
    height: 2,
    backgroundColor: 'rgba(255, 215, 0, 0.5)',
    marginTop: 15,
    borderRadius: 1,
  },
  cardWrapper: {
    marginBottom: 20,
  },
  glassCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 16,
    borderWidth: 0.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    overflow: 'hidden',
    shadowColor: 'rgba(0, 0, 0, 0.3)',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 5,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 18,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    borderWidth: 0.5,
    borderColor: 'rgba(255, 215, 0, 0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  introIconCircle: {
    backgroundColor: 'rgba(139, 69, 19, 0.3)',
    borderColor: 'rgba(139, 69, 19, 0.6)',
  },
  cardIcon: {
    fontSize: 26,
  },
  cardTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    letterSpacing: 0.5,
  },
  expandIcon: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    marginLeft: 10,
  },
  cardContentContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  contentDivider: {
    height: 0.5,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    marginBottom: 16,
  },
  cardContent: {
    fontSize: 15,
    lineHeight: 24,
    color: 'rgba(255, 255, 255, 0.95)',
    textAlign: 'justify',
  },
  boldText: {
    fontWeight: '700',
    color: '#FFD700',
  },
  italicText: {
    fontStyle: 'italic',
    color: 'rgba(255, 215, 0, 0.9)',
  },
  introBoldText: {
    fontWeight: '700',
    color: '#4a0080',
  },
  introItalicText: {
    fontStyle: 'italic',
    color: '#4a0080',
  },
  paragraphSpacing: {
    marginTop: 12,
  },
  footerContainer: {
    marginTop: 30,
    marginBottom: 20,
  },
  footerGradient: {
    borderRadius: 16,
    padding: 25,
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 0.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  footerIcon: {
    fontSize: 30,
    marginBottom: 10,
  },
  footerText: {
    fontSize: 16,
    color: '#FFD700',
    fontWeight: 'bold',
    marginBottom: 5,
  },
  footerSubtext: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    fontStyle: 'italic',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorIcon: {
    fontSize: 60,
    marginBottom: 20,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 15,
    textAlign: 'center',
  },
  errorText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 24,
  },
  retryButton: {
    borderRadius: 30,
    overflow: 'hidden',
    marginBottom: 15,
  },
  retryGradient: {
    paddingHorizontal: 40,
    paddingVertical: 15,
  },
  retryText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a0033',
  },
  backButton: {
    marginTop: 10,
  },
  backText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  startContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  startTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFD700',
    marginTop: 20,
    textAlign: 'center',
  },
  startSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 10,
    marginBottom: 40,
    textAlign: 'center',
  },
  startButton: {
    borderRadius: 30,
    overflow: 'hidden',
  },
  startGradient: {
    paddingHorizontal: 50,
    paddingVertical: 16,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a0033',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#2d1b4e',
    borderRadius: 20,
    padding: 30,
    width: '85%',
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 15,
    textAlign: 'center',
  },
  modalText: {
    fontSize: 16,
    color: '#fff',
    marginBottom: 10,
    textAlign: 'center',
  },
  modalBalance: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 25,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 15,
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  modalButtonPrimary: {
    backgroundColor: '#FFD700',
    borderColor: '#FFD700',
  },
  modalButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
  },
  modalButtonTextPrimary: {
    color: '#1a0033',
  },
});

export default KarmaAnalysisScreen;
