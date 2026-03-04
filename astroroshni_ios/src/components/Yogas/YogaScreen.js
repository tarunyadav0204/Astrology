import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, TouchableOpacity, Animated } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { yogaAPI } from '../../services/api';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const YogaScreen = () => {
    const navigation = useNavigation();
    const { t } = useTranslation();
    const { theme, colors } = useTheme();
    const isClassic = theme === 'classic';
    const [yogas, setYogas] = useState(null);
    const [loading, setLoading] = useState(true);
    const [currentNative, setCurrentNative] = useState(null);
    const [expandedCategories, setExpandedCategories] = useState(new Set());
    const [initialized, setInitialized] = useState(false);
    const fadeAnim = useRef(new Animated.Value(0)).current;

    useFocusEffect(
        React.useCallback(() => {
            loadInitialNative();
        }, [])
    );

    useEffect(() => {
        Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
        }).start();
    }, []);

    const loadInitialNative = async () => {
        try {
            let birthData = await storage.getBirthDetails();
            if (!birthData) {
                const profiles = await storage.getBirthProfiles();
                if (profiles?.length) birthData = profiles.find(p => p.relation === 'self') || profiles[0];
            }
            if (!birthData?.name) {
                navigation.replace('BirthProfileIntro', { returnTo: 'Yogas' });
                return;
            }
            if (!currentNative || currentNative.id !== birthData.id) {
                setCurrentNative(birthData);
                fetchYogas(birthData);
            }
        } catch (error) {
            console.error('Error loading initial native:', error);
            setLoading(false);
        }
    };
    
    useEffect(() => {
        // Expand all categories by default when yogas load (only once)
        if (yogas && !initialized) {
            const allCategories = new Set();
            Object.keys(yogas).forEach(category => {
                if (category === 'nabhasa_yogas' || category === 'parivartana_yogas') {
                    Object.keys(yogas[category]).forEach(subCategory => {
                        allCategories.add(`${category}_${subCategory}`);
                    });
                } else {
                    allCategories.add(category);
                }
            });
            setExpandedCategories(allCategories);
            setInitialized(true);
        }
    }, [yogas, initialized]);

    const fetchYogas = async (birthData) => {
        try {
            setLoading(true);
            if (birthData) {
                const response = await yogaAPI.getYogas(birthData);
                if (response.data && response.data.status === 'success') {
                    setYogas(response.data.yogas);
                }
            }
        } catch (error) {
            console.error('Error fetching yogas:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleCategory = (category) => {
        setExpandedCategories(prev => {
            const newSet = new Set(prev);
            if (newSet.has(category)) {
                newSet.delete(category);
            } else {
                newSet.add(category);
            }
            return newSet;
        });
    };

    const getStrengthColor = (strength) => {
        switch(strength?.toLowerCase()) {
            case 'high': return '#22c55e';
            case 'medium': return '#f59e0b';
            case 'low': return '#ef4444';
            default: return colors.text;
        }
    };

    const getCategoryIcon = (category) => {
        // Map category IDs to relevant icons
        const icons = {
            'raj_yogas': '👑',
            'dhana_yogas': '💰',
            'panch_mahapurusha_yogas': '💎',
            'nabhasa_yogas': '🌌',
            'parivartana_yogas': '🔄',
            'major_doshas': '⚠️',
            'chandra_yogas': '🌙',
            'surya_yogas': '☀️',
            'neecha_bhanga_yogas': '📈',
            'gaja_kesari_yogas': '🐘',
            'amala_yogas': '🌿',
            'viparita_raja_yogas': '⚡',
            'dharma_karma_yogas': '🏛️',
            'career_specific_yogas': '💼',
            'health_yogas': '🏥',
            'education_yogas': '🎓',
            'marriage_yogas': '💕',
            'sankhya_yogas': '🔢',
            'akriti_yogas': '📐',
            'ashraya_yogas': '🏠',
            'maha_yogas': '🌟',
            'dainya_yogas': '📉',
            'khala_yogas': '🔥',
        };
        
        // Handle subcategories or direct matches
        if (icons[category]) return icons[category];
        
        // Fallback for subcategories like nabhasa_yogas_dal_yogas
        const baseCategory = category.split('_').slice(0, 2).join('_');
        if (icons[baseCategory]) return icons[baseCategory];
        
        const firstPart = category.split('_')[0];
        if (icons[firstPart]) return icons[firstPart];

        return '✨'; // Default symbol
    };

    const getCategoryGradient = (category) => {
        // Sophisticated celestial gradients
        const gradients = {
            'raj_yogas': ['#9a3412', '#c2410c'], // Deep Burnt Orange
            'dhana_yogas': ['#065f46', '#059669'], // Deep Emerald
            'panch_mahapurusha_yogas': ['#92400e', '#d97706'], // Deep Amber/Gold
            'nabhasa_yogas': ['#1e40af', '#3b82f6'], // Deep Royal Blue
            'parivartana_yogas': ['#5b21b6', '#8b5cf6'], // Deep Violet
            'major_doshas': ['#7f1d1d', '#b91c1c'], // Deep Red
            'chandra_yogas': ['#1e3a8a', '#3b82f6'], // Blue
            'surya_yogas': ['#92400e', '#f59e0b'], // Gold
            'marriage_yogas': ['#831843', '#db2777'], // Pink/Rose
            'health_yogas': ['#064e3b', '#10b981'], // Teal
            'career_specific_yogas': ['#312e81', '#6366f1'], // Indigo
        };
        
        if (gradients[category]) return gradients[category];
        
        // Match by base category
        const baseCategory = category.split('_').slice(0, 2).join('_');
        if (gradients[baseCategory]) return gradients[baseCategory];

        return gradients['raj_yogas'];
    };

    const renderYogaCard = (yoga, index) => (
        <Animated.View 
            key={index}
            style={[styles.yogaCard, { opacity: fadeAnim }]}
        >
            <LinearGradient
                colors={isClassic
                    ? [colors.cardBackground, colors.cardBackground]
                    : (theme === 'dark'
                        ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']
                        : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)'])}
                style={styles.yogaCardGradient}
            >
                <View style={styles.yogaHeader}>
                    <Text style={[styles.yogaName, { color: colors.text }]}>{yoga.name}</Text>
                    {yoga.strength && (
                        <View style={[styles.strengthBadge, { backgroundColor: getStrengthColor(yoga.strength) + '20', borderColor: getStrengthColor(yoga.strength) }]}>
                            <Text style={[styles.strengthText, { color: getStrengthColor(yoga.strength) }]}>
                                {yoga.strength}
                            </Text>
                        </View>
                    )}
                </View>
                
                <Text style={[styles.yogaDescription, { color: colors.textSecondary }]}>
                    {yoga.description}
                </Text>
                
                {yoga.planets && yoga.planets.length > 0 && (
                    <View style={styles.planetsContainer}>
                        <Text style={[styles.planetsLabel, { color: colors.textSecondary }]}>Planets:</Text>
                        <View style={styles.planetChips}>
                            {yoga.planets.map((planet, idx) => (
                                <View key={idx} style={[styles.planetChip, { backgroundColor: colors.primary + '20' }]}>
                                    <Text style={[styles.planetText, { color: colors.primary }]}>{planet}</Text>
                                </View>
                            ))}
                        </View>
                    </View>
                )}
                
                {yoga.houses && yoga.houses.length > 0 && (
                    <View style={styles.housesContainer}>
                        <Text style={[styles.housesLabel, { color: colors.textSecondary }]}>Houses:</Text>
                        <Text style={[styles.housesText, { color: colors.text }]}>
                            {yoga.houses.join(', ')}
                        </Text>
                    </View>
                )}
            </LinearGradient>
        </Animated.View>
    );

    const renderCategory = (category, yogaList) => {
        const isExpanded = expandedCategories.has(category);
        const yogaCount = Array.isArray(yogaList) ? yogaList.length : 0;

        if (yogaCount === 0) return null;

        return (
            <View key={category} style={[styles.categoryCard, isClassic && { borderColor: colors.cardBorder, shadowOpacity: 0.12 }]}>
                <TouchableOpacity 
                    onPress={() => toggleCategory(category)}
                    activeOpacity={0.8}
                >
                    <LinearGradient
                        colors={isClassic ? [colors.cardBackground, colors.cardBackground] : getCategoryGradient(category)}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={[styles.categoryHeader, isClassic && { borderBottomColor: 'rgba(0, 0, 0, 0.08)' }]}
                    >
                        <View style={styles.categoryTitleRow}>
                            <Text style={styles.categoryIcon}>{getCategoryIcon(category)}</Text>
                            <View style={styles.categoryTitleContainer}>
                                <Text style={[styles.categoryTitle, isClassic && { color: colors.text }]}>{t('yogas.' + category, category.replace(/_/g, ' ').toUpperCase())}</Text>
                                <Text style={[styles.categoryCount, isClassic && { color: colors.textSecondary }]}>{yogaCount} Yoga{yogaCount > 1 ? 's' : ''}</Text>
                            </View>
                        </View>
                        <Ionicons 
                            name={isExpanded ? 'chevron-up' : 'chevron-down'} 
                            size={24} 
                            color={isClassic ? colors.textSecondary : '#fff'} 
                        />
                    </LinearGradient>
                </TouchableOpacity>
                
                {isExpanded && (
                    <View style={[styles.yogasListContainer, { backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.9)' }]}>
                        {yogaList.map((yoga, index) => (
                            <View key={index} style={styles.yogaItem}>
                                {renderYogaCard(yoga, index)}
                                {index < yogaList.length - 1 && (
                                    <View style={[styles.yogaDivider, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)' }]} />
                                )}
                            </View>
                        ))}
                    </View>
                )}
            </View>
        );
    };

    return (
        <View style={{ flex: 1 }}>
            <LinearGradient
                colors={isClassic
                    ? [colors.background, colors.backgroundSecondary, colors.backgroundSecondary, colors.background]
                    : (theme === 'dark'
                        ? ['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']
                        : ['#fefcfb', '#fef7f0', '#fed7d7', '#fefcfb'])}
                style={styles.container}
            >
                <SafeAreaView style={styles.safeArea}>
                    <View style={styles.header}>
                        <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.backButton, isClassic && { backgroundColor: 'rgba(0, 0, 0, 0.06)' }] }>
                            <Ionicons name="arrow-back" size={24} color={colors.text} />
                        </TouchableOpacity>
                        <Text style={[styles.headerTitle, { color: colors.text }]}>🌟 Yogas</Text>
                        <NativeSelectorChip 
                            birthData={currentNative}
                            onPress={() => navigation.navigate('SelectNative', { returnTo: 'Yogas' })}
                            maxLength={10}
                        />
                    </View>

                    <ScrollView 
                        style={styles.scrollView}
                        contentContainerStyle={styles.scrollContent}
                        showsVerticalScrollIndicator={false}
                    >
                        <Animated.View style={{ opacity: fadeAnim }}>
                            <View style={styles.introCard}>
                                <LinearGradient
                                    colors={isClassic
                                        ? [colors.cardBackground, colors.cardBackground]
                                        : (theme === 'dark'
                                            ? ['rgba(255, 215, 0, 0.15)', 'rgba(255, 107, 53, 0.1)']
                                            : ['rgba(249, 115, 22, 0.15)', 'rgba(236, 72, 153, 0.1)'])}
                                    style={[styles.introGradient, isClassic && { borderColor: colors.cardBorder }]}
                                >
                                    <Text style={[styles.introTitle, { color: colors.text }]}>
                                        Your Astrological Yogas
                                    </Text>
                                    <Text style={[styles.introText, { color: colors.textSecondary }]}>
                                        Yogas are special planetary combinations that shape your destiny and life path
                                    </Text>
                                </LinearGradient>
                            </View>

                            {yogas && Object.keys(yogas).map((category) => {
                                if (category === 'nabhasa_yogas' || category === 'parivartana_yogas') {
                                    return Object.keys(yogas[category]).map((subCategory) => 
                                        renderCategory(`${category}_${subCategory}`, yogas[category][subCategory])
                                    );
                                }
                                return renderCategory(category, yogas[category]);
                            })}
                        </Animated.View>
                    </ScrollView>
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
        gap: 8,
    },
    backButton: {
        width: 36,
        height: 36,
        borderRadius: 18,
        backgroundColor: 'rgba(255, 255, 255, 0.15)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    headerTitle: {
        fontSize: 20,
        fontWeight: '800',
        flex: 1,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: 16,
        paddingBottom: 32,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingGradient: {
        flex: 1,
        width: '100%',
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        marginTop: 16,
        fontSize: 16,
        fontWeight: '600',
    },
    introCard: {
        marginBottom: 24,
        borderRadius: 20,
        overflow: 'hidden',
    },
    introGradient: {
        padding: 24,
        borderWidth: 1,
        borderColor: 'rgba(255, 215, 0, 0.3)',
        borderRadius: 20,
    },
    introTitle: {
        fontSize: 22,
        fontWeight: '700',
        marginBottom: 8,
        textAlign: 'center',
    },
    introText: {
        fontSize: 14,
        lineHeight: 20,
        textAlign: 'center',
    },
    categoryCard: {
        marginBottom: 16,
        borderRadius: 16,
        overflow: 'hidden',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 6,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.1)',
    },
    categoryCardGradient: {
        borderRadius: 16,
    },
    categoryHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 18,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255, 255, 255, 0.1)',
    },
    categoryTitleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
    },
    categoryIcon: {
        fontSize: 32,
        marginRight: 16,
    },
    categoryTitleContainer: {
        flex: 1,
    },
    categoryTitle: {
        fontSize: 16,
        fontWeight: '800',
        color: '#fff',
        marginBottom: 2,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
    },
    categoryCount: {
        fontSize: 13,
        color: 'rgba(255, 255, 255, 0.9)',
        fontWeight: '600',
    },
    yogasListContainer: {
        padding: 20,
    },
    yogaItem: {
        marginTop: 16,
    },
    yogaItemHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 8,
    },
    yogaDivider: {
        height: 1.5,
        marginTop: 16,
    },
    yogaName: {
        fontSize: 17,
        fontWeight: '700',
        flex: 1,
        marginRight: 8,
    },
    strengthBadge: {
        paddingHorizontal: 12,
        paddingVertical: 4,
        borderRadius: 12,
        borderWidth: 1.5,
    },
    strengthText: {
        fontSize: 12,
        fontWeight: '700',
        textTransform: 'uppercase',
    },
    yogaDescription: {
        fontSize: 14,
        lineHeight: 20,
        marginBottom: 12,
    },
    planetsContainer: {
        marginTop: 8,
    },
    planetsLabel: {
        fontSize: 12,
        fontWeight: '600',
        marginBottom: 6,
    },
    planetChips: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 6,
    },
    planetChip: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
    },
    planetText: {
        fontSize: 12,
        fontWeight: '600',
    },
    housesContainer: {
        marginTop: 8,
        flexDirection: 'row',
        alignItems: 'center',
    },
    housesLabel: {
        fontSize: 12,
        fontWeight: '600',
        marginRight: 6,
    },
    housesText: {
        fontSize: 12,
        fontWeight: '500',
    },
});

export default YogaScreen;
