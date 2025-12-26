import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';
import './CreditsPage.css';

const CreditsPage = () => {
    const { credits, fetchBalance } = useCredits();
    const [promoCode, setPromoCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [transactions, setTransactions] = useState([]);
    
    // Credit request state
    const [requestAmount, setRequestAmount] = useState('');
    const [requestReason, setRequestReason] = useState('');
    const [requestLoading, setRequestLoading] = useState(false);
    const [requestMessage, setRequestMessage] = useState('');
    const [myRequests, setMyRequests] = useState([]);

    useEffect(() => {
        fetchBalance();
        loadTransactionHistory();
        loadMyRequests();
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

    const loadMyRequests = async () => {
        try {
            const response = await fetch('/api/credits/requests/my');
            if (response.ok) {
                const data = await response.json();
                setMyRequests(data.requests || []);
            }
        } catch (error) {
            console.error('Error loading requests:', error);
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

    const validateReason = (reason) => {
        return reason
            .replace(/<[^>]*>/g, '')
            .replace(/[<>'"]/g, '')
            .trim()
            .substring(0, 500);
    };

    const handleCreditRequest = async (e) => {
        e.preventDefault();
        if (!requestAmount || !requestReason.trim()) return;

        const sanitizedReason = validateReason(requestReason);
        if (sanitizedReason.length < 10) {
            setRequestMessage('❌ Reason must be at least 10 characters');
            return;
        }

        setRequestLoading(true);
        setRequestMessage('');

        try {
            const response = await fetch('/api/credits/request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    amount: parseInt(requestAmount),
                    reason: sanitizedReason
                })
            });

            const data = await response.json();
            
            if (data.success) {
                setRequestMessage(`✅ ${data.message}`);
                setRequestAmount('');
                setRequestReason('');
                loadMyRequests();
            } else {
                setRequestMessage(`❌ ${data.message}`);
            }
        } catch (error) {
            setRequestMessage('❌ Error submitting request');
        } finally {
            setRequestLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch(status) {
            case 'approved': return '#4CAF50';
            case 'rejected': return '#f44336';
            default: return '#ff9800';
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

                <div className="request-section">
                    <h2>🙋♂️ Request Credits</h2>
                    <form onSubmit={handleCreditRequest} className="request-form">
                        <input
                            type="number"
                            value={requestAmount}
                            onChange={(e) => setRequestAmount(e.target.value)}
                            placeholder="Credits needed (1-100)"
                            min="1"
                            max="100"
                            className="request-input"
                            disabled={requestLoading}
                        />
                        <textarea
                            value={requestReason}
                            onChange={(e) => setRequestReason(validateReason(e.target.value))}
                            placeholder="Reason for request (e.g., student discount, financial hardship)"
                            rows="3"
                            className="request-textarea"
                            disabled={requestLoading}
                            maxLength="500"
                        />
                        <button 
                            type="submit" 
                            className="request-btn"
                            disabled={requestLoading || !requestAmount || !requestReason.trim()}
                        >
                            {requestLoading ? 'Submitting...' : 'Submit Request'}
                        </button>
                    </form>
                    {requestMessage && (
                        <div className={`message ${requestMessage.includes('✅') ? 'success' : 'error'}`}>
                            {requestMessage}
                        </div>
                    )}
                </div>

                {myRequests.length > 0 && (
                    <div className="my-requests-section">
                        <h2>📋 My Credit Requests</h2>
                        <div className="requests-list">
                            {myRequests.slice(0, 5).map((request) => (
                                <div key={request.id} className="request-item">
                                    <div className="request-info">
                                        <span className="request-amount">{request.requested_amount} credits</span>
                                        <span 
                                            className="request-status"
                                            style={{ color: getStatusColor(request.status) }}
                                        >
                                            {request.status.toUpperCase()}
                                        </span>
                                    </div>
                                    <div className="request-details">
                                        <p className="request-reason">{request.reason}</p>
                                        {request.admin_notes && (
                                            <p className="admin-notes">Admin: {request.admin_notes}</p>
                                        )}
                                        <span className="request-date">
                                            {new Date(request.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

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