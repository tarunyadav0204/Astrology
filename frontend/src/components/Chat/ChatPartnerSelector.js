import React, { useState, useEffect } from 'react';

const ChatPartnerSelector = ({ isOpen, onClose, onSelectPartner }) => {
    const [savedCharts, setSavedCharts] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            loadSavedCharts();
        }
    }, [isOpen]);

    const loadSavedCharts = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/birth-charts', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                setSavedCharts(data.charts || []);
            }
        } catch (error) {
            console.error('Error loading charts:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectChart = (chart) => {
        onSelectPartner(chart);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000
        }}>
            <div style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '24px',
                maxWidth: '500px',
                width: '90%',
                maxHeight: '70vh',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column'
            }}>
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '20px',
                    borderBottom: '1px solid #eee',
                    paddingBottom: '12px'
                }}>
                    <h3 style={{ margin: 0, color: '#333' }}>Select Partner Chart</h3>
                    <button 
                        onClick={onClose}
                        style={{
                            background: 'none',
                            border: 'none',
                            fontSize: '24px',
                            cursor: 'pointer',
                            color: '#666'
                        }}
                    >
                        ×
                    </button>
                </div>

                <div style={{ flex: 1, overflow: 'auto' }}>
                    {loading ? (
                        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                            Loading charts...
                        </div>
                    ) : savedCharts.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                            No saved charts found
                        </div>
                    ) : (
                        savedCharts.map((chart, index) => (
                            <div
                                key={index}
                                onClick={() => handleSelectChart(chart)}
                                style={{
                                    padding: '16px',
                                    border: '1px solid #eee',
                                    borderRadius: '8px',
                                    marginBottom: '12px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                    backgroundColor: '#fafafa'
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.backgroundColor = '#f0f0f0';
                                    e.target.style.borderColor = '#ff6b35';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.backgroundColor = '#fafafa';
                                    e.target.style.borderColor = '#eee';
                                }}
                            >
                                <div style={{ fontWeight: '600', color: '#333', marginBottom: '4px' }}>
                                    {chart.name}
                                </div>
                                <div style={{ fontSize: '14px', color: '#666', marginBottom: '2px' }}>
                                    {chart.date} • {chart.time}
                                </div>
                                <div style={{ fontSize: '12px', color: '#999' }}>
                                    {chart.place}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChatPartnerSelector;