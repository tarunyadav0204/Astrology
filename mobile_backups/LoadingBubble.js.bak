import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing, Image, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import NorthIndianChart from './Chart/NorthIndianChart';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';

const LoadingBubble = ({ chartInsights, chartData, scrollViewRef }) => {
    const { t } = useTranslation();
    const { theme, colors } = useTheme();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [fadeAnim] = useState(new Animated.Value(1));
    const glowAnim = useRef(new Animated.Value(0)).current;
    const pulseAnim = useRef(new Animated.Value(1)).current;
    const shimmerAnim = useRef(new Animated.Value(0)).current;
    const chartContainerRef = useRef(null);
    const hasScrolled = useRef(false);

    const hasChartInsights = chartInsights && Array.isArray(chartInsights) && chartInsights.length > 0;

    useEffect(() => {
        if (hasChartInsights && !hasScrolled.current && chartContainerRef.current && scrollViewRef?.current) {
            setTimeout(() => {
                chartContainerRef.current?.measureLayout(
                    scrollViewRef.current,
                    (x, y, width, height) => {
                        scrollViewRef.current?.scrollTo({ y: Math.max(0, y - 100), animated: true });
                        hasScrolled.current = true;
                    },
                    () => {}
                );
            }, 300);
        }
    }, [hasChartInsights]);

    useEffect(() => {
        if (hasChartInsights) {
            Animated.loop(
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
            ).start();
            
            const interval = setInterval(() => {
                Animated.timing(fadeAnim, {
                    toValue: 0,
                    duration: 500,
                    useNativeDriver: true,
                }).start(() => {
                    setCurrentIndex((prevIndex) => (prevIndex + 1) % chartInsights.length);
                    Animated.timing(fadeAnim, {
                        toValue: 1,
                        duration: 500,
                        useNativeDriver: true,
                    }).start();
                });
            }, 10000);
            
            return () => clearInterval(interval);
        } else {
            Animated.loop(
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
            ).start();
            
            Animated.loop(
                Animated.timing(shimmerAnim, {
                    toValue: 1,
                    duration: 2000,
                    easing: Easing.linear,
                    useNativeDriver: true,
                })
            ).start();
        }
    }, [hasChartInsights, chartInsights]);

    const isDarkMode = theme === 'dark';

    if (hasChartInsights && chartData) {
        const currentInsight = chartInsights[currentIndex];
        
        if (!currentInsight || !currentInsight.house_number) {
            return (
                <View style={styles.container}>
                    <LinearGradient
                        colors={Platform.OS === 'android' 
                            ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] 
                            : ['rgba(255, 107, 53, 0.15)', 'rgba(255, 215, 0, 0.1)', 'rgba(255, 107, 53, 0.15)']}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={styles.welcomeBubble}
                    >
                        <Text style={[styles.welcomeTitle, { color: isDarkMode ? '#ffd700' : '#ff6b35' }]}>☀️ AstroRoshni</Text>
                        <Text style={[styles.welcomeSubtext, { color: isDarkMode ? '#fff' : '#1a1a1a' }]}>{t('chat.preparingInsights', 'Preparing your cosmic insights...')}</Text>
                    </LinearGradient>
                </View>
            );
        }
        
        return (
            <View style={styles.container} ref={chartContainerRef}>
                <LinearGradient
                    colors={Platform.OS === 'android' 
                        ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] 
                        : ['rgba(255, 107, 53, 0.15)', 'rgba(255, 215, 0, 0.1)', 'rgba(255, 107, 53, 0.15)']}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={styles.chartBubble}
                >
                    <Text style={[styles.chartTitle, { color: isDarkMode ? '#ffd700' : '#ff6b35' }]}>☀️ AstroRoshni</Text>
                    
                    <Animated.View style={[styles.chartContainer, { opacity: fadeAnim }]}>
                        <NorthIndianChart 
                            chartData={chartData}
                            showDegreeNakshatra={false}
                            highlightHouse={currentInsight.house_number}
                            glowAnimation={glowAnim}
                            hideInstructions={true}
                        />
                    </Animated.View>
                    
                    <Animated.Text style={[styles.insightText, { color: isDarkMode ? '#fff' : '#1a1a1a', opacity: fadeAnim }]}>
                        {currentInsight.message}
                    </Animated.Text>
                </LinearGradient>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <LinearGradient
                colors={Platform.OS === 'android' 
                    ? ['rgba(0, 0, 0, 0.4)', 'rgba(0, 0, 0, 0.2)'] 
                    : ['rgba(255, 107, 53, 0.15)', 'rgba(255, 215, 0, 0.1)', 'rgba(255, 107, 53, 0.15)']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.welcomeBubble}
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
                
                <Text style={[styles.welcomeTitle, { color: theme === 'dark' ? '#ffd700' : '#ff6b35' }]}>AstroRoshni</Text>
                
                <View style={styles.divider}>
                    <View style={styles.dividerLine} />
                    <Text style={styles.dividerStar}>✨</Text>
                    <View style={styles.dividerLine} />
                </View>
                
                <Text style={[styles.welcomeMessage, { color: theme === 'dark' ? '#fff' : '#1a1a1a' }]}>
                    {t('chat.thankYou', 'Thank you for reaching out to AstroRoshni with your question.')}
                </Text>
                
                <Text style={[styles.welcomeSubtext, { color: theme === 'dark' ? 'rgba(255, 255, 255, 0.85)' : '#4b5563' }]}>
                    {t('chat.deeplyAnalyzing', 'I am deeply analyzing your celestial chart to provide you with the most accurate insights. This sacred process takes a moment...')}
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
        fontSize: 28,
        fontWeight: '800',
        marginBottom: 16,
        textShadowColor: 'rgba(255, 107, 53, 0.3)',
        textShadowOffset: { width: 0, height: 2 },
        textShadowRadius: 8,
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
    chartTitle: {
        fontSize: 28,
        fontWeight: '800',
        marginBottom: 20,
        textShadowColor: 'rgba(255, 107, 53, 0.3)',
        textShadowOffset: { width: 0, height: 2 },
        textShadowRadius: 8,
    },
    chartContainer: {
        width: 300,
        height: 300,
        marginBottom: 16,
    },
    insightText: {
        fontSize: 15,
        textAlign: 'center',
        fontWeight: '400',
        fontStyle: 'italic',
        lineHeight: 22,
        paddingHorizontal: 12,
    },
});

export default LoadingBubble;
