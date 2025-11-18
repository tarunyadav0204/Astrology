import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';
import './CreditsPage.css';

const CreditsPage = () => {
    const { credits, fetchBalance } = useCredits();
    const [promoCode, setPromoCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [transactions, setTransactions] = useState([]);

    useEffect(() => {
        fetchBalance();
        loadTransactionHistory();
    }, []);

    const loadTransactionHistory = async () => {
        try {
            const response = await fetch('/api/credits/history');
            if (response.ok) {
                const data = await response.json();
                setTransactions(data.transactions || []);
            }
        } catch (error) {
            console.error('Error loading transaction history:', error);
        }
    };

    const handleRedeemPromo = async (e) => {
        e.preventDefault();
        if (!promoCode.trim()) return;

        setLoading(true);
        setMessage('');

        try {
            const response = await fetch('/api/credits/redeem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: promoCode.trim() })
            });

            const data = await response.json();
            
            if (data.success) {
                setMessage(`✅ ${data.message}`);
                setPromoCode('');
                fetchBalance();
                loadTransactionHistory();
            } else {
                setMessage(`❌ ${data.message}`);
            }
        } catch (error) {
            setMessage('❌ Error redeeming promo code');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="credits-page">
            <div className="credits-header">
                <h1>💳 Credits</h1>
                <div className="current-balance">
                    <span className="balance-label">Current Balance:</span>
                    <span className="balance-amount">{credits}</span>
                </div>
            </div>

            <div className="credits-content">
                <div className="promo-section">
                    <h2>🎫 Redeem Promo Code</h2>
                    <form onSubmit={handleRedeemPromo} className="promo-form">
                        <input
                            type="text"
                            value={promoCode}
                            onChange={(e) => setPromoCode(e.target.value)}
                            placeholder="Enter promo code"
                            className="promo-input"
                            disabled={loading}
                        />
                        <button 
                            type="submit" 
                            className="redeem-btn"
                            disabled={loading || !promoCode.trim()}
                        >
                            {loading ? 'Redeeming...' : 'Redeem'}
                        </button>
                    </form>
                    {message && (
                        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
                            {message}
                        </div>
                    )}
                </div>

                <div className="pricing-section">
                    <h2>💰 Credit Costs</h2>
                    <div className="pricing-grid">
                        <div className="pricing-item">
                            <span className="feature">Chat Question</span>
                            <span className="cost">1 credit</span>
                        </div>
                    </div>
                </div>

                {transactions.length > 0 && (
                    <div className="history-section">
                        <h2>📊 Transaction History</h2>
                        <div className="transactions-list">
                            {transactions.slice(0, 10).map((transaction, index) => (
                                <div key={index} className="transaction-item">
                                    <div className="transaction-info">
                                        <span className="transaction-type">
                                            {transaction.type === 'earned' ? '➕' : '➖'} 
                                            {transaction.description || transaction.source}
                                        </span>
                                        <span className="transaction-date">
                                            {new Date(transaction.date).toLocaleDateString()}
                                        </span>
                                    </div>
                                    <div className="transaction-amount">
                                        <span className={transaction.type === 'earned' ? 'earned' : 'spent'}>
                                            {transaction.type === 'earned' ? '+' : ''}{transaction.amount}
                                        </span>
                                        <span className="balance-after">
                                            Balance: {transaction.balance_after}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CreditsPage;