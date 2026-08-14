import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing, Image, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import NorthIndianChart from './Chart/NorthIndianChart';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { stopAnimatedValue, stopAnimationLoop } from '../utils/safeAnimated';
import { DISPLAY_FONT_FAMILY } from '../theme/tokens';

const HOUSE_DOMAINS = {
    1: 'SELF & IDENTITY',
    2: 'WEALTH & FAMILY',
    3: 'COURAGE & COMMUNICATION',
    4: 'HOME & INNER LIFE',
    5: 'CREATIVITY & CHILDREN',
    6: 'WORK & WELLBEING',
    7: 'PARTNERSHIPS',
    8: 'CHANGE & SHARED RESOURCES',
    9: 'WISDOM & PURPOSE',
    10: 'CAREER & PUBLIC LIFE',
    11: 'GAINS & COMMUNITY',
    12: 'REST & RELEASE',
};

const PLANET_NAMES = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

function getInsightPlanets(chartData, houseNumber) {
    const houseSign = Number(chartData?.houses?.[houseNumber - 1]?.sign);
    const planets = chartData?.planets;
    if (!Number.isFinite(houseSign) || !planets || typeof planets !== 'object') return [];
    return PLANET_NAMES.filter((name) => Number(planets[name]?.sign) === houseSign);
}

const LoadingBubble = ({
    chartInsights,
    chartData,
    expectedWaitSeconds = 80,
    startedAt = null,
}) => {
    const { t } = useTranslation();
    const { theme, colors } = useTheme();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [fadeAnim] = useState(new Animated.Value(1));
    const glowAnim = useRef(new Animated.Value(0)).current;
    const pulseAnim = useRef(new Animated.Value(1)).current;
    const shimmerAnim = useRef(new Animated.Value(0)).current;
    const chartContainerRef = useRef(null);
    const mountedRef = useRef(true);
    const insightFadeHandleRef = useRef(null);
    const mountMsRef = useRef(Date.now());
    const waitStartMsRef = useRef(null);
    const [remainingSeconds, setRemainingSeconds] = useState(Math.max(0, Number(expectedWaitSeconds) || 0));
    const [zodiacIndex, setZodiacIndex] = useState(0);
    const zodiacSymbols = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];

    const hasChartInsights = chartInsights && Array.isArray(chartInsights) && chartInsights.length > 0;
    const hasChartData = chartData && (chartData.planets || chartData.houses);
    const chartInsightsCount = Array.isArray(chartInsights) ? chartInsights.length : 0;

    useEffect(() => {
        if (!hasChartInsights) {
            if (currentIndex !== 0) {
                setCurrentIndex(0);
            }
            return;
        }
        if (currentIndex >= chartInsightsCount) {
            setCurrentIndex(0);
        }
    }, [hasChartInsights, chartInsightsCount, currentIndex]);

    useEffect(() => {
        const total = Math.max(0, Number(expectedWaitSeconds) || 0);
        if (waitStartMsRef.current == null) {
            const mountMs = mountMsRef.current;
            let startMs = mountMs;
            if (startedAt) {
                const startedMillis = new Date(startedAt).getTime();
                if (Number.isFinite(startedMillis) && startedMillis > 0 && startedMillis >= mountMs - 20_000) {
                    startMs = startedMillis;
                }
            }
            waitStartMsRef.current = startMs;
        }
        const elapsedSeconds = Math.max(
            0,
            Math.floor((Date.now() - waitStartMsRef.current) / 1000)
        );
        setRemainingSeconds(Math.max(0, total - elapsedSeconds));
    }, [expectedWaitSeconds, startedAt]);

    // Single interval for the whole wait — do not recreate on every remainingSeconds tick.
    useEffect(() => {
        const timer = setInterval(() => {
            setRemainingSeconds((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    useEffect(() => {
        if (remainingSeconds > 0) return;
        const zodiacTimer = setInterval(() => {
            setZodiacIndex((prev) => (prev + 1) % zodiacSymbols.length);
        }, 800);
        return () => clearInterval(zodiacTimer);
    }, [remainingSeconds, zodiacSymbols.length]);

    useEffect(() => {
        mountedRef.current = true;
        return () => {
            mountedRef.current = false;
        };
    }, []);

    useEffect(() => {
        const loops = [];
        let interval;
        const stopInsightFade = () => {
            insightFadeHandleRef.current?.cancel?.();
            insightFadeHandleRef.current = null;
        };

        if (hasChartInsights) {
            const glowLoop = Animated.loop(
                Animated.sequence([
                    Animated.timing(glowAnim, {
                        toValue: 1,
                        duration: 1000,
                        easing: Easing.inOut(Easing.ease),
                        useNativeDriver: true,
                    }),
                    Animated.timing(glowAnim, {
                        toValue: 0,
                        duration: 1000,
                        easing: Easing.inOut(Easing.ease),
                        useNativeDriver: true,
                    }),
                ])
            );
            glowLoop.start();
            loops.push(glowLoop);

            interval = setInterval(() => {
                if (!mountedRef.current) return;
                stopInsightFade();
                const fadeOut = Animated.timing(fadeAnim, {
                    toValue: 0,
                    duration: 250,
                    useNativeDriver: true,
                });
                fadeOut.start(({ finished }) => {
                    if (!mountedRef.current || !finished) return;
                    setCurrentIndex((prevIndex) => (prevIndex + 1) % chartInsightsCount);
                    const fadeIn = Animated.timing(fadeAnim, {
                        toValue: 1,
                        duration: 250,
                        useNativeDriver: true,
                    });
                    insightFadeHandleRef.current = {
                        cancel: () => stopAnimatedValue(fadeAnim, 1),
                    };
                    fadeIn.start();
                });
            }, 12000);
        } else {
            const pulseLoop = Animated.loop(
                Animated.sequence([
                    Animated.timing(pulseAnim, {
                        toValue: 1.1,
                        duration: 1500,
                        easing: Easing.inOut(Easing.ease),
                        useNativeDriver: true,
                    }),
                    Animated.timing(pulseAnim, {
                        toValue: 1,
                        duration: 1500,
                        easing: Easing.inOut(Easing.ease),
                        useNativeDriver: true,
                    }),
                ])
            );
            pulseLoop.start();
            loops.push(pulseLoop);

            const shimmerLoop = Animated.loop(
                Animated.timing(shimmerAnim, {
                    toValue: 1,
                    duration: 2000,
                    easing: Easing.linear,
                    useNativeDriver: true,
                })
            );
            shimmerLoop.start();
            loops.push(shimmerLoop);
        }
        return () => {
            if (interval) clearInterval(interval);
            stopInsightFade();
            loops.forEach((loop) => stopAnimationLoop(loop));
            stopAnimatedValue(glowAnim, 0);
            stopAnimatedValue(pulseAnim, 1);
            stopAnimatedValue(shimmerAnim, 0);
            stopAnimatedValue(fadeAnim, 1);
        };
    }, [hasChartInsights, chartInsightsCount]);

    const isDarkMode = theme === 'dark';
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    const timerText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    const timerProgress = Math.max(0, Math.min(1, remainingSeconds / Math.max(1, Number(expectedWaitSeconds) || 1)));
    const trafficNotice = remainingSeconds === 0
        ? "High traffic right now - your study is still being prepared and may take a little longer than usual."
        : null;
    const showZodiacLoop = remainingSeconds === 0;

    if (hasChartInsights) {
        const currentInsight = chartInsights[currentIndex];
        
        if (!currentInsight || !currentInsight.message) {
            return (
                <View style={styles.container}>
                    <LinearGradient
                        colors={[colors.cosmicSurface, colors.cosmicRaised]}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={[styles.welcomeBubble, { borderColor: colors.cosmicLine, backgroundColor: colors.cosmicSurface }]}
                    >
                        <Text
                          style={[
                            styles.welcomeTitle,
                            { color: colors.accent },
                            isDarkMode && {
                              textShadowColor: 'rgba(255, 107, 53, 0.3)',
                              textShadowOffset: { width: 0, height: 2 },
                              textShadowRadius: 8,
                            },
                          ]}
                        >
                          {t('premiumUi.chat.readingChart')}
                        </Text>
                        <Text style={[styles.welcomeSubtext, { color: colors.textInverseMuted }]}>{t('chat.preparingInsights', 'Preparing your chart insights...')}</Text>
                    </LinearGradient>
                </View>
            );
        }
        
        const insightHouse = Math.max(1, Math.min(12, Number(currentInsight.house_number) || 1));
        const insightPlanets = getInsightPlanets(chartData, insightHouse);
        const focusDetail = insightPlanets.length > 0
            ? `${insightPlanets.join(' · ')} ${insightPlanets.length === 1 ? 'is' : 'are'} active here`
            : 'This area is highlighted in the chart';

        return (
            <View style={styles.container} ref={chartContainerRef}>
                <LinearGradient
                    colors={[colors.cosmicSurface, colors.cosmicRaised]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={[styles.chartBubble, { borderColor: colors.cosmicLine, backgroundColor: colors.cosmicSurface }]}
                >
                    <Text
                      style={[
                        styles.chartTitle,
                        { color: colors.accent },
                        isDarkMode && {
                          textShadowColor: 'rgba(255, 107, 53, 0.3)',
                          textShadowOffset: { width: 0, height: 2 },
                          textShadowRadius: 8,
                        },
                      ]}
                    >
                      {t('premiumUi.chat.synthesizing')}
                    </Text>
                    <View style={[styles.timerCard, { backgroundColor: colors.cosmicGlow, borderColor: colors.cosmicLine }]}>
                        <View style={styles.timerTopRow}>
                            <Text style={[styles.timerTitle, { color: colors.textInverseMuted }]}>{t('premiumUi.chat.timeRemaining')}</Text>
                        </View>
                        <View style={styles.timerCountdownWrap}>
                            {showZodiacLoop ? (
                                <Text style={[styles.zodiacLoopText, { color: colors.textInverse }]}>{zodiacSymbols[zodiacIndex]}</Text>
                            ) : (
                                <Text style={[styles.timerText, { color: colors.textInverse }]}>{timerText}</Text>
                            )}
                        </View>
                        <View style={styles.timerProgressTrack}>
                            <LinearGradient
                                colors={[colors.accent, colors.primary]}
                                start={{ x: 0, y: 0.5 }}
                                end={{ x: 1, y: 0.5 }}
                                style={[styles.timerProgressFill, { width: `${Math.max(6, timerProgress * 100)}%` }]}
                            />
                        </View>
                        {!!trafficNotice && (
                            <Text style={styles.timerTrafficNotice}>{trafficNotice}</Text>
                        )}
                    </View>
                    
                    <Animated.View style={[styles.insightFocusHeader, { opacity: fadeAnim }]}>
                        <Text style={[styles.insightFocusEyebrow, { color: colors.accent }]}>{t('premiumUi.chat.currentInsight')}</Text>
                        <Text style={[styles.insightFocusTitle, { color: colors.textInverse }]}>
                            {t('premiumUi.chat.houseNumber', { number: insightHouse })} · {t(`premiumUi.chat.houseDomains.${insightHouse}`)}
                        </Text>
                        <Text style={[styles.insightFocusDetail, { color: colors.textInverseMuted }]}>{focusDetail}</Text>
                    </Animated.View>

                    {hasChartData && (
                        <Animated.View style={[styles.chartContainer, { opacity: fadeAnim, borderColor: colors.cosmicLine, backgroundColor: colors.cosmicSurface }]}>
                            <NorthIndianChart 
                                chartData={chartData}
                                showDegreeNakshatra={false}
                                highlightHouse={insightHouse}
                                highlightColor={colors.accent}
                                highlightFill={colors.cosmicGlow}
                                hideInstructions={true}
                                cosmicTheme
                                onDarkSurface
                                gridLineColor={colors.textInverseMuted}
                                gridLineWidth={1.5}
                            />
                        </Animated.View>
                    )}

                    {hasChartData && (
                        <View style={styles.chartLegend}>
                            <View style={[styles.chartLegendMark, { borderColor: colors.accent }]} />
                            <Text style={[styles.chartLegendText, { color: colors.textInverseMuted }]}>{t('premiumUi.chat.highlightLegend')}</Text>
                        </View>
                    )}
                    
                    <View style={[styles.insightTextBlock, { backgroundColor: colors.cosmicGlow, borderColor: colors.cosmicLine }]}>
                        <Animated.Text style={[styles.insightText, { color: colors.textInverse, opacity: fadeAnim }]}>
                            {currentInsight.message}
                        </Animated.Text>
                    </View>
                </LinearGradient>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <LinearGradient
                colors={[colors.cosmicSurface, colors.cosmicRaised]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[styles.welcomeBubble, { borderColor: colors.cosmicLine, backgroundColor: colors.cosmicSurface }]}
            >
                <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
                    <View style={styles.logoContainer}>
                        <Image 
                            source={require('../../assets/logo.png')}
                            style={styles.logoImage}
                            resizeMode="contain"
                        />
                    </View>
                </Animated.View>
                
                <Text
                  style={[
                    styles.welcomeTitle,
                    { color: colors.accent },
                    theme === 'dark' && {
                      textShadowColor: 'rgba(255, 107, 53, 0.3)',
                      textShadowOffset: { width: 0, height: 2 },
                      textShadowRadius: 8,
                    },
                  ]}
                >
                  {t('premiumUi.chat.synthesizing')}
                </Text>
                <View style={[styles.timerCard, { backgroundColor: colors.cosmicGlow, borderColor: colors.cosmicLine }]}>
                    <View style={styles.timerTopRow}>
                        <Text style={[styles.timerTitle, { color: colors.textInverseMuted }]}>{t('premiumUi.chat.timeRemaining')}</Text>
                    </View>
                    <View style={styles.timerCountdownWrap}>
                        {showZodiacLoop ? (
                            <Text style={[styles.zodiacLoopText, { color: colors.textInverse }]}>{zodiacSymbols[zodiacIndex]}</Text>
                        ) : (
                            <Text style={[styles.timerText, { color: colors.textInverse }]}>{timerText}</Text>
                        )}
                    </View>
                    <View style={styles.timerProgressTrack}>
                        <LinearGradient
                            colors={[colors.accent, colors.primary]}
                            start={{ x: 0, y: 0.5 }}
                            end={{ x: 1, y: 0.5 }}
                            style={[styles.timerProgressFill, { width: `${Math.max(6, timerProgress * 100)}%` }]}
                        />
                    </View>
                    {!!trafficNotice && (
                        <Text style={styles.timerTrafficNotice}>{trafficNotice}</Text>
                    )}
                </View>
                
                <View style={styles.divider}>
                    <View style={styles.dividerLine} />
                    <Text style={styles.dividerStar}>✨</Text>
                    <View style={styles.dividerLine} />
                </View>
                
                <Text style={[styles.welcomeMessage, { color: colors.textInverse }]}>
                    {t('chat.thankYou', 'Your question is now being read against the full chart.')}
                </Text>
                
                <Text style={[styles.welcomeSubtext, { color: colors.textInverseMuted }]}>
                    {t('chat.deeplyAnalyzing', 'Parashari, Nadi, Jaimini and KP signals are being combined into one clear answer.')}
                </Text>
                
                <View style={styles.cosmicDots}>
                    <Animated.View style={[styles.dot, { 
                        opacity: shimmerAnim.interpolate({
                            inputRange: [0, 0.33, 0.66, 1],
                            outputRange: [0.3, 1, 0.3, 0.3]
                        })
                    }]} />
                    <Animated.View style={[styles.dot, { 
                        opacity: shimmerAnim.interpolate({
                            inputRange: [0, 0.33, 0.66, 1],
                            outputRange: [0.3, 0.3, 1, 0.3]
                        })
                    }]} />
                    <Animated.View style={[styles.dot, { 
                        opacity: shimmerAnim.interpolate({
                            inputRange: [0, 0.33, 0.66, 1],
                            outputRange: [0.3, 0.3, 0.3, 1]
                        })
                    }]} />
                </View>
                
                <Text style={styles.chartPreview}>
                    {t('chat.fascinatingInsights', 'Meanwhile, let me show you some fascinating insights about your chart...')}
                </Text>
            </LinearGradient>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        padding: 16,
        alignItems: 'center',
        justifyContent: 'center',
    },
    welcomeBubble: {
        borderRadius: 24,
        padding: 32,
        alignItems: 'center',
        borderWidth: Platform.OS === 'android' ? StyleSheet.hairlineWidth : 2,
        borderColor: 'rgba(255, 215, 0, 0.15)',
        maxWidth: '95%',
        shadowColor: '#ff6b35',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.2,
        shadowRadius: 16,
        elevation: 4,
        // Android Glassmorphism Fix - Use dark tint instead of white
        backgroundColor: Platform.OS === 'android' ? 'rgba(0, 0, 0, 0.4)' : 'transparent',
    },
    welcomeIcon: {
        fontSize: 64,
        marginBottom: 16,
    },
    logoContainer: {
        width: 80,
        height: 80,
        borderRadius: 40,
        marginBottom: 16,
        backgroundColor: 'rgba(255, 107, 53, 0.1)',
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#ff6b35',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 4,
        overflow: 'hidden',
    },
    logoImage: {
        width: 70,
        height: 70,
        borderRadius: 35,
    },
    welcomeTitle: {
        fontFamily: DISPLAY_FONT_FAMILY,
        fontSize: 28,
        fontWeight: '400',
        marginBottom: 16,
    },
    timerCard: {
        width: '100%',
        backgroundColor: 'rgba(255, 255, 255, 0.14)',
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.22)',
        borderRadius: 18,
        paddingHorizontal: 16,
        paddingTop: 12,
        paddingBottom: 14,
        marginBottom: 18,
    },
    timerTopRow: {
        alignItems: 'flex-start',
        marginBottom: 10,
    },
    timerCountdownWrap: {
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 12,
    },
    timerTitle: {
        color: '#ffe9c7',
        fontSize: 13,
        fontWeight: '700',
        letterSpacing: 0.2,
    },
    timerText: {
        color: '#ffffff',
        fontSize: 36,
        fontWeight: '900',
        letterSpacing: 2,
        lineHeight: 40,
        ...(Platform.OS === 'ios' ? { fontVariant: ['tabular-nums'] } : {}),
        textShadowColor: 'rgba(255, 255, 255, 0.35)',
        textShadowOffset: { width: 0, height: 0 },
        textShadowRadius: 10,
    },
    zodiacLoopText: {
        color: '#ffffff',
        fontSize: 44,
        fontWeight: '900',
        lineHeight: 48,
        textShadowColor: 'rgba(255, 255, 255, 0.4)',
        textShadowOffset: { width: 0, height: 0 },
        textShadowRadius: 12,
    },
    timerProgressTrack: {
        width: '100%',
        height: 8,
        borderRadius: 999,
        overflow: 'hidden',
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
    },
    timerProgressFill: {
        height: '100%',
        borderRadius: 999,
    },
    timerTrafficNotice: {
        marginTop: 8,
        color: '#fde68a',
        fontSize: 11,
        lineHeight: 16,
        fontWeight: '600',
    },
    divider: {
        flexDirection: 'row',
        alignItems: 'center',
        marginVertical: 16,
        width: '80%',
    },
    dividerLine: {
        flex: 1,
        height: 1,
        backgroundColor: 'rgba(255, 215, 0, 0.3)',
    },
    dividerStar: {
        fontSize: 16,
        marginHorizontal: 12,
        color: '#ffd700',
    },
    welcomeMessage: {
        fontSize: 16,
        textAlign: 'center',
        marginBottom: 12,
        fontWeight: '600',
        lineHeight: 24,
    },
    welcomeSubtext: {
        fontSize: 14,
        textAlign: 'center',
        marginBottom: 20,
        lineHeight: 22,
        fontStyle: 'italic',
    },
    cosmicDots: {
        flexDirection: 'row',
        gap: 12,
        marginVertical: 16,
    },
    dot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        backgroundColor: '#ff6b35',
    },
    chartPreview: {
        fontSize: 13,
        color: '#ff6b35',
        textAlign: 'center',
        fontWeight: '700',
        marginTop: 8,
    },
    chartBubble: {
        borderRadius: 24,
        padding: 20,
        alignItems: 'center',
        borderWidth: Platform.OS === 'android' ? StyleSheet.hairlineWidth : 2,
        borderColor: 'rgba(255, 215, 0, 0.15)',
        width: '100%',
        maxWidth: 420,
        shadowColor: '#ff6b35',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.2,
        shadowRadius: 16,
        elevation: 4,
        // Android Glassmorphism Fix - Use dark tint instead of white
        backgroundColor: Platform.OS === 'android' ? 'rgba(0, 0, 0, 0.4)' : 'transparent',
    },
    chartTitle: {
        fontFamily: DISPLAY_FONT_FAMILY,
        fontSize: 28,
        fontWeight: '400',
        marginBottom: 16,
    },
    insightFocusHeader: {
        width: '100%',
        marginBottom: 14,
    },
    insightFocusEyebrow: {
        fontSize: 10,
        fontWeight: '800',
        letterSpacing: 1.5,
        marginBottom: 5,
    },
    insightFocusTitle: {
        fontFamily: DISPLAY_FONT_FAMILY,
        fontSize: 20,
        lineHeight: 25,
        fontWeight: '600',
        marginBottom: 4,
    },
    insightFocusDetail: {
        fontSize: 12,
        lineHeight: 17,
        fontWeight: '600',
    },
    chartContainer: {
        width: 276,
        height: 276,
        borderRadius: 18,
        borderWidth: 1,
        padding: 8,
        marginBottom: 10,
        overflow: 'hidden',
    },
    chartLegend: {
        width: '100%',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        marginBottom: 14,
    },
    chartLegendMark: {
        width: 14,
        height: 10,
        borderRadius: 3,
        borderWidth: 2,
    },
    chartLegendText: {
        fontSize: 11,
        fontWeight: '600',
    },
    insightTextBlock: {
        width: '100%',
        justifyContent: 'center',
        borderWidth: 1,
        borderRadius: 18,
        paddingHorizontal: 16,
        paddingVertical: 14,
    },
    insightText: {
        fontSize: 14,
        textAlign: 'left',
        fontWeight: '600',
        lineHeight: 21,
    },
});

export default LoadingBubble;
