import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, TouchableOpacity, Animated } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { yogaAPI } from '../../services/api';

const YogaScreen = ({ navigation }) => {
    const { t } = useTranslation();
    const { theme, colors } = useTheme();
    const [yogas, setYogas] = useState(null);
    const [loading, setLoading] = useState(true);
    const [expandedCategories, setExpandedCategories] = useState(new Set());
    const [initialized, setInitialized] = useState(false);
    const fadeAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        fetchYogas();
        Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
        }).start();
    }, []);
    
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

    const fetchYogas = async () => {
        try {
            const birthData = await storage.getBirthDetails();
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
        const icons = {
            'raj_yogas': '👑',
            'dhana_yogas': '💰',
            'panch_mahapurusha_yogas': '⭐',
            'nabhasa_yogas': '🌌',
            'parivartana_yogas': '🔄',
        };
        return icons[category] || '✨';
    };

    const getCategoryGradient = (category) => {
        const gradients = {
            'raj_yogas': ['#8b5cf6', '#6366f1'],
            'dhana_yogas': ['#10b981', '#059669'],
            'panch_mahapurusha_yogas': ['#f59e0b', '#d97706'],
            'nabhasa_yogas': ['#06b6d4', '#0891b2'],
            'parivartana_yogas': ['#ec4899', '#d946ef'],
        };
        return gradients[category] || ['#6366f1', '#8b5cf6'];
    };

    const renderYogaCard = (yoga, index) => (
        <Animated.View 
            key={index}
            style={[styles.yogaCard, { opacity: fadeAnim }]}
        >
            <LinearGradient
                colors={theme === 'dark' 
                    ? ['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']
                    : ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.05)']}
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
            <View key={category} style={styles.categoryCard}>
                <TouchableOpacity 
                    onPress={() => toggleCategory(category)}
                    activeOpacity={0.8}
                >
                    <LinearGradient
                        colors={getCategoryGradient(category)}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={styles.categoryHeader}
                    >
                        <View style={styles.categoryTitleRow}>
                            <Text style={styles.categoryIcon}>{getCategoryIcon(category)}</Text>
                            <View style={styles.categoryTitleContainer}>
                                <Text style={styles.categoryTitle}>
                                    {t(`yogas.${category}`, category.replace(/_/g, ' ').toUpperCase())}
                                </Text>
                                <Text style={styles.categoryCount}>{yogaCount} Yoga{yogaCount > 1 ? 's' : ''}</Text>
                            </View>
                        </View>
                        <Ionicons 
                            name={isExpanded ? 'chevron-up' : 'chevron-down'} 
                            size={24} 
                            color="#fff" 
                        />
                    </LinearGradient>
                </TouchableOpacity>
                
                {isExpanded && (
                    <View style={[styles.yogasListContainer, { backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.9)' }]}>
                        {yogaList.map((yoga, index) => (
                            <View key={index} style={styles.yogaItem}>
                                <View style={styles.yogaItemHeader}>
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

    if (loading) {
        return (
            <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
                <LinearGradient
                    colors={theme === 'dark' 
                        ? ['#1a0033', '#2d1b4e', '#4a2c6d']
                        : ['#fefcfb', '#fef7f0', '#fed7d7']}
                    style={styles.loadingGradient}
                >
                    <ActivityIndicator size="large" color={colors.primary} />
                    <Text style={[styles.loadingText, { color: colors.text }]}>
                        Analyzing Yogas...
                    </Text>
                </LinearGradient>
            </View>
        );
    }

    return (
        <View style={{ flex: 1 }}>
            <LinearGradient
                colors={theme === 'dark' 
                    ? ['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']
                    : ['#fefcfb', '#fef7f0', '#fed7d7', '#fefcfb']}
                style={styles.container}
            >
                <SafeAreaView style={styles.safeArea}>
                    <View style={styles.header}>
                        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                            <Ionicons name="arrow-back" size={24} color={colors.text} />
                        </TouchableOpacity>
                        <Text style={[styles.headerTitle, { color: colors.text }]}>🌟 Yogas</Text>
                        <View style={{ width: 40 }} />
                    </View>

                    <ScrollView 
                        style={styles.scrollView}
                        contentContainerStyle={styles.scrollContent}
                        showsVerticalScrollIndicator={false}
                    >
                        <Animated.View style={{ opacity: fadeAnim }}>
                            <View style={styles.introCard}>
                                <LinearGradient
                                    colors={theme === 'dark'
                                        ? ['rgba(255, 215, 0, 0.15)', 'rgba(255, 107, 53, 0.1)']
                                        : ['rgba(249, 115, 22, 0.15)', 'rgba(236, 72, 153, 0.1)']}
                                    style={styles.introGradient}
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
        fontSize: 24,
        fontWeight: '800',
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
    },
    categoryCardGradient: {
        borderRadius: 16,
    },
    categoryHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
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
        fontSize: 18,
        fontWeight: '700',
        color: '#fff',
        marginBottom: 4,
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
