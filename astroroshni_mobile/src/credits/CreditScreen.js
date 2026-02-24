import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  Modal,
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
import { useTheme } from '../context/ThemeContext';
import { useCredits } from './CreditContext';
import { creditAPI } from './creditService';
import { useAnalytics } from '../hooks/useAnalytics';

const { width } = Dimensions.get('window');

// Lazy-load IAP only on Android to avoid iOS/build issues
let RNIap = null;
if (Platform.OS === 'android') {
  try {
    RNIap = require('react-native-iap');
  } catch (e) {
    console.warn('react-native-iap not available:', e?.message);
  }
}

const CreditScreen = ({ navigation }) => {
  useAnalytics('CreditScreen');
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const { credits, loading, redeemCode, fetchBalance } = useCredits();
  const [promoCode, setPromoCode] = useState('');
  const [redeeming, setRedeeming] = useState(false);
  const [history, setHistory] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [purchasingProductId, setPurchasingProductId] = useState(null);
  const [iapReady, setIapReady] = useState(false);
  const [googlePlayProducts, setGooglePlayProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [purchaseModal, setPurchaseModal] = useState({ visible: false, type: 'success', title: '', message: '', creditsAdded: 0 });
  const purchaseListenerRef = useRef(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scrollViewRef = useRef(null);

  /** Call this after a successful Google Play purchase (e.g. from react-native-iap listener). */
  const handleGooglePlayPurchaseSuccess = async (purchaseToken, productId, orderId) => {
    if (!purchaseToken || !productId || !orderId) return;
    setPurchasingProductId(productId);
    try {
      const { data } = await creditAPI.verifyGooglePlayPurchase(purchaseToken, productId, orderId);
      await fetchBalance();
      await fetchHistory();
      const isAlreadyCredited = data.credits_added === 0 && (data.message || '').toLowerCase().includes('already credited');
      setPurchaseModal({
        visible: true,
        type: isAlreadyCredited ? 'already_credited' : 'success',
        title: isAlreadyCredited ? 'Already credited' : 'Thank you!',
        message: isAlreadyCredited
          ? 'This purchase was already added to your balance. Your credits are safe and ready to use.'
          : `${data.message || 'Credits added.'}${data.credits_added ? ` ${data.credits_added} credits have been added to your balance.` : ''}`,
        creditsAdded: data.credits_added || 0,
      });
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to add credits';
      setPurchaseModal({
        visible: true,
        type: 'error',
        title: 'Purchase verification failed',
        message: msg,
        creditsAdded: 0,
      });
    } finally {
      setPurchasingProductId(null);
    }
  };

  const closePurchaseModal = () => setPurchaseModal((prev) => ({ ...prev, visible: false }));

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
    
    // Refresh credits when screen comes into focus
    const unsubscribe = navigation.addListener('focus', () => {
      fetchBalance();
    });
    
    return unsubscribe;
  }, [navigation]);

  // Fetch Google Play products from backend (Android only)
  useEffect(() => {
    if (Platform.OS !== 'android') return;
    let mounted = true;
    const fetchProducts = async () => {
      setProductsLoading(true);
      try {
        const { data } = await creditAPI.getGooglePlayProducts();
        if (mounted && Array.isArray(data?.products)) setGooglePlayProducts(data.products);
      } catch (e) {
        if (mounted) setGooglePlayProducts([]);
        console.warn('Failed to load Google Play products:', e?.message);
      } finally {
        if (mounted) setProductsLoading(false);
      }
    };
    fetchProducts();
  }, []);

  // Google Play IAP: init connection and purchase listener (Android only)
  const productIds = googlePlayProducts.map((p) => p.product_id);
  useEffect(() => {
    if (Platform.OS !== 'android' || !RNIap || productIds.length === 0) return;
    let mounted = true;
    const initIap = async () => {
      try {
        await RNIap.initConnection();
        if (!mounted) return;
        await RNIap.flushFailedPurchasesCachedAsPendingAndroid?.();
        await RNIap.getProducts({ skus: productIds });
        if (!mounted) return;
        setIapReady(true);
      } catch (e) {
        if (mounted) setIapReady(false);
        console.warn('IAP init failed:', e?.message);
      }
    };
    initIap();
    const updateSub = RNIap.purchaseUpdatedListener(async (purchase) => {
      try {
        const token = purchase.purchaseToken ?? purchase.purchaseTokenAndroid;
        const productId = purchase.productId ?? purchase.productIds?.[0];
        const orderId = purchase.transactionId ?? purchase.transactionIdAndroid ?? purchase.purchaseToken;
        if (token && productId && orderId) {
          await handleGooglePlayPurchaseSuccess(token, productId, orderId);
          await RNIap.finishTransaction({ purchase, isConsumable: true });
        }
      } catch (e) {
        console.warn('Purchase listener error:', e?.message);
      }
    });
    const errorSub = RNIap.purchaseErrorListener?.((error) => {
      setPurchasingProductId(null);
      if (error?.code !== 'E_USER_CANCELLED') {
        console.warn('Purchase error:', error?.message);
      }
    });
    purchaseListenerRef.current = { updateSub, errorSub };
    return () => {
      mounted = false;
      try {
        updateSub?.remove?.();
        errorSub?.remove?.();
        RNIap.endConnection?.();
      } catch (e) {
        console.warn('IAP cleanup:', e?.message);
      }
    };
  }, [productIds.join(',')]);

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

  const handleBuyCreditsPress = async (product) => {
    if (Platform.OS !== 'android') return;
    if (!RNIap) {
      Alert.alert('Not available', 'In-app purchase is not available on this device.');
      return;
    }
    if (!iapReady) {
      Alert.alert('Loading…', 'Store is loading. Please try again in a moment.');
      return;
    }
    const productId = product.product_id || product.id;
    setPurchasingProductId(productId);
    try {
      await RNIap.requestPurchase({ skus: [productId] });
    } catch (e) {
      if (e?.code !== 'E_USER_CANCELLED') {
        Alert.alert('Purchase failed', e?.message ?? 'Could not start purchase. Try again.');
      }
      setPurchasingProductId(null);
    }
  };


  const bgGradient = isDark
    ? [colors.gradientStart, colors.gradientMid, colors.gradientEnd]
    : [colors.gradientStart, colors.gradientMid];
  const balanceCardGradient = isDark
    ? [colors.cardBackground, colors.surface]
    : [colors.cardBackground, colors.backgroundSecondary];
  const promoCardBg = colors.cardBackground;
  const promoInputBg = isDark ? colors.surface : colors.backgroundSecondary;
  const backButtonBg = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.9)';

  const renderTransaction = ({ item }) => (
    <View style={styles.transactionItem}>
      <View style={styles.transactionIcon}>
        <Ionicons
          name={item.type === 'earned' ? 'add-circle' : 'remove-circle'}
          size={20}
          color={item.type === 'earned' ? colors.success : colors.primary}
        />
      </View>
      <View style={styles.transactionDetails}>
        <View style={styles.transactionHeader}>
          <Text style={[styles.transactionDescription, { color: colors.text }]}>
            {item.description || item.source}
          </Text>
          <Text style={[styles.transactionAmount, { color: item.type === 'earned' ? colors.success : colors.primary }]}>
            {item.type === 'earned' ? '+' : '-'}{Math.abs(item.amount)}
          </Text>
        </View>
        <View style={styles.transactionFooter}>
          <Text style={[styles.transactionDate, { color: colors.textSecondary }]}>
            {new Date(item.date).toLocaleDateString()}
          </Text>
          <Text style={[styles.transactionBalance, { color: colors.textTertiary }]}>
            Balance: {item.balance_after}
          </Text>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={bgGradient}
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
                tintColor={colors.primary}
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
                style={[styles.backButton, { backgroundColor: backButtonBg }]}
              >
                <Ionicons name="arrow-back" size={24} color={colors.text} />
              </TouchableOpacity>

              <View style={styles.headerContent}>
                <View style={styles.cosmicOrb}>
                  <LinearGradient
                    colors={[colors.primary, colors.accent, colors.primary]}
                    style={styles.orbGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  >
                    <Ionicons name="diamond" size={32} color="white" />
                  </LinearGradient>
                </View>

                <Text style={[styles.headerTitle, { color: colors.text }]}>Cosmic Credits</Text>
                <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>Fuel your astrological journey</Text>
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
                colors={balanceCardGradient}
                style={styles.balanceGradient}
              >
                <View style={styles.balanceContent}>
                  <Text style={[styles.balanceLabel, { color: colors.textSecondary }]}>Your Balance</Text>
                  <Text style={[styles.balanceAmount, { color: colors.primary }]}>{credits}</Text>
                  <Text style={[styles.balanceCreditsText, { color: colors.textTertiary }]}>Credits</Text>
                </View>

                <View style={styles.balanceDecoration}>
                  <View style={[styles.decorationCircle, { backgroundColor: isDark ? 'rgba(249,115,22,0.08)' : 'rgba(255,107,53,0.05)' }]} />
                  <View style={[styles.decorationCircle, styles.decorationCircle2, { backgroundColor: isDark ? 'rgba(249,115,22,0.12)' : 'rgba(255,107,53,0.08)' }]} />
                  <View style={[styles.decorationCircle, styles.decorationCircle3, { backgroundColor: isDark ? 'rgba(249,115,22,0.15)' : 'rgba(255,107,53,0.12)' }]} />
                </View>
              </LinearGradient>
            </Animated.View>

            {/* Promo Code Section */}
            <View style={styles.promoSection}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Have a Promo Code?</Text>
              <View style={[styles.promoCard, { backgroundColor: promoCardBg, borderWidth: isDark ? 1 : 0, borderColor: colors.cardBorder }]}>
                <View style={[styles.promoInputContainer, { backgroundColor: promoInputBg, borderColor: colors.cardBorder }]}>
                  <Ionicons name="ticket" size={20} color={colors.primary} style={styles.promoIcon} />
                  <TextInput
                    style={[styles.promoInput, { color: colors.text }]}
                    placeholder="Enter promo code"
                    placeholderTextColor={colors.textTertiary}
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
                    colors={redeeming ? [colors.textTertiary, colors.textSecondary] : [colors.primary, colors.secondary]}
                    style={styles.redeemGradient}
                  >
                    <Text style={styles.redeemText}>
                      {redeeming ? 'Redeeming...' : 'Redeem'}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </View>

            {/* Buy credits (Google Play) - Android only; products fetched from backend/Play */}
            {Platform.OS === 'android' && (
              <View style={styles.buySection}>
                <Text style={[styles.sectionTitle, { color: colors.text }]}>Buy Credits</Text>
                {productsLoading ? (
                  <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>Loading products…</Text>
                ) : googlePlayProducts.length === 0 ? (
                  <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>No products available. Check back later.</Text>
                ) : (
                  <View style={styles.buyProductGrid}>
                    {googlePlayProducts.map((product) => (
                      <TouchableOpacity
                        key={product.product_id}
                        style={[styles.buyProductCard, { backgroundColor: promoCardBg, borderWidth: isDark ? 1 : 0, borderColor: colors.cardBorder }]}
                        onPress={() => handleBuyCreditsPress(product)}
                        disabled={purchasingProductId === product.product_id}
                      >
                        <Text style={[styles.buyProductLabel, { color: colors.text }]}>{product.title || `${product.credits} Credits`}</Text>
                        <Text style={[styles.buyProductCredits, { color: colors.primary }]}>{product.credits} credits</Text>
                        <View style={[styles.buyProductButton, { backgroundColor: colors.primary }]}>
                          <Text style={styles.buyProductButtonText}>
                            {purchasingProductId === product.product_id ? 'Processing…' : 'Buy'}
                          </Text>
                        </View>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </View>
            )}

            {/* Request Credits Section */}
            <View style={styles.requestSection}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Need More Credits?</Text>
              <TouchableOpacity
                style={styles.requestButton}
                onPress={() => navigation.navigate('CreditRequest')}
              >
                <LinearGradient
                  colors={[colors.success, '#34ce57']}
                  style={styles.requestGradient}
                >
                  <Ionicons name="hand-right" size={20} color="white" style={styles.requestIcon} />
                  <Text style={styles.requestText}>Request Credits</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>

            {/* Transaction History */}
            <View style={styles.historySection}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>Transaction History</Text>
              {history.length > 0 ? (
                <View style={[styles.historyCard, { backgroundColor: promoCardBg, borderWidth: isDark ? 1 : 0, borderColor: colors.cardBorder }]}>
                  {history.map((item, index) => (
                    <View key={index}>
                      {renderTransaction({ item })}
                      {index < history.length - 1 && <View style={[styles.transactionDivider, { backgroundColor: colors.cardBorder }]} />}
                    </View>
                  ))}
                </View>
              ) : (
                <View style={[styles.emptyState, { backgroundColor: promoCardBg, borderWidth: isDark ? 1 : 0, borderColor: colors.cardBorder }]}>
                  <Ionicons name="receipt-outline" size={48} color={colors.textTertiary} />
                  <Text style={[styles.emptyStateText, { color: colors.textSecondary }]}>No transactions yet</Text>
                  <Text style={[styles.emptyStateSubtext, { color: colors.textTertiary }]}>Your credit history will appear here</Text>
                </View>
              )}
            </View>
          </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </LinearGradient>

      {/* Purchase result modal */}
      <Modal
        visible={purchaseModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closePurchaseModal}
      >
        <TouchableOpacity
          activeOpacity={1}
          style={styles.modalOverlay}
          onPress={closePurchaseModal}
        >
          <TouchableOpacity activeOpacity={1} onPress={(e) => e.stopPropagation()} style={styles.modalContentWrap}>
            <View style={[styles.purchaseModalCard, { backgroundColor: promoCardBg, borderColor: colors.cardBorder }]}>
              <View style={[styles.purchaseModalIconWrap, { backgroundColor: purchaseModal.type === 'error' ? (isDark ? 'rgba(239,68,68,0.15)' : 'rgba(239,68,68,0.12)') : purchaseModal.type === 'already_credited' ? (isDark ? 'rgba(59,130,246,0.15)' : 'rgba(59,130,246,0.12)') : (isDark ? 'rgba(34,197,94,0.15)' : 'rgba(34,197,94,0.12)') }]}>
                <Ionicons
                  name={purchaseModal.type === 'error' ? 'alert-circle' : purchaseModal.type === 'already_credited' ? 'information-circle' : 'checkmark-circle'}
                  size={48}
                  color={purchaseModal.type === 'error' ? '#ef4444' : purchaseModal.type === 'already_credited' ? '#3b82f6' : colors.success}
                />
              </View>
              <Text style={[styles.purchaseModalTitle, { color: colors.text }]}>{purchaseModal.title}</Text>
              <Text style={[styles.purchaseModalMessage, { color: colors.textSecondary }]}>{purchaseModal.message}</Text>
              {purchaseModal.creditsAdded > 0 && (
                <View style={[styles.purchaseModalCreditsBadge, { backgroundColor: isDark ? 'rgba(34,197,94,0.2)' : 'rgba(34,197,94,0.15)' }]}>
                  <Text style={[styles.purchaseModalCreditsText, { color: colors.success }]}>+{purchaseModal.creditsAdded} credits</Text>
                </View>
              )}
              <TouchableOpacity
                style={styles.purchaseModalButtonWrap}
                onPress={closePurchaseModal}
                activeOpacity={0.9}
              >
                <LinearGradient
                  colors={purchaseModal.type === 'error' ? [colors.primary, colors.secondary] : [colors.success, '#22c55e']}
                  style={styles.purchaseModalButton}
                >
                  <Text style={styles.purchaseModalButtonText}>Got it</Text>
                </LinearGradient>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
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
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 16,
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
    marginBottom: 8,
    fontWeight: '500',
  },
  balanceAmount: {
    fontSize: 48,
    fontWeight: '800',
    marginBottom: 4,
  },
  balanceCreditsText: {
    fontSize: 18,
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
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 16,
    marginBottom: 20,
    lineHeight: 22,
  },

  promoSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  buySection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  buyProductGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  buyProductPlaceholder: {
    fontSize: 14,
    paddingVertical: 12,
    textAlign: 'center',
  },
  buyProductCard: {
    width: (width - 52) / 2 - 6,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
  },
  buyProductLabel: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  buyProductCredits: {
    fontSize: 14,
    marginBottom: 12,
  },
  buyProductButton: {
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  buyProductButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  requestSection: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  requestButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  requestGradient: {
    paddingVertical: 16,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
  },
  requestIcon: {
    marginRight: 8,
  },
  requestText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '700',
  },
  promoCard: {
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
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
    borderWidth: 1,
  },
  promoIcon: {
    marginRight: 12,
  },
  promoInput: {
    flex: 1,
    paddingVertical: 16,
    fontSize: 16,
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
  },
  transactionBalance: {
    fontSize: 14,
  },
  transactionDivider: {
    height: 1,
    marginHorizontal: 16,
  },
  emptyState: {
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
    marginTop: 16,
    marginBottom: 4,
  },
  emptyStateSubtext: {
    fontSize: 14,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContentWrap: {
    width: '100%',
    maxWidth: 340,
  },
  purchaseModalCard: {
    borderRadius: 24,
    padding: 28,
    alignItems: 'center',
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.2,
    shadowRadius: 24,
    elevation: 12,
  },
  purchaseModalIconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  purchaseModalTitle: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
  },
  purchaseModalMessage: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
    marginBottom: 20,
  },
  purchaseModalCreditsBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
    marginBottom: 20,
  },
  purchaseModalCreditsText: {
    fontSize: 18,
    fontWeight: '700',
  },
  purchaseModalButtonWrap: {
    borderRadius: 14,
    overflow: 'hidden',
    width: '100%',
  },
  purchaseModalButton: {
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  purchaseModalButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '700',
  },
});

export default CreditScreen;