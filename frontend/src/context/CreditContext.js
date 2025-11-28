import React, { createContext, useContext, useState, useEffect } from 'react';

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
    const [wealthCost, setWealthCost] = useState(5);
    const [marriageCost, setMarriageCost] = useState(3);
    const [healthCost, setHealthCost] = useState(3);
    const [educationCost, setEducationCost] = useState(3);
    const [loading, setLoading] = useState(true);

    const fetchBalance = async () => {
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
    };

    const fetchCosts = async () => {
        try {
            const response = await fetch('/api/credits/settings/chat-cost');
            if (response.ok) {
                const data = await response.json();
                setChatCost(data.cost || 1);
            }
        } catch (error) {
            console.error('Error fetching chat cost:', error);
        }
        
        try {
            const response = await fetch('/api/credits/settings/wealth-cost');
            if (response.ok) {
                const data = await response.json();
                setWealthCost(data.cost || 5);
            }
        } catch (error) {
            console.error('Error fetching wealth cost:', error);
        }
        
        try {
            const response = await fetch('/api/credits/settings/marriage-cost');
            if (response.ok) {
                const data = await response.json();
                setMarriageCost(data.cost || 3);
            }
        } catch (error) {
            console.error('Error fetching marriage cost:', error);
        }
        
        try {
            const response = await fetch('/api/credits/settings/health-cost');
            if (response.ok) {
                const data = await response.json();
                setHealthCost(data.cost || 3);
            }
        } catch (error) {
            console.error('Error fetching health cost:', error);
        }
        
        try {
            const response = await fetch('/api/credits/settings/education-cost');
            if (response.ok) {
                const data = await response.json();
                setEducationCost(data.cost || 3);
            }
        } catch (error) {
            console.error('Error fetching education cost:', error);
        }
        
        try {
            const response = await fetch('/api/credits/settings/premium-chat-cost');
            if (response.ok) {
                const data = await response.json();
                setPremiumChatCost(data.cost || 10);
            }
        } catch (error) {
            console.error('Error fetching premium chat cost:', error);
        }
    };

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            await Promise.all([fetchBalance(), fetchCosts()]);
            setLoading(false);
        };
        loadData();
    }, []);

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

    return (
        <CreditContext.Provider value={{
            credits,
            chatCost,
            premiumChatCost,
            wealthCost,
            marriageCost,
            healthCost,
            educationCost,
            loading,
            fetchBalance,
            spendCredits
        }}>
            {children}
        </CreditContext.Provider>
    );
};