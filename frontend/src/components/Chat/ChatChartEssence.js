import React from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatChartEssence.css';

const ZODIAC_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

function glyphForSign(sign) {
    if (typeof sign !== 'number' || sign < 0 || sign > 11) return '';
    return ZODIAC_GLYPHS[sign];
}

function formatPlanetSign(chartData, planetKey) {
    if (!chartData?.planets?.[planetKey]) return null;
    const p = chartData.planets[planetKey];
    const g = glyphForSign(p.sign);
    const name = p.sign_name || '';
    if (!name && !g) return null;
    return [g, name].filter(Boolean).join(' ');
}

function formatAsc(chartData) {
    const h = chartData?.houses?.[0];
    if (!h) return null;
    const g = glyphForSign(h.sign);
    const name = h.sign_name || '';
    if (!name && !g) return null;
    return [g, name].filter(Boolean).join(' ');
}

function getPlanetColor(planetName) {
    const colors = {
        Sun: '#ff6b35',
        Moon: '#e0e0e0',
        Mars: '#d32f2f',
        Mercury: '#4caf50',
        Jupiter: '#ffd700',
        Venus: '#e91e63',
        Saturn: '#2196f3',
        Rahu: '#9e9e9e',
        Ketu: '#795548',
    };
    return colors[planetName] || '#7c2d12';
}

function parseDashaYmd(iso) {
    if (iso == null || iso === '') return null;
    const s = String(iso).split('T')[0];
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
    if (!m) return null;
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), 12, 0, 0, 0);
}

/**
 * Match mobile ChatScreen: use the row the API marked current (truthy `current` only).
 * Do not infer from local clock + date strings — that diverges from the server and produced wrong chips on web.
 */
function pickCurrentDasha(list) {
    if (!Array.isArray(list) || list.length === 0) return null;
    return list.find((d) => d && d.current) || null;
}

function currentDashaChips(dashaData) {
    if (!dashaData) return [];
    return [
        pickCurrentDasha(dashaData.maha_dashas),
        pickCurrentDasha(dashaData.antar_dashas),
        pickCurrentDasha(dashaData.pratyantar_dashas),
        pickCurrentDasha(dashaData.sookshma_dashas),
        pickCurrentDasha(dashaData.prana_dashas),
    ].filter(Boolean);
}

function formatDashaRangeLabel(startRaw, endRaw) {
    const opts = { month: 'short', day: 'numeric', year: '2-digit' };
    const start = parseDashaYmd(startRaw);
    const end = parseDashaYmd(endRaw);
    const startLabel =
        start && !Number.isNaN(start.getTime()) ? start.toLocaleDateString(undefined, opts) : '…';
    const endLabel = end && !Number.isNaN(end.getTime()) ? end.toLocaleDateString(undefined, opts) : '…';
    return { startLabel, endLabel };
}

const ChatChartEssence = ({ chartData, dashaData, personName, isLoading }) => {
    const navigate = useNavigate();
    const displayName = (personName && String(personName).trim()) || 'Your';
    const title =
        displayName === 'Your' ? "✨ Your Chart Essence" : `✨ ${displayName}'s Chart Essence`;

    const sun = formatPlanetSign(chartData, 'Sun');
    const moon = formatPlanetSign(chartData, 'Moon');
    const asc = formatAsc(chartData);

    const chips = currentDashaChips(dashaData);

    const handleChipClick = () => {
        navigate('/dashboard');
    };

    return (
        <div className="chat-chart-essence" aria-label="Chart essence and current dashas">
            <div className="chat-chart-essence__gradient">
                <h2 className="chat-chart-essence__title">{title}</h2>
                <div className="chat-chart-essence__signs">
                    <div className="chat-chart-essence__sign">
                        <div className="chat-chart-essence__sign-label">☀️ Sun</div>
                        <div className="chat-chart-essence__sign-value">
                            {isLoading && !sun ? '…' : sun || '—'}
                        </div>
                    </div>
                    <div className="chat-chart-essence__sign">
                        <div className="chat-chart-essence__sign-label">🌙 Moon</div>
                        <div className="chat-chart-essence__sign-value">
                            {isLoading && !moon ? '…' : moon || '—'}
                        </div>
                    </div>
                    <div className="chat-chart-essence__sign">
                        <div className="chat-chart-essence__sign-label">⬆️ Asc</div>
                        <div className="chat-chart-essence__sign-value">
                            {isLoading && !asc ? '…' : asc || '—'}
                        </div>
                    </div>
                </div>

                {chips.length > 0 && (
                    <div className="chat-chart-essence__dasha-scroll">
                        <div className="chat-chart-essence__dasha-row">
                            {chips.map((dasha, index) => {
                                if (!dasha?.planet) return null;
                                const planetColor = getPlanetColor(dasha.planet);
                                const { startLabel, endLabel } = formatDashaRangeLabel(
                                    dasha.start,
                                    dasha.end
                                );

                                return (
                                    <button
                                        key={`${dasha.planet}-${index}-${String(dasha.start)}`}
                                        type="button"
                                        className="chat-chart-essence__chip"
                                        style={{
                                            borderColor: planetColor,
                                            backgroundColor: `${planetColor}40`,
                                        }}
                                        onClick={handleChipClick}
                                        title="Open dashboard (Dasha browser)"
                                    >
                                        <span
                                            className="chat-chart-essence__chip-planet"
                                            style={{ color: '#1a1a1a' }}
                                        >
                                            {dasha.planet}
                                        </span>
                                        <span className="chat-chart-essence__chip-date">{startLabel}</span>
                                        <span className="chat-chart-essence__chip-date">{endLabel}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatChartEssence;
