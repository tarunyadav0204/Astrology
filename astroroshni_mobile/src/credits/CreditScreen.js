import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  FlatList,
  RefreshControl,
  ScrollView,
  Animated,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../utils/constants';
import { useCredits } from './CreditContext';
import { creditAPI } from './creditService';

const { width } = Dimensions.get('window');

const CreditScreen = ({ navigation }) => {
  const { credits, loading, redeemCode, fetchBalance } = useCredits();
  const [promoCode, setPromoCode] = useState('');
  const [redeeming, setRedeeming] = useState(false);
  const [history, setHistory] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scrollViewRef = useRef(null);

  useEffect(() => {
    fetchHistory();
    
    // Entrance animations
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();
    
    // Pulse animation for credit balance
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.05,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await creditAPI.getHistory();
      setHistory(response.data.transactions);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleRedeemCode = async () => {
    if (!promoCode.trim()) {
      Alert.alert('Error', 'Please enter a promo code');
      return;
    }

    setRedeeming(true);
    
    try {
      const result = await redeemCode(promoCode.trim());
      Alert.alert('Success', result.message || 'Promo code redeemed successfully!');
      setPromoCode('');
      fetchHistory();
    } catch (error) {
      console.error('❌ Redeem code error details:', {
        error,
        response: error.response,
        data: error.response?.data,
        status: error.response?.status,
        message: error.message
      });
      
      // Extract error message from different possible sources
      let errorMessage = error.message || error.detail || 'Failed to redeem code';
      
      
      // Decode HTML entities
      errorMessage = errorMessage
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&#39;/g, "'");
      
      // Provide user-friendly messages for common errors
      if (errorMessage.toLowerCase().includes('already used') || errorMessage.toLowerCase().includes('already redeemed')) {
        errorMessage = 'You have already used this promo code. Each code can only be used once per user.';
      } else if (errorMessage.toLowerCase().includes('invalid') || errorMessage.toLowerCase().includes('not found')) {
        errorMessage = 'Invalid promo code. Please check the code and try again.';
      } else if (errorMessage.toLowerCase().includes('expired')) {
        errorMessage = 'This promo code has expired and is no longer valid.';
      } else if (errorMessage.toLowerCase().includes('internal server error')) {
        errorMessage = 'Server error occurred. Please try again later.';
      }
      
      Alert.alert('Redemption Failed', errorMessage);
    } finally {
      setRedeeming(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchBalance(), fetchHistory()]);
    setRefreshing(false);
  };


  const renderTransaction = ({ item }) => (
    <View style={styles.transactionItem}>
      <View style={styles.transactionIcon}>
        <Ionicons 
          name={item.type === 'earned' ? 'add-circle' : 'remove-circle'} 
          size={20} 
          color={item.type === 'earned' ? '#4CAF50' : '#ff6b35'} 
        />
      </View>
      <View style={styles.transactionDetails}>
        <View style={styles.transactionHeader}>
          <Text style={styles.transactionDescription}>
            {item.description || item.source}
          </Text>
          <Text style={[
            styles.transactionAmount,
            { color: item.type === 'earned' ? '#4CAF50' : '#ff6b35' }
          ]}>
            {item.type === 'earned' ? '+' : '-'}{Math.abs(item.amount)}
          </Text>
        </View>
        <View style={styles.transactionFooter}>
          <Text style={styles.transactionDate}>
            {new Date(item.date).toLocaleDateString()}
          </Text>
          <Text style={styles.transactionBalance}>
            Balance: {item.balance_after}
          </Text>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#fafafa', '#f5f5f5']}
        style={styles.backgroundGradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <KeyboardAvoidingView 
            style={styles.keyboardAvoidingView}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={0}
          >
          <ScrollView 
            ref={scrollViewRef}
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            refreshControl={
              <RefreshControl 
                refreshing={refreshing} 
                onRefresh={onRefresh}
                tintColor="#ff6b35"
              />
            }
          >
            {/* Header */}
            <Animated.View 
              style={[
                styles.header,
                {
                  opacity: fadeAnim,
                  transform: [{ translateY: slideAnim }]
                }
              ]}
            >
              <TouchableOpacity 
                onPress={() => navigation.goBack()}
                style={styles.backButton}
              >
                <Ionicons name="arrow-back" size={24} color="#333" />
              </TouchableOpacity>
              
              <View style={styles.headerContent}>
                <View style={styles.cosmicOrb}>
                  <LinearGradient
                    colors={['#ff6b35', '#ffd700', '#ff6b35']}
                    style={styles.orbGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  >
                    <Ionicons name="diamond" size={32} color="white" />
                  </LinearGradient>
                </View>
                
                <Text style={styles.headerTitle}>Cosmic Credits</Text>
                <Text style={styles.headerSubtitle}>Fuel your astrological journey</Text>
              </View>
            </Animated.View>

            {/* Current Balance */}
            <Animated.View 
              style={[
                styles.balanceCard,
                {
                  opacity: fadeAnim,
                  transform: [{ scale: pulseAnim }]
                }
              ]}
            >
              <LinearGradient
                colors={['#ffffff', '#f8f9fa']}
                style={styles.balanceGradient}
              >
                <View style={styles.balanceContent}>
                  <Text style={styles.balanceLabel}>Your Balance</Text>
                  <Text style={styles.balanceAmount}>{credits}</Text>
                  <Text style={styles.balanceCreditsText}>Credits</Text>
                </View>
                
                <View style={styles.balanceDecoration}>
                  <View style={styles.decorationCircle} />
                  <View style={[styles.decorationCircle, styles.decorationCircle2]} />
                  <View style={[styles.decorationCircle, styles.decorationCircle3]} />
                </View>
              </LinearGradient>
            </Animated.View>

            {/* Promo Code Section */}
            <View style={styles.promoSection}>
              <Text style={styles.sectionTitle}>Have a Promo Code?</Text>
              <View style={styles.promoCard}>
                <View style={styles.promoInputContainer}>
                  <Ionicons name="ticket" size={20} color="#ff6b35" style={styles.promoIcon} />
                  <TextInput
                    style={styles.promoInput}
                    placeholder="Enter promo code"
                    placeholderTextColor="#999"
                    value={promoCode}
                    onChangeText={setPromoCode}
                    autoCapitalize="characters"
                    onFocus={() => {
                      setTimeout(() => {
                        scrollViewRef.current?.scrollTo({ y: 200, animated: true });
                      }, 100);
                    }}
                  />
                </View>
                <TouchableOpacity
                  style={[styles.redeemButton, redeeming && styles.buttonDisabled]}
                  onPress={handleRedeemCode}
                  disabled={redeeming}
                >
                  <LinearGradient
                    colors={redeeming ? ['#ccc', '#999'] : ['#ff6b35', '#ff8c5a']}
                    style={styles.redeemGradient}
                  >
                    <Text style={styles.redeemText}>
                      {redeeming ? 'Redeeming...' : 'Redeem'}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </View>

            {/* Transaction History */}
            <View style={styles.historySection}>
              <Text style={styles.sectionTitle}>Transaction History</Text>
              {history.length > 0 ? (
                <View style={styles.historyCard}>
                  {history.map((item, index) => (
                    <View key={index}>
                      {renderTransaction({ item })}
                      {index < history.length - 1 && <View style={styles.transactionDivider} />}
                    </View>
                  ))}
                </View>
              ) : (
                <View style={styles.emptyState}>
                  <Ionicons name="receipt-outline" size={48} color="#ccc" />
                  <Text style={styles.emptyStateText}>No transactions yet</Text>
                  <Text style={styles.emptyStateSubtext}>Your credit history will appear here</Text>
                </View>
              )}
            </View>
          </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  backgroundGradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 20,
    position: 'relative',
  },
  backButton: {
    position: 'absolute',
    left: 20,
    top: 20,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  headerContent: {
    alignItems: 'center',
  },
  cosmicOrb: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 16,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 8,
  },
  orbGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#333',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
    fontStyle: 'italic',
  },
  balanceCard: {
    marginHorizontal: 20,
    marginBottom: 24,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 8,
  },
  balanceGradient: {
    padding: 24,
    position: 'relative',
    overflow: 'hidden',
  },
  balanceContent: {
    alignItems: 'center',
    zIndex: 2,
  },
  balanceLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
    fontWeight: '500',
  },
  balanceAmount: {
    fontSize: 48,
    fontWeight: '800',
    color: '#ff6b35',
    marginBottom: 4,
  },
  balanceCreditsText: {
    fontSize: 18,
    color: '#999',
    fontWeight: '600',
  },
  balanceDecoration: {
    position: 'absolute',
    right: -20,
    top: -20,
    zIndex: 1,
  },
  decorationCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 107, 53, 0.05)',
    position: 'absolute',
  },
  decorationCircle2: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 107, 53, 0.08)',
    top: 20,
    right: 20,
  },
  decorationCircle3: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 107, 53, 0.12)',
    top: 40,
    right: 40,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 150,
  },

  sectionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#333',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 20,
    lineHeight: 22,
  },

  promoSection: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  promoCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  promoInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  promoIcon: {
    marginRight: 12,
  },
  promoInput: {
    flex: 1,
    paddingVertical: 16,
    fontSize: 16,
    color: '#333',
  },
  redeemButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  redeemGradient: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  redeemText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '700',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  historySection: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  historyCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  transactionIcon: {
    marginRight: 16,
  },
  transactionDetails: {
    flex: 1,
  },
  transactionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  transactionDescription: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  transactionAmount: {
    fontSize: 16,
    fontWeight: '700',
  },
  transactionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  transactionDate: {
    fontSize: 14,
    color: '#666',
  },
  transactionBalance: {
    fontSize: 14,
    color: '#999',
  },
  transactionDivider: {
    height: 1,
    backgroundColor: '#f0f0f0',
    marginHorizontal: 16,
  },
  emptyState: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 40,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 4,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
    marginBottom: 4,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});

export default CreditScreen;