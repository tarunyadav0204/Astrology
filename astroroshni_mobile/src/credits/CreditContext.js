import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { creditAPI } from './creditService';
import { pricingAPI } from '../services/api';

const CreditContext = createContext();

export const CreditProvider = ({ children }) => {
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(false);
  const [partnershipCost, setPartnershipCost] = useState(2);
  const [freeQuestionAvailable, setFreeQuestionAvailable] = useState(false);
  const [subscriptionTierName, setSubscriptionTierName] = useState(null);
  const [subscriptionDiscountPercent, setSubscriptionDiscountPercent] = useState(0);

  const fetchBalance = useCallback(async () => {
    try {
      // Check if user is authenticated first
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        setCredits(0);
        setFreeQuestionAvailable(false);
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
          headers: error.config?.headers
        }
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
        method: error.config?.method
      });
      
      // Handle different error response formats
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
      const response = await pricingAPI.getPricing();
      const data = response?.data || response;
      const cost = data?.pricing?.partnership != null ? Number(data.pricing.partnership) : 2;
      setPartnershipCost(cost);
    } catch (error) {
      console.error('Error fetching partnership cost:', error);
    }
  };

  useEffect(() => {
    fetchBalance();
    fetchPartnershipCost();
  }, []);

  return (
    <CreditContext.Provider value={{
      credits,
      loading,
      partnershipCost,
      freeQuestionAvailable,
      subscriptionTierName,
      subscriptionDiscountPercent,
      fetchBalance,
      redeemCode,
      spendCredits,
      refreshCredits: fetchBalance // Expose for manual refresh
    }}>
      {children}
    </CreditContext.Provider>
  );
};

export const useCredits = () => useContext(CreditContext);