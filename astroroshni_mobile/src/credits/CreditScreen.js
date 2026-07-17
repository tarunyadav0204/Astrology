import React, { useState, useEffect, useRef, useMemo, useLayoutEffect } from 'react';
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
  Linking,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../context/ThemeContext';
import { useCredits } from './CreditContext';
import { creditAPI } from './creditService';
import { useAnalytics } from '../hooks/useAnalytics';
import { trackAstrologyEvent } from '../utils/analytics';
import { useTranslation } from 'react-i18next';
import { appLocaleForI18n } from '../utils/appLocale';
import {
  creditsFromGooglePlayProductId,
  resolveUserChoiceCatalogSkus,
  userChoiceIapLog,
  describeUserChoiceRawProductsForLog,
} from './androidUserChoiceRazorpay';
import { getCreditPackMeta } from './creditPackCatalog';
import { openRazorpayCheckout } from '../platform/payments';
import { useAuthGate } from '../auth/AuthGateContext';
import { useFocusEffect } from '@react-navigation/native';

const { width } = Dimensions.get('window');
const PENDING_GOOGLE_PLAY_CREDIT_PURCHASES_KEY = 'pendingGooglePlayCreditPurchasesV1';
const PACK_RELAUNCH_BANNER_KEY = 'creditPackRelaunchBannerDismissedV1';


/** Map react-native-iap v14 product shapes to fields used by this screen (legacy v12-style accessors). */
function normalizeIapProductForLegacyHelpers(raw) {
  if (!raw) return raw;
  const productId = raw.productId || raw.id;
  const o = raw.oneTimePurchaseOfferDetails || raw.oneTimePurchaseOfferDetailsAndroid;
  const oneTime = o
    ? {
        priceAmountMicros: o.priceAmountMicros,
        priceCurrencyCode: o.priceCurrencyCode,
        formattedPrice: o.formattedPrice,
      }
    : raw.oneTimePurchaseOfferDetails;
  const offers = raw.subscriptionOfferDetails || raw.subscriptionOfferDetailsAndroid;
  let subscriptionOfferDetails = raw.subscriptionOfferDetails;
  if (Array.isArray(offers)) {
    subscriptionOfferDetails = offers.map((x) => ({
      offerToken: x.offerToken,
      pricingPhases: x.pricingPhases || { pricingPhaseList: x.pricingPhases?.pricingPhaseList || [] },
    }));
  }
  return {
    ...raw,
    productId,
    product_id: productId,
    localizedPrice: raw.localizedPrice || raw.displayPrice,
    oneTimePurchaseOfferDetails: oneTime,
    subscriptionOfferDetails,
  };
}

function getIapPriceNumber(iapProduct) {
  const offer = iapProduct?.oneTimePurchaseOfferDetails || {};
  const micros = offer.priceAmountMicros ? parseInt(offer.priceAmountMicros, 10) : 0;
  if (micros > 0) return micros / 1_000_000;
  const localized = iapProduct?.localizedPrice || iapProduct?.price;
  if (typeof localized === 'string') {
    const parsed = parseFloat(localized.replace(/[^\d.]/g, ''));
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function getIapCurrency(iapProduct) {
  return (
    iapProduct?.oneTimePurchaseOfferDetails?.priceCurrencyCode ||
    iapProduct?.currency ||
    'INR'
  );
}

function subscriptionHasFreeTrial(subscription) {
  const phases = subscription?.subscriptionOfferDetails?.[0]?.pricingPhases?.pricingPhaseList;
  if (!Array.isArray(phases) || phases.length === 0) return false;
  const micros = parseInt(phases[0]?.priceAmountMicros || '0', 10);
  return micros === 0;
}

function formatSubscriptionDate(isoDate, locale = 'en-US') {
  if (!isoDate || typeof isoDate !== 'string') return isoDate || '—';
  const d = new Date(isoDate);
  if (isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' });
}

function normalizePendingCreditPurchase(entry) {
  if (!entry) return null;
  const purchaseToken = String(entry.purchaseToken || '').trim();
  const productId = String(entry.productId || '').trim();
  const orderId = String(entry.orderId || '').trim();
  if (!purchaseToken || !productId || !orderId) return null;
  return {
    purchaseToken,
    productId,
    orderId,
    price_amount_micros: Number.isFinite(Number(entry.price_amount_micros))
      ? parseInt(entry.price_amount_micros, 10)
      : null,
    price_currency: entry.price_currency || null,
    localized_price: entry.localized_price || null,
    savedAt: entry.savedAt || new Date().toISOString(),
  };
}

async function getGooglePlayObfuscatedAccountId() {
  try {
    const raw = await AsyncStorage.getItem('userData');
    const parsed = raw ? JSON.parse(raw) : null;
    const userId = parsed?.userid ?? parsed?.user_id ?? parsed?.id;
    if (userId == null) return null;
    return `user:${String(userId).trim()}`;
  } catch (_) {
    return null;
  }
}

/** Get subscription price: prefer backend formatted_price (from Google Play), then iapSubscriptions, then plan.price. */
function getSubscriptionDisplayPrice(plan, iapSubscriptions) {
  if (plan.formatted_price != null && plan.formatted_price !== '') return plan.formatted_price;
  const productId = plan.google_play_product_id || plan.productId;
  if (!productId || !Array.isArray(iapSubscriptions)) return plan.price;
  const iap = iapSubscriptions.find((s) => (s.productId || s.product_id) === productId);
  if (!iap) return plan.price;
  // Android: price is in subscriptionOfferDetails[].pricingPhases.pricingPhaseList[].formattedPrice
  const offers = iap.subscriptionOfferDetails || iap.subscriptionOfferDetailsList;
  const firstOffer = Array.isArray(offers) ? offers[0] : null;
  const phases = firstOffer?.pricingPhases?.pricingPhaseList ?? firstOffer?.pricingPhaseList;
  const firstPhase = Array.isArray(phases) ? phases[0] : null;
  const formatted = firstPhase?.formattedPrice ?? firstPhase?.price;
  if (formatted != null && formatted !== '') return formatted;
  // iOS or legacy: top-level localizedPrice / price
  return iap.localizedPrice ?? iap.price ?? plan.price;
}

function formatBillingPeriodLabel(period) {
  const raw = String(period || '').trim().toUpperCase();
  if (!raw) return '';
  const m = raw.match(/^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?$/);
  if (!m) return '';
  const years = parseInt(m[1] || '0', 10);
  const months = parseInt(m[2] || '0', 10);
  const weeks = parseInt(m[3] || '0', 10);
  const days = parseInt(m[4] || '0', 10);
  if (years > 0) return years === 1 ? 'year' : `${years} years`;
  if (months > 0) return months === 1 ? 'month' : `${months} months`;
  if (weeks > 0) return weeks === 1 ? 'week' : `${weeks} weeks`;
  if (days > 0) return days === 1 ? 'day' : `${days} days`;
  return '';
}

function getSubscriptionOfferInfo(plan, iapSubscriptions) {
  const productId = plan.google_play_product_id || plan.productId;
  if (!productId || !Array.isArray(iapSubscriptions)) return null;
  const iap = iapSubscriptions.find((s) => (s.productId || s.product_id) === productId);
  if (!iap) return null;
  const offers = iap.subscriptionOfferDetails || iap.subscriptionOfferDetailsList;
  const firstOffer = Array.isArray(offers) ? offers[0] : null;
  const phases = firstOffer?.pricingPhases?.pricingPhaseList ?? firstOffer?.pricingPhaseList;
  const phaseList = Array.isArray(phases) ? phases : [];
  if (!phaseList.length) return null;
  const freeTrialPhase = phaseList.find((phase) => parseInt(phase?.priceAmountMicros || '0', 10) === 0);
  const paidPhase = phaseList.find((phase) => parseInt(phase?.priceAmountMicros || '0', 10) > 0) || phaseList[0];
  return {
    freeTrialPeriod: formatBillingPeriodLabel(freeTrialPhase?.billingPeriod),
    paidPeriod: formatBillingPeriodLabel(paidPhase?.billingPeriod),
    recurrenceMode: paidPhase?.recurrenceMode,
  };
}

/** One-time credit pack price: prefer IAP localized price, fallback to backend fields if available. */
function getCreditPackDisplayPrice(product, iapProducts) {
  const productId = product?.product_id || product?.id;
  const iap = Array.isArray(iapProducts)
    ? iapProducts.find((p) => (p.productId || p.product_id) === productId)
    : null;
  const iapPrice =
    iap?.localizedPrice ||
    iap?.oneTimePurchaseOfferDetails?.formattedPrice ||
    iap?.price ||
    null;
  if (iapPrice) return iapPrice;
  if (product?.localized_price) return product.localized_price;
  if (product?.formatted_price) return product.formatted_price;
  return null;
}

function getFirstPurchaseBonus(product) {
  const bonus = product?.first_purchase_bonus || {};
  const discount = product?.purchase_discount || {};
  const firstBonusCredits = bonus.eligible ? Number(bonus.bonus_credits || 0) : 0;
  const discountCredits = discount.eligible ? Number(discount.bonus_credits || 0) : 0;
  const bonusCredits = Number(product?.bonus_credits ?? (firstBonusCredits + discountCredits));
  const packCredits = Number(product?.credits) || 0;
  const totalCredits = Number(product?.total_credits ?? (packCredits + bonusCredits));
  const activeOffer = discount.eligible && discountCredits > 0 ? discount : bonus;
  return {
    eligible: Boolean((bonus.eligible && firstBonusCredits > 0) || (discount.eligible && discountCredits > 0)),
    bonusCredits,
    totalCredits,
    percent: Number(activeOffer.percent || 0),
    fixedCredits: Number(activeOffer.fixed_credits || 0),
    bonusType: String(activeOffer.bonus_type || '').toLowerCase(),
    windowMinutes: Number(activeOffer.window_minutes || 0),
    firstPurchaseBonus: bonus,
    purchaseDiscount: discount,
  };
}

function formatFirstPurchaseBonusLabel(bonus) {
  if (!bonus?.eligible) return '';
  if (bonus.bonusType === 'fixed' && bonus.fixedCredits > 0) {
    return `${bonus.fixedCredits} bonus credits`;
  }
  if (bonus.bonusType === 'percent' && bonus.percent > 0) {
    return `${bonus.percent}% extra credits`;
  }
  return `${bonus.bonusCredits} bonus credits`;
}

// Lazy-load IAP only on Android to avoid iOS/build issues
let RNIap = null;
if (Platform.OS === 'android') {
  try {
    RNIap = require('react-native-iap');
  } catch (e) {
    console.warn('react-native-iap not available:', e?.message);
  }
}

/**
 * If the account already has an active subscription (server + balance tier hint), prompt before
 * starting another subscription purchase. Returns false if the user cancels.
 */
async function confirmProceedDespiteActiveSubscription({
  creditAPI: creditApi,
  t,
  subscriptionDetails: detailsSnapshot,
  subscriptionTierName: tierNameSnapshot,
}) {
  let freshSubscription = detailsSnapshot ?? null;
  try {
    const { data: subDetailsPayload } = await creditApi.getSubscriptionDetails();
    freshSubscription = subDetailsPayload?.subscription ?? null;
  } catch (_) {
    /* keep snapshot */
  }
  const hasActiveSubscription = Boolean(freshSubscription || tierNameSnapshot);
  if (!hasActiveSubscription) return true;
  return new Promise((resolve) => {
    Alert.alert(
      t('credits.page.activeSubscriptionWarningTitle'),
      t('credits.page.activeSubscriptionWarningBody'),
      [
        {
          text: t('credits.page.activeSubscriptionWarningCancel'),
          style: 'cancel',
          onPress: () => resolve(false),
        },
        {
          text: t('credits.page.activeSubscriptionWarningConfirm'),
          onPress: () => resolve(true),
        },
      ]
    );
  });
}

const CreditScreen = ({ navigation }) => {
  useAnalytics('CreditScreen');
  const { t, i18n } = useTranslation();
  const dateLocale = appLocaleForI18n(i18n.language);
  const { theme, colors, androidLightCardFixStyle } = useTheme();
  const isDark = theme === 'dark';
  // Glass cards + Android elevation produce a white halo; flatten elevation on Android for all themes.
  const androidGlassFixStyle = Platform.OS === 'android'
    ? {
        elevation: 0,
        shadowColor: 'transparent',
        shadowOpacity: 0,
        shadowRadius: 0,
        shadowOffset: { width: 0, height: 0 },
      }
    : androidLightCardFixStyle;
  const { credits, loading, redeemCode, fetchBalance, subscriptionTierName, subscriptionDiscountPercent } = useCredits();
  const { requireAuthForPaid } = useAuthGate();

  useFocusEffect(
    React.useCallback(() => {
      let cancelled = false;
      (async () => {
        const ok = await requireAuthForPaid({
          feature: 'credits',
          message: 'Sign in to buy credits and unlock paid insights.',
          resume: { resumeRoute: 'Credits', resumeParams: {} },
        });
        if (!cancelled && !ok) {
          navigation.goBack();
        }
      })();
      return () => {
        cancelled = true;
      };
    }, [navigation, requireAuthForPaid])
  );

  const [promoCode, setPromoCode] = useState('');
  const [redeeming, setRedeeming] = useState(false);
  const [history, setHistory] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [purchasingProductId, setPurchasingProductId] = useState(null);
  const [iapReady, setIapReady] = useState(false);
  const [iapProducts, setIapProducts] = useState([]);
  const [googlePlayProducts, setGooglePlayProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [subscriptionPlansLoading, setSubscriptionPlansLoading] = useState(false);
  const [iapSubscriptions, setIapSubscriptions] = useState([]); // from getSubscriptions (productId + subscriptionOfferDetails for offerToken)
  const [purchasingSubscriptionId, setPurchasingSubscriptionId] = useState(null);
  const [subscriptionDetails, setSubscriptionDetails] = useState(null);
  const [vipPlansExpanded, setVipPlansExpanded] = useState(false);
  const [refreshSubscriptionStatusLoading, setRefreshSubscriptionStatusLoading] = useState(false);
  const [purchaseModal, setPurchaseModal] = useState({ visible: false, type: 'success', title: '', message: '', creditsAdded: 0 });
  const [showPackRelaunchBanner, setShowPackRelaunchBanner] = useState(false);
  const [razorpayCatalog, setRazorpayCatalog] = useState(null);
  const [razorpayCatalogLoading, setRazorpayCatalogLoading] = useState(false);
  const [razorpayCatalogError, setRazorpayCatalogError] = useState('');
  const [purchasingRazorpayCredits, setPurchasingRazorpayCredits] = useState(null);
  const purchaseListenerRef = useRef(null);
  const iapCallbacksRef = useRef({});
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scrollViewRef = useRef(null);
  const creditHeaderTitle =
    Platform.OS === 'ios' ? 'Study Credits' : t('credits.page.title');
  const creditHeaderSubtitle =
    Platform.OS === 'ios'
      ? 'Credits for chart study tools'
      : t('credits.page.subtitle');
  /**
   * IMPORTANT: Always force endConnection on the very first mount of this screen.
   * Google Play's BillingClient can sometimes get stuck in a default state if the app
   * was previously connected without the user-choice flag. By forcing a reset here,
   * we ensure the first 'user-choice' init attempt actually takes effect.
   */
  const iapDisconnectBeforeNextConnectRef = useRef(true);

  const fetchProducts = async ({ silent = false } = {}) => {
    if (Platform.OS !== 'android') return;
    if (!silent) setProductsLoading(true);
    try {
      const { data } = await creditAPI.getGooglePlayProducts();
      setGooglePlayProducts(Array.isArray(data?.products) ? data.products : []);
    } catch (e) {
      setGooglePlayProducts([]);
      console.warn('Failed to load Google Play products:', e?.message);
    } finally {
      if (!silent) setProductsLoading(false);
    }
  };

  const fetchPlans = async ({ silent = false } = {}) => {
    if (Platform.OS !== 'android') return;
    if (!silent) setSubscriptionPlansLoading(true);
    try {
      const { data } = await creditAPI.getSubscriptionPlans();
      setSubscriptionPlans(Array.isArray(data?.plans) ? data.plans : []);
    } catch (e) {
      setSubscriptionPlans([]);
      console.warn('Failed to load subscription plans:', e?.message);
    } finally {
      if (!silent) setSubscriptionPlansLoading(false);
    }
  };

  const fetchRazorpayCatalog = async ({ silent = false } = {}) => {
    if (Platform.OS !== 'web') return;
    if (!silent) setRazorpayCatalogLoading(true);
    setRazorpayCatalogError('');
    try {
      // Web: main API only (same as frontend CreditsModal) — never Google Play / payment-service IAP.
      const { data } = await creditAPI.getRazorpayCatalog({ preferMainApi: true });
      setRazorpayCatalog(data || null);
    } catch (e) {
      setRazorpayCatalog(null);
      setRazorpayCatalogError(e?.message || 'Could not load payment options');
    } finally {
      if (!silent) setRazorpayCatalogLoading(false);
    }
  };

  const productIds = useMemo(
    () => googlePlayProducts.map((p) => p.product_id).filter(Boolean),
    [googlePlayProducts]
  );
  const subscriptionProductIds = useMemo(
    () => subscriptionPlans.map((p) => p.google_play_product_id).filter(Boolean),
    [subscriptionPlans]
  );
  // Only show plans that actually exist in Google Play (returned by getSubscriptions)
  const subscriptionPlansFromPlay = useMemo(
    () =>
      subscriptionPlans.filter((plan) =>
        plan.google_play_product_id &&
        iapSubscriptions.some((s) => (s.productId || s.product_id) === plan.google_play_product_id)
      ),
    [subscriptionPlans, iapSubscriptions]
  );
  const hasAnyIapProducts = productIds.length > 0 || subscriptionProductIds.length > 0;

  const loadPendingGooglePlayCreditPurchases = async () => {
    try {
      const raw = await AsyncStorage.getItem(PENDING_GOOGLE_PLAY_CREDIT_PURCHASES_KEY);
      const parsed = JSON.parse(raw || '[]');
      return Array.isArray(parsed)
        ? parsed.map(normalizePendingCreditPurchase).filter(Boolean)
        : [];
    } catch (_) {
      return [];
    }
  };

  const savePendingGooglePlayCreditPurchase = async (entry) => {
    const normalized = normalizePendingCreditPurchase(entry);
    if (!normalized) return;
    try {
      const existing = await loadPendingGooglePlayCreditPurchases();
      const filtered = existing.filter(
        (item) =>
          !(
            item.purchaseToken === normalized.purchaseToken &&
            item.productId === normalized.productId &&
            item.orderId === normalized.orderId
          )
      );
      filtered.unshift(normalized);
      await AsyncStorage.setItem(
        PENDING_GOOGLE_PLAY_CREDIT_PURCHASES_KEY,
        JSON.stringify(filtered.slice(0, 50))
      );
    } catch (_) {
      /* ignore */
    }
  };

  const removePendingGooglePlayCreditPurchase = async ({ purchaseToken, productId, orderId }) => {
    try {
      const existing = await loadPendingGooglePlayCreditPurchases();
      const filtered = existing.filter(
        (item) =>
          !(
            item.purchaseToken === String(purchaseToken || '').trim() &&
            item.productId === String(productId || '').trim() &&
            item.orderId === String(orderId || '').trim()
          )
      );
      await AsyncStorage.setItem(PENDING_GOOGLE_PLAY_CREDIT_PURCHASES_KEY, JSON.stringify(filtered));
    } catch (_) {
      /* ignore */
    }
  };

  /** Call this after a successful Google Play purchase (e.g. from react-native-iap listener). */
  const handleGooglePlayPurchaseSuccess = async (
    purchaseToken,
    productId,
    orderId,
    pricingOverride = null
  ) => {
    if (!purchaseToken || !productId || !orderId) return;
    setPurchasingProductId(productId);
    try {
      const iapProduct = iapProducts.find((p) => (p.productId || p.product_id) === productId);
      const oneTimeOffer = iapProduct?.oneTimePurchaseOfferDetails || {};
      const pricingPayload = {
        price_amount_micros: pricingOverride?.price_amount_micros ?? (oneTimeOffer.priceAmountMicros
          ? parseInt(oneTimeOffer.priceAmountMicros, 10)
          : null),
        price_currency: pricingOverride?.price_currency ?? oneTimeOffer.priceCurrencyCode ?? null,
        localized_price: pricingOverride?.localized_price ?? iapProduct?.localizedPrice ?? iapProduct?.price ?? null,
      };
      await savePendingGooglePlayCreditPurchase({
        purchaseToken,
        productId,
        orderId,
        ...pricingPayload,
      });
      const { data } = await creditAPI.verifyGooglePlayPurchase(
        purchaseToken,
        productId,
        orderId,
        pricingPayload
      );
      await removePendingGooglePlayCreditPurchase({ purchaseToken, productId, orderId });
      await fetchBalance();
      await fetchHistory();
      const isAlreadyCredited = data.credits_added === 0 && (data.message || '').toLowerCase().includes('already credited');
      if (!isAlreadyCredited) {
        trackAstrologyEvent.creditPurchased(getIapPriceNumber(iapProduct), {
          content_id: productId,
          content_type: 'credits',
          currency: getIapCurrency(iapProduct),
        });
      }
      const successMsg = isAlreadyCredited
        ? t('credits.page.purchaseAlreadyCreditedBody')
        : (() => {
            const base = data.message || t('credits.page.purchaseCreditsAddedDefault');
            return data.credits_added
              ? `${base} ${t('credits.page.purchaseCreditsAddedSuffix', { count: data.credits_added })}`
              : base;
          })();
      setPurchaseModal({
        visible: true,
        type: isAlreadyCredited ? 'already_credited' : 'success',
        title: isAlreadyCredited ? t('credits.page.purchaseAlreadyCreditedTitle') : t('credits.page.purchaseThankYou'),
        message: successMsg,
        creditsAdded: data.credits_added || 0,
      });
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || t('credits.page.failedAddCredits');
      setPurchaseModal({
        visible: true,
        type: 'error',
        title: t('credits.page.purchaseVerifyFailed'),
        message: msg,
        creditsAdded: 0,
      });
    } finally {
      setPurchasingProductId(null);
    }
  };

  const closePurchaseModal = () => setPurchaseModal((prev) => ({ ...prev, visible: false }));

  /** Call this after a successful Google Play subscription purchase. */
  const handleGooglePlaySubscriptionSuccess = async (purchaseToken, productId, orderId) => {
    if (!purchaseToken || !productId || !orderId) return;
    setPurchasingSubscriptionId(productId);
    try {
      const { data } = await creditAPI.verifyGooglePlaySubscription(purchaseToken, productId, orderId);
      await fetchBalance();
      await fetchSubscriptionDetails();
      const tierName = data?.tier_name || t('credits.page.vipFallback');
      const subscription = iapSubscriptions.find(
        (s) => (s.productId || s.product_id) === productId
      );
      const subPayload = {
        content_id: productId,
        content_type: 'subscription',
        currency: getIapCurrency(subscription),
        value: getIapPriceNumber(subscription),
      };
      if (subscriptionHasFreeTrial(subscription)) {
        trackAstrologyEvent.startTrial(subPayload);
      } else {
        trackAstrologyEvent.subscribe(subPayload);
      }
      setPurchaseModal({
        visible: true,
        type: 'success',
        title: t('credits.page.subscribedTitle'),
        message: t('credits.page.subscribedMessage', { tier: tierName }),
        creditsAdded: 0,
      });
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || t('credits.page.failedActivateSubscription');
      setPurchaseModal({
        visible: true,
        type: 'error',
        title: t('credits.page.subscriptionVerifyFailed'),
        message: msg,
        creditsAdded: 0,
      });
    } finally {
      setPurchasingSubscriptionId(null);
    }
  };

  useEffect(() => {
    fetchHistory();
    fetchSubscriptionDetails();

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
    const pulseLoop = Animated.loop(
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
    );
    pulseLoop.start();
    
    // Refresh credits + history when screen comes into focus.
    // Android: sync with Google Play. Web: Razorpay catalog only (never Play IAP).
    const unsubscribe = navigation.addListener('focus', () => {
      fetchBalance();
      if (Platform.OS === 'web') {
        fetchRazorpayCatalog({ silent: true });
        fetchHistory();
        fetchSubscriptionDetails();
        return;
      }
      if (Platform.OS === 'android') {
        fetchProducts({ silent: true });
        fetchPlans({ silent: true });
      }
      if (Platform.OS === 'android' && iapReady && productIds.length > 0 && RNIap) {
        syncOneTimePurchasesWithPlay().then(fetchHistory).catch(() => fetchHistory());
      } else {
        fetchHistory();
      }
      if (Platform.OS === 'android' && iapReady && subscriptionProductIds.length > 0 && RNIap) {
        syncSubscriptionWithPlay().then(fetchSubscriptionDetails).catch(() => fetchSubscriptionDetails());
      } else {
        fetchSubscriptionDetails();
      }
    });

    return () => {
      pulseLoop.stop();
      unsubscribe();
    };
  }, [navigation, iapReady, productIds, subscriptionProductIds]);

  // Fetch Google Play products from backend (Android only)
  useEffect(() => {
    if (Platform.OS !== 'android') return;
    fetchProducts();
  }, []);

  // Warm Razorpay native module so alternative-billing open is faster after create-order.
  useEffect(() => {
    if (Platform.OS !== 'android') return;
    try {
      require('react-native-razorpay');
    } catch (_) {
      /* optional until User Choice */
    }
  }, []);

  // Web: load Razorpay INR catalog (same packs as the website CreditsModal flow).
  useEffect(() => {
    if (Platform.OS !== 'web') return;
    fetchRazorpayCatalog();
  }, []);

  useEffect(() => {
    // Pack relaunch banner is Android Play catalog messaging — skip on web.
    if (Platform.OS !== 'android') return undefined;
    let cancelled = false;
    (async () => {
      try {
        const dismissed = await AsyncStorage.getItem(PACK_RELAUNCH_BANNER_KEY);
        if (!cancelled && dismissed !== '1') {
          setShowPackRelaunchBanner(true);
        }
      } catch (_) {
        if (!cancelled) setShowPackRelaunchBanner(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const dismissPackRelaunchBanner = async () => {
    setShowPackRelaunchBanner(false);
    try {
      await AsyncStorage.setItem(PACK_RELAUNCH_BANNER_KEY, '1');
    } catch (_) {}
  };

  // Fetch subscription plans (Android only)
  useEffect(() => {
    if (Platform.OS !== 'android') return;
    fetchPlans();
  }, []);

  useLayoutEffect(() => {
    iapCallbacksRef.current = {
      googlePlayProducts,
      subscriptionPlans,
      iapSubscriptions,
      iapProducts,
      productIds,
      subscriptionProductIds,
      subscriptionDetails,
      subscriptionTierName,
      creditAPI,
      t,
      fetchBalance,
      fetchHistory,
      fetchSubscriptionDetails,
      setPurchaseModal,
      setPurchasingProductId,
      setPurchasingSubscriptionId,
      trackAstrologyEvent,
    };
  });

  // Google Play IAP: user-choice billing, product fetch, purchase listeners (Android only)
  // Wait until both backend catalog requests finish so SKU list is stable (avoids init →
  // teardown → re-init when credits load before subscription plans). On reconnect only, await
  // endConnection before initConnection. Listeners are registered before init (same order as
  // react-native-iap useIAP) so Google user-choice / alternative billing can attach correctly.
  useEffect(() => {
    if (Platform.OS !== 'android') {
      return;
    }
    if (!RNIap) {
      return;
    }
    if (!hasAnyIapProducts) {
      return;
    }
    if (productsLoading || subscriptionPlansLoading) {
      return;
    }

    let alive = true;
    let updateSub = null;
    let errorSub = null;
    let userChoiceSub = null;
    const initIap = async () => {
      setIapReady(false);
      try {
        if (iapDisconnectBeforeNextConnectRef.current) {
          try {
            await RNIap.endConnection?.();
            // Small delay to let native BillingClient settle
            await new Promise(resolve => setTimeout(resolve, 800));
          } catch (e) {
            /* ignore pre-init disconnect errors */
          }
          iapDisconnectBeforeNextConnectRef.current = false;
        }
        if (!alive) {
          return;
        }

        const tryInit = async (mode) => {
          try {
            await RNIap.initConnection({ alternativeBillingModeAndroid: mode });
            return true;
          } catch (err) {
            console.warn(`IAP: Init with mode "${mode}" failed:`, err?.message);
            return false;
          }
        };

        const clearBillingListeners = () => {
          try {
            updateSub?.remove?.();
            errorSub?.remove?.();
            userChoiceSub?.remove?.();
          } catch (_) {
            /* ignore */
          }
          updateSub = null;
          errorSub = null;
          userChoiceSub = null;
        };

        const registerBillingListeners = () => {
          try {
            userChoiceSub = RNIap.userChoiceBillingListenerAndroid(async (details) => {
            const externalTransactionToken = details?.externalTransactionToken;
            const rawProducts = details?.products || [];
            const C = iapCallbacksRef.current;
            const { playProductIds, creditSku, subSku } = resolveUserChoiceCatalogSkus(
              rawProducts,
              C.productIds,
              C.subscriptionProductIds
            );

            const tok = externalTransactionToken ? String(externalTransactionToken) : '';
            userChoiceIapLog('listener_raw', {
              hasToken: !!tok,
              tokenLen: tok.length,
              tokenPrefix: tok ? `${tok.slice(0, 12)}…` : null,
              rawProductsLen: rawProducts.length,
              rawProductsShape: describeUserChoiceRawProductsForLog(rawProducts),
            });
            userChoiceIapLog('listener_resolved', {
              playProductIds,
              creditSku,
              subSku,
              nCreditCatalog: (C.productIds || []).length,
              nSubCatalog: (C.subscriptionProductIds || []).length,
              subscriptionProductIds: C.subscriptionProductIds,
              creditProductIds: C.productIds,
            });

            if (!externalTransactionToken || !playProductIds.length) {
              userChoiceIapLog('listener_early_exit', {
                reason: !externalTransactionToken ? 'no_token' : 'no_play_product_ids',
                playProductIds,
              });
              return;
            }

            const { payCreditPackUserChoiceRazorpay, paySubscriptionUserChoiceRazorpay } = require('./androidUserChoiceRazorpay');

            C.setPurchasingProductId?.(null);
            C.setPurchasingSubscriptionId?.(null);

            const confirmed = await new Promise((resolve) => {
              Alert.alert(
                C.t('credits.page.userChoiceBillingTitle'),
                C.t('credits.page.userChoiceBillingBody'),
                [
                  { text: C.t('credits.page.userChoiceBillingCancel'), style: 'cancel', onPress: () => resolve(false) },
                  { text: C.t('credits.page.userChoiceBillingContinue'), onPress: () => resolve(true) },
                ]
              );
            });
            if (!confirmed) return;

            if (subSku) {
              const proceedSub = await confirmProceedDespiteActiveSubscription({
                creditAPI: C.creditAPI,
                t: C.t,
                subscriptionDetails: C.subscriptionDetails,
                subscriptionTierName: C.subscriptionTierName,
              });
              if (!proceedSub) return;
            }

            userChoiceIapLog('listener_user_confirmed', { creditSku, subSku });

            // Keep pack/sub button in "processing" while create-order runs (often 1–3s).
            if (creditSku) C.setPurchasingProductId?.(creditSku);
            if (subSku) C.setPurchasingSubscriptionId?.(subSku);

            try {
              if (creditSku) {
                const credits = creditsFromGooglePlayProductId(creditSku);
                if (!credits) throw new Error(`Invalid credit product: ${creditSku}`);
                
                const product = (C.googlePlayProducts || []).find((p) => 
                  String(p.product_id || p.id).toLowerCase() === String(creditSku).toLowerCase()
                );
                const iapProduct = (C.iapProducts || []).find((p) => 
                  String(p.productId || p.product_id).toLowerCase() === String(creditSku).toLowerCase()
                );
                const desc = product
                  ? C.t('credits.page.productTitleFallback', { count: credits })
                  : `${credits} credits`;

                const data = await payCreditPackUserChoiceRazorpay({
                  creditAPI: C.creditAPI,
                  credits,
                  externalTransactionToken,
                  description: desc,
                });
                C.setPurchasingProductId?.(null);
                await C.fetchBalance();
                await C.fetchHistory();
                const creditsAdded = data.credits_added || 0;
                const isAlready =
                  creditsAdded === 0 && (data.message || '').toLowerCase().includes('already credited');
                
                if (!isAlready && creditsAdded > 0 && iapProduct) {
                  C.trackAstrologyEvent.creditPurchased(getIapPriceNumber(iapProduct), {
                    content_id: creditSku,
                    content_type: 'credits',
                    currency: getIapCurrency(iapProduct),
                  });
                }
                
                const successMsg = isAlready
                  ? C.t('credits.page.purchaseAlreadyCreditedBody')
                  : (() => {
                      const base = data.message || C.t('credits.page.purchaseCreditsAddedDefault');
                      return creditsAdded
                        ? `${base} ${C.t('credits.page.purchaseCreditsAddedSuffix', { count: creditsAdded })}`
                        : base;
                    })();
                    
                C.setPurchaseModal({
                  visible: true,
                  type: isAlready ? 'already_credited' : 'success',
                  title: isAlready ? C.t('credits.page.purchaseAlreadyCreditedTitle') : C.t('credits.page.purchaseThankYou'),
                  message: successMsg,
                  creditsAdded,
                });
                userChoiceIapLog('listener_credit_flow_ok', { creditSku, creditsAdded });
                return;
              }
              
              if (subSku) {
                const plan = (C.subscriptionPlans || []).find((p) => 
                  String(p.google_play_product_id).toLowerCase() === String(subSku).toLowerCase()
                );
                if (!plan?.plan_id) throw new Error(`Missing plan details for: ${subSku}`);
                
                const subscription = (C.iapSubscriptions || []).find(
                  (s) => String(s.productId || s.product_id).toLowerCase() === String(subSku).toLowerCase()
                );
                
                const data = await paySubscriptionUserChoiceRazorpay({
                  creditAPI: C.creditAPI,
                  planId: plan.plan_id,
                  externalTransactionToken,
                  tierName: plan.tier_name,
                });
                C.setPurchasingSubscriptionId?.(null);
                
                await C.fetchBalance();
                await C.fetchSubscriptionDetails();
                
                const tierName =
                  data?.subscription?.tier_name ||
                  data?.tier_name ||
                  plan.tier_name ||
                  C.t('credits.page.vipFallback');
                  
                const subPayload = {
                  content_id: subSku,
                  content_type: 'subscription',
                  currency: getIapCurrency(subscription),
                  value: getIapPriceNumber(subscription),
                };
                
                if (subscriptionHasFreeTrial(subscription)) {
                  C.trackAstrologyEvent.startTrial(subPayload);
                } else {
                  C.trackAstrologyEvent.subscribe(subPayload);
                }
                
                C.setPurchaseModal({
                  visible: true,
                  type: 'success',
                  title: C.t('credits.page.subscribedTitle'),
                  message: C.t('credits.page.subscribedMessage', { tier: tierName }),
                  creditsAdded: 0,
                });
                userChoiceIapLog('listener_sub_flow_ok', { subSku, planId: plan.plan_id });
                return;
              }
              
              userChoiceIapLog('listener_no_catalog_match', {
                playProductIds,
                creditSku,
                subSku,
              });
              console.error('IAP: Failed to match any known product ID in listener');
              Alert.alert(C.t('credits.page.alertError'), C.t('credits.page.userChoiceUnknownProducts'));
            } catch (e) {
              C.setPurchasingProductId?.(null);
              C.setPurchasingSubscriptionId?.(null);
              userChoiceIapLog('listener_flow_error', {
                message: e?.message,
                code: e?.code,
                status: e?.response?.status,
                detail: e?.response?.data?.detail,
              });
              console.error('IAP: User choice Razorpay flow failed:', e);
              const msg =
                e?.response?.data?.detail ||
                e?.message ||
                C.t('credits.page.userChoiceRazorpayFailed');
              C.setPurchaseModal({
                visible: true,
                type: 'error',
                title: C.t('credits.page.userChoiceRazorpayFailed'),
                message: typeof msg === 'string' ? msg : C.t('credits.page.userChoiceRazorpayFailed'),
                creditsAdded: 0,
              });
            }
          });
        } catch (listenerErr) {
          console.warn('userChoiceBillingListenerAndroid registration failed:', listenerErr?.message);
        }

        updateSub = RNIap.purchaseUpdatedListener(async (purchase) => {
          try {
            const token = purchase.purchaseToken ?? purchase.purchaseTokenAndroid;
            const productId = purchase.productId ?? purchase.productIds?.[0];
            const orderId = purchase.transactionId ?? purchase.transactionIdAndroid ?? purchase.purchaseToken;
            if (!token || !productId || !orderId) return;
            const isSubscription = subscriptionProductIds.includes(productId);
            trackAstrologyEvent.addPaymentInfo(true, {
              content_id: productId,
              content_type: isSubscription ? 'subscription' : 'credits',
            });
            if (isSubscription) {
              await handleGooglePlaySubscriptionSuccess(token, productId, orderId);
              await RNIap.finishTransaction({ purchase, isConsumable: false });
            } else {
              await handleGooglePlayPurchaseSuccess(token, productId, orderId);
              await RNIap.finishTransaction({ purchase, isConsumable: true });
            }
          } catch (e) {
            console.warn('Purchase listener error:', e?.message);
          }
        });
        errorSub = RNIap.purchaseErrorListener?.((error) => {
          setPurchasingProductId(null);
          setPurchasingSubscriptionId(null);
          if (error?.code !== 'E_USER_CANCELLED') {
            console.warn('Purchase error:', error?.message);
          }
        });
        };

        const runBillingConnectionInit = async () => {
          let initOutcome = 'unknown';
          let ok = false;
          // Nitro bridge expects 'user-choice'. We removed the numeric fallback to avoid
          // unnecessary disconnect/reconnect cycles that were causing timing issues.
          ok = await tryInit('user-choice');
          if (ok) initOutcome = 'user-choice';

          if (!ok && alive) {
            await RNIap.endConnection?.().catch(() => {});
            await new Promise(r => setTimeout(r, 600));
            // Fallback to uppercase variant name
            ok = await tryInit('USER_CHOICE');
            if (ok) initOutcome = 'USER_CHOICE';
          }

          if (!ok && alive) {
            console.warn('IAP: User-choice init failed, falling back to default Play billing');
            await RNIap.endConnection?.().catch(() => {});
            await new Promise(r => setTimeout(r, 600));
            try {
              await RNIap.initConnection();
              initOutcome = 'plain_fallback';
            } catch (plainErr) {
              initOutcome = 'plain_fallback_failed';
              throw plainErr;
            }
          }
          return { initOutcome, ok };
        };

        registerBillingListeners();
        let { initOutcome } = await runBillingConnectionInit();

        const userChoiceBillingActive =
          initOutcome === 'user-choice' || initOutcome === 'USER_CHOICE';
        if (
          alive &&
          userChoiceBillingActive &&
          !globalThis.__ASTRO_ANDROID_PLAY_BILLING_WARM__
        ) {
          globalThis.__ASTRO_ANDROID_PLAY_BILLING_WARM__ = true;
          clearBillingListeners();
          await RNIap.endConnection?.().catch(() => {});
          await new Promise(r => setTimeout(r, 600));
          if (!alive) {
            return;
          }
          registerBillingListeners();
          const second = await runBillingConnectionInit();
          initOutcome = second.initOutcome;
        }

        if (!alive) {
          return;
        }

        // Mark as ready early so user can click Buy without waiting for fetch
        setIapReady(true);

        if (productIds.length > 0) {
          RNIap.fetchProducts({ skus: productIds, type: 'in-app' })
            .then(products => {
              if (alive && Array.isArray(products)) {
                setIapProducts(products.map(normalizeIapProductForLegacyHelpers));
              }
            })
            .catch(fetchErr => {
              console.warn('IAP fetch in-app products failed:', fetchErr?.message);
            });
        }
        if (subscriptionProductIds.length > 0) {
          RNIap.fetchProducts({ skus: subscriptionProductIds, type: 'subs' })
            .then(subs => {
              if (alive && Array.isArray(subs)) {
                setIapSubscriptions(subs.map(normalizeIapProductForLegacyHelpers));
              }
            })
            .catch(fetchErr => {
              console.warn('IAP fetch subscriptions failed:', fetchErr?.message);
            });
        }

        purchaseListenerRef.current = { updateSub, errorSub, userChoiceSub };
      } catch (e) {
        if (!alive) return;
        try {
          updateSub?.remove?.();
          errorSub?.remove?.();
          userChoiceSub?.remove?.();
        } catch (_) {
          /* ignore */
        }
        try {
          await RNIap.endConnection?.();
        } catch (_) {
          /* ignore */
        }
        setIapReady(false);
        setIapProducts([]);
        setIapSubscriptions([]);
        console.warn('IAP init failed:', e?.message);
      }
    };
    initIap();
    return () => {
      iapDisconnectBeforeNextConnectRef.current = true;
      alive = false;
      try {
        updateSub?.remove?.();
        errorSub?.remove?.();
        userChoiceSub?.remove?.();
      } catch (e) {
        console.warn('IAP listener cleanup:', e?.message);
      }
      void RNIap.endConnection?.().catch(() => {
        /* ignore */
      });
    };
  }, [
    hasAnyIapProducts,
    productsLoading,
    subscriptionPlansLoading,
    productIds.join(','),
    subscriptionProductIds.join(','),
  ]);

  const fetchSubscriptionDetails = async () => {
    try {
      const { data } = await creditAPI.getSubscriptionDetails();
      setSubscriptionDetails(data?.subscription ?? null);
    } catch (e) {
      setSubscriptionDetails(null);
    }
  };

  /** On Android: get current subscription from Play and sync to our backend when a token is available. */
  const syncSubscriptionWithPlay = async () => {
    if (Platform.OS !== 'android' || !RNIap || subscriptionProductIds.length === 0) return;
    try {
      let subscriptionPurchases = [];
      const available = await RNIap.getAvailablePurchases().catch(() => []);
      subscriptionPurchases = (available || []).filter(
        (p) => p.productId && subscriptionProductIds.includes(p.productId)
      );
      let synced = false;
      for (const p of subscriptionPurchases) {
        const token = p.purchaseToken ?? p.purchaseTokenAndroid;
        const productId = p.productId ?? p.productIds?.[0];
        if (token && productId) {
          const orderId = p.transactionId ?? p.transactionIdAndroid ?? null;
          await creditAPI.syncSubscription(token, productId, orderId);
          synced = true;
          break;
        }
      }
      if (!synced) {
        console.warn('No Google Play subscription purchase found to sync; preserving server subscription until its end date.');
      }
      await fetchBalance();
      await fetchSubscriptionDetails();
    } catch (e) {
      console.warn('Subscription sync with Play failed:', e?.message);
      await fetchBalance();
      await fetchSubscriptionDetails();
    }
  };

  /** On Android: recover missed one-time credit purchases from Play and re-verify on backend. */
  const syncOneTimePurchasesWithPlay = async () => {
    if (Platform.OS !== 'android' || !RNIap || productIds.length === 0) return;
    try {
      const pending = await loadPendingGooglePlayCreditPurchases();
      for (const pendingPurchase of pending) {
        try {
          await handleGooglePlayPurchaseSuccess(
            pendingPurchase.purchaseToken,
            pendingPurchase.productId,
            pendingPurchase.orderId,
            pendingPurchase
          );
        } catch (_) {
          // keep going; unresolved purchases stay in local retry storage
        }
      }
      let creditPurchases = [];
      const available = await RNIap.getAvailablePurchases().catch(() => []);
      creditPurchases = (available || []).filter(
        (p) => p.productId && productIds.includes(p.productId)
      );
      for (const p of creditPurchases) {
        const token = p.purchaseToken ?? p.purchaseTokenAndroid;
        const productId = p.productId ?? p.productIds?.[0];
        const orderId = p.transactionId ?? p.transactionIdAndroid ?? p.purchaseToken;
        if (!token || !productId || !orderId) continue;
        try {
          await handleGooglePlayPurchaseSuccess(token, productId, orderId);
        } catch (_) {
          // Keep iterating so one failed purchase does not block recovery of others.
        }
      }
    } catch (e) {
      console.warn('One-time purchase sync with Play failed:', e?.message);
    }
  };

  /** Force-clear subscription status and refetch (e.g. after user cancelled on Play and app still shows subscribed). */
  const handleRefreshSubscriptionStatus = async () => {
    if (refreshSubscriptionStatusLoading) return;
    setRefreshSubscriptionStatusLoading(true);
    try {
      await syncSubscriptionWithPlay();
      await fetchBalance();
      await fetchSubscriptionDetails();
      setPurchaseModal({
        visible: true,
        type: 'success',
        title: t('credits.page.subscriptionStatusUpdated'),
        message: t('credits.page.subscriptionStatusUpdatedBody'),
        creditsAdded: 0,
      });
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || t('credits.page.couldNotRefresh');
      setPurchaseModal({
        visible: true,
        type: 'error',
        title: t('credits.page.refreshFailed'),
        message: msg,
        creditsAdded: 0,
      });
    } finally {
      setRefreshSubscriptionStatusLoading(false);
    }
  };

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
      Alert.alert(t('credits.page.alertError'), t('credits.page.enterPromoCode'));
      return;
    }

    setRedeeming(true);
    
    try {
      const result = await redeemCode(promoCode.trim());
      Alert.alert(t('credits.page.alertSuccess'), result.message || t('credits.page.promoRedeemedDefault'));
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
      let errorMessage = error.message || error.detail || t('credits.page.failedRedeem');
      
      
      // Decode HTML entities
      errorMessage = errorMessage
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&#39;/g, "'");
      
      // Provide user-friendly messages for common errors
      if (errorMessage.toLowerCase().includes('already used') || errorMessage.toLowerCase().includes('already redeemed')) {
        errorMessage = t('credits.page.promoAlreadyUsed');
      } else if (errorMessage.toLowerCase().includes('invalid') || errorMessage.toLowerCase().includes('not found')) {
        errorMessage = t('credits.page.promoInvalid');
      } else if (errorMessage.toLowerCase().includes('expired')) {
        errorMessage = t('credits.page.promoExpired');
      } else if (errorMessage.toLowerCase().includes('internal server error')) {
        errorMessage = t('credits.page.serverError');
      }
      
      Alert.alert(t('credits.page.redemptionFailed'), errorMessage);
    } finally {
      setRedeeming(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    if (Platform.OS === 'android') {
      await Promise.all([
        fetchProducts({ silent: true }),
        fetchPlans({ silent: true }),
      ]);
    }
    if (Platform.OS === 'web') {
      await fetchRazorpayCatalog({ silent: true });
    }
    if (Platform.OS === 'android' && iapReady && productIds.length > 0 && RNIap) {
      await syncOneTimePurchasesWithPlay();
    }
    await fetchBalance();
    await fetchHistory();
    if (Platform.OS === 'android' && iapReady && subscriptionProductIds.length > 0 && RNIap) {
      await syncSubscriptionWithPlay();
    }
    await fetchSubscriptionDetails();
    setRefreshing(false);
  };

  const handleBuyRazorpayPack = async (pack) => {
    if (Platform.OS !== 'web') return;
    const creditsAmount = Number(pack?.credits);
    if (!Number.isFinite(creditsAmount) || creditsAmount <= 0) return;
    setPurchasingRazorpayCredits(creditsAmount);
    try {
      // Same path as frontend: main API create-order → Checkout.js → verify (no Play / Cloud Run hop).
      const { data: orderData } = await creditAPI.createRazorpayOrder(
        creditsAmount,
        {},
        { preferMainApi: true }
      );
      const verifyPayload = await openRazorpayCheckout({
        orderData,
        description: pack?.name || `${creditsAmount} credits`,
        themeColor: colors.primary || '#f97316',
        onDismiss: () => setPurchasingRazorpayCredits(null),
        verifyPayment: async (payment) => {
          const { data } = await creditAPI.verifyRazorpayPayment(payment, {
            preferMainApi: true,
          });
          return data;
        },
      });
      const added = Number(verifyPayload?.credits_added) || 0;
      setPurchaseModal({
        visible: true,
        type: 'success',
        title: t('credits.page.purchaseSuccessTitle', { defaultValue: 'Purchase successful' }),
        message:
          added > 0
            ? t('credits.page.purchaseCreditsAddedSuffix', {
                count: added,
                defaultValue: `Added ${added} credits`,
              })
            : verifyPayload?.message || t('credits.page.purchaseCreditsAddedDefault', { defaultValue: 'Your balance is up to date.' }),
        creditsAdded: added,
      });
      await fetchBalance();
      await fetchHistory();
    } catch (e) {
      if (e?.code === 'USER_CANCELLED') {
        return;
      }
      Alert.alert(
        t('credits.page.purchaseFailed', { defaultValue: 'Purchase failed' }),
        e?.message || t('credits.page.couldNotStartPurchase', { defaultValue: 'Could not start payment' })
      );
    } finally {
      setPurchasingRazorpayCredits(null);
    }
  };

  const handleBuyCreditsPress = async (product) => {
    if (Platform.OS !== 'android') return;
    if (!RNIap) {
      Alert.alert(t('credits.page.notAvailable'), t('credits.page.iapNotAvailable'));
      return;
    }
    if (!iapReady) {
      Alert.alert(t('credits.page.storeLoadingTitle'), t('credits.page.storeLoadingBody'));
      return;
    }

    startGooglePlayPurchase(product);
  };

  const startGooglePlayPurchase = async (product) => {
    const productId = product.product_id || product.id;
    const iapProduct = iapProducts.find((p) => (p.productId || p.product_id) === productId);
    const obfuscatedAccountIdAndroid = await getGooglePlayObfuscatedAccountId();
    trackAstrologyEvent.initiateCheckout({
      content_id: productId,
      content_type: 'credits',
      currency: getIapCurrency(iapProduct),
      value: getIapPriceNumber(iapProduct) || Number(product.price_inr || product.price || 0),
    });
    setPurchasingProductId(productId);
    try {
      await RNIap.requestPurchase({
        type: 'in-app',
        request: {
          android: {
            skus: [productId],
            ...(obfuscatedAccountIdAndroid ? { obfuscatedAccountIdAndroid } : {}),
          },
        },
      });
    } catch (e) {
      if (e?.code !== 'E_USER_CANCELLED') {
        Alert.alert(t('credits.page.purchaseFailed'), e?.message ?? t('credits.page.couldNotStartPurchase'));
      }
      setPurchasingProductId(null);
    }
  };

  const handleSubscribePress = async (plan) => {
    if (Platform.OS !== 'android') return;
    if (!RNIap) {
      Alert.alert(t('credits.page.notAvailable'), t('credits.page.iapNotAvailable'));
      return;
    }
    if (!iapReady) {
      Alert.alert(t('credits.page.storeLoadingTitle'), t('credits.page.storeLoadingBody'));
      return;
    }
    const productId = plan.google_play_product_id;
    if (!productId) return;
    startGooglePlaySubscription(plan);
  };

  const startGooglePlaySubscription = async (plan) => {
    const productId = plan.google_play_product_id;
    const obfuscatedAccountIdAndroid = await getGooglePlayObfuscatedAccountId();
    // Google Play requires subscriptionOffers with offerToken (from getSubscriptions)
    const subscription = iapSubscriptions.find(
      (s) => (s.productId || s.product_id) === productId
    );
    const offerDetails = subscription?.subscriptionOfferDetails;
    const offerToken = offerDetails?.[0]?.offerToken;
    if (!offerToken) {
      Alert.alert(
        t('credits.page.subscriptionUnavailable'),
        t('credits.page.subscriptionUnavailableBody')
      );
      return;
    }

    const proceedDespiteActive = await confirmProceedDespiteActiveSubscription({
      creditAPI,
      t,
      subscriptionDetails,
      subscriptionTierName,
    });
    if (!proceedDespiteActive) return;

    trackAstrologyEvent.initiateCheckout({
      content_id: productId,
      content_type: 'subscription',
      currency: getIapCurrency(subscription),
      value: getIapPriceNumber(subscription) || Number(plan.price_inr || plan.price || 0),
    });
    setPurchasingSubscriptionId(productId);
    try {
      await RNIap.requestPurchase({
        type: 'subs',
        request: {
          android: {
            skus: [productId],
            subscriptionOffers: [{ sku: productId, offerToken }],
            ...(obfuscatedAccountIdAndroid ? { obfuscatedAccountIdAndroid } : {}),
          },
        },
      });
    } catch (e) {
      if (e?.code !== 'E_USER_CANCELLED') {
        Alert.alert(t('credits.page.subscriptionFailed'), e?.message ?? t('credits.page.couldNotStartSubscription'));
      }
      setPurchasingSubscriptionId(null);
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
          <View style={styles.transactionDescriptionWrap}>
            <Text
              style={[styles.transactionDescription, { color: colors.text }]}
              numberOfLines={2}
              ellipsizeMode="tail"
            >
              {item.description || item.source}
            </Text>
          </View>
          <Text style={[styles.transactionAmount, { color: item.type === 'earned' ? colors.success : colors.primary }]}>
            {item.type === 'earned' ? '+' : '-'}{Math.abs(item.amount)}
          </Text>
        </View>
        <View style={styles.transactionFooter}>
          <Text style={[styles.transactionDate, { color: colors.textSecondary }]}>
            {new Date(item.date).toLocaleDateString(dateLocale)}
          </Text>
          <Text
            style={[styles.transactionBalance, { color: colors.textTertiary }]}
            numberOfLines={1}
          >
            {t('credits.page.transactionBalance', { amount: item.balance_after })}
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
                style={[styles.backButton, androidGlassFixStyle, { backgroundColor: backButtonBg }]}
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

                <Text style={[styles.headerTitle, { color: colors.text }]}>{creditHeaderTitle}</Text>
                <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>{creditHeaderSubtitle}</Text>
              </View>
            </Animated.View>

            {/* Current Balance */}
            <Animated.View
              style={[
                styles.balanceCard,
                androidGlassFixStyle,
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
                  <Text style={[styles.balanceLabel, { color: colors.textSecondary }]}>{t('credits.page.yourBalance')}</Text>
                  <Text style={[styles.balanceAmount, { color: colors.primary }]}>{credits}</Text>
                  <Text style={[styles.balanceCreditsText, { color: colors.textTertiary }]}>{t('credits.page.creditsLabel')}</Text>
                </View>

                <View style={styles.balanceDecoration}>
                  <View style={[styles.decorationCircle, { backgroundColor: isDark ? 'rgba(249,115,22,0.08)' : 'rgba(255,107,53,0.05)' }]} />
                  <View style={[styles.decorationCircle, styles.decorationCircle2, { backgroundColor: isDark ? 'rgba(249,115,22,0.12)' : 'rgba(255,107,53,0.08)' }]} />
                  <View style={[styles.decorationCircle, styles.decorationCircle3, { backgroundColor: isDark ? 'rgba(249,115,22,0.15)' : 'rgba(255,107,53,0.12)' }]} />
                </View>
              </LinearGradient>
            </Animated.View>

            {/* Buy credits (Google Play) - Android only; products fetched from backend/Play */}
            {Platform.OS === 'android' && (
              <View style={styles.buySection}>
                <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('credits.page.chooseYourPackWithTara')}</Text>
                {showPackRelaunchBanner ? (
                  <View style={[styles.packRelaunchBanner, { backgroundColor: isDark ? 'rgba(34,197,94,0.16)' : 'rgba(34,197,94,0.1)', borderColor: isDark ? 'rgba(34,197,94,0.45)' : 'rgba(22,163,74,0.35)' }]}>
                    <Ionicons name="gift-outline" size={18} color="#16a34a" />
                    <Text style={[styles.packRelaunchText, { color: colors.text }]}>
                      {t('credits.page.packRelaunchBanner')}
                    </Text>
                    <TouchableOpacity onPress={dismissPackRelaunchBanner} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                      <Ionicons name="close" size={18} color={colors.textSecondary} />
                    </TouchableOpacity>
                  </View>
                ) : null}
                {productsLoading ? (
                  <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>{t('credits.page.loadingProducts')}</Text>
                ) : googlePlayProducts.length === 0 ? (
                  <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>{t('credits.page.noProducts')}</Text>
                ) : (
                  <>
                    {(() => {
                      const firstEligible = googlePlayProducts.map(getFirstPurchaseBonus).find((b) => b.eligible);
                      return firstEligible ? (
                        <View style={[styles.firstPurchaseBonusBanner, { backgroundColor: isDark ? 'rgba(249,115,22,0.16)' : 'rgba(255,107,53,0.1)', borderColor: colors.primary }]}>
                          <Ionicons name="flash-outline" size={18} color={colors.primary} />
                          <Text style={[styles.firstPurchaseBonusText, { color: colors.text }]}>
                            Limited offer: get {formatFirstPurchaseBonusLabel(firstEligible)} on your first pack.
                          </Text>
                        </View>
                      ) : null;
                    })()}
                    <View style={styles.buyProductStack}>
                      {googlePlayProducts.map((product) => {
                        const bonus = getFirstPurchaseBonus(product);
                        const meta = getCreditPackMeta(product.credits);
                        // Prefer app/catalog names (Shuruaat/Guru) over Play Console titles ("999 Credits").
                        const packName = meta.name || product.name || product.title;
                        const badge = meta.badge ?? product.badge;
                        const questions = meta.questions ?? product.questions;
                        const savePercent = Number(meta.savePercent ?? product.save_percent) || 0;
                        const packBonusCredits = Number(meta.bonusCredits ?? product.pack_bonus_credits) || 0;
                        const displayPrice = getCreditPackDisplayPrice(product, iapProducts);
                        const isPopular = Boolean(badge);
                        const totalCredits =
                          Number(product.total_credits) ||
                          (bonus.eligible
                            ? bonus.totalCredits
                            : product.credits + packBonusCredits);
                        const showPackBonus = packBonusCredits > 0 && !bonus.eligible;
                        return (
                          <TouchableOpacity
                            key={product.product_id}
                            style={[
                              styles.creditPackCardWide,
                              androidGlassFixStyle,
                              {
                                backgroundColor: promoCardBg,
                                borderColor: isPopular || bonus.eligible ? colors.primary : colors.cardBorder,
                                borderWidth: isPopular ? 2 : 1,
                              },
                            ]}
                            onPress={() => handleBuyCreditsPress(product)}
                            disabled={purchasingProductId === product.product_id}
                          >
                            <View style={styles.creditPackWideTop}>
                              <View style={{ flex: 1 }}>
                                <View style={styles.creditPackNameRow}>
                                  <Text style={[styles.creditPackName, { color: colors.text }]}>{packName}</Text>
                                  {badge ? (
                                    <View style={[styles.creditPackBadge, { backgroundColor: colors.primary }]}>
                                      <Text style={styles.creditPackBadgeText}>{badge}</Text>
                                    </View>
                                  ) : null}
                                </View>
                                {displayPrice ? (
                                  <Text style={[styles.creditPackPricePrimary, { color: colors.text }]}>{displayPrice}</Text>
                                ) : null}
                                <Text style={[styles.creditPackCreditsSecondary, { color: colors.textSecondary }]}>
                                  {t('credits.page.creditsCountTitle', { count: totalCredits })}
                                </Text>
                                {questions != null ? (
                                  <Text style={[styles.creditPackQuestions, { color: colors.text }]}>
                                    {product.credits >= 999
                                      ? t('credits.page.questionsWithTara', { count: questions })
                                      : t('credits.page.questionsCount', { count: questions })}
                                  </Text>
                                ) : null}
                                {showPackBonus ? (
                                  <Text style={[styles.creditPackBonus, { color: colors.primary }]}>
                                    {t('credits.page.packBonusLine', {
                                      base: product.credits,
                                      bonus: packBonusCredits,
                                    })}
                                  </Text>
                                ) : null}
                                {bonus.eligible ? (
                                  <Text style={[styles.creditPackBonus, { color: colors.primary }]}>
                                    {product.credits} + {bonus.bonusCredits} bonus
                                  </Text>
                                ) : null}
                                {savePercent > 0 ? (
                                  <Text style={[styles.creditPackSave, { color: colors.primary }]}>
                                    {t('credits.page.savePercent', { percent: savePercent })}
                                  </Text>
                                ) : null}
                              </View>
                              <View style={[styles.creditPackButton, { backgroundColor: colors.primary }]}>
                                <Text style={styles.creditPackButtonText}>
                                  {purchasingProductId === product.product_id ? t('credits.page.processing') : t('credits.page.buy')}
                                </Text>
                              </View>
                            </View>
                          </TouchableOpacity>
                        );
                      })}
                    </View>
                  </>
                )}
              </View>
            )}

            {/* Buy credits (Razorpay Checkout.js) — Expo Web / mobile browsers */}
            {Platform.OS === 'web' && (
              <View style={styles.buySection}>
                <Text style={[styles.sectionTitle, { color: colors.text }]}>
                  {t('credits.page.chooseYourPackWithTara')}
                </Text>
                <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary, marginBottom: 12 }]}>
                  Secure checkout (UPI, cards, netbanking) — same packs as the website.
                </Text>
                {razorpayCatalogLoading ? (
                  <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>
                    {t('credits.page.loadingProducts')}
                  </Text>
                ) : razorpayCatalogError ? (
                  <Text style={[styles.buyProductPlaceholder, { color: colors.error || '#dc2626' }]}>
                    {razorpayCatalogError}
                  </Text>
                ) : !(razorpayCatalog?.packs?.length) ? (
                  <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>
                    {t('credits.page.noProducts')}
                  </Text>
                ) : (
                  <View style={styles.buyProductStack}>
                    {razorpayCatalog.packs.map((pack) => {
                      const meta = getCreditPackMeta(pack.credits);
                      const packName = pack.name || meta.name || `${pack.credits} Credits`;
                      const badge = pack.badge || meta.badge;
                      const questions = pack.questions ?? meta.questions;
                      const packBonusCredits =
                        Number(pack.pack_bonus_credits ?? meta.bonusCredits) || 0;
                      const totalCredits =
                        Number(pack.total_credits) || pack.credits + packBonusCredits;
                      const isPopular = Boolean(badge);
                      return (
                        <TouchableOpacity
                          key={`rzp-${pack.credits}`}
                          style={[
                            styles.creditPackCardWide,
                            {
                              backgroundColor: promoCardBg,
                              borderColor: isPopular ? colors.primary : colors.cardBorder,
                              borderWidth: isPopular ? 2 : 1,
                            },
                          ]}
                          onPress={() => handleBuyRazorpayPack(pack)}
                          disabled={purchasingRazorpayCredits !== null}
                        >
                          <View style={styles.creditPackWideTop}>
                            <View style={{ flex: 1 }}>
                              <View style={styles.creditPackNameRow}>
                                <Text style={[styles.creditPackName, { color: colors.text }]}>
                                  {packName}
                                </Text>
                                {badge ? (
                                  <View style={[styles.creditPackBadge, { backgroundColor: colors.primary }]}>
                                    <Text style={styles.creditPackBadgeText}>{badge}</Text>
                                  </View>
                                ) : null}
                              </View>
                              {pack.amount_display ? (
                                <Text style={[styles.creditPackPricePrimary, { color: colors.text }]}>
                                  {pack.amount_display}
                                </Text>
                              ) : null}
                              <Text style={[styles.creditPackCreditsSecondary, { color: colors.textSecondary }]}>
                                {t('credits.page.creditsCountTitle', { count: totalCredits })}
                              </Text>
                              {questions != null ? (
                                <Text style={[styles.creditPackQuestions, { color: colors.text }]}>
                                  {pack.credits >= 999
                                    ? t('credits.page.questionsWithTara', { count: questions })
                                    : t('credits.page.questionsCount', { count: questions })}
                                </Text>
                              ) : null}
                              {packBonusCredits > 0 ? (
                                <Text style={[styles.creditPackBonus, { color: colors.primary }]}>
                                  {t('credits.page.packBonusLine', {
                                    base: pack.credits,
                                    bonus: packBonusCredits,
                                  })}
                                </Text>
                              ) : null}
                            </View>
                            <View style={[styles.creditPackButton, { backgroundColor: colors.primary }]}>
                              <Text style={styles.creditPackButtonText}>
                                {purchasingRazorpayCredits === pack.credits
                                  ? t('credits.page.processing')
                                  : t('credits.page.buy')}
                              </Text>
                            </View>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                )}
              </View>
            )}

            {/* VIP subscriptions are discounts, not credit packs. Keep them secondary to reduce purchase confusion. */}
            {Platform.OS === 'android' && (
              <View style={styles.buySection}>
                <View style={[styles.vipDiscountPanel, androidGlassFixStyle, { backgroundColor: promoCardBg, borderColor: colors.cardBorder }]}>
                  <View style={styles.vipDiscountHeader}>
                    <View style={[styles.vipDiscountIcon, { backgroundColor: isDark ? 'rgba(249,115,22,0.16)' : 'rgba(255,107,53,0.1)' }]}>
                      <Ionicons name="shield-checkmark-outline" size={22} color={colors.primary} />
                    </View>
                    <View style={styles.vipDiscountCopy}>
                      <Text style={[styles.vipDiscountTitle, { color: colors.text }]}>
                        {subscriptionDetails
                          ? subscriptionDetails.tier_name
                          : subscriptionTierName && subscriptionDiscountPercent > 0
                            ? t('credits.page.vipDiscountBadge', { tier: subscriptionTierName, percent: subscriptionDiscountPercent })
                            : t('credits.page.vipPlans')}
                      </Text>
                      <Text style={[styles.vipDiscountText, { color: colors.textSecondary }]}>
                        {subscriptionDetails
                          ? t('credits.page.subscriptionBenefit', { percent: subscriptionDetails.discount_percent })
                          : t('credits.page.subscriptionCreditClarifier')}
                      </Text>
                    </View>
                  </View>

                  {subscriptionDetails ? (
                    <View style={[styles.subscriptionCardDates, styles.vipDiscountDates, { borderTopColor: colors.cardBorder }]}>
                      {subscriptionDetails.start_date ? (
                        <Text style={[styles.subscriptionCardDateLabel, { color: colors.textTertiary }]}>
                          {t('credits.page.subscribedOn', { date: formatSubscriptionDate(subscriptionDetails.start_date, dateLocale) })}
                        </Text>
                      ) : null}
                      {subscriptionDetails.end_date ? (
                        <Text style={[styles.subscriptionCardDateLabel, { color: colors.textTertiary }]}>
                          {t('credits.page.renewsOn', { date: formatSubscriptionDate(subscriptionDetails.end_date, dateLocale) })}
                        </Text>
                      ) : null}
                    </View>
                  ) : null}

                  <View style={styles.vipDiscountActions}>
                    <TouchableOpacity
                      style={[styles.vipDiscountPrimaryAction, { backgroundColor: isDark ? 'rgba(249,115,22,0.16)' : 'rgba(255,107,53,0.1)' }]}
                      onPress={() => setVipPlansExpanded((open) => !open)}
                    >
                      <Text style={[styles.vipDiscountPrimaryActionText, { color: colors.primary }]}>
                        {t('credits.page.vipPlans')}
                      </Text>
                      <Ionicons name={vipPlansExpanded ? 'chevron-up' : 'chevron-down'} size={18} color={colors.primary} />
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.vipDiscountSecondaryAction, { borderColor: colors.cardBorder }]}
                      onPress={() => navigation.navigate('MembershipComparison')}
                    >
                      <Ionicons name="help-buoy-outline" size={16} color={colors.primary} />
                      <Text style={[styles.vipDiscountSecondaryActionText, { color: colors.primary }]}>
                        Need help?
                      </Text>
                    </TouchableOpacity>
                  </View>

                  {vipPlansExpanded ? (
                    <View style={[styles.vipPlanList, { borderTopColor: colors.cardBorder }]}>
                      {subscriptionPlansLoading ? (
                        <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>{t('credits.page.loadingPlans')}</Text>
                      ) : subscriptionPlansFromPlay.length === 0 ? (
                        subscriptionPlans.length > 0 && iapReady ? (
                          <Text style={[styles.buyProductPlaceholder, { color: colors.textSecondary }]}>{t('credits.page.noSubscriptionPlansStore')}</Text>
                        ) : null
                      ) : (
                        <>
                          <Text style={[styles.vipPlanComplianceIntro, { color: colors.textSecondary }]}>
                            {t('credits.page.subscriptionOptionalNotice')}
                          </Text>
                          {subscriptionPlansFromPlay.map((plan) => {
                          const productId = plan.google_play_product_id;
                          const isCurrentPlan = subscriptionTierName && plan.tier_name === subscriptionTierName;
                          const isPurchasing = purchasingSubscriptionId === productId;
                          const displayPrice = getSubscriptionDisplayPrice(plan, iapSubscriptions);
                          const offerInfo = getSubscriptionOfferInfo(plan, iapSubscriptions);
                          const priceWithPeriod = offerInfo?.paidPeriod
                            ? t('credits.page.subscriptionPriceWithPeriod', { price: displayPrice || t('credits.page.vipFallback'), period: offerInfo.paidPeriod })
                            : displayPrice;
                          const renewsText = offerInfo?.paidPeriod
                            ? t('credits.page.subscriptionAutoRenewNotice', { period: offerInfo.paidPeriod })
                            : t('credits.page.subscriptionAutoRenewGeneric');
                          const trialText = offerInfo?.freeTrialPeriod
                            ? t('credits.page.subscriptionTrialNotice', { period: offerInfo.freeTrialPeriod, price: displayPrice || t('credits.page.vipFallback'), paid_period: offerInfo.paidPeriod || t('credits.page.subscriptionGenericPeriod') })
                            : null;
                          return (
                            <TouchableOpacity
                              key={plan.plan_id ?? productId}
                              style={[styles.vipPlanRow, { borderColor: colors.cardBorder }]}
                              onPress={() => handleSubscribePress(plan)}
                              disabled={isCurrentPlan || isPurchasing}
                            >
                              <View style={styles.vipPlanRowCopy}>
                                <Text style={[styles.vipPlanRowTitle, { color: colors.text }]}>{plan.tier_name || t('credits.page.vipFallback')}</Text>
                                <Text style={[styles.vipPlanRowMeta, { color: colors.textSecondary }]}>
                                  {t('credits.page.offPercent', { percent: plan.discount_percent ?? 0 })}
                                  {priceWithPeriod ? ` • ${priceWithPeriod}` : ''}
                                </Text>
                                {!!trialText && (
                                  <Text style={[styles.vipPlanRowTerms, { color: colors.textSecondary }]}>
                                    {trialText}
                                  </Text>
                                )}
                                <Text style={[styles.vipPlanRowTerms, { color: colors.textSecondary }]}>
                                  {renewsText}
                                </Text>
                                <Text style={[styles.vipPlanRowTerms, { color: colors.textSecondary }]}>
                                  {t('credits.page.subscriptionOptionalShort')}
                                </Text>
                              </View>
                              <View style={[styles.vipPlanRowButton, { backgroundColor: isCurrentPlan ? colors.textTertiary : colors.primary }]}>
                                <Text style={styles.vipPlanRowButtonText}>
                                  {isCurrentPlan ? t('credits.page.currentPlan') : isPurchasing ? t('credits.page.processing') : t('credits.page.subscribe')}
                                </Text>
                              </View>
                            </TouchableOpacity>
                          );
                        })}
                        </>
                      )}
                    </View>
                  ) : null}

                  {(subscriptionDetails || subscriptionTierName) && (
                    <View style={styles.vipManageActions}>
                      <TouchableOpacity
                        style={[styles.manageSubscriptionLink, { borderColor: colors.cardBorder }]}
                        onPress={() => Linking.openURL('https://play.google.com/store/account/subscriptions')}
                      >
                        <Ionicons name="open-outline" size={16} color={colors.primary} />
                        <Text style={[styles.manageSubscriptionLinkText, { color: colors.primary }]}>{t('credits.page.manageSubscription')}</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.manageSubscriptionLink, { borderColor: colors.cardBorder, marginTop: 6 }]}
                        onPress={handleRefreshSubscriptionStatus}
                        disabled={refreshSubscriptionStatusLoading}
                      >
                        <Ionicons name="refresh-outline" size={16} color={colors.primary} />
                        <Text style={[styles.manageSubscriptionLinkText, { color: colors.primary }]}>
                          {refreshSubscriptionStatusLoading ? t('credits.page.refreshing') : t('credits.page.refreshSubscriptionStatus')}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  )}
                </View>
              </View>
            )}

            {/* Promo Code Section */}
            <View style={styles.promoSection}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('credits.page.promoHeading')}</Text>
              <View style={[styles.promoCard, androidGlassFixStyle, { backgroundColor: promoCardBg, borderWidth: (isDark || Platform.OS === 'android') ? 1 : 0, borderColor: colors.cardBorder }]}>
                <View style={[styles.promoInputContainer, { backgroundColor: promoInputBg, borderColor: colors.cardBorder }]}>
                  <Ionicons name="ticket" size={20} color={colors.primary} style={styles.promoIcon} />
                  <TextInput
                    style={[styles.promoInput, { color: colors.text }]}
                    placeholder={t('credits.page.promoPlaceholder')}
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
                      {redeeming ? t('credits.page.redeeming') : t('credits.page.redeem')}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            </View>

            {/* Transaction History */}
            <View style={styles.historySection}>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{t('credits.page.transactionHistory')}</Text>
              {history.length > 0 ? (
                <View style={[styles.historyCard, androidGlassFixStyle, { backgroundColor: promoCardBg, borderWidth: (isDark || Platform.OS === 'android') ? 1 : 0, borderColor: colors.cardBorder }]}>
                  {history.map((item, index) => (
                    <View key={index}>
                      {renderTransaction({ item })}
                      {index < history.length - 1 && <View style={[styles.transactionDivider, { backgroundColor: colors.cardBorder }]} />}
                    </View>
                  ))}
                </View>
              ) : (
                <View style={[styles.emptyState, androidGlassFixStyle, { backgroundColor: promoCardBg, borderWidth: (isDark || Platform.OS === 'android') ? 1 : 0, borderColor: colors.cardBorder }]}>
                  <Ionicons name="receipt-outline" size={48} color={colors.textTertiary} />
                  <Text style={[styles.emptyStateText, { color: colors.textSecondary }]}>{t('credits.page.noTransactions')}</Text>
                  <Text style={[styles.emptyStateSubtext, { color: colors.textTertiary }]}>{t('credits.page.historyHint')}</Text>
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
            <View style={[styles.purchaseModalCard, androidGlassFixStyle, { backgroundColor: promoCardBg, borderColor: colors.cardBorder }]}>
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
                  <Text style={[styles.purchaseModalCreditsText, { color: colors.success }]}>{t('credits.page.modalCreditsAdded', { count: purchaseModal.creditsAdded })}</Text>
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
                  <Text style={styles.purchaseModalButtonText}>{t('credits.page.modalGotIt')}</Text>
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
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: { elevation: 0 },
    }),
  },
  headerContent: {
    alignItems: 'center',
  },
  cosmicOrb: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#ff6b35',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.3,
        shadowRadius: 16,
      },
      android: { elevation: 0 },
    }),
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
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.1,
        shadowRadius: 16,
      },
      android: { elevation: 0 },
    }),
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
  subscriptionCardDates: {
    borderTopWidth: 1,
    paddingTop: 12,
    gap: 4,
  },
  subscriptionCardDateLabel: {
    fontSize: 13,
  },
  manageSubscriptionLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 10,
  },
  manageSubscriptionLinkText: {
    fontSize: 14,
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
  firstPurchaseBonusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 12,
  },
  firstPurchaseBonusText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
  },
  packRelaunchBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 12,
  },
  packRelaunchText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
  },
  buyProductStack: {
    gap: 12,
  },
  creditPackCardWide: {
    width: '100%',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
  },
  creditPackWideTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  creditPackNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 4,
  },
  creditPackName: {
    fontSize: 16,
    fontWeight: '800',
  },
  creditPackBadge: {
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  creditPackBadgeText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  creditPackPricePrimary: {
    fontSize: 28,
    fontWeight: '800',
    marginBottom: 2,
  },
  creditPackCreditsSecondary: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 2,
  },
  creditPackQuestions: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 2,
  },
  creditPackSave: {
    fontSize: 13,
    fontWeight: '800',
    marginTop: 2,
  },
  creditPackCard: {
    width: (width - 52) / 2 - 6,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    minHeight: 132,
    justifyContent: 'space-between',
  },
  creditPackCredits: {
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 6,
  },
  creditPackBonus: {
    fontSize: 12,
    fontWeight: '800',
    marginTop: 2,
    marginBottom: 2,
  },
  creditPackPrice: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 12,
  },
  creditPackButton: {
    alignSelf: 'flex-start',
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 18,
  },
  creditPackButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  vipDiscountPanel: {
    borderWidth: 1,
    borderRadius: 18,
    padding: 16,
  },
  vipDiscountHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  vipDiscountIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  vipDiscountCopy: {
    flex: 1,
  },
  vipDiscountTitle: {
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 6,
  },
  vipDiscountText: {
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '600',
  },
  vipDiscountDates: {
    marginTop: 14,
  },
  vipDiscountActions: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 14,
  },
  vipDiscountPrimaryAction: {
    flex: 1,
    minHeight: 44,
    borderRadius: 12,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  vipDiscountPrimaryActionText: {
    fontSize: 14,
    fontWeight: '800',
  },
  vipDiscountSecondaryAction: {
    minHeight: 44,
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  vipDiscountSecondaryActionText: {
    fontSize: 13,
    fontWeight: '800',
  },
  vipPlanList: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: 1,
    gap: 10,
  },
  vipPlanComplianceIntro: {
    fontSize: 12,
    lineHeight: 18,
  },
  vipPlanRow: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  vipPlanRowCopy: {
    flex: 1,
  },
  vipPlanRowTitle: {
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 4,
  },
  vipPlanRowMeta: {
    fontSize: 13,
    fontWeight: '600',
  },
  vipPlanRowTerms: {
    fontSize: 11,
    lineHeight: 16,
    marginTop: 4,
  },
  vipPlanRowButton: {
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 12,
    minWidth: 92,
    alignItems: 'center',
  },
  vipPlanRowButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '800',
  },
  vipManageActions: {
    marginTop: 12,
  },
  promoCard: {
    borderRadius: 16,
    padding: 20,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
      },
      android: { elevation: 0 },
    }),
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
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
      },
      android: { elevation: 0 },
    }),
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
    minWidth: 0,
  },
  transactionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
    gap: 10,
  },
  transactionDescriptionWrap: {
    flex: 1,
    minWidth: 0,
    marginRight: 4,
  },
  transactionDescription: {
    fontSize: 16,
    fontWeight: '600',
  },
  transactionAmount: {
    fontSize: 16,
    fontWeight: '700',
    flexShrink: 0,
    textAlign: 'right',
    minWidth: 44,
  },
  transactionFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  transactionDate: {
    fontSize: 14,
    flex: 1,
    minWidth: 0,
    flexShrink: 1,
  },
  transactionBalance: {
    fontSize: 14,
    flexShrink: 0,
    textAlign: 'right',
  },
  transactionDivider: {
    height: 1,
    marginHorizontal: 16,
  },
  emptyState: {
    borderRadius: 16,
    padding: 40,
    alignItems: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 12,
      },
      android: { elevation: 0 },
    }),
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
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.2,
        shadowRadius: 24,
      },
      android: { elevation: 0 },
    }),
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
