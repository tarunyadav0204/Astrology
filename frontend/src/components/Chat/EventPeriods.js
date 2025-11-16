import React, { useState, useEffect } from 'react';

const EventPeriods = ({ birthData, onPeriodSelect, onBack }) => {
    const [periods, setPeriods] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [viewMode, setViewMode] = useState(window.innerWidth <= 768 ? 'cards' : 'timeline');

    useEffect(() => {
        loadEventPeriods();
    }, [selectedYear]);

    const loadEventPeriods = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/chat/event-periods', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...birthData, selectedYear })
            });

            if (!response.ok) {
                throw new Error('Failed to load event periods');
            }

            const data = await response.json();
            console.log('Event periods API response:', data);
            // Filter periods for selected year and sort by date
            const filteredPeriods = (data.periods || []).filter(period => {
                const periodYear = new Date(period.start_date).getFullYear();
                return periodYear === selectedYear;
            }).sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
            console.log('Filtered periods:', filteredPeriods);
            if (filteredPeriods.length > 0) {
                console.log('Sample period data:', filteredPeriods[0]);
            }
            setPeriods(filteredPeriods);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateStr) => {
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const getAspectText = (aspectNumber) => {
        if (!aspectNumber) return null;
        if (aspectNumber === 1) return 'conjunction';
        const suffix = aspectNumber === 1 ? 'st' : aspectNumber === 2 ? 'nd' : aspectNumber === 3 ? 'rd' : 'th';
        return `${aspectNumber}${suffix} aspect`;
    };

    const getSignificanceColor = (significance) => {
        switch (significance) {
            case 'maximum': return '#ff4757';
            case 'high': return '#ff6b35';
            default: return '#3742fa';
        }
    };

    const getSignificanceLabel = (significance) => {
        switch (significance) {
            case 'maximum': return '🔥 Maximum';
            case 'high': return '📈 High';
            default: return '📊 Moderate';
        }
    };

    if (loading) {
        return (
            <div className="event-periods-loading">
                <div className="loading-spinner">🔮</div>
                <p>Analyzing your chart for significant periods...</p>
                <p className="loading-subtext">This may take a moment as we calculate transit activations</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="event-periods-error">
                <h4>Unable to Load Event Periods</h4>
                <p>{error}</p>
                <button onClick={onBack} className="back-btn">← Back to Options</button>
            </div>
        );
    }

    const currentYear = new Date().getFullYear();
    const yearOptions = Array.from({ length: 131 }, (_, i) => 1950 + i);

    return (
        <div className="event-periods">
            <div className="periods-header">
                <div className="mobile-compact-header">
                    <button onClick={onBack} className="back-btn-compact">←</button>
                    <select 
                        value={selectedYear} 
                        onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                        className="year-select-compact"
                    >
                        {yearOptions.map(year => (
                            <option key={year} value={year}>{year}</option>
                        ))}
                    </select>
                    <button onClick={() => setViewMode(viewMode === 'timeline' ? 'cards' : 'timeline')} className="toggle-btn-compact">
                        {viewMode === 'timeline' ? '📋' : '📊'}
                    </button>
                </div>
            </div>

            {periods.length === 0 ? (
                <div className="no-periods">
                    <p>No high-significance periods found for {selectedYear}.</p>
                    <button onClick={onBack} className="back-btn">← Back to Options</button>
                </div>
            ) : viewMode === 'timeline' ? (
                <div className="timeline-container">
                    <div className="timeline-visualization">
                        {(() => {
                            // Group periods by significance
                            const groupedPeriods = {
                                maximum: periods.filter(p => p.significance === 'maximum'),
                                high: periods.filter(p => p.significance === 'high'),
                                moderate: periods.filter(p => p.significance === 'moderate')
                            };
                            
                            // Calculate timeline bounds based on actual period dates
                            const allDates = periods.flatMap(p => [new Date(p.start_date), new Date(p.end_date)]);
                            let minDate, maxDate, timelineWidth;
                            
                            if (allDates.length === 0) {
                                // Fallback if no periods
                                minDate = new Date(selectedYear, 0, 1);
                                maxDate = new Date(selectedYear, 11, 31);
                            } else {
                                const earliestDate = new Date(Math.min(...allDates));
                                const latestDate = new Date(Math.max(...allDates));
                                
                                // Start from beginning of month of earliest period
                                minDate = new Date(earliestDate.getFullYear(), earliestDate.getMonth(), 1);
                                // End at end of month of latest period
                                maxDate = new Date(latestDate.getFullYear(), latestDate.getMonth() + 1, 0);
                            }
                            
                            timelineWidth = maxDate.getTime() - minDate.getTime();
                            
                            const getPositionAndWidth = (period) => {
                                const start = new Date(period.start_date).getTime();
                                const end = new Date(period.end_date).getTime();
                                const timelineWidthPx = 1200; // Fixed timeline width in pixels
                                const leftPx = ((start - minDate.getTime()) / timelineWidth) * timelineWidthPx;
                                const calculatedWidthPx = ((end - start) / timelineWidth) * timelineWidthPx;
                                
                                // Ensure minimum width for readability
                                const minWidthPx = 180; // Minimum 180px width
                                const widthPx = Math.max(calculatedWidthPx, minWidthPx);
                                
                                return { left: `${leftPx}px`, width: `${widthPx}px` };
                            };
                            
                            return (
                                <>
                                    {/* Month markers */}
                                    <div className="timeline-months">
                                        {(() => {
                                            const months = [];
                                            const startMonth = new Date(minDate.getFullYear(), minDate.getMonth(), 1);
                                            const endMonth = new Date(maxDate.getFullYear(), maxDate.getMonth(), 1);
                                            
                                            let currentMonth = new Date(startMonth);
                                            while (currentMonth <= endMonth) {
                                                const pos = ((currentMonth.getTime() - minDate.getTime()) / timelineWidth) * 1200;
                                                const monthKey = `${currentMonth.getFullYear()}-${currentMonth.getMonth()}`;
                                                
                                                months.push(
                                                    <div key={monthKey} className="month-marker" style={{left: `${pos}px`}}>
                                                        {currentMonth.toLocaleDateString('en-US', {month: 'short'})}
                                                        <span className="year-indicator">{currentMonth.getFullYear()}</span>
                                                    </div>
                                                );
                                                
                                                currentMonth.setMonth(currentMonth.getMonth() + 1);
                                            }
                                            
                                            return months;
                                        })()
                                        }
                                    </div>
                                    
                                    {/* Timeline tracks - only show if periods exist */}
                                    {Object.entries(groupedPeriods)
                                        .filter(([significance, periodList]) => periodList.length > 0)
                                        .map(([significance, periodList]) => {
                                        return (
                                            <div key={significance} className={`timeline-track timeline-${significance}`}>
                                                <div className="track-label">
                                                    <span className="significance-icon">
                                                        {significance === 'maximum' && '🔥'}
                                                        {significance === 'high' && '📈'}
                                                        {significance === 'moderate' && '📊'}
                                                    </span>
                                                    <span className="significance-text">
                                                        {significance === 'maximum' && 'Maximum'}
                                                        {significance === 'high' && 'High'}
                                                        {significance === 'moderate' && 'Moderate'}
                                                    </span>
                                                </div>
                                                <div className="track-periods">
                                                    {(() => {
                                                        // Arrange overlapping periods in separate rows
                                                        const rows = [];
                                                        const sortedPeriods = [...periodList].sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
                                                        
                                                        sortedPeriods.forEach(period => {
                                                            const periodStyle = getPositionAndWidth(period);
                                                            const periodLeft = parseFloat(periodStyle.left);
                                                            const periodWidth = parseFloat(periodStyle.width);
                                                            const periodRight = periodLeft + periodWidth;
                                                            
                                                            // Find a row where this period doesn't overlap
                                                            let rowIndex = 0;
                                                            while (rowIndex < rows.length) {
                                                                const hasOverlap = rows[rowIndex].some(existingPeriod => {
                                                                    const existingStyle = getPositionAndWidth(existingPeriod);
                                                                    const existingLeft = parseFloat(existingStyle.left);
                                                                    const existingWidth = parseFloat(existingStyle.width);
                                                                    const existingRight = existingLeft + existingWidth;
                                                                    return !(periodRight <= existingLeft || periodLeft >= existingRight);
                                                                });
                                                                
                                                                if (!hasOverlap) break;
                                                                rowIndex++;
                                                            }
                                                            
                                                            // Create new row if needed
                                                            if (rowIndex >= rows.length) {
                                                                rows.push([]);
                                                            }
                                                            
                                                            rows[rowIndex].push(period);
                                                        });
                                                        
                                                        return rows.map((row, rowIndex) => (
                                                            <div key={rowIndex} className="period-row">
                                                                {row.map((period) => {
                                                                    const style = getPositionAndWidth(period);
                                                                    return (
                                                                        <div
                                                                            key={period.id}
                                                                            className="timeline-period"
                                                                            style={style}
                                                                            onClick={() => onPeriodSelect(period)}
                                                                            title={`${period.transit_planet} → ${period.natal_planet}\n${formatDate(period.start_date)} - ${formatDate(period.end_date)}`}
                                                                        >
                                                                            <span className="period-label">
                                                                                {period.transit_planet}→{period.natal_planet}
                                                                            </span>
                                                                        </div>
                                                                    );
                                                                })}
                                                            </div>
                                                        ));
                                                    })()
                                                    }
                                                </div>
                                            </div>
                                        );
                                    })}
                                </>
                            );
                        })()
                        }
                    </div>
                </div>
            ) : (
                <div className="periods-grid-container">
                            <div className="periods-grid">
                            {periods.map((period) => {
                        const getLifeAreaDescription = () => {
                            const transitHouse = period.period_data?.transit_house;
                            const natalHouse = period.period_data?.natal_house;
                            
                            // Simple life area mapping for laymen
                            const houseAreas = {
                                1: "Personal growth & health",
                                2: "Money & family matters", 
                                3: "Communication & siblings",
                                4: "Home & mother",
                                5: "Children & creativity",
                                6: "Work & health issues",
                                7: "Marriage & partnerships",
                                8: "Major life changes",
                                9: "Higher learning & father",
                                10: "Career & reputation",
                                11: "Income & friendships",
                                12: "Spirituality & expenses"
                            };
                            
                            const areas = [];
                            if (transitHouse && houseAreas[transitHouse]) areas.push(houseAreas[transitHouse]);
                            if (natalHouse && houseAreas[natalHouse] && natalHouse !== transitHouse) areas.push(houseAreas[natalHouse]);
                            
                            return areas.length > 0 ? areas.join(" & ") : "Important life developments";
                        };
                        
                        return (
                            <div
                                key={period.id}
                                className="period-chip-rect"
                                onClick={() => onPeriodSelect(period)}
                            >
                                <div className="chip-header">
                                    <h4 className="period-dates-header">{formatDate(period.start_date)} - {formatDate(period.end_date)}</h4>
                                </div>
                                <div className="chip-content">
                                    <div className="life-area-description">
                                        <p>{getLifeAreaDescription()}</p>
                                        <p className="simple-description">
                                            {period.transit_planet === 'Jupiter' && 'Opportunities for growth and expansion'}
                                            {period.transit_planet === 'Saturn' && 'Important decisions and responsibilities'}
                                            {period.transit_planet === 'Mars' && 'Action-oriented period with energy boost'}
                                            {period.transit_planet === 'Venus' && 'Focus on relationships and finances'}
                                            {period.transit_planet === 'Mercury' && 'Communication and learning opportunities'}
                                            {period.transit_planet === 'Sun' && 'Recognition and leadership opportunities'}
                                            {period.transit_planet === 'Moon' && 'Emotional developments and family matters'}
                                            {(period.transit_planet === 'Rahu' || period.transit_planet === 'Ketu') && 'Significant life changes and new directions'}
                                        </p>
                                    </div>
                                    <div className="technical-details">
                                        {(() => {
                                            const transitHouse = period.period_data?.transit_house;
                                            const natalHouse = period.period_data?.natal_house;
                                            const aspectNumber = period.period_data?.aspect_number;
                                            const aspectText = getAspectText(aspectNumber);
                                            
                                            return (
                                                <>
                                                    {transitHouse && natalHouse && aspectText ? (
                                                        <p className="aspect-description">
                                                            {period.transit_planet} in House {transitHouse} will {aspectText === 'conjunction' ? 'conjunct' : `aspect with ${aspectText}`} its Natal Position of House {natalHouse}.
                                                        </p>
                                                    ) : (
                                                        <p className="aspect-description">
                                                            {period.transit_planet} will activate natal {period.natal_planet} during this period.
                                                        </p>
                                                    )}
                                                    {period.period_data?.transit_planet_dashas && period.period_data.transit_planet_dashas.length > 0 && (
                                                        <p className="dasha-description">
                                                            During this period {period.transit_planet} will be in {period.period_data.transit_planet_dashas[0].type} from {formatDate(period.period_data.transit_planet_dashas[0].start_date)} to {formatDate(period.period_data.transit_planet_dashas[0].end_date)}.
                                                        </p>
                                                    )}
                                                    <div className="period-summary">
                                                        <div className="planet-activation">{period.transit_planet} → {period.natal_planet}</div>
                                                        <div className="house-details">
                                                            {period.period_data?.transit_house && <span>Transit: H{period.period_data.transit_house}</span>}
                                                            {period.period_data?.natal_house && <span>Natal: H{period.period_data.natal_house}</span>}
                                                        </div>
                                                        {period.period_data?.transit_planet_dashas && period.period_data.transit_planet_dashas.length > 0 && (
                                                            <div className="dasha-summary">{period.period_data.transit_planet_dashas[0].type}</div>
                                                        )}
                                                    </div>
                                                </>
                                            );
                                        })()
                                        }
                                    </div>
                                </div>
                                <div className="chip-footer">
                                    <span 
                                        className="significance-badge-bottom"
                                        style={{ background: getSignificanceColor(period.significance) }}
                                    >
                                        {getSignificanceLabel(period.significance)} Probability
                                    </span>
                                </div>
                            </div>
                        );
                            })}
                            </div>
                </div>
            )}
        </div>
    );
};

export default EventPeriods;