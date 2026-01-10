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
import { API_BASE_URL, getEndpoint } from '../../utils/constants';
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
      const birthDetails = await storage.getBirthDetails();
      if (birthDetails?.name) {
        setNativeName(birthDetails.name);
      }
      if (birthDetails?.id) {
        // If chartId changed, reset analysis and load new one
        if (birthDetails.id !== selectedChartId) {
          setSelectedChartId(birthDetails.id);
          setAnalysis(null);
          setError(null);
        }
      }
    } catch (err) {
      console.error('Error loading birth data:', err);
    }
  };

  useEffect(() => {
    if (selectedChartId) {
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

  const confirmStartAnalysis = () => {
    setShowStartModal(false);
    setLoading(true);
    initiateAnalysis(false);
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
      setError(err.message);
      setLoading(false);
    }
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
          setAnalysis(data.data);
          await saveAnalysis(data.data);
          await fetchBalance();
          setLoading(false);
          clearInterval(interval);
        } else if (data.status === 'error') {
          setError(data.error);
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        setError(err.message);
        setLoading(false);
        clearInterval(interval);
      }
    }, 2000);
    
    setPollingInterval(interval);
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
          <Text style={styles.loadingSubtitle}>Analyzing your soul's journey through time...</Text>
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
          <TouchableOpacity onPress={handleRegenerate} style={styles.regenerateButton}>
            <Text style={styles.regenerateIcon}>↻</Text>
          </TouchableOpacity>
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
    return text
      .replace(/###\s*(.+?)\n/g, '\n$1\n')
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/^\s*[-*]\s+/gm, '• ')
      .replace(/^\s*(\d+\.\s+)/gm, '$1')
      .replace(/^(•.+)$/gm, '$1\n')
      .replace(/^(\d+\..+)$/gm, '$1\n')
      .replace(/\n{3,}/g, '\n\n');
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
          <Text style={styles.cardTitle} numberOfLines={2}>{formatContent(title)}</Text>
          <Text style={styles.expandIcon}>{expanded ? '▼' : '▶'}</Text>
        </TouchableOpacity>
        {expanded && (
          <View style={styles.cardContentContainer}>
            <View style={styles.contentDivider} />
            <Text style={styles.cardContent}>{formatContent(content)}</Text>
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
