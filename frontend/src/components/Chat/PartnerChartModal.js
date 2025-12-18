import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';
import './PartnerChartModal.css';

const PartnerChartModal = ({ isOpen, onClose, onSelectPartner }) => {
    const [charts, setCharts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        if (isOpen) {
            loadCharts();
        }
    }, [isOpen]);

    const loadCharts = async (search = '') => {
        try {
            setLoading(true);
            const response = await apiService.getExistingCharts(search);
            setCharts(response.charts || []);
        } catch (error) {
            console.error('Failed to load charts:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        setTimeout(() => loadCharts(query), 300);
    };

    const selectPartner = (chart) => {
        onSelectPartner(chart);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="partner-modal-overlay">
            <div className="partner-modal">
                <div className="partner-modal-header">
                    <h3>Select Partner's Chart</h3>
                    <button onClick={onClose} className="close-btn">×</button>
                </div>
                
                <div className="partner-modal-content">
                    <input
                        type="text"
                        placeholder="Search charts..."
                        value={searchQuery}
                        onChange={handleSearch}
                        className="partner-search-input"
                    />
                    
                    {loading ? (
                        <div className="partner-loading">Loading charts...</div>
                    ) : charts.length === 0 ? (
                        <div className="partner-no-charts">No charts found</div>
                    ) : (
                        <div className="partner-charts-list">
                            {charts.map(chart => (
                                <div
                                    key={chart.id}
                                    onClick={() => selectPartner(chart)}
                                    className="partner-chart-item"
                                >
                                    <div className="partner-chart-name">{chart.name}</div>
                                    <div className="partner-chart-details">
                                        <div>📅 {new Date(chart.date).toLocaleDateString()}</div>
                                        <div>📍 {chart.place || `${chart.latitude.toFixed(2)}, ${chart.longitude.toFixed(2)}`}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PartnerChartModal;