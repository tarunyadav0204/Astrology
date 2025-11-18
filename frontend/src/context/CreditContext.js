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
    const [loading, setLoading] = useState(true);

    const fetchBalance = async () => {
        try {
            const token = localStorage.getItem('token');
            console.log('🔄 Fetching credit balance...', { hasToken: !!token });
            const response = await fetch('/api/credits/balance', {
                headers: {
                    ...(token && { 'Authorization': `Bearer ${token}` })
                }
            });
            console.log('💳 Credit balance response:', { status: response.status, ok: response.ok });
            if (response.ok) {
                const data = await response.json();
                console.log('💳 Credit balance data:', data);
                setCredits(data.credits || 0);
            } else {
                console.error('Credit balance fetch failed:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('Error fetching credit balance:', error);
        }
    };

    const fetchChatCost = async () => {
        try {
            const response = await fetch('/api/credits/settings/chat-cost');
            if (response.ok) {
                const data = await response.json();
                setChatCost(data.cost || 1);
            }
        } catch (error) {
            console.error('Error fetching chat cost:', error);
        }
    };

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            await Promise.all([fetchBalance(), fetchChatCost()]);
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
            loading,
            fetchBalance,
            spendCredits
        }}>
            {children}
        </CreditContext.Provider>
    );
};