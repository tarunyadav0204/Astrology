import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const CreditContext = createContext();

export const useCredits = () => {
    const context = useContext(CreditContext);
    if (!context) {
        throw new Error('useCredits must be used within a CreditProvider');
    }
    return context;
};

export const CreditProvider = ({ children }) => {
    const [credits, setCredits] = useState(0);
    const [chatCost, setChatCost] = useState(1);
    const [premiumChatCost, setPremiumChatCost] = useState(10);
    const [partnershipCost, setPartnershipCost] = useState(2);
    const [wealthCost, setWealthCost] = useState(5);
    const [marriageCost, setMarriageCost] = useState(3);
    const [healthCost, setHealthCost] = useState(3);
    const [educationCost, setEducationCost] = useState(3);
    const [careerCost, setCareerCost] = useState(12);
    const [podcastCost, setPodcastCost] = useState(2);
    const [loading, setLoading] = useState(true);

    const fetchBalance = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            
            // Only fetch balance if user is authenticated
            if (!token) {
                console.log('🔄 No token found, skipping credit balance fetch');
                setCredits(0);
                return;
            }
            
            console.log('🔄 Fetching credit balance...', { hasToken: !!token });
            const response = await fetch('/api/credits/balance', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            console.log('💳 Credit balance response:', { status: response.status, ok: response.ok });
            
            if (response.ok) {
                const data = await response.json();
                console.log('💳 Credit balance data:', data);
                setCredits(data.credits || 0);
            } else if (response.status === 403 || response.status === 401) {
                // User not authenticated or token expired
                console.log('💳 Authentication failed, setting credits to 0');
                setCredits(0);
            } else {
                console.error('Credit balance fetch failed:', response.status, response.statusText);
                setCredits(0);
            }
        } catch (error) {
            console.error('Error fetching credit balance:', error);
            setCredits(0);
        }
    }, []);

    const fetchCosts = useCallback(async () => {
        try {
            const token = localStorage.getItem('token');
            let pricing = {};
            if (token) {
                const response = await fetch('/api/credits/settings/my-pricing', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    pricing = data.pricing || {};
                }
            }
            if (Object.keys(pricing).length === 0) {
                const response = await fetch('/api/credits/settings/analysis-pricing');
                if (response.ok) {
                    const data = await response.json();
                    pricing = data.pricing || {};
                }
            }
            if (pricing.chat != null) setChatCost(Number(pricing.chat) || 1);
            if (pricing.premium_chat != null) setPremiumChatCost(Number(pricing.premium_chat) || 10);
            if (pricing.partnership != null) setPartnershipCost(Number(pricing.partnership) || 2);
            if (pricing.wealth != null) setWealthCost(Number(pricing.wealth) || 5);
            if (pricing.marriage != null) setMarriageCost(Number(pricing.marriage) || 3);
            if (pricing.health != null) setHealthCost(Number(pricing.health) || 3);
            if (pricing.education != null) setEducationCost(Number(pricing.education) || 3);
            if (pricing.career != null) setCareerCost(Number(pricing.career) || 12);
        } catch (error) {
            console.error('Error fetching pricing:', error);
        }
    }, []);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            await Promise.all([fetchBalance(), fetchCosts()]);
            setLoading(false);
        };
        loadData();
    }, [fetchBalance, fetchCosts]);

    const spendCredits = async (amount, feature, description) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/credits/spend', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({ amount, feature, description })
            });
            
            if (response.ok) {
                await fetchBalance();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error spending credits:', error);
            return false;
        }
    };

    // Add refresh mechanism
    const refreshBalance = () => {
        fetchBalance();
    };

    // Listen for credit updates from other parts of the app
    useEffect(() => {
        const handleCreditUpdate = () => {
            fetchBalance();
            fetchCosts();
        };
        
        const handleFocus = () => {
            // Refresh balance and pricing when user returns to tab
            const token = localStorage.getItem('token');
            if (token) {
                fetchBalance();
                fetchCosts();
            }
        };
        
        window.addEventListener('creditUpdated', handleCreditUpdate);
        window.addEventListener('focus', handleFocus);
        
        return () => {
            window.removeEventListener('creditUpdated', handleCreditUpdate);
            window.removeEventListener('focus', handleFocus);
        };
    }, [fetchBalance, fetchCosts]);

    return (
        <CreditContext.Provider value={{
            credits,
            chatCost,
            premiumChatCost,
            partnershipCost,
            wealthCost,
            marriageCost,
            healthCost,
            educationCost,
            careerCost,
            podcastCost,
            loading,
            fetchBalance,
            fetchCosts,
            refreshBalance,
            spendCredits
        }}>
            {children}
        </CreditContext.Provider>
    );
};