import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { creditAPI } from './creditService';

const CreditContext = createContext();

export const CreditProvider = ({ children }) => {
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(false);
  const [partnershipCost, setPartnershipCost] = useState(2);
  const [podcastCost, setPodcastCost] = useState(2);
  const [freeQuestionAvailable, setFreeQuestionAvailable] = useState(false);
  const [freeQuestionRequiresNotifications, setFreeQuestionRequiresNotifications] = useState(false);
  const [subscriptionTierName, setSubscriptionTierName] = useState(null);
  const [subscriptionDiscountPercent, setSubscriptionDiscountPercent] = useState(0);

  const fetchBalance = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        setCredits(0);
        setFreeQuestionAvailable(false);
        setFreeQuestionRequiresNotifications(false);
        setSubscriptionTierName(null);
        setSubscriptionDiscountPercent(0);
        return;
      }

      setLoading(true);
      const response = await creditAPI.getBalance();
      const data = response?.data;
      const balance = data?.credits ?? data?.balance ?? 0;
      setCredits(Number(balance) || 0);
      setFreeQuestionAvailable(Boolean(data?.free_question_available));
      setFreeQuestionRequiresNotifications(Boolean(data?.free_question_requires_notifications));
      setSubscriptionTierName(data?.subscription_tier_name ?? null);
      setSubscriptionDiscountPercent(Number(data?.subscription_discount_percent) || 0);
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
        setCredits(0);
        setSubscriptionTierName(null);
        setSubscriptionDiscountPercent(0);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const redeemCode = async (code) => {
    try {
      const response = await creditAPI.redeemPromoCode(code);
      await fetchBalance();
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

  const fetchPartnershipCost = async () => {
    try {
      const { API_BASE_URL, getEndpoint } = require('../utils/constants');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/credits/settings/partnership-cost')}`);
      if (response.ok) {
        const data = await response.json();
        setPartnershipCost(data.cost || 2);
      }
    } catch (error) {
      console.error('Error fetching partnership cost:', error);
    }
  };

  const fetchPodcastCost = async () => {
    try {
      const { API_BASE_URL, getEndpoint } = require('../utils/constants');
      const response = await fetch(`${API_BASE_URL}${getEndpoint('/credits/settings/my-pricing')}`, {
        headers: { Authorization: `Bearer ${await AsyncStorage.getItem('authToken')}` },
      });
      if (response.ok) {
        const data = await response.json();
        const p = data?.pricing?.podcast;
        if (p != null) setPodcastCost(Number(p));
      }
    } catch (_) {
      /* optional */
    }
  };

  useEffect(() => {
    fetchBalance();
    fetchPartnershipCost();
    fetchPodcastCost();
  }, []);

  return (
    <CreditContext.Provider
      value={{
        credits,
        loading,
        partnershipCost,
        podcastCost,
        freeQuestionAvailable,
        freeQuestionRequiresNotifications,
        subscriptionTierName,
        subscriptionDiscountPercent,
        fetchBalance,
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
