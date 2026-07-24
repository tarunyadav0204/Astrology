import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { creditAPI } from './creditService';
import { pricingAPI } from '../services/api';

const CreditContext = createContext();

/** Shared TTL so Home + Chat do not each hit my-pricing on every focus. */
const PRICING_TTL_MS = 5 * 60 * 1000;

const normalizePricingPayload = (raw) => {
  const payload = raw?.data ?? raw ?? {};
  if (payload?.pricing && typeof payload.pricing === 'object') {
    return {
      pricing: payload.pricing,
      pricingOriginal: payload.pricing_original || {},
      features: payload.features || {},
      chatCountdownSeconds: payload.chat_countdown_seconds || {},
    };
  }
  if (payload && typeof payload.career !== 'undefined') {
    return {
      pricing: payload,
      pricingOriginal: {},
      features: {},
      chatCountdownSeconds: {},
    };
  }
  return {
    pricing: {},
    pricingOriginal: {},
    features: {},
    chatCountdownSeconds: {},
  };
};

export const CreditProvider = ({ children }) => {
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isGuest, setIsGuest] = useState(true);
  const [partnershipCost, setPartnershipCost] = useState(2);
  const [podcastCost, setPodcastCost] = useState(2);
  const [freeQuestionAvailable, setFreeQuestionAvailable] = useState(false);
  const [freeQuestionRequiresNotifications, setFreeQuestionRequiresNotifications] = useState(false);
  const [subscriptionTierName, setSubscriptionTierName] = useState(null);
  const [subscriptionDiscountPercent, setSubscriptionDiscountPercent] = useState(0);
  const [entitlements, setEntitlements] = useState([]);
  const [isAstrologerLicensed, setIsAstrologerLicensed] = useState(false);
  const [isGuruMember, setIsGuruMember] = useState(false);
  const [pricing, setPricing] = useState({});
  const [pricingOriginal, setPricingOriginal] = useState({});
  const [pricingFeatures, setPricingFeatures] = useState({});
  const [chatCountdownSeconds, setChatCountdownSeconds] = useState({ standard: 110, premium: 210 });

  const pricingFetchedAtRef = useRef(0);
  const pricingInFlightRef = useRef(null);

  const applyPricingPayload = useCallback((raw) => {
    const normalized = normalizePricingPayload(raw);
    setPricing(normalized.pricing);
    setPricingOriginal(normalized.pricingOriginal);
    setPricingFeatures(normalized.features);
    setChatCountdownSeconds(normalized.chatCountdownSeconds);
    if (normalized.pricing.partnership != null) {
      setPartnershipCost(Number(normalized.pricing.partnership));
    }
    if (normalized.pricing.podcast != null) {
      setPodcastCost(Number(normalized.pricing.podcast));
    }
    return normalized;
  }, []);

  const fetchPricing = useCallback(async ({ force = false } = {}) => {
    const now = Date.now();
    if (
      !force &&
      pricingFetchedAtRef.current > 0 &&
      now - pricingFetchedAtRef.current < PRICING_TTL_MS
    ) {
      return {
        pricing,
        pricingOriginal,
        features: pricingFeatures,
        chatCountdownSeconds,
      };
    }

    if (pricingInFlightRef.current) {
      return pricingInFlightRef.current;
    }

    const run = (async () => {
      try {
        const token = await AsyncStorage.getItem('authToken');
        // Guests: public analysis-pricing so Home can still show costs.
        const response = token
          ? await pricingAPI.getPricing()
          : await pricingAPI.getAnalysisPricing();
        pricingFetchedAtRef.current = Date.now();
        return applyPricingPayload(response);
      } catch (error) {
        console.error('Error fetching pricing:', error);
        return {
          pricing,
          pricingOriginal,
          features: pricingFeatures,
          chatCountdownSeconds,
        };
      }
    })();

    pricingInFlightRef.current = run;
    try {
      return await run;
    } finally {
      pricingInFlightRef.current = null;
    }
  }, [applyPricingPayload]);

  const fetchBalance = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        setIsGuest(true);
        setCredits(0);
        setFreeQuestionAvailable(false);
        setFreeQuestionRequiresNotifications(false);
        setSubscriptionTierName(null);
        setSubscriptionDiscountPercent(0);
        setEntitlements([]);
        setIsAstrologerLicensed(false);
        setIsGuruMember(false);
        return 0;
      }

      setIsGuest(false);
      setLoading(true);
      const response = await creditAPI.getBalance();
      const data = response?.data;
      const balance = Number(data?.credits ?? data?.balance ?? 0) || 0;
      setCredits(balance);
      setFreeQuestionAvailable(Boolean(data?.free_question_available));
      setFreeQuestionRequiresNotifications(Boolean(data?.free_question_requires_notifications));
      setSubscriptionTierName(data?.subscription_tier_name ?? null);
      setSubscriptionDiscountPercent(Number(data?.subscription_discount_percent) || 0);
      setEntitlements(Array.isArray(data?.entitlements) ? data.entitlements : []);
      setIsAstrologerLicensed(Boolean(data?.is_astrologer_licensed));
      setIsGuruMember(Boolean(data?.is_guru_member));
      return balance;
    } catch (error) {
      console.error('❌ Error fetching credits:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          headers: error.config?.headers,
        },
      });
      if (error.response?.status === 401) {
        setIsGuest(true);
        setCredits(0);
        setFreeQuestionAvailable(false);
        setFreeQuestionRequiresNotifications(false);
        setSubscriptionTierName(null);
        setSubscriptionDiscountPercent(0);
        setEntitlements([]);
        setIsAstrologerLicensed(false);
        setIsGuruMember(false);
        return 0;
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const redeemCode = async (code) => {
    try {
      const response = await creditAPI.redeemPromoCode(code);
      await fetchBalance();
      await fetchPricing({ force: true });
      return response.data;
    } catch (error) {
      console.error('❌ CreditContext: Redeem error details:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
        url: error.config?.url,
        method: error.config?.method,
      });

      let errorData;
      if (error.response?.data) {
        if (typeof error.response.data === 'string') {
          errorData = { message: error.response.data };
        } else {
          errorData = error.response.data;
        }
      } else {
        errorData = { message: error.message || 'Failed to redeem code' };
      }

      throw errorData;
    }
  };

  const spendCredits = async (amount, feature, description) => {
    try {
      await creditAPI.spendCredits(amount, feature, description);
      await fetchBalance();
      return true;
    } catch (error) {
      return false;
    }
  };

  useEffect(() => {
    fetchBalance();
    fetchPricing({ force: true });
  }, [fetchBalance, fetchPricing]);

  return (
    <CreditContext.Provider
      value={{
        credits,
        loading,
        isGuest,
        partnershipCost,
        podcastCost,
        freeQuestionAvailable,
        freeQuestionRequiresNotifications,
        subscriptionTierName,
        subscriptionDiscountPercent,
        entitlements,
        isAstrologerLicensed,
        isGuruMember,
        pricing,
        pricingOriginal,
        pricingFeatures,
        chatCountdownSeconds,
        fetchBalance,
        fetchPricing,
        redeemCode,
        spendCredits,
        refreshCredits: fetchBalance,
      }}
    >
      {children}
    </CreditContext.Provider>
  );
};

export const useCredits = () => useContext(CreditContext);
