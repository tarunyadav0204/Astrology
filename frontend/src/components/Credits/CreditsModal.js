import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';

const CreditsModal = ({ isOpen, onClose }) => {
    const { credits, fetchBalance, chatCost } = useCredits();
    const [promoCode, setPromoCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const handleRedeemPromo = async (e) => {
        e.preventDefault();
        if (!promoCode.trim()) return;

        setLoading(true);
        setMessage('');

        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/credits/redeem', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` })
                },
                body: JSON.stringify({ code: promoCode.trim() })
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                setMessage(`✅ ${data.message}`);
                setPromoCode('');
                fetchBalance();
            } else {
                // Handle FastAPI HTTPException format
                const errorMessage = data.detail || data.message || 'Invalid promo code';
                setMessage(`❌ ${errorMessage}`);
            }
        } catch (error) {
            setMessage('❌ Error redeeming promo code');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10001
        }}>
            <div style={{
                background: 'white',
                borderRadius: '15px',
                padding: '30px',
                maxWidth: '450px',
                width: '90%',
                position: 'relative',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)'
            }}>
                <button 
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '15px',
                        right: '15px',
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        cursor: 'pointer',
                        color: '#666'
                    }}
                >
                    ×
                </button>

                <div style={{ textAlign: 'center', marginBottom: '25px' }}>
                    <h2 style={{ color: '#ff6b35', marginBottom: '10px', fontSize: '24px' }}>💳 Credits</h2>
                    <div style={{ 
                        background: 'linear-gradient(135deg, #ff6b35 0%, #f7931e 100%)',
                        color: 'white',
                        padding: '15px',
                        borderRadius: '10px',
                        fontSize: '18px',
                        fontWeight: 'bold'
                    }}>
                        Current Balance: {credits} credits
                    </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ color: '#333', marginBottom: '15px', fontSize: '18px' }}>🎫 Redeem Promo Code</h3>
                    <form onSubmit={handleRedeemPromo} style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
                        <input
                            type="text"
                            value={promoCode}
                            onChange={(e) => setPromoCode(e.target.value)}
                            placeholder="Enter promo code"
                            style={{
                                flex: 1,
                                padding: '12px',
                                border: '2px solid #ddd',
                                borderRadius: '8px',
                                fontSize: '16px',
                                outline: 'none'
                            }}
                            disabled={loading}
                        />
                        <button 
                            type="submit"
                            disabled={loading || !promoCode.trim()}
                            style={{
                                background: '#ff6b35',
                                color: 'white',
                                border: 'none',
                                padding: '12px 20px',
                                borderRadius: '8px',
                                fontSize: '16px',
                                fontWeight: 'bold',
                                cursor: 'pointer',
                                opacity: (loading || !promoCode.trim()) ? 0.6 : 1
                            }}
                        >
                            {loading ? 'Redeeming...' : 'Redeem'}
                        </button>
                    </form>
                    {message && (
                        <div style={{
                            padding: '10px',
                            borderRadius: '8px',
                            fontSize: '14px',
                            fontWeight: '500',
                            background: message.includes('✅') ? '#d4edda' : '#f8d7da',
                            color: message.includes('✅') ? '#155724' : '#721c24',
                            border: `1px solid ${message.includes('✅') ? '#c3e6cb' : '#f5c6cb'}`
                        }}>
                            {message}
                        </div>
                    )}
                </div>

                <div style={{ 
                    background: '#f8f9fa',
                    padding: '15px',
                    borderRadius: '10px',
                    borderLeft: '4px solid #ff6b35'
                }}>
                    <h4 style={{ color: '#333', margin: '0 0 10px 0', fontSize: '16px' }}>💰 Credit Costs</h4>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: '#333', fontWeight: '500' }}>Chat Question</span>
                        <span style={{ color: '#ff6b35', fontWeight: 'bold' }}>{chatCost} credit{chatCost > 1 ? 's' : ''}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CreditsModal;