import React, { useState, useEffect, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, Animated, StatusBar } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { kpAPI } from '../services/api';
import { storage } from '../services/storage';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';
import NativeSelectorChip from '../components/Common/NativeSelectorChip';
import DateNavigator from '../components/Common/DateNavigator';
import { typographyTokens } from '../theme/tokens';

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
                <View style={[styles.tableRow, styles.tableHeadingRow, { backgroundColor: colors.surfaceMuted, borderBottomColor: colors.borderStrong }]}>
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
                        <View key={index} style={[styles.tableRow, { borderBottomColor: colors.cardBorder }, index % 2 === 0 && { backgroundColor: colors.backgroundSecondary }]}>
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
                <View style={[styles.tableRow, styles.tableHeadingRow, { backgroundColor: colors.surfaceMuted, borderBottomColor: colors.borderStrong }]}>
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
                        <View key={index} style={[styles.tableRow, { borderBottomColor: colors.cardBorder }, index % 2 === 0 && { backgroundColor: colors.backgroundSecondary }]}>
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
    return {
        cardBg: colors.surfaceRaised,
        cardBorder: colors.cardBorder,
        chipBg: colors.selectionSurface,
        chipBorder: colors.selectionBorder,
        chipText: colors.selectionText,
        title: colors.primary,
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

    const renderStep = (num, label, lord, houses) => (
        <View style={styles.stepContainer}>
            <View style={styles.stepIndicator}>
                <View style={[styles.stepDot, { backgroundColor: colors.primary }]} />
                {num < 4 && <View style={[styles.stepLine, { backgroundColor: colors.cardBorder }]} />}
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
                    backgroundColor: colors.surfaceRaised,
                    borderColor: colors.cardBorder,
                }]}>
                    <View style={[styles.fourStepHeader, { borderBottomColor: colors.cardBorder }]}>
                        <View style={[styles.planetIconCircle, { backgroundColor: colors.primary }]}>
                            <Text style={[styles.planetIconText, { color: colors.onPrimary }]}>{planet.substring(0, 2)}</Text>
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
    if (!data) return null;

    const renderRPChip = (label, value) => (
        <View style={[styles.rpChip, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
            <Text style={[styles.rpChipLabel, { color: colors.textSecondary }]}>{label}:</Text>
            <Text style={[styles.rpChipValue, { color: colors.primary }]}>{value}</Text>
        </View>
    );

    return (
        <View style={styles.rpContainer}>
            <View style={[styles.rpCard, {
                backgroundColor: colors.surfaceRaised,
                borderColor: colors.cardBorder,
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

                <View style={[styles.rpFooter, { borderTopColor: colors.cardBorder }]}>
                    <View style={[styles.dayLordBadge, { backgroundColor: colors.primary }]}>
                        <Text style={[styles.dayLordLabel, { color: colors.onPrimary }]}>Day Lord</Text>
                        <Text style={[styles.dayLordValue, { color: colors.onPrimary }]}>{data.day_lord}</Text>
                    </View>
                </View>
            </View>
        </View>
    );
};

const TONE_LABELS = {
    supportive: 'Favourable',
    mixed: 'Mixed',
    challenging: 'Under pressure',
    neutral: 'Neutral',
};

const toneUi = (tone, colors) => {
    const accents = {
        supportive: colors.success,
        mixed: colors.info,
        challenging: colors.error,
        neutral: colors.textSecondary,
    };
    const accent = accents[tone] || accents.neutral;
    return {
        accent,
        pillBg: accent,
        pillText: colors.textInverse,
        softBg: colors.surfaceMuted,
    };
};

const RP_ROLE_SHORT = {
    day_lord: 'Day Lord',
    moon_star_lord: 'Moon Star',
    moon_sign_lord: 'Moon Sign',
    asc_star_lord: 'Asc Star',
    asc_sub_lord: 'Asc Sub',
    moon_sub_lord: 'Moon Sub',
};

const FructificationView = ({ data, theme, colors, initialScope = 'today' }) => {
    const [scopeTab, setScopeTab] = useState(initialScope === 'hour' ? 'hour' : 'today'); // 'today' | 'hour'
    const [expandedHouse, setExpandedHouse] = useState(null);
    const [calcOpen, setCalcOpen] = useState(false);

    useEffect(() => {
        setScopeTab(initialScope === 'hour' ? 'hour' : 'today');
    }, [initialScope, data?.as_of]);

    useEffect(() => {
        setExpandedHouse(null);
        setCalcOpen(false);
    }, [scopeTab, data?.as_of]);

    if (!data) return null;

    const surface = colors.surfaceRaised;
    const surfaceMuted = colors.surfaceMuted;
    const border = colors.cardBorder;
    const bodyText = colors.text;
    const mutedText = colors.textSecondary;
    const subtleText = colors.textTertiary;
    const linkColor = colors.primary;

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
            blurb: 'Houses that can give results across the day (Day Lord + Moon star lord), including any house already confirmed this hour.',
            formulaHint: 'AD/PD ∩ Sookshma ∩ Day ruling planets ∪ this hour',
        }
        : {
            title: 'This hour',
            blurb: 'Sharper timing for the selected hour, using the full ruling-planet set.',
            formulaHint: 'AD/PD ∩ Sookshma ∩ Prana ∩ Hour ruling planets',
        };

    const renderHowSteps = (how, accent) => {
        if (!how?.steps?.length) return null;
        const passTone = toneUi('supportive', colors);
        const failTone = toneUi('challenging', colors);
        return (
            <View style={[styles.fructHowBox, { borderColor: border, backgroundColor: surfaceMuted }]}>
                {how.summary ? (
                    <Text style={[styles.fructHowSummary, { color: bodyText }]}>{how.summary}</Text>
                ) : null}
                {how.steps.map((step) => (
                    <View key={`${step.step}-${step.title}`} style={[styles.fructHowStep, { borderTopColor: border }]}>
                        <View style={styles.fructHowStepHead}>
                            <Text style={[styles.fructHowStepTitle, { color: accent || linkColor }]}>
                                Step {step.step} · {step.title}
                            </Text>
                            {typeof step.passed === 'boolean' ? (
                                <View style={[styles.fructPassPill, { backgroundColor: step.passed ? passTone.pillBg : failTone.pillBg }]}>
                                    <Text style={{ color: step.passed ? passTone.pillText : failTone.pillText, fontSize: 11, fontWeight: '800' }}>
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
        const tone = soft ? toneUi('neutral', colors) : toneUi(row.tone, colors);
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
                            borderColor: soft ? border : tone.accent,
                            borderLeftColor: tone.accent,
                        },
                    ]}
                >
                    <View style={[styles.fructHouseBadge, { backgroundColor: tone.pillBg }]}>
                        <Text style={[styles.fructHouseNum, { color: tone.pillText }]}>H{row.house}</Text>
                    </View>
                    <View style={{ flex: 1, minWidth: 0 }}>
                        <Text style={[styles.fructHouseTitle, { color: bodyText }]} numberOfLines={2}>
                            {row.label || `House ${row.house}`}
                        </Text>
                        <Text style={[styles.fructHouseMeta, { color: mutedText }]} numberOfLines={2}>
                            {(row.activating_rps || []).join(' · ') || 'No ruling planet'}
                        </Text>
                        <View style={[styles.fructTonePill, { backgroundColor: tone.pillBg, alignSelf: 'flex-start' }]}>
                            <Text style={[styles.fructTonePillText, { color: tone.pillText }]}>{toneLabel}</Text>
                        </View>
                        {row.included_from_hour ? (
                            <Text style={[styles.fructHouseMeta, { color: subtleText, marginTop: 4, marginBottom: 0 }]}>
                                Confirmed this hour
                            </Text>
                        ) : null}
                    </View>
                    <View style={styles.fructHowLinkRow}>
                        <Text style={[styles.fructHowLink, { color: linkColor }]}>
                            {expanded ? 'Hide' : 'Why'}
                        </Text>
                        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={16} color={linkColor} />
                    </View>
                </TouchableOpacity>
                {expanded ? renderHowSteps(row.how, soft ? linkColor : tone.accent) : null}
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

            <View style={[styles.fructScopeBar, { backgroundColor: colors.surfaceMuted, borderColor: border }]}>
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
                                { backgroundColor: active ? colors.selectionControl : 'transparent' },
                            ]}
                            onPress={() => setScopeTab(tab.id)}
                            activeOpacity={0.9}
                        >
                            <Text style={[styles.fructScopeChipText, { color: active ? colors.selectionText : bodyText }]}>
                                {tab.label}
                            </Text>
                            <Text style={[styles.fructScopeCount, { color: active ? colors.selectionTextMuted : subtleText }]}>
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
                <View style={[styles.fructNotice, { backgroundColor: colors.surfaceMuted, borderColor: colors.info }]}>
                    <Ionicons name="information-circle-outline" size={16} color={colors.info} />
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
                <View style={[styles.fructCalcIcon, { backgroundColor: colors.selectionSurface }]}>
                    <Ionicons name="git-branch-outline" size={16} color={linkColor} />
                </View>
                <View style={{ flex: 1 }}>
                    <Text style={[styles.fructHowLink, { color: bodyText }]}>
                        {calcOpen ? 'Hide full calculation' : 'Show full calculation'}
                    </Text>
                    <Text style={[styles.fructBody, { color: mutedText, marginBottom: 0 }]} numberOfLines={calcOpen ? 0 : 2}>
                        {calc.formula || scopeCopy.formulaHint}
                    </Text>
                </View>
                <Ionicons name={calcOpen ? 'chevron-up' : 'chevron-down'} size={18} color={linkColor} />
            </TouchableOpacity>

            {calcOpen && calc.steps?.length ? (
                <View style={[styles.fructHowBox, { borderColor: border, backgroundColor: surfaceMuted, marginBottom: 14 }]}>
                    {calc.steps.map((step) => (
                        <View key={`${scopeTab}-calc-${step.step}`} style={[styles.fructHowStep, { borderTopColor: border }]}>
                            <Text style={[styles.fructHowStepTitle, { color: linkColor }]}>
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

            <Text style={[styles.fructSectionTitle, { color: bodyText, marginTop: 8 }]}>Combined life themes</Text>
            <Text style={[styles.fructBody, { color: mutedText }]}>
                Same house-set wording cache as What’s activated now — for you, spouse, mother, and father — so either screen can fill the cache for the other.
            </Text>
            {manifestations.length ? (() => {
                const order = ['self', 'spouse', 'mother', 'father'];
                const groups = [];
                manifestations.forEach((item) => {
                    const subject = item.subject || 'self';
                    const existing = groups.find((g) => g.subject === subject);
                    if (existing) existing.items.push(item);
                    else groups.push({ subject, items: [item] });
                });
                groups.sort((a, b) => {
                    const ai = order.indexOf(a.subject);
                    const bi = order.indexOf(b.subject);
                    return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi);
                });
                const subjectLabel = (subject) => (subject === 'self' ? 'For you' : `Your ${subject}`);
                return groups.map((group) => (
                    <View key={group.subject} style={{ marginBottom: 14 }}>
                        <View style={styles.fructSubjectHead}>
                            <View style={[styles.fructSubjectIcon, { backgroundColor: colors.selectionSurface }]}>
                                <Ionicons
                                    name={group.subject === 'self' ? 'person-outline' : 'people-outline'}
                                    size={16}
                                    color={linkColor}
                                />
                            </View>
                            <Text style={[styles.fructSubjectTitle, { color: bodyText }]}>
                                {subjectLabel(group.subject)}
                            </Text>
                        </View>
                        {group.items.map((item) => {
                            const tone = toneUi(item.outcome_tone, colors);
                            return (
                                <View
                                    key={item.manifestation_id || item.signature_key || item.label}
                                    style={[styles.fructCard, { backgroundColor: surface, borderColor: border, borderLeftColor: tone.accent }]}
                                >
                                    <View style={styles.fructCardTop}>
                                        <Text style={[styles.fructCardEyebrow, { color: subtleText }]}>
                                            {(item.domain || 'theme').toString()}
                                        </Text>
                                        <View style={[styles.fructTonePill, { backgroundColor: tone.pillBg }]}>
                                            <Text style={[styles.fructTonePillText, { color: tone.pillText }]}>
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
                                            <View style={[styles.fructDot, { backgroundColor: tone.accent }]} />
                                            <Text style={[styles.fructBullet, { color: bodyText }]}>{p}</Text>
                                        </View>
                                    ))}
                                    <View style={[styles.fructHouseRow, { marginTop: 10 }]}>
                                        {(item.house_roles || []).map((role) => (
                                            <View
                                                key={`${item.manifestation_id}-${role.native_house}-${role.relative_house}`}
                                                style={[styles.fructTinyChipWrap, { backgroundColor: tone.pillBg }]}
                                            >
                                                <Text style={[styles.fructTinyChip, { color: tone.pillText }]}>
                                                    {group.subject === 'self'
                                                        ? `H${role.native_house}`
                                                        : `H${role.native_house}→H${role.relative_house}`}
                                                </Text>
                                            </View>
                                        ))}
                                    </View>
                                </View>
                            );
                        })}
                    </View>
                ));
            })() : (
                <View style={[styles.fructEmpty, { backgroundColor: surfaceMuted, borderColor: border }]}>
                    <Text style={[styles.fructBody, { color: mutedText, marginBottom: 0, textAlign: 'center' }]}>
                        No combined house themes matched for {scopeCopy.title.toLowerCase()}. Activated houses still show above.
                    </Text>
                </View>
            )}
        </View>
    );
};

const KPScreen = ({ route, navigation }) => {
    const { birthDetails: initialBirthDetails, initialTab, initialPredictionsScope } = route.params || {};
    const [birthDetails, setBirthDetails] = useState(initialBirthDetails);
    const [activeTab, setActiveTab] = useState(
        initialTab === 'results' || !initialTab ? 'results' : initialTab
    );
    const [processedData, setProcessedData] = useState(null);
    const [rulingPlanets, setRulingPlanets] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    // H-Sig / P-Sig: Birth (default) or Today/explore at birth place.
    const [sigMode, setSigMode] = useState('birth'); // 'birth' | 'today'
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
                setFructError(null);
            } else {
                // Keep prior results visible if we already have them.
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

    // Debounced refetch when mode / birth / explorer moment changes.
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

    // Results tab: always uses clock moment at birth place (natal chart × current dasha/RPs).
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

            // Natal KP chart + ruling planets (birth moment). Significators use sigMoment separately.
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
        const segmentActiveBg = colors.selectionControl;
        const segmentIdleBg = colors.surfaceMuted;

        return (
            <>
                <View style={[styles.sigModeBar, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                    {['birth', 'today'].map((mode) => {
                        const active = sigMode === mode;
                        return (
                            <TouchableOpacity
                                key={mode}
                                style={[styles.sigModeChip, { backgroundColor: active ? segmentActiveBg : segmentIdleBg }]}
                                onPress={() => selectSigMode(mode)}
                                activeOpacity={0.85}
                            >
                                <Text style={[styles.sigModeChipText, { color: active ? colors.selectionText : colors.text }]}>
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
                            cosmicTheme={isDark}
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
        const segmentIdleBg = colors.surfaceMuted;
        const activeMoment = sigMoment instanceof Date ? sigMoment : new Date();
        const bodyText = colors.text;
        const mutedText = colors.textSecondary;
        return (
            <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }} contentContainerStyle={{ paddingBottom: 24 }}>
                <View style={[styles.fructMomentBar, {
                    backgroundColor: colors.surfaceRaised,
                    borderColor: colors.cardBorder,
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
                            {fructData ? 'Refreshing today & this hour…' : 'Computing today & this hour…'}
                        </Text>
                    </View>
                ) : null}
                {fructError ? (
                    <Text style={[styles.errorText, { color: colors.error }]}>{fructError}</Text>
                ) : null}
                {fructData ? (
                    <FructificationView
                        data={fructData}
                        theme={theme}
                        colors={colors}
                        initialScope={initialPredictionsScope === 'hour' ? 'hour' : 'today'}
                    />
                ) : (!fructLoading && !fructError) ? (
                    <Text style={[styles.fructBodyLoading, { color: mutedText, marginTop: 12 }]}>
                        No results loaded yet. Tap Now to compute.
                    </Text>
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
            // Moment-driven tabs share Birth/Today + navigator (independent of natal planets/cusps).
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
                        <View style={styles.sectionHeading}>
                            <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>NATAL KP MAP</Text>
                            <Text style={[styles.sectionTitle, { color: colors.text }]}>Planetary lords</Text>
                            <Text style={[styles.sectionCopy, { color: colors.textSecondary }]}>Sign, star, sub and sub-sub lords at the birth moment.</Text>
                        </View>
                        <RulingPlanetsView data={rulingPlanets} theme={theme} colors={colors} />
                        <PlanetaryTable data={processedData.planets} theme={theme} colors={colors} />
                    </ScrollView>
                );
            case 'cusps':
                return (
                    <ScrollView showsVerticalScrollIndicator={false} style={{ flex: 1 }}>
                        <View style={styles.sectionHeading}>
                            <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>HOUSE PROMISE</Text>
                            <Text style={[styles.sectionTitle, { color: colors.text }]}>Cuspal lords</Text>
                            <Text style={[styles.sectionCopy, { color: colors.textSecondary }]}>The fine-grained lordship chain for every house cusp.</Text>
                        </View>
                        <CuspalTable data={processedData.cusps} theme={theme} colors={colors} />
                    </ScrollView>
                );
            default:
                return null;
        }
    };

    const tabs = [
        { id: 'results', label: 'Predictions' },
        { id: 'planets', label: 'Planets' },
        { id: 'cusps', label: 'Cusps' },
        { id: 'significators', label: 'House significators' },
        { id: 'planetSignificators', label: 'Planet significators' },
        { id: 'fourStep', label: 'Four step' },
    ];

    return (
        <View style={[styles.container, { backgroundColor: colors.background }]}>
            <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} />
            <LinearGradient
                colors={[colors.background, colors.backgroundSecondary, colors.background]}
                style={styles.container}
            >
                <SafeAreaView edges={['top']} style={{ backgroundColor: colors.headerSurface }}>
                    <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
                        <View style={styles.headerSide}>
                            <TouchableOpacity
                                onPress={() => navigation.goBack()}
                                style={[styles.backButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}
                            >
                                <Ionicons name="arrow-back" size={22} color={colors.textInverse} />
                            </TouchableOpacity>
                        </View>
                        <View style={styles.headerCenter}>
                            <Text style={[styles.headerEyebrow, { color: colors.accent }]}>KRISHNAMURTI PADDHATI</Text>
                            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>KP System</Text>
                        </View>
                        <View style={[styles.headerSide, styles.headerSideRight]}>
                            {birthDetails ? (
                                <NativeSelectorChip
                                    birthData={birthDetails}
                                    onPress={() => navigation.navigate('SelectNative', { returnTo: 'KP' })}
                                    maxLength={7}
                                    showIcon={false}
                                    style={{ backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }}
                                    textStyle={{ color: colors.textInverse }}
                                    iconColor={colors.textInverseMuted}
                                />
                            ) : null}
                        </View>
                    </View>
                </SafeAreaView>

                <SafeAreaView edges={['bottom']} style={styles.safeArea}>
                    <Animated.View style={[styles.content, { opacity: fadeAnim }]}>
                        <View style={[styles.heroCard, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
                            <View style={[styles.heroOrbit, styles.heroOrbitLarge, { borderColor: colors.cosmicLine }]} />
                            <View style={[styles.heroOrbit, styles.heroOrbitSmall, { borderColor: colors.cosmicLine }]} />
                            <Text style={[styles.heroEyebrow, { color: colors.accent }]}>PRECISION DESK</Text>
                            <Text style={[styles.heroTitle, { color: colors.textInverse }]}>Read the promise. Then time it.</Text>
                            <Text style={[styles.heroCopy, { color: colors.textInverseMuted }]}>Natal significators, ruling planets and dasha gates brought into one coherent KP workspace.</Text>
                        </View>

                        <View style={[styles.tabContainer, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabScrollContent}>
                                {tabs.map((tab) => {
                                    const active = activeTab === tab.id;
                                    return (
                                        <TouchableOpacity
                                            key={tab.id}
                                            onPress={() => {
                                                if (tab.id === 'results' && activeTab !== 'results') setSigMoment(new Date());
                                                setActiveTab(tab.id);
                                            }}
                                            style={[
                                                styles.tab,
                                                {
                                                    backgroundColor: active ? colors.selectionControl : 'transparent',
                                                    borderColor: active ? colors.selectionBorder : 'transparent',
                                                },
                                            ]}
                                        >
                                            <Text numberOfLines={1} style={[styles.tabText, { color: active ? colors.selectionText : colors.textSecondary }]}>
                                                {tab.label}
                                            </Text>
                                        </TouchableOpacity>
                                    );
                                })}
                            </ScrollView>
                        </View>

                        <View style={[styles.contentCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                            {renderContent()}

                            {activeTab !== 'results' ? (
                                <View style={[styles.legend, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                                    <Text style={[styles.legendTitle, { color: colors.text }]}>Reading the table</Text>
                                    <Text style={[styles.legendText, { color: colors.textSecondary }]}>SL Sign Lord  ·  NL Nakshatra Lord  ·  SB Sub Lord  ·  SS Sub-Sub Lord  ·  Pd Pada</Text>
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
        paddingVertical: 11,
        borderBottomWidth: StyleSheet.hairlineWidth,
        minHeight: 74,
    },
    backButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 1,
    },
    headerTitle: {
        ...typographyTokens.display,
        fontSize: 25,
        lineHeight: 28,
    },
    headerEyebrow: {
        ...typographyTokens.eyebrow,
        fontSize: 9,
        letterSpacing: 1.5,
    },
    headerCenter: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        paddingHorizontal: 8,
    },
    headerSide: {
        width: 84,
        alignItems: 'flex-start',
    },
    headerSideRight: {
        alignItems: 'flex-end',
    },
    content: {
        flex: 1,
        paddingHorizontal: 14,
        paddingTop: 14,
        paddingBottom: 10,
    },
    heroCard: {
        borderWidth: 1,
        borderRadius: 22,
        paddingHorizontal: 18,
        paddingVertical: 16,
        marginBottom: 12,
        minHeight: 130,
        overflow: 'hidden',
    },
    heroEyebrow: {
        ...typographyTokens.eyebrow,
        marginBottom: 8,
    },
    heroTitle: {
        ...typographyTokens.display,
        fontSize: 25,
        lineHeight: 29,
        maxWidth: '82%',
        marginBottom: 7,
    },
    heroCopy: {
        fontSize: 13,
        lineHeight: 19,
        fontWeight: '500',
        maxWidth: '88%',
    },
    heroOrbit: {
        position: 'absolute',
        borderWidth: 1,
        borderRadius: 999,
    },
    heroOrbitLarge: {
        width: 138,
        height: 138,
        right: -54,
        top: -48,
    },
    heroOrbitSmall: {
        width: 88,
        height: 88,
        right: -21,
        top: -26,
    },
    tabContainer: {
        marginBottom: 10,
        borderWidth: 1,
        borderRadius: 16,
        padding: 4,
    },
    tabScrollContent: {
        gap: 4,
        paddingRight: 4,
    },
    tab: {
        borderRadius: 12,
        flexShrink: 0,
        paddingVertical: 10,
        paddingHorizontal: 13,
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
    },
    tabText: {
        fontSize: 12,
        fontWeight: '700',
    },
    contentCard: {
        flex: 1,
        borderRadius: 22,
        padding: 14,
        borderWidth: 1,
        overflow: 'hidden',
    },
    sigModeBar: {
        flexDirection: 'row',
        gap: 8,
        padding: 4,
        borderRadius: 12,
        marginBottom: 10,
        borderWidth: 1,
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
    fructSubjectHead: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: 10,
    },
    fructSubjectIcon: {
        width: 28,
        height: 28,
        borderRadius: 14,
        alignItems: 'center',
        justifyContent: 'center',
    },
    fructSubjectTitle: {
        flex: 1,
        fontSize: 15,
        fontWeight: '800',
        letterSpacing: -0.2,
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
        borderRadius: 14,
        overflow: 'hidden',
    },
    tableRow: {
        flexDirection: 'row',
        paddingVertical: 12,
        borderBottomWidth: 1,
    },
    tableHeadingRow: {
        paddingVertical: 11,
    },
    tableHeader: {
        fontSize: 12,
        fontWeight: '800',
        paddingHorizontal: 8,
    },
    tableCell: {
        fontSize: 12,
        paddingHorizontal: 8,
        fontWeight: '600',
    },
    significatorCard: {
        padding: 16,
        borderRadius: 16,
        marginBottom: 12,
        borderWidth: 1,
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
        padding: 14,
        borderRadius: 16,
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
        paddingBottom: 12,
    },
    fourStepCard: {
        borderWidth: 1,
        borderRadius: 18,
        padding: 14,
        marginBottom: 12,
    },
    planetIconCircle: {
        width: 36,
        height: 36,
        borderRadius: 18,
        justifyContent: 'center',
        alignItems: 'center',
    },
    planetIconText: {
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
        fontSize: 11,
        fontWeight: '600',
    },
    dayLordValue: {
        fontSize: 14,
        fontWeight: '800',
    },
    sectionHeading: {
        marginBottom: 14,
    },
    sectionEyebrow: {
        ...typographyTokens.eyebrow,
        marginBottom: 5,
    },
    sectionTitle: {
        ...typographyTokens.sectionTitle,
        marginBottom: 4,
    },
    sectionCopy: {
        fontSize: 13,
        lineHeight: 19,
        fontWeight: '500',
    },
});

export default KPScreen;
