import React, { useState, useEffect, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, Animated, Platform, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { kpAPI } from '../services/api';
import { storage } from '../services/storage';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';
import NativeSelectorChip from '../components/Common/NativeSelectorChip';
import DateNavigator from '../components/Common/DateNavigator';

function formatLocalDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}

function formatLocalTime(d) {
    const h = String(d.getHours()).padStart(2, '0');
    const m = String(d.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
}

function birthMomentFromDetails(birthDetails) {
    if (!birthDetails?.date || !birthDetails?.time) return null;
    const dateStr = String(birthDetails.date).split('T')[0];
    let timeStr = String(birthDetails.time);
    if (timeStr.includes('T')) timeStr = timeStr.split('T')[1];
    timeStr = timeStr.slice(0, 5);
    const [y, mo, d] = dateStr.split('-').map(Number);
    const [hh, mm] = timeStr.split(':').map(Number);
    if (![y, mo, d].every(Number.isFinite)) return null;
    return new Date(y, mo - 1, d, hh || 0, mm || 0, 0, 0);
}

function formatFriendlyDateTime(d) {
    if (!(d instanceof Date) || Number.isNaN(d.getTime())) return '';
    return d.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
    });
}

const PlanetaryTable = ({ data, theme, colors }) => {
    const isClassic = theme === 'classic';
    if (!data || data.length === 0) return <Text style={[styles.errorText, { color: colors.textSecondary }]}>No data available</Text>;

    const getNakshatraInfo = (longitude) => {
        const nakshatras = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'];
        const nakIndex = Math.floor(longitude / 13.333333);
        const nakPosition = longitude % 13.333333;
        const pada = Math.floor(nakPosition / 3.333333) + 1;
        return { name: nakshatras[nakIndex], pada };
    };
    
    const shortPlanet = (name) => {
        const map = { 
            'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me', 
            'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 
            'Ketu': 'Ke', 'Ascendant': 'Asc' 
        };
        return map[name] || name.substring(0, 2);
    };

    return (
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.table}>
                <View style={styles.tableRow}>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 60 }]}>Planet</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 60 }]}>Deg</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 90 }]}>Star</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 40 }]}>Pd</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>SL</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>NL</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>SB</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>SS</Text>
                </View>
                {data.map((item, index) => {
                    const nakInfo = getNakshatraInfo(item.longitude);
                    return (
                        <View key={index} style={[styles.tableRow, index % 2 === 0 && (isClassic ? { backgroundColor: colors.backgroundSecondary } : styles.tableRowAlt) ]}>
                            <Text style={[styles.tableCell, { color: colors.primary, width: 60 }]}>{shortPlanet(item.planet)}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 60 }]}>{item.longitude.toFixed(1)}°</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 90 }]}>{nakInfo.name}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 40 }]}>{nakInfo.pada}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.sign_lord)}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.star_lord)}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.sub_lord)}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.sub_sub_lord)}</Text>
                        </View>
                    );
                })}
            </View>
        </ScrollView>
    );
};

const CuspalTable = ({ data, theme, colors }) => {
    const isClassic = theme === 'classic';
    if (!data || data.length === 0) return <Text style={[styles.errorText, { color: colors.textSecondary }]}>No data available</Text>;

    const getNakshatraInfo = (longitude) => {
        const nakshatras = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'];
        const nakIndex = Math.floor(longitude / 13.333333);
        const nakPosition = longitude % 13.333333;
        const pada = Math.floor(nakPosition / 3.333333) + 1;
        return { name: nakshatras[nakIndex], pada };
    };
    
    const shortPlanet = (name) => {
        const map = { 
            'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me', 
            'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 
            'Ketu': 'Ke', 'Ascendant': 'Asc' 
        };
        return map[name] || name.substring(0, 2);
    };

    return (
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={styles.table}>
                <View style={styles.tableRow}>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>Cusp</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 60 }]}>Deg</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 90 }]}>Star</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 40 }]}>Pd</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>SL</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>NL</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>SB</Text>
                    <Text style={[styles.tableHeader, { color: colors.text, width: 50 }]}>SS</Text>
                </View>
                {data.map((item, index) => {
                    const nakInfo = getNakshatraInfo(item.longitude);
                    return (
                        <View key={index} style={[styles.tableRow, index % 2 === 0 && (isClassic ? { backgroundColor: colors.backgroundSecondary } : styles.tableRowAlt) ]}>
                            <Text style={[styles.tableCell, { color: colors.primary, width: 50 }]}>{item.cusp}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 60 }]}>{item.longitude.toFixed(1)}°</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 90 }]}>{nakInfo.name}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 40 }]}>{nakInfo.pada}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.sign_lord)}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.star_lord)}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.sub_lord)}</Text>
                            <Text style={[styles.tableCell, { color: colors.text, width: 50 }]}>{shortPlanet(item.sub_sub_lord)}</Text>
                        </View>
                    );
                })}
            </View>
        </ScrollView>
    );
};

const sigChipStyles = (theme, colors) => {
    const isClassic = theme === 'classic';
    const isDark = theme === 'dark';
    if (isClassic) {
        return {
            cardBg: colors.surface,
            cardBorder: colors.cardBorder,
            chipBg: colors.backgroundSecondary,
            chipBorder: colors.primary,
            chipText: colors.primary,
            title: colors.primary,
        };
    }
    return {
        cardBg: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(249, 115, 22, 0.05)',
        cardBorder: undefined,
        chipBg: isDark ? colors.primary : 'rgba(249, 115, 22, 0.14)',
        chipBorder: isDark ? colors.primary : 'rgba(249, 115, 22, 0.55)',
        chipText: isDark ? '#fff7ed' : colors.primary,
        title: isDark ? '#fdba74' : colors.primary,
    };
};

const SignificatorsView = ({ data, theme, colors }) => {
    if (!data) return <Text style={[styles.errorText, { color: colors.textSecondary }]}>No data available</Text>;
    const chip = sigChipStyles(theme, colors);

    return (
        <ScrollView showsVerticalScrollIndicator={false}>
            {Object.entries(data).map(([house, significators]) => (
                <View key={house} style={[styles.significatorCard, { backgroundColor: chip.cardBg, borderColor: chip.cardBorder }]}>
                    <Text style={[styles.significatorHouse, { color: chip.title }]}>House {house}</Text>
                    <View style={styles.significatorChips}>
                        {significators.map((sig, idx) => (
                            <View key={idx} style={[styles.significatorChip, { backgroundColor: chip.chipBg, borderColor: chip.chipBorder }]}>
                                <Text style={[styles.significatorText, { color: chip.chipText }]}>{sig}</Text>
                            </View>
                        ))}
                    </View>
                </View>
            ))}
        </ScrollView>
    );
};

const PlanetSignificatorsView = ({ data, theme, colors }) => {
    if (!data) return <Text style={[styles.errorText, { color: colors.textSecondary }]}>No data available</Text>;
    const chip = sigChipStyles(theme, colors);

    return (
        <ScrollView showsVerticalScrollIndicator={false}>
            {Object.entries(data).map(([planet, houses]) => (
                <View key={planet} style={[styles.significatorCard, { backgroundColor: chip.cardBg, borderColor: chip.cardBorder }]}>
                    <Text style={[styles.significatorHouse, { color: chip.title }]}>{planet}</Text>
                    <View style={styles.significatorChips}>
                        {houses.map((house, idx) => (
                            <View key={idx} style={[styles.significatorChip, { backgroundColor: chip.chipBg, borderColor: chip.chipBorder }]}>
                                <Text style={[styles.significatorText, { color: chip.chipText }]}>House {house}</Text>
                            </View>
                        ))}
                    </View>
                </View>
            ))}
        </ScrollView>
    );
};

const FourStepTheoryView = ({ data, theme, colors }) => {
    if (!data) return <Text style={[styles.errorText, { color: colors.textSecondary }]}>No data available</Text>;
    const chip = sigChipStyles(theme, colors);
    const isClassic = theme === 'classic';
    const isDark = theme === 'dark';

    const renderStep = (num, label, lord, houses) => (
        <View style={styles.stepContainer}>
            <View style={styles.stepIndicator}>
                <View style={[styles.stepDot, { backgroundColor: colors.primary }]} />
                {num < 4 && (
                    <View style={[styles.stepLine, {
                        backgroundColor: isClassic
                            ? colors.cardBorder
                            : (isDark ? 'rgba(253, 186, 116, 0.35)' : 'rgba(249, 115, 22, 0.25)'),
                    }]} />
                )}
            </View>
            <View style={styles.stepContent}>
                <Text style={[styles.stepNumber, { color: colors.textSecondary }]}>Step {num}: {label}</Text>
                <View style={styles.stepDetails}>
                    <Text style={[styles.stepLord, { color: colors.text }]}>{lord}</Text>
                    <View style={styles.stepHouses}>
                        {houses.length > 0 ? houses.map((h, idx) => (
                            <View key={idx} style={[styles.miniHouseChip, { backgroundColor: chip.chipBg, borderColor: chip.chipBorder, borderWidth: 1 }]}>
                                <Text style={[styles.miniHouseText, { color: chip.chipText }]}>{h}</Text>
                            </View>
                        )) : <Text style={[styles.noHousesText, { color: colors.textSecondary }]}>No houses</Text>}
                    </View>
                </View>
            </View>
        </View>
    );

    return (
        <ScrollView showsVerticalScrollIndicator={false}>
            {Object.entries(data).map(([planet, steps]) => (
                <View key={planet} style={[styles.fourStepCard, {
                    backgroundColor: isClassic
                        ? colors.surface
                        : (Platform.OS === 'android'
                            ? (isDark ? 'rgba(0, 0, 0, 0.2)' : 'rgba(249, 115, 22, 0.08)')
                            : (isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(249, 115, 22, 0.03)')),
                    borderColor: isClassic
                        ? colors.cardBorder
                        : (isDark ? 'rgba(253, 186, 116, 0.35)' : 'rgba(249, 115, 22, 0.2)'),
                }]}>
                    <View style={styles.fourStepHeader}>
                        <View style={[styles.planetIconCircle, { backgroundColor: colors.primary }]}>
                            <Text style={[styles.planetIconText, isClassic && { color: colors.background }]}>{planet.substring(0, 2)}</Text>
                        </View>
                        <Text style={[styles.fourStepPlanetTitle, { color: colors.text }]}>{planet} Analysis</Text>
                    </View>

                    <View style={styles.stepsList}>
                        {renderStep(1, 'Planet', steps.planet.name, steps.planet.houses)}
                        {renderStep(2, 'Star Lord', steps.star_lord.name, steps.star_lord.houses)}
                        {renderStep(3, 'Sub Lord', steps.sub_lord.name, steps.sub_lord.houses)}
                        {renderStep(4, 'Sub-Sub Lord', steps.sub_sub_lord.name, steps.sub_sub_lord.houses)}
                    </View>
                </View>
            ))}
        </ScrollView>
    );
};

const RulingPlanetsView = ({ data, theme, colors }) => {
    const isClassic = theme === 'classic';
    if (!data) return null;

    const renderRPChip = (label, value) => (
        <View style={[styles.rpChip, { backgroundColor: isClassic ? colors.backgroundSecondary : (colors.primary + '15'), borderColor: isClassic ? colors.cardBorder : (colors.primary + '40') }]}>
            <Text style={[styles.rpChipLabel, { color: colors.textSecondary }]}>{label}:</Text>
            <Text style={[styles.rpChipValue, { color: colors.primary }]}>{value}</Text>
        </View>
    );

    return (
        <View style={styles.rpContainer}>
            <View style={[styles.rpCard, { 
                backgroundColor: isClassic ? colors.surface : (Platform.OS === 'android'
                    ? (theme === 'dark' ? 'rgba(0, 0, 0, 0.2)' : 'rgba(249, 115, 22, 0.08)')
                    : (theme === 'dark' ? 'rgba(255, 255, 255, 0.03)' : 'rgba(249, 115, 22, 0.03)')), 
                borderColor: isClassic ? colors.cardBorder : (colors.primary + '30')
            }]}>
                <View style={styles.rpHeader}>
                    <Ionicons name="flash" size={16} color={colors.primary} />
                    <Text style={[styles.rpTitle, { color: colors.text }]}>Ruling Planets (Birth Moment)</Text>
                </View>
                
                <View style={styles.rpSection}>
                    <Text style={[styles.rpSectionTitle, { color: colors.textSecondary }]}>Ascendant</Text>
                    <View style={styles.rpChipGroup}>
                        {renderRPChip('Sign', data.ascendant.sign_lord)}
                        {renderRPChip('Star', data.ascendant.star_lord)}
                        {renderRPChip('Sub', data.ascendant.sub_lord)}
                    </View>
                </View>

                <View style={styles.rpSection}>
                    <Text style={[styles.rpSectionTitle, { color: colors.textSecondary }]}>Moon</Text>
                    <View style={styles.rpChipGroup}>
                        {renderRPChip('Sign', data.moon.sign_lord)}
                        {renderRPChip('Star', data.moon.star_lord)}
                        {renderRPChip('Sub', data.moon.sub_lord)}
                    </View>
                </View>

                <View style={styles.rpFooter}>
                    <View style={[styles.dayLordBadge, { backgroundColor: colors.primary }]}>
                        <Text style={[styles.dayLordLabel, isClassic && { color: colors.background }]}>Day Lord</Text>
                        <Text style={[styles.dayLordValue, isClassic && { color: colors.background }]}>{data.day_lord}</Text>
                    </View>
                </View>
            </View>
        </View>
    );
};

const TONE_COLORS = {
    supportive: '#15803d',
    mixed: '#a16207',
    challenging: '#b91c1c',
    neutral: '#475569',
};

const TONE_LABELS = {
    supportive: 'Favourable',
    mixed: 'Mixed',
    challenging: 'Under pressure',
    neutral: 'Neutral',
};

const RP_ROLE_SHORT = {
    day_lord: 'Day Lord',
    moon_star_lord: 'Moon Star',
    moon_sign_lord: 'Moon Sign',
    asc_star_lord: 'Asc Star',
    asc_sub_lord: 'Asc Sub',
    moon_sub_lord: 'Moon Sub',
};

const FructificationView = ({ data, theme, colors }) => {
    const [scopeTab, setScopeTab] = useState('today'); // 'today' | 'hour'
    const [expandedHouse, setExpandedHouse] = useState(null);
    const [calcOpen, setCalcOpen] = useState(false);

    useEffect(() => {
        setExpandedHouse(null);
        setCalcOpen(false);
    }, [scopeTab, data?.as_of]);

    if (!data) return null;

    const isDark = theme === 'dark';
    const isClassic = theme === 'classic';
    const surface = isClassic ? colors.surface : (isDark ? 'rgba(255,255,255,0.08)' : '#ffffff');
    const surfaceMuted = isClassic ? colors.backgroundSecondary : (isDark ? 'rgba(255,255,255,0.05)' : 'rgba(255,247,237,0.95)');
    const border = isClassic ? colors.cardBorder : (isDark ? 'rgba(255,255,255,0.16)' : 'rgba(194, 65, 12, 0.18)');
    const bodyText = isClassic ? colors.text : (isDark ? 'rgba(255,255,255,0.92)' : '#1c1917');
    const mutedText = isClassic ? colors.textSecondary : (isDark ? 'rgba(255,255,255,0.72)' : '#44403c');
    const subtleText = isClassic ? colors.textSecondary : (isDark ? 'rgba(255,255,255,0.55)' : '#78716c');

    const block = scopeTab === 'hour' ? data.hour : data.today;
    const houses = block?.houses_giving_results || [];
    const secondary = block?.houses_secondary || [];
    const manifestations = block?.manifestations || [];
    const gate = block?.dasha_gate || {};
    const calc = block?.calculation || {};
    const roleMap = block?.ruling_planets_used || {};

    const dasha = data.dasha || {};
    const dashaBits = [
        ['MD', dasha.mahadasha?.planet || dasha.mahadasha],
        ['AD', dasha.antardasha?.planet || dasha.antardasha],
        ['PD', dasha.pratyantardasha?.planet || dasha.pratyantardasha],
        ['SK', dasha.sookshma?.planet || dasha.sookshma],
        ['PR', dasha.prana?.planet || dasha.prana],
    ].filter(([, p]) => p);

    const scopeCopy = scopeTab === 'today'
        ? {
            title: 'Today',
            blurb: 'Houses that can give results across the day, using Day Lord and Moon star lord.',
            formulaHint: 'AD/PD ∩ Sookshma ∩ Day ruling planets',
        }
        : {
            title: 'This hour',
            blurb: 'Sharper timing for the selected hour, using the full ruling-planet set.',
            formulaHint: 'AD/PD ∩ Sookshma ∩ Prana ∩ Hour ruling planets',
        };

    const renderHowSteps = (how, accent) => {
        if (!how?.steps?.length) return null;
        return (
            <View style={[styles.fructHowBox, { borderColor: border, backgroundColor: surfaceMuted }]}>
                {how.summary ? (
                    <Text style={[styles.fructHowSummary, { color: bodyText }]}>{how.summary}</Text>
                ) : null}
                {how.steps.map((step) => (
                    <View key={`${step.step}-${step.title}`} style={[styles.fructHowStep, { borderTopColor: border }]}>
                        <View style={styles.fructHowStepHead}>
                            <Text style={[styles.fructHowStepTitle, { color: accent || colors.primary }]}>
                                Step {step.step} · {step.title}
                            </Text>
                            {typeof step.passed === 'boolean' ? (
                                <View style={[styles.fructPassPill, { backgroundColor: step.passed ? 'rgba(22,163,74,0.15)' : 'rgba(220,38,38,0.15)' }]}>
                                    <Text style={{ color: step.passed ? '#15803d' : '#b91c1c', fontSize: 11, fontWeight: '800' }}>
                                        {step.passed ? 'Pass' : 'Fail'}
                                    </Text>
                                </View>
                            ) : null}
                        </View>
                        <Text style={[styles.fructBody, { color: mutedText }]}>{step.detail}</Text>
                        {step.dasha_hits?.length ? (
                            <Text style={[styles.fructBody, { color: mutedText, marginTop: 6 }]}>
                                Dasha hits: {step.dasha_hits.map((h) => `${h.label} (${h.planet}) → H${(h.planet_houses || []).join(', H')}`).join(' · ')}
                            </Text>
                        ) : null}
                        {step.activating_rps?.length ? (
                            <Text style={[styles.fructBody, { color: mutedText, marginTop: 6 }]}>
                                {step.activating_rps.map((r) => (
                                    `${r.planet}${r.roles?.length ? ` as ${r.roles.join(' / ')}` : ''} → H${(r.natal_houses || []).join(', H')}`
                                )).join('\n')}
                            </Text>
                        ) : null}
                        {step.linked_by_planet ? (
                            <Text style={[styles.fructBody, { color: mutedText, marginTop: 6 }]}>
                                Linked houses: {Object.entries(step.linked_by_planet).map(([p, hs]) => `${p} → H${(hs || []).join(', H')}`).join(' · ')}
                            </Text>
                        ) : null}
                    </View>
                ))}
            </View>
        );
    };

    const renderHouseCard = (row, soft = false) => {
        const key = `${scopeTab}-${row.tier || 'p'}-${row.house}`;
        const expanded = expandedHouse === key;
        const tone = soft ? TONE_COLORS.neutral : (TONE_COLORS[row.tone] || TONE_COLORS.neutral);
        const toneLabel = soft ? 'Background' : (TONE_LABELS[row.tone] || 'Neutral');
        return (
            <View key={key} style={{ marginBottom: 10 }}>
                <TouchableOpacity
                    activeOpacity={0.88}
                    onPress={() => setExpandedHouse(expanded ? null : key)}
                    style={[
                        styles.fructHouseCard,
                        {
                            backgroundColor: soft ? surfaceMuted : surface,
                            borderColor: soft ? border : `${tone}66`,
                            borderLeftColor: tone,
                        },
                    ]}
                >
                    <View style={[styles.fructHouseBadge, { backgroundColor: `${tone}18` }]}>
                        <Text style={[styles.fructHouseNum, { color: tone }]}>H{row.house}</Text>
                    </View>
                    <View style={{ flex: 1, minWidth: 0 }}>
                        <Text style={[styles.fructHouseTitle, { color: bodyText }]} numberOfLines={2}>
                            {row.label || `House ${row.house}`}
                        </Text>
                        <Text style={[styles.fructHouseMeta, { color: mutedText }]} numberOfLines={2}>
                            {(row.activating_rps || []).join(' · ') || 'No ruling planet'}
                        </Text>
                        <View style={[styles.fructTonePill, { backgroundColor: `${tone}18`, alignSelf: 'flex-start' }]}>
                            <Text style={[styles.fructTonePillText, { color: tone }]}>{toneLabel}</Text>
                        </View>
                    </View>
                    <View style={styles.fructHowLinkRow}>
                        <Text style={[styles.fructHowLink, { color: colors.primary }]}>
                            {expanded ? 'Hide' : 'Why'}
                        </Text>
                        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={16} color={colors.primary} />
                    </View>
                </TouchableOpacity>
                {expanded ? renderHowSteps(row.how, soft ? colors.primary : tone) : null}
            </View>
        );
    };

    return (
        <View>
            <View style={[styles.fructIntroCard, { backgroundColor: surface, borderColor: border }]}>
                <Text style={[styles.fructIntroTitle, { color: bodyText }]}>What can give results</Text>
                <Text style={[styles.fructBody, { color: mutedText, marginBottom: 0 }]}>
                    Natal KP significators × current dasha × ruling planets at the selected moment.
                </Text>
            </View>

            {dashaBits.length ? (
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.fructDashaRow}>
                    {dashaBits.map(([label, planet]) => (
                        <View key={label} style={[styles.fructDashaChip, { backgroundColor: surface, borderColor: border }]}>
                            <Text style={[styles.fructDashaLabel, { color: subtleText }]}>{label}</Text>
                            <Text style={[styles.fructDashaPlanet, { color: bodyText }]}>{planet}</Text>
                        </View>
                    ))}
                </ScrollView>
            ) : null}

            <View style={[styles.fructScopeBar, { backgroundColor: isClassic ? colors.backgroundSecondary : (isDark ? 'rgba(0,0,0,0.28)' : 'rgba(255,237,213,0.9)'), borderColor: border }]}>
                {[
                    { id: 'today', label: 'Today', count: (data.today?.houses_giving_results || []).length },
                    { id: 'hour', label: 'This hour', count: (data.hour?.houses_giving_results || []).length },
                ].map((tab) => {
                    const active = scopeTab === tab.id;
                    return (
                        <TouchableOpacity
                            key={tab.id}
                            style={[
                                styles.fructScopeChip,
                                { backgroundColor: active ? colors.primary : 'transparent' },
                            ]}
                            onPress={() => setScopeTab(tab.id)}
                            activeOpacity={0.9}
                        >
                            <Text style={[styles.fructScopeChipText, { color: active ? '#fff' : bodyText }]}>
                                {tab.label}
                            </Text>
                            <Text style={[styles.fructScopeCount, { color: active ? 'rgba(255,255,255,0.85)' : subtleText }]}>
                                {tab.count} house{tab.count === 1 ? '' : 's'}
                            </Text>
                        </TouchableOpacity>
                    );
                })}
            </View>

            <Text style={[styles.fructScopeBlurb, { color: mutedText }]}>{scopeCopy.blurb}</Text>

            {Object.keys(roleMap).length ? (
                <View style={[styles.fructRpStrip, { backgroundColor: surfaceMuted, borderColor: border }]}>
                    <Text style={[styles.fructSubheadInline, { color: subtleText }]}>Ruling planets used</Text>
                    <View style={styles.fructHouseRow}>
                        {Object.entries(roleMap).filter(([, v]) => v).map(([key, planet]) => (
                            <View key={key} style={[styles.fructRpChip, { backgroundColor: surface, borderColor: border }]}>
                                <Text style={[styles.fructRpRole, { color: subtleText }]}>{RP_ROLE_SHORT[key] || key}</Text>
                                <Text style={[styles.fructRpPlanet, { color: bodyText }]}>{planet}</Text>
                            </View>
                        ))}
                    </View>
                </View>
            ) : null}

            {gate.prana_fallback ? (
                <View style={[styles.fructNotice, { backgroundColor: 'rgba(249,115,22,0.12)', borderColor: 'rgba(249,115,22,0.35)' }]}>
                    <Ionicons name="information-circle-outline" size={16} color={colors.primary} />
                    <Text style={[styles.fructBody, { color: bodyText, flex: 1, marginBottom: 0 }]}>
                        Prana did not confirm this hour. Showing Sookshma ∩ ruling planets instead.
                    </Text>
                </View>
            ) : null}

            <TouchableOpacity
                onPress={() => setCalcOpen((v) => !v)}
                style={[styles.fructCalcToggle, { borderColor: border, backgroundColor: surface }]}
                activeOpacity={0.88}
            >
                <View style={[styles.fructCalcIcon, { backgroundColor: `${colors.primary}18` }]}>
                    <Ionicons name="git-branch-outline" size={16} color={colors.primary} />
                </View>
                <View style={{ flex: 1 }}>
                    <Text style={[styles.fructHowLink, { color: bodyText }]}>
                        {calcOpen ? 'Hide full calculation' : 'Show full calculation'}
                    </Text>
                    <Text style={[styles.fructBody, { color: mutedText, marginBottom: 0 }]} numberOfLines={calcOpen ? 0 : 2}>
                        {calc.formula || scopeCopy.formulaHint}
                    </Text>
                </View>
                <Ionicons name={calcOpen ? 'chevron-up' : 'chevron-down'} size={18} color={colors.primary} />
            </TouchableOpacity>

            {calcOpen && calc.steps?.length ? (
                <View style={[styles.fructHowBox, { borderColor: border, backgroundColor: surfaceMuted, marginBottom: 14 }]}>
                    {calc.steps.map((step) => (
                        <View key={`${scopeTab}-calc-${step.step}`} style={[styles.fructHowStep, { borderTopColor: border }]}>
                            <Text style={[styles.fructHowStepTitle, { color: colors.primary }]}>
                                Step {step.step} · {step.title}
                            </Text>
                            <Text style={[styles.fructBody, { color: mutedText }]}>{step.detail}</Text>
                            {step.ruling_planets_used ? (
                                <Text style={[styles.fructBody, { color: mutedText, marginTop: 6 }]}>
                                    {Object.entries(step.ruling_planets_used)
                                        .filter(([, v]) => v)
                                        .map(([k, v]) => `${RP_ROLE_SHORT[k] || k}: ${v}`)
                                        .join(' · ')}
                                </Text>
                            ) : null}
                            {step.houses_by_level ? (
                                <Text style={[styles.fructBody, { color: mutedText, marginTop: 6 }]}>
                                    {Object.entries(step.houses_by_level)
                                        .map(([k, hs]) => `${k}: H${(hs || []).join(', H') || '—'}`)
                                        .join('\n')}
                                </Text>
                            ) : null}
                        </View>
                    ))}
                </View>
            ) : null}

            <Text style={[styles.fructSectionTitle, { color: bodyText }]}>Houses giving results</Text>
            {houses.length ? houses.map((row) => renderHouseCard(row, false)) : (
                <View style={[styles.fructEmpty, { backgroundColor: surfaceMuted, borderColor: border }]}>
                    <Text style={[styles.fructBody, { color: mutedText, marginBottom: 0, textAlign: 'center' }]}>
                        No primary fructifying houses for {scopeCopy.title.toLowerCase()}.
                    </Text>
                </View>
            )}

            {secondary.length ? (
                <>
                    <Text style={[styles.fructSectionTitle, { color: bodyText, marginTop: 8 }]}>Background only</Text>
                    <Text style={[styles.fructBody, { color: mutedText }]}>
                        Present through a weaker ruling-planet link — not counted as primary results.
                    </Text>
                    {secondary.map((row) => renderHouseCard(row, true))}
                </>
            ) : null}

            <Text style={[styles.fructSectionTitle, { color: bodyText, marginTop: 8 }]}>Predictions</Text>
            {manifestations.length ? manifestations.map((item) => {
                const tone = TONE_COLORS[item.outcome_tone] || TONE_COLORS.neutral;
                return (
                    <View
                        key={item.manifestation_id || item.signature_key || item.label}
                        style={[styles.fructCard, { backgroundColor: surface, borderColor: border, borderLeftColor: tone }]}
                    >
                        <View style={styles.fructCardTop}>
                            <Text style={[styles.fructCardEyebrow, { color: subtleText }]}>
                                {(item.domain || 'theme').toString()}
                            </Text>
                            <View style={[styles.fructTonePill, { backgroundColor: `${tone}18` }]}>
                                <Text style={[styles.fructTonePillText, { color: tone }]}>
                                    {TONE_LABELS[item.outcome_tone] || 'Neutral'}
                                </Text>
                            </View>
                        </View>
                        <Text style={[styles.fructCardTitle, { color: bodyText }]}>{item.label}</Text>
                        {item.summary ? (
                            <Text style={[styles.fructBody, { color: mutedText }]}>{item.summary}</Text>
                        ) : null}
                        {(item.possibilities || []).slice(0, 5).map((p) => (
                            <View key={p} style={styles.fructPossibilityRow}>
                                <View style={[styles.fructDot, { backgroundColor: tone }]} />
                                <Text style={[styles.fructBullet, { color: bodyText }]}>{p}</Text>
                            </View>
                        ))}
                        <View style={[styles.fructHouseRow, { marginTop: 10 }]}>
                            {(item.house_roles || []).map((role) => (
                                <View
                                    key={`${item.manifestation_id}-${role.native_house}`}
                                    style={[styles.fructTinyChipWrap, { backgroundColor: `${tone}16` }]}
                                >
                                    <Text style={[styles.fructTinyChip, { color: tone }]}>H{role.native_house}</Text>
                                </View>
                            ))}
                        </View>
                    </View>
                );
            }) : (
                <View style={[styles.fructEmpty, { backgroundColor: surfaceMuted, borderColor: border }]}>
                    <Text style={[styles.fructBody, { color: mutedText, marginBottom: 0, textAlign: 'center' }]}>
                        No life themes matched for {scopeCopy.title.toLowerCase()}.
                    </Text>
                </View>
            )}
        </View>
    );
};

const KPScreen = ({ route, navigation }) => {
    const { birthDetails: initialBirthDetails } = route.params || {};
    const [birthDetails, setBirthDetails] = useState(initialBirthDetails);
    const [activeTab, setActiveTab] = useState('planets');
    const [processedData, setProcessedData] = useState(null);
    const [rulingPlanets, setRulingPlanets] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sigMode, setSigMode] = useState('birth');
    const [sigMoment, setSigMoment] = useState(() => new Date());
    const [sigData, setSigData] = useState({
        significators: null,
        planetSignificators: null,
        fourStepTheory: null,
    });
    const [sigLoading, setSigLoading] = useState(false);
    const [sigError, setSigError] = useState(null);
    const [fructData, setFructData] = useState(null);
    const [fructLoading, setFructLoading] = useState(false);
    const [fructError, setFructError] = useState(null);
    const { t } = useTranslation();
    const { theme, colors } = useTheme();
    const isClassic = theme === 'classic';
    const fadeAnim = useRef(new Animated.Value(0)).current;
    const sigRequestIdRef = useRef(0);
    const fructRequestIdRef = useRef(0);

    useEffect(() => {
        fetchAndProcessKPData();
        Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
        }).start();
    }, [birthDetails]);

    // When no birthDetails from params, try storage and redirect if none
    useEffect(() => {
        let mounted = true;
        (async () => {
            if (birthDetails?.name) return;
            const fromStorage = await storage.getBirthDetails();
            if (!mounted) return;
            if (fromStorage?.name) {
                setBirthDetails(fromStorage);
            } else {
                navigation.replace('BirthProfileIntro', { returnTo: 'KPSystem' });
            }
        })();
        return () => { mounted = false; };
    }, []);

    useEffect(() => {
        const unsubscribe = navigation.addListener('focus', () => {
            if (route.params?.birthDetails) {
                const newDetails = route.params.birthDetails;
                if (newDetails.name !== birthDetails?.name || 
                    newDetails.date !== birthDetails?.date || 
                    newDetails.time !== birthDetails?.time) {
                    setBirthDetails(newDetails);
                }
            }
        });
        return unsubscribe;
    }, [navigation, route.params?.birthDetails, birthDetails]);

    const buildKpPayload = useCallback((dateStr, timeStr) => ({
        birth_date: dateStr,
        birth_time: timeStr,
        latitude: birthDetails?.latitude,
        longitude: birthDetails?.longitude,
        timezone: '',
    }), [birthDetails?.latitude, birthDetails?.longitude]);

    const resolveSigMoment = useCallback(() => {
        if (sigMode === 'birth') {
            return birthMomentFromDetails(birthDetails);
        }
        return sigMoment instanceof Date ? sigMoment : new Date();
    }, [sigMode, birthDetails, sigMoment]);

    const fetchSignificatorsForMoment = useCallback(async (moment) => {
        if (birthDetails?.latitude == null || birthDetails?.longitude == null) {
            setSigError('Birth location is incomplete.');
            return;
        }
        if (!(moment instanceof Date) || Number.isNaN(moment.getTime())) {
            setSigError('Invalid date/time for significators.');
            return;
        }
        const requestId = ++sigRequestIdRef.current;
        setSigLoading(true);
        setSigError(null);
        try {
            const payload = buildKpPayload(formatLocalDate(moment), formatLocalTime(moment));
            const response = await kpAPI.getKPChart(payload);
            if (requestId !== sigRequestIdRef.current) return;
            if (response.data && response.data.success) {
                const rawData = response.data.data;
                setSigData({
                    significators: rawData.significators,
                    planetSignificators: rawData.planet_significators,
                    fourStepTheory: rawData.four_step_theory,
                });
            } else {
                setSigError(response.data?.detail || 'Failed to update for selected moment.');
            }
        } catch (e) {
            if (requestId !== sigRequestIdRef.current) return;
            setSigError(e.message || 'Failed to update for selected moment.');
            console.error('KP moment API Error:', e.response?.data || e);
        } finally {
            if (requestId === sigRequestIdRef.current) {
                setSigLoading(false);
            }
        }
    }, [birthDetails?.latitude, birthDetails?.longitude, buildKpPayload]);

    const fetchFructificationForMoment = useCallback(async (moment) => {
        if (birthDetails?.latitude == null || birthDetails?.longitude == null) {
            setFructError('Birth location is incomplete.');
            return;
        }
        if (!birthDetails?.date || !birthDetails?.time) {
            setFructError('Birth details are incomplete.');
            return;
        }
        if (!(moment instanceof Date) || Number.isNaN(moment.getTime())) {
            setFructError('Invalid date/time.');
            return;
        }
        const requestId = ++fructRequestIdRef.current;
        setFructLoading(true);
        setFructError(null);
        try {
            const birthDate = String(birthDetails.date).split('T')[0];
            let birthTime = String(birthDetails.time);
            if (birthTime.includes('T')) birthTime = birthTime.split('T')[1];
            birthTime = birthTime.slice(0, 5);
            const payload = {
                birth_date: birthDate,
                birth_time: birthTime,
                latitude: birthDetails.latitude,
                longitude: birthDetails.longitude,
                timezone: '',
                as_of_date: formatLocalDate(moment),
                as_of_time: formatLocalTime(moment),
                language: 'en',
                synthesize: true,
            };
            const response = await kpAPI.getFructification(payload);
            if (requestId !== fructRequestIdRef.current) return;
            if (response.data && response.data.success) {
                setFructData(response.data.data);
            } else {
                setFructError(response.data?.detail || 'Failed to load results for this moment.');
            }
        } catch (e) {
            if (requestId !== fructRequestIdRef.current) return;
            setFructError(e.message || 'Failed to load results for this moment.');
            console.error('KP fructification API Error:', e.response?.data || e);
        } finally {
            if (requestId === fructRequestIdRef.current) {
                setFructLoading(false);
            }
        }
    }, [birthDetails]);

    useEffect(() => {
        if (birthDetails?.latitude == null || birthDetails?.longitude == null) return;
        const moment = resolveSigMoment();
        if (!moment) return;
        const timer = setTimeout(() => {
            fetchSignificatorsForMoment(moment);
        }, sigMode === 'today' ? 280 : 0);
        return () => clearTimeout(timer);
    }, [
        sigMode,
        sigMoment,
        birthDetails?.latitude,
        birthDetails?.longitude,
        birthDetails?.date,
        birthDetails?.time,
        birthDetails?.name,
        resolveSigMoment,
        fetchSignificatorsForMoment,
    ]);

    useEffect(() => {
        if (activeTab !== 'results') return;
        if (birthDetails?.latitude == null || birthDetails?.longitude == null) return;
        const moment = sigMoment instanceof Date ? sigMoment : new Date();
        const timer = setTimeout(() => {
            fetchFructificationForMoment(moment);
        }, 280);
        return () => clearTimeout(timer);
    }, [
        activeTab,
        sigMoment,
        birthDetails?.latitude,
        birthDetails?.longitude,
        birthDetails?.date,
        birthDetails?.time,
        birthDetails?.name,
        fetchFructificationForMoment,
    ]);

    const selectSigMode = (mode) => {
        if (mode === 'today') {
            setSigMoment(new Date());
        }
        setSigMode(mode);
    };

    const fetchAndProcessKPData = async () => {
        if (!birthDetails || !birthDetails.date || !birthDetails.time) {
            setError('Birth details are incomplete.');
            setLoading(false);
            return;
        }
        try {
            setLoading(true);
            const apiPayload = buildKpPayload(
                birthDetails.date.split('T')[0],
                birthDetails.time.split('T')[1] ? birthDetails.time.split('T')[1].slice(0, 5) : birthDetails.time,
            );

            const [response, rpResponse] = await Promise.all([
                kpAPI.getKPChart(apiPayload),
                kpAPI.getRulingPlanets(apiPayload)
            ]);

            if (response.data && response.data.success) {
                const rawData = response.data.data;
                const planetsData = Object.keys(rawData.planet_positions).map(p => ({
                    planet: p,
                    longitude: rawData.planet_positions[p],
                    ...rawData.planet_lords[p]
                }));
                const cuspsData = Object.keys(rawData.house_cusps).map(c => ({
                    cusp: c,
                    longitude: rawData.house_cusps[c],
                    ...rawData.cusp_lords[c]
                }));
                setProcessedData({
                    planets: planetsData,
                    cusps: cuspsData,
                });
            } else {
                setError(response.data.detail || 'Failed to fetch KP data.');
            }

            if (rpResponse.data && rpResponse.data.success) {
                setRulingPlanets(rpResponse.data.data);
            }
        } catch (e) {
            setError(e.message || 'An error occurred.');
            console.error("KP API Error:", e.response?.data || e);
        } finally {
            setLoading(false);
        }
    };

    const renderMomentControls = () => {
        const birthMoment = birthMomentFromDetails(birthDetails);
        const activeMoment = resolveSigMoment();
        const isDark = theme === 'dark';
        const segmentActiveBg = isClassic ? colors.primary : (isDark ? 'rgba(255, 107, 53, 0.95)' : colors.primary);
        const segmentIdleBg = isClassic
            ? colors.surface
            : (isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(249, 115, 22, 0.1)');

        return (
            <>
                <View style={[styles.sigModeBar, { backgroundColor: isClassic ? colors.cardBackground : (isDark ? 'rgba(0,0,0,0.35)' : 'rgba(255,255,255,0.65)') }]}>
                    {['birth', 'today'].map((mode) => {
                        const active = sigMode === mode;
                        return (
                            <TouchableOpacity
                                key={mode}
                                style={[styles.sigModeChip, { backgroundColor: active ? segmentActiveBg : segmentIdleBg }]}
                                onPress={() => selectSigMode(mode)}
                                activeOpacity={0.85}
                            >
                                <Text style={[styles.sigModeChipText, { color: active ? (isClassic ? colors.background : '#fff') : colors.text }]}>
                                    {mode === 'birth' ? 'Birth' : 'Today'}
                                </Text>
                            </TouchableOpacity>
                        );
                    })}
                </View>

                {sigMode === 'birth' ? (
                    <View style={styles.sigMetaRow}>
                        <Ionicons name="sparkles-outline" size={14} color={colors.primary} />
                        <Text style={[styles.sigHint, { color: colors.textSecondary, marginBottom: 0, flex: 1 }]}>
                            Natal moment{birthMoment ? ` · ${formatFriendlyDateTime(birthMoment)}` : ''}
                        </Text>
                    </View>
                ) : (
                    <>
                        <View style={styles.sigMetaRow}>
                            <Ionicons name="time-outline" size={14} color={colors.primary} />
                            <Text style={[styles.sigHint, { color: colors.textSecondary, marginBottom: 0, flex: 1 }]}>
                                Explore any moment at birth place
                            </Text>
                            <TouchableOpacity
                                style={[styles.sigNowBtn, { backgroundColor: segmentIdleBg }]}
                                onPress={() => setSigMoment(new Date())}
                                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                            >
                                <Ionicons name="refresh" size={13} color={colors.primary} />
                                <Text style={[styles.sigNowBtnText, { color: colors.primary }]}>Now</Text>
                            </TouchableOpacity>
                        </View>
                        <DateNavigator
                            date={sigMoment}
                            onDateChange={setSigMoment}
                            includeTime
                            resetDate={new Date()}
                            cosmicTheme={isDark && !isClassic}
                        />
                    </>
                )}

                {sigLoading ? (
                    <View style={styles.sigLoadingRow}>
                        <ActivityIndicator size="small" color={colors.primary} />
                        <Text style={[styles.loadingText, { color: colors.textSecondary, marginLeft: 8 }]}>
                            Updating…
                        </Text>
                    </View>
                ) : null}
                {!sigLoading && activeMoment && sigMode === 'today' ? (
                    <Text style={[styles.sigActiveStamp, { color: colors.textSecondary }]}>
                        Showing {formatFriendlyDateTime(activeMoment)}
                    </Text>
                ) : null}
                {sigError ? (
                    <Text style={[styles.errorText, { color: colors.error }]}>{sigError}</Text>
                ) : null}
            </>
        );
    };

    const renderMomentDrivenTab = (kind) => {
        let body = null;
        if (!sigError) {
            if (kind === 'house') {
                body = <SignificatorsView data={sigData.significators} theme={theme} colors={colors} />;
            } else if (kind === 'planet') {
                body = <PlanetSignificatorsView data={sigData.planetSignificators} theme={theme} colors={colors} />;
            } else {
                body = <FourStepTheoryView data={sigData.fourStepTheory} theme={theme} colors={colors} />;
            }
        }

        return (
            <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }}>
                {renderMomentControls()}
                {body}
            </ScrollView>
        );
    };

    const renderResultsTab = () => {
        const isDark = theme === 'dark';
        const segmentIdleBg = isClassic ? colors.backgroundSecondary : (isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(249, 115, 22, 0.12)');
        const activeMoment = sigMoment instanceof Date ? sigMoment : new Date();
        const bodyText = isClassic ? colors.text : (isDark ? 'rgba(255,255,255,0.92)' : '#1c1917');
        const mutedText = isClassic ? colors.textSecondary : (isDark ? 'rgba(255,255,255,0.72)' : '#44403c');
        return (
            <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }} contentContainerStyle={{ paddingBottom: 24 }}>
                <View style={[styles.fructMomentBar, {
                    backgroundColor: isClassic ? colors.surface : (isDark ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.92)'),
                    borderColor: isClassic ? colors.cardBorder : (isDark ? 'rgba(255,255,255,0.14)' : 'rgba(194, 65, 12, 0.16)'),
                }]}>
                    <View style={{ flex: 1 }}>
                        <Text style={[styles.fructMomentTitle, { color: bodyText }]}>Selected moment</Text>
                        <Text style={[styles.fructMomentMeta, { color: mutedText }]}>
                            Birth place · {formatFriendlyDateTime(activeMoment)}
                        </Text>
                    </View>
                    <TouchableOpacity
                        style={[styles.sigNowBtn, { backgroundColor: segmentIdleBg }]}
                        onPress={() => setSigMoment(new Date())}
                        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                    >
                        <Ionicons name="refresh" size={14} color={colors.primary} />
                        <Text style={[styles.sigNowBtnText, { color: colors.primary }]}>Now</Text>
                    </TouchableOpacity>
                </View>
                <DateNavigator
                    date={activeMoment}
                    onDateChange={setSigMoment}
                    includeTime
                    resetDate={new Date()}
                    cosmicTheme={isDark}
                />
                {fructLoading ? (
                    <View style={[styles.sigLoadingRow, { marginTop: 8 }]}>
                        <ActivityIndicator size="small" color={colors.primary} />
                        <Text style={[styles.fructBodyLoading, { color: mutedText }]}>
                            Computing today & this hour…
                        </Text>
                    </View>
                ) : null}
                {fructError ? (
                    <Text style={[styles.errorText, { color: colors.error }]}>{fructError}</Text>
                ) : null}
                {!fructError && !fructLoading ? (
                    <FructificationView data={fructData} theme={theme} colors={colors} />
                ) : null}
            </ScrollView>
        );
    };

    const renderContent = () => {
        if (activeTab === 'results') {
            if (birthDetails?.latitude == null || birthDetails?.longitude == null) {
                if (loading) {
                    return (
                        <View style={styles.loadingContainer}>
                            <ActivityIndicator size="large" color={colors.primary} />
                            <Text style={[styles.loadingText, { color: colors.text }]}>Loading KP Analysis...</Text>
                        </View>
                    );
                }
                return <Text style={[styles.errorText, { color: colors.error }]}>{error || 'Birth location is incomplete.'}</Text>;
            }
            return renderResultsTab();
        }

        if (
            activeTab === 'significators'
            || activeTab === 'planetSignificators'
            || activeTab === 'fourStep'
        ) {
            if (birthDetails?.latitude == null || birthDetails?.longitude == null) {
                if (loading) {
                    return (
                        <View style={styles.loadingContainer}>
                            <ActivityIndicator size="large" color={colors.primary} />
                            <Text style={[styles.loadingText, { color: colors.text }]}>Loading KP Analysis...</Text>
                        </View>
                    );
                }
                return <Text style={[styles.errorText, { color: colors.error }]}>{error || 'Birth location is incomplete.'}</Text>;
            }
            const kind = activeTab === 'significators'
                ? 'house'
                : activeTab === 'planetSignificators'
                    ? 'planet'
                    : 'fourStep';
            return renderMomentDrivenTab(kind);
        }

        if (loading) {
            return (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color={colors.primary} />
                    <Text style={[styles.loadingText, { color: colors.text }]}>Loading KP Analysis...</Text>
                </View>
            );
        }
        if (error) {
            return <Text style={[styles.errorText, { color: colors.error }]}>{error}</Text>;
        }
        if (!processedData) {
            return <Text style={{ color: colors.textSecondary }}>No data available</Text>;
        }

        switch (activeTab) {
            case 'planets':
                return (
                    <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }}>
                        <RulingPlanetsView data={rulingPlanets} theme={theme} colors={colors} />
                        <PlanetaryTable data={processedData.planets} theme={theme} colors={colors} />
                    </ScrollView>
                );
            case 'cusps':
                return <CuspalTable data={processedData.cusps} theme={theme} colors={colors} />;
            default:
                return null;
        }
    };

    return (
        <View style={{ flex: 1 }}>
            {isClassic && <StatusBar barStyle="dark-content" backgroundColor={colors.background} />}
            <LinearGradient
                colors={isClassic ? [colors.background, colors.backgroundSecondary] : (theme === 'dark' 
                    ? ['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']
                    : ['#fefcfb', '#fef7f0', '#fed7d7', '#fefcfb'])}
                style={styles.container}
            >
                <SafeAreaView style={styles.safeArea}>
                    <View style={styles.header}>
                        <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.backButton, isClassic && { backgroundColor: colors.surface }]}>
                            <Ionicons name="arrow-back" size={24} color={colors.text} />
                        </TouchableOpacity>
                        <View style={styles.headerCenter}>
                            <Text style={[styles.headerTitle, { color: colors.text }]}>🎯 KP System</Text>
                            {birthDetails && (
                                <NativeSelectorChip 
                                    birthData={birthDetails}
                                    onPress={() => navigation.navigate('SelectNative', { returnTo: 'KP' })}
                                    maxLength={7}
                                />
                            )}
                        </View>
                        <View style={{ width: 40 }} />
                    </View>

                    <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
                        <View style={styles.tabContainer}>
                            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
                                {['planets', 'cusps', 'significators', 'planetSignificators', 'fourStep', 'results'].map((tab) => (
                                    <TouchableOpacity
                                        key={tab}
                                        onPress={() => {
                                            if (tab === 'results') setSigMoment(new Date());
                                            setActiveTab(tab);
                                        }}
                                        style={[styles.tab, activeTab === tab && styles.activeTab]}
                                    >
                                        <LinearGradient
                                            colors={activeTab === tab 
                                                ? (isClassic ? [colors.primary, colors.textSecondary] : ['#ff6b35', '#ff8c5a'])
                                                : (isClassic ? [colors.surface, colors.backgroundSecondary] : (Platform.OS === 'android'
                                                    ? (theme === 'dark' ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.1)'] : ['rgba(249, 115, 22, 0.15)', 'rgba(249, 115, 22, 0.1)'])
                                                    : (theme === 'dark' ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'] : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])))}
                                            style={[styles.tabGradient, isClassic && { borderWidth: 1, borderColor: activeTab === tab ? colors.primary : colors.cardBorder }]}
                                        >
                                            <Text
                                                numberOfLines={1}
                                                style={[styles.tabText, { color: activeTab === tab ? (isClassic ? colors.background : '#fff') : colors.text }]}
                                            >
                                                {tab === 'planets' ? 'Planets' :
                                                 tab === 'cusps' ? 'Cusps' :
                                                 tab === 'significators' ? 'H-Sig' :
                                                 tab === 'planetSignificators' ? 'P-Sig' :
                                                 tab === 'fourStep' ? 'Steps' : 'Results'}
                                            </Text>
                                        </LinearGradient>
                                    </TouchableOpacity>
                                ))}
                            </ScrollView>
                        </View>

                        <View style={[styles.contentCard, { backgroundColor: isClassic ? colors.cardBackground : (theme === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.9)'), borderWidth: isClassic ? 1 : 0, borderColor: isClassic ? colors.cardBorder : undefined }]}>
                            {renderContent()}
                            
                            {activeTab !== 'results' ? (
                                <View style={[styles.legend, { backgroundColor: isClassic ? colors.surface : (theme === 'dark' ? 'rgba(255, 107, 53, 0.1)' : 'rgba(249, 115, 22, 0.08)'), borderColor: isClassic ? colors.cardBorder : undefined }]}>
                                    <Text style={[styles.legendTitle, { color: colors.text }]}>Legend:</Text>
                                    <Text style={[styles.legendText, { color: colors.textSecondary }]}>SL = Sign Lord  •  NL = Nakshatra Lord  •  SB = Sub Lord  •  SS = Sub-Sub Lord  •  Pd = Pada</Text>
                                </View>
                            ) : null}
                        </View>
                    </Animated.View>
                </SafeAreaView>
            </LinearGradient>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    safeArea: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingVertical: 12,
    },
    backButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    headerTitle: {
        fontSize: 20,
        fontWeight: '800',
    },
    headerCenter: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        gap: 4,
    },
    content: {
        flex: 1,
        padding: 16,
    },
    tabContainer: {
        flexDirection: 'row',
        gap: 8,
        marginBottom: 16,
    },
    tab: {
        borderRadius: 12,
        overflow: 'hidden',
        flexShrink: 0,
    },
    tabGradient: {
        paddingVertical: 10,
        paddingHorizontal: 14,
        alignItems: 'center',
        borderRadius: 12,
    },
    tabText: {
        fontSize: 13,
        fontWeight: '700',
    },
    contentCard: {
        flex: 1,
        borderRadius: 16,
        padding: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
        elevation: 4,
        // Android Glassmorphism Fix - Use dark tint instead of white
        backgroundColor: Platform.OS === 'android' ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.05)',
    },
    sigModeBar: {
        flexDirection: 'row',
        gap: 8,
        padding: 4,
        borderRadius: 12,
        marginBottom: 10,
    },
    sigModeChip: {
        flex: 1,
        paddingVertical: 9,
        borderRadius: 10,
        alignItems: 'center',
    },
    sigModeChipText: {
        fontSize: 13,
        fontWeight: '700',
    },
    sigMetaRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginBottom: 10,
    },
    sigHint: {
        fontSize: 12,
        marginBottom: 8,
        lineHeight: 16,
    },
    sigNowBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        paddingHorizontal: 8,
        paddingVertical: 5,
        borderRadius: 8,
    },
    sigNowBtnText: {
        fontSize: 12,
        fontWeight: '700',
    },
    sigActiveStamp: {
        fontSize: 11,
        marginBottom: 8,
        fontWeight: '600',
    },
    sigLoadingRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 10,
    },
    fructMomentBar: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
        borderWidth: 1,
        borderRadius: 14,
        paddingHorizontal: 12,
        paddingVertical: 12,
        marginBottom: 10,
    },
    fructMomentTitle: {
        fontSize: 15,
        fontWeight: '800',
        marginBottom: 2,
    },
    fructMomentMeta: {
        fontSize: 13,
        lineHeight: 18,
        fontWeight: '500',
    },
    fructBodyLoading: {
        marginLeft: 10,
        fontSize: 14,
        fontWeight: '600',
    },
    fructIntroCard: {
        borderWidth: 1,
        borderRadius: 14,
        padding: 14,
        marginBottom: 12,
    },
    fructIntroTitle: {
        fontSize: 18,
        fontWeight: '800',
        marginBottom: 6,
    },
    fructBody: {
        fontSize: 14,
        lineHeight: 21,
        marginBottom: 6,
        fontWeight: '500',
    },
    fructSectionTitle: {
        fontSize: 16,
        fontWeight: '800',
        marginBottom: 10,
        marginTop: 4,
    },
    fructSubheadInline: {
        fontSize: 11,
        fontWeight: '800',
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        marginBottom: 8,
    },
    fructScopeBar: {
        flexDirection: 'row',
        gap: 6,
        padding: 4,
        borderRadius: 14,
        borderWidth: 1,
        marginBottom: 10,
    },
    fructScopeChip: {
        flex: 1,
        borderRadius: 11,
        paddingVertical: 10,
        paddingHorizontal: 8,
        alignItems: 'center',
    },
    fructScopeChipText: {
        fontSize: 14,
        fontWeight: '800',
    },
    fructScopeCount: {
        fontSize: 11,
        fontWeight: '600',
        marginTop: 2,
    },
    fructScopeBlurb: {
        fontSize: 14,
        lineHeight: 20,
        marginBottom: 12,
        fontWeight: '500',
    },
    fructRpStrip: {
        borderWidth: 1,
        borderRadius: 14,
        padding: 12,
        marginBottom: 12,
    },
    fructRpChip: {
        borderWidth: 1,
        borderRadius: 10,
        paddingHorizontal: 10,
        paddingVertical: 7,
    },
    fructRpRole: {
        fontSize: 10,
        fontWeight: '700',
        textTransform: 'uppercase',
        letterSpacing: 0.3,
    },
    fructRpPlanet: {
        fontSize: 13,
        fontWeight: '800',
        marginTop: 2,
    },
    fructNotice: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: 8,
        borderWidth: 1,
        borderRadius: 12,
        padding: 12,
        marginBottom: 12,
    },
    fructHouseRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    fructHouseCard: {
        borderWidth: 1,
        borderLeftWidth: 4,
        borderRadius: 14,
        paddingHorizontal: 12,
        paddingVertical: 12,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
    },
    fructHouseBadge: {
        width: 46,
        height: 46,
        borderRadius: 12,
        alignItems: 'center',
        justifyContent: 'center',
    },
    fructHouseNum: {
        fontSize: 16,
        fontWeight: '800',
    },
    fructHouseTitle: {
        fontSize: 14,
        fontWeight: '800',
        marginBottom: 3,
        lineHeight: 19,
    },
    fructHouseMeta: {
        fontSize: 13,
        lineHeight: 18,
        fontWeight: '500',
        marginBottom: 6,
    },
    fructTonePill: {
        borderRadius: 999,
        paddingHorizontal: 8,
        paddingVertical: 3,
    },
    fructTonePillText: {
        fontSize: 11,
        fontWeight: '800',
    },
    fructHowLinkRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 2,
    },
    fructHowLink: {
        fontSize: 13,
        fontWeight: '800',
    },
    fructHowBox: {
        borderWidth: 1,
        borderRadius: 14,
        paddingHorizontal: 12,
        paddingTop: 4,
        paddingBottom: 8,
        marginTop: 8,
    },
    fructHowSummary: {
        fontSize: 14,
        fontWeight: '700',
        marginTop: 10,
        marginBottom: 4,
        lineHeight: 20,
    },
    fructHowStep: {
        paddingTop: 10,
        marginTop: 6,
        borderTopWidth: StyleSheet.hairlineWidth,
    },
    fructHowStepHead: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
        gap: 8,
    },
    fructHowStepTitle: {
        fontSize: 13,
        fontWeight: '800',
        flex: 1,
    },
    fructPassPill: {
        borderRadius: 999,
        paddingHorizontal: 8,
        paddingVertical: 3,
    },
    fructCalcToggle: {
        borderWidth: 1,
        borderRadius: 14,
        padding: 12,
        marginBottom: 12,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
    },
    fructCalcIcon: {
        width: 34,
        height: 34,
        borderRadius: 10,
        alignItems: 'center',
        justifyContent: 'center',
    },
    fructCard: {
        borderWidth: 1,
        borderLeftWidth: 4,
        borderRadius: 14,
        padding: 14,
        marginBottom: 12,
    },
    fructCardTop: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 6,
        gap: 8,
    },
    fructCardEyebrow: {
        fontSize: 11,
        fontWeight: '800',
        textTransform: 'uppercase',
        letterSpacing: 0.4,
        flex: 1,
    },
    fructCardTitle: {
        fontSize: 16,
        fontWeight: '800',
        marginBottom: 6,
        lineHeight: 22,
    },
    fructPossibilityRow: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: 8,
        marginBottom: 6,
    },
    fructDot: {
        width: 6,
        height: 6,
        borderRadius: 3,
        marginTop: 7,
    },
    fructBullet: {
        flex: 1,
        fontSize: 14,
        lineHeight: 21,
        fontWeight: '500',
    },
    fructTinyChipWrap: {
        borderRadius: 8,
        paddingHorizontal: 8,
        paddingVertical: 4,
    },
    fructTinyChip: {
        fontSize: 12,
        fontWeight: '800',
    },
    fructDashaRow: {
        flexDirection: 'row',
        gap: 8,
        marginBottom: 12,
        paddingRight: 4,
    },
    fructDashaChip: {
        borderRadius: 12,
        borderWidth: 1,
        paddingHorizontal: 12,
        paddingVertical: 8,
        alignItems: 'center',
        minWidth: 58,
    },
    fructDashaLabel: {
        fontSize: 10,
        fontWeight: '800',
        letterSpacing: 0.4,
    },
    fructDashaPlanet: {
        fontSize: 13,
        fontWeight: '800',
        marginTop: 2,
    },
    fructEmpty: {
        borderWidth: 1,
        borderRadius: 14,
        padding: 16,
        marginBottom: 12,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        marginTop: 16,
        fontSize: 16,
        fontWeight: '600',
    },
    errorText: {
        fontSize: 14,
        textAlign: 'center',
        marginTop: 20,
    },
    table: {
        minWidth: '100%',
    },
    tableRow: {
        flexDirection: 'row',
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(0, 0, 0, 0.25)',
    },
    tableRowAlt: {
        backgroundColor: 'rgba(249, 115, 22, 0.03)',
    },
    tableHeader: {
        fontSize: 12,
        fontWeight: '700',
        paddingHorizontal: 8,
        borderRightWidth: 1,
        borderRightColor: 'rgba(0, 0, 0, 0.25)',
    },
    tableCell: {
        fontSize: 12,
        paddingHorizontal: 8,
        borderRightWidth: 1,
        borderRightColor: 'rgba(0, 0, 0, 0.2)',
    },
    significatorCard: {
        padding: 16,
        borderRadius: 12,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: 'rgba(249, 115, 22, 0.2)',
        // Android Glassmorphism Fix - Use dark tint instead of white
        backgroundColor: Platform.OS === 'android' ? 'rgba(0, 0, 0, 0.15)' : 'rgba(255, 255, 255, 0.05)',
    },
    significatorHouse: {
        fontSize: 16,
        fontWeight: '700',
        marginBottom: 12,
    },
    significatorChips: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    significatorChip: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 12,
        borderWidth: 1,
    },
    significatorText: {
        fontSize: 13,
        fontWeight: '700',
    },
    legend: {
        marginTop: 16,
        padding: 12,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: 'rgba(249, 115, 22, 0.2)',
    },
    legendTitle: {
        fontSize: 13,
        fontWeight: '700',
        marginBottom: 6,
    },
    legendText: {
        fontSize: 12,
        lineHeight: 18,
    },
    // Ruling Planets Styles
    rpContainer: {
        marginBottom: 16,
    },
    rpCard: {
        padding: 12,
        borderRadius: 12,
        borderWidth: 1,
    },
    rpTitle: {
        fontSize: 14,
        fontWeight: '800',
        marginBottom: 8,
        textAlign: 'center',
    },
    rpSection: {
        marginBottom: 6,
    },
    rpSectionTitle: {
        fontSize: 12,
        fontWeight: '700',
    },
    rpText: {
        fontSize: 12,
    },
    // 4-Step Theory Improved Styles
    fourStepHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        marginBottom: 16,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(0,0,0,0.05)',
        paddingBottom: 12,
    },
    planetIconCircle: {
        width: 36,
        height: 36,
        borderRadius: 18,
        justifyContent: 'center',
        alignItems: 'center',
    },
    planetIconText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '800',
    },
    fourStepPlanetTitle: {
        fontSize: 18,
        fontWeight: '800',
    },
    stepsList: {
        paddingLeft: 4,
    },
    stepContainer: {
        flexDirection: 'row',
        minHeight: 50,
    },
    stepIndicator: {
        width: 20,
        alignItems: 'center',
    },
    stepDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginTop: 6,
    },
    stepLine: {
        width: 2,
        flex: 1,
        marginVertical: 2,
    },
    stepContent: {
        flex: 1,
        paddingLeft: 12,
        paddingBottom: 16,
    },
    stepNumber: {
        fontSize: 10,
        fontWeight: '600',
        textTransform: 'uppercase',
        marginBottom: 2,
    },
    stepDetails: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    stepLord: {
        fontSize: 14,
        fontWeight: '700',
    },
    stepHouses: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 4,
        justifyContent: 'flex-end',
        flex: 1,
        marginLeft: 10,
    },
    miniHouseChip: {
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 6,
        minWidth: 22,
        alignItems: 'center',
    },
    miniHouseText: {
        fontSize: 11,
        fontWeight: '800',
    },
    noHousesText: {
        fontSize: 10,
        fontStyle: 'italic',
    },
    // Ruling Planets Improved Styles
    rpHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        marginBottom: 12,
    },
    rpChipGroup: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
        marginTop: 4,
    },
    rpChip: {
        flexDirection: 'row',
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: 20,
        borderWidth: 1,
        alignItems: 'center',
        gap: 4,
    },
    rpChipLabel: {
        fontSize: 10,
        fontWeight: '600',
        textTransform: 'uppercase',
    },
    rpChipValue: {
        fontSize: 12,
        fontWeight: '700',
    },
    rpFooter: {
        marginTop: 12,
        alignItems: 'center',
        borderTopWidth: 1,
        borderTopColor: 'rgba(0,0,0,0.05)',
        paddingTop: 12,
    },
    dayLordBadge: {
        flexDirection: 'row',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 25,
        alignItems: 'center',
        gap: 8,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    dayLordLabel: {
        color: 'rgba(255,255,255,0.8)',
        fontSize: 11,
        fontWeight: '600',
    },
    dayLordValue: {
        color: '#fff',
        fontSize: 14,
        fontWeight: '800',
    },
});

export default KPScreen;
