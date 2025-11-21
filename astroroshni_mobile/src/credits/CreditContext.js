import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { creditAPI } from './creditService';

const CreditContext = createContext();

export const CreditProvider = ({ children }) => {
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchBalance = async () => {
    try {
      // Check if user is authenticated first
      const token = await AsyncStorage.getItem('authToken');
      if (!token) {
        console.log('⚠️ No auth token, skipping credit fetch');
        setCredits(0);
        return;
      }
      
      setLoading(true);
      console.log('🔄 Fetching credits from API...');
      const response = await creditAPI.getBalance();
      console.log('✅ Credits response:', response.data);
      setCredits(response.data.credits);
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
        console.log('User not authenticated for credits');
        setCredits(0);
      }
    } finally {
      setLoading(false);
    }
  };

  const redeemCode = async (code) => {
    try {
      const response = await creditAPI.redeemPromoCode(code);
      await fetchBalance();
      return response.data;
    } catch (error) {
      console.error('Redeem error:', error.response?.data || error.message);
      throw error.response?.data || { message: 'Failed to redeem code' };
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
  }, []);

  return (
    <CreditContext.Provider value={{
      credits,
      loading,
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