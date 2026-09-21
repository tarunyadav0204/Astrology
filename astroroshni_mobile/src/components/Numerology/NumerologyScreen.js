import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  Alert,
  ActivityIndicator,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { API_BASE_URL } from '../../utils/constants';
import { formatBirthDateForDisplay } from '../../utils/birthDateUtils';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../../context/ThemeContext';
import SoulBlueprint from './SoulBlueprint';
import CosmicWeather from './CosmicWeather';
import NameAlchemist from './NameAlchemist';

export default function NumerologyScreen({ navigation, route }) {
  const { colors } = useTheme();
  const [modalVisible, setModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('soul');
  const [numerologyData, setNumerologyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [birthData, setBirthData] = useState(null);

  useEffect(() => {
    loadBirthData();
  }, []);

  const loadBirthData = async () => {
    try {
      const { storage } = require('../../services/storage');
      let selectedBirthData = await storage.getBirthDetails();
      if (!selectedBirthData) {
        const profiles = await storage.getBirthProfiles();
        if (profiles?.length) selectedBirthData = profiles.find(p => p.relation === 'self') || profiles[0];
      }
      if (!selectedBirthData?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'Numerology' });
        return;
      }
      setBirthData(selectedBirthData);
    } catch (error) {
      console.error('Error loading birth data:', error);
    }
  };

  const fetchNumerologyData = async () => {
    if (!birthData) {
      console.log('No birth data available');
      return;
    }
    
    console.log('Fetching numerology data for:', birthData.name, birthData.date);
    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const requestData = {
        name: birthData.name,
        dob: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date
      };
      console.log('Request data:', requestData);
      
      const response = await fetch(`${API_BASE_URL}/api/numerology/full-report`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      console.log('Response status:', response.status);
      const result = await response.json();
      console.log('Response data:', result);
      
      if (response.ok && result.success) {
        setNumerologyData(result.data);
        console.log('Numerology data set:', result.data);
      } else {
        console.error('API error:', result);
        Alert.alert('Error', result.detail || 'Failed to fetch numerology data');
      }
    } catch (error) {
      console.error('Error fetching numerology data:', error);
      Alert.alert('Error', 'Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  const openModal = (tab) => {
    setActiveTab(tab);
    setModalVisible(true);
    if (!numerologyData) {
      fetchNumerologyData();
    }
  };

  const cards = [
    {
      id: 'soul',
      title: 'Soul Blueprint',
      subtitle: 'Core Numbers & Life Path',
      icon: 'calculator-outline',
    },
    {
      id: 'cosmic',
      title: 'Cosmic Weather',
      subtitle: 'Daily Cycles & Timeline',
      icon: 'calendar-outline',
    },
    {
      id: 'name',
      title: 'Name Alchemist',
      subtitle: 'Discover your name\'s power & find lucky variations',
      icon: 'create-outline',
    }
  ];

  const renderHeader = (title, onBack, backIcon = 'arrow-back') => (
    <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine || colors.cardBorder }]}>
      <TouchableOpacity
        onPress={onBack}
        style={[styles.backButton, { backgroundColor: colors.cosmicGlow, borderColor: colors.cosmicLine || colors.cardBorder }]}
        accessibilityRole="button"
      >
        <Ionicons name={backIcon} size={22} color={colors.textInverse} />
      </TouchableOpacity>
      <Text style={[styles.headerTitle, { color: colors.textInverse }]} numberOfLines={1}>{title}</Text>
      <View style={styles.placeholder} />
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        {renderHeader('Numerology', () => navigation.goBack())}

          <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
            <Text style={[styles.welcomeText, { color: colors.textSecondary }]}>
              Unlock the secrets hidden in your numbers
            </Text>
            
            <View style={styles.cardsGrid}>
              {cards.map((card) => (
                <TouchableOpacity
                  key={card.id}
                  style={[
                    styles.card,
                    {
                      backgroundColor: colors.cardBackground,
                      borderColor: colors.cardBorder,
                    },
                  ]}
                  onPress={() => openModal(card.id)}
                  activeOpacity={0.8}
                  accessibilityRole="button"
                  accessibilityLabel={card.title}
                >
                  <View style={[styles.cardIconWrap, { backgroundColor: colors.selectionSurface }]}>
                    <Ionicons name={card.icon} size={22} color={colors.selectionText} />
                  </View>
                  <Text style={[styles.cardTitle, { color: colors.text }]}>{card.title}</Text>
                  <Text style={[styles.cardSubtitle, { color: colors.textSecondary }]}>{card.subtitle}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>

          <Modal
            visible={modalVisible}
            animationType="slide"
            presentationStyle="pageSheet"
            onRequestClose={() => setModalVisible(false)}
          >
            <View style={[styles.modalContainer, { backgroundColor: colors.background }]}>
              <SafeAreaView style={styles.modalSafeArea} edges={['top']}>
                <View style={[styles.modalHeader, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine || colors.cardBorder }]}>
                    <TouchableOpacity
                      onPress={() => setModalVisible(false)}
                      style={[styles.backButton, { backgroundColor: colors.cosmicGlow, borderColor: colors.cosmicLine || colors.cardBorder }]}
                      accessibilityRole="button"
                    >
                      <Ionicons name="close" size={22} color={colors.textInverse} />
                    </TouchableOpacity>
                    <View style={styles.modalHeaderCenter}>
                      <Text style={[styles.modalTitle, { color: colors.textInverse }]}>
                        {birthData?.name || 'Numerology'}
                      </Text>
                      <Text style={[styles.modalSubtitle, { color: colors.textInverseMuted }]}>
                        {birthData?.date ? formatBirthDateForDisplay(birthData.date) : ''}
                      </Text>
                    </View>
                    <View style={styles.placeholder} />
                  </View>

                  <View style={[styles.tabContainer, { backgroundColor: colors.background, borderBottomColor: colors.cardBorder }]}>
                    {[
                      { id: 'soul', title: 'Soul Blueprint', icon: 'calculator-outline' },
                      { id: 'cosmic', title: 'Cosmic Weather', icon: 'calendar-outline' },
                      { id: 'name', title: 'Name Alchemist', icon: 'create-outline' }
                    ].map((tab) => {
                      const selected = activeTab === tab.id;
                      return (
                      <TouchableOpacity
                        key={tab.id}
                        style={[
                          styles.tab,
                          {
                            backgroundColor: selected ? colors.selectionSurface : colors.surfaceMuted,
                            borderColor: selected ? colors.selectionBorder : colors.cardBorder,
                          },
                        ]}
                        onPress={() => setActiveTab(tab.id)}
                        accessibilityRole="button"
                        accessibilityState={{ selected }}
                      >
                        <Ionicons
                          name={tab.icon}
                          size={16}
                          color={selected ? colors.selectionText : colors.textSecondary}
                        />
                        <Text style={[
                          styles.tabText,
                          { color: selected ? colors.selectionText : colors.textSecondary },
                        ]}>
                          {tab.title}
                        </Text>
                      </TouchableOpacity>
                      );
                    })}
                  </View>

                  <ScrollView style={styles.modalContent} contentContainerStyle={styles.modalContentInner}>
                    {loading ? (
                      <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color={colors.primary} />
                        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading numerology data...</Text>
                      </View>
                    ) : (
                      <>

                        {activeTab === 'soul' && <SoulBlueprint data={numerologyData?.numerology_chart} />}
                        {activeTab === 'cosmic' && <CosmicWeather data={numerologyData?.forecast} />}
                        {activeTab === 'name' && <NameAlchemist data={numerologyData} birthData={birthData} />}
                      </>
                    )}
                  </ScrollView>
                </SafeAreaView>
            </View>
          </Modal>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    flex: 1,
    textAlign: 'center',
  },
  placeholder: { width: 40 },
  scrollView: { flex: 1 },
  content: { padding: 20 },
  welcomeText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 22,
  },
  cardsGrid: {
    gap: 16,
  },
  card: {
    width: '100%',
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    minHeight: 132,
    justifyContent: 'center',
  },
  cardIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
  },
  modalContainer: { flex: 1 },
  modalSafeArea: { flex: 1 },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalHeaderCenter: { flex: 1, alignItems: 'center' },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  modalSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 4,
    borderRadius: 12,
    marginHorizontal: 4,
    borderWidth: 1,
    gap: 4,
  },
  tabText: {
    fontSize: 10,
    fontWeight: '600',
    textAlign: 'center',
  },
  modalContent: { flex: 1 },
  modalContentInner: { paddingHorizontal: 20, paddingBottom: 32 },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
});
