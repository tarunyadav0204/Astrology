import React, { createContext, useContext, useState, useEffect } from 'react';
import { creditAPI } from './creditService';

const CreditContext = createContext();

export const CreditProvider = ({ children }) => {
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchBalance = async () => {
    try {
      setLoading(true);
      const response = await creditAPI.getBalance();
      setCredits(response.data.credits);
    } catch (error) {
      console.error('Error fetching credits:', error);
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
      spendCredits
    }}>
      {children}
    </CreditContext.Provider>
  );
};

export const useCredits = () => useContext(CreditContext);