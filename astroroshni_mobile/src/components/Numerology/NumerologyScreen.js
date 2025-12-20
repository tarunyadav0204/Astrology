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
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import SoulBlueprint from './SoulBlueprint';
import CosmicWeather from './CosmicWeather';
import NameAlchemist from './NameAlchemist';

export default function NumerologyScreen({ navigation, route }) {
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
        if (profiles && profiles.length > 0) {
          selectedBirthData = profiles.find(p => p.relation === 'self') || profiles[0];
        }
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
      icon: '🧮',
      gradient: ['#667eea', '#764ba2'],
    },
    {
      id: 'cosmic',
      title: 'Cosmic Weather',
      subtitle: 'Daily Cycles & Timeline',
      icon: '📅',
      gradient: ['#f093fb', '#f5576c'],
    },
    {
      id: 'name',
      title: 'Name Alchemist',
      subtitle: 'Discover your name\'s power & find lucky variations',
      icon: '✍️',
      gradient: ['#4facfe', '#00f2fe'],
    }
  ];

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Numerology</Text>
            <View style={styles.placeholder} />
          </View>

          <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
            <Text style={styles.welcomeText}>
              Unlock the secrets hidden in your numbers
            </Text>
            
            <View style={styles.cardsGrid}>
              {cards.map((card) => (
                <TouchableOpacity
                  key={card.id}
                  style={styles.cardContainer}
                  onPress={() => openModal(card.id)}
                  activeOpacity={0.8}
                >
                  <LinearGradient colors={card.gradient} style={styles.card}>
                    <Text style={styles.cardIcon}>{card.icon}</Text>
                    <Text style={styles.cardTitle}>{card.title}</Text>
                    <Text style={styles.cardSubtitle}>{card.subtitle}</Text>
                  </LinearGradient>
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
            <View style={styles.modalContainer}>
              <LinearGradient colors={['#1a0033', '#2d1b4e']} style={styles.modalGradient}>
                <SafeAreaView style={styles.modalSafeArea}>
                  <View style={styles.modalHeader}>
                    <TouchableOpacity onPress={() => setModalVisible(false)}>
                      <Ionicons name="close" size={24} color={COLORS.white} />
                    </TouchableOpacity>
                    <View style={styles.modalHeaderCenter}>
                      <Text style={styles.modalTitle}>
                        {birthData?.name || 'Numerology'}
                      </Text>
                      <Text style={styles.modalSubtitle}>
                        {birthData?.date ? new Date(birthData.date).toLocaleDateString() : ''}
                      </Text>
                    </View>
                    <View style={styles.placeholder} />
                  </View>

                  <View style={styles.tabContainer}>
                    {[
                      { id: 'soul', title: 'Soul Blueprint', icon: '🧮' },
                      { id: 'cosmic', title: 'Cosmic Weather', icon: '📅' },
                      { id: 'name', title: 'Name Alchemist', icon: '✍️' }
                    ].map((tab) => (
                      <TouchableOpacity
                        key={tab.id}
                        style={[styles.tab, activeTab === tab.id && styles.activeTab]}
                        onPress={() => setActiveTab(tab.id)}
                      >
                        <Text style={styles.tabIcon}>{tab.icon}</Text>
                        <Text style={[styles.tabText, activeTab === tab.id && styles.activeTabText]}>
                          {tab.title}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>

                  <ScrollView style={styles.modalContent}>
                    {loading ? (
                      <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#ff6b35" />
                        <Text style={styles.loadingText}>Loading numerology data...</Text>
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
              </LinearGradient>
            </View>
          </Modal>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
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
    fontWeight: '700',
    color: COLORS.white,
  },
  placeholder: { width: 40 },
  scrollView: { flex: 1 },
  content: { padding: 20 },
  welcomeText: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginBottom: 30,
    fontStyle: 'italic',
  },
  cardsGrid: {
    gap: 16,
  },
  cardContainer: {
    width: '100%',
    marginBottom: 16,
  },
  card: {
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
    minHeight: 140,
    justifyContent: 'center',
  },
  cardIcon: { fontSize: 32, marginBottom: 12 },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
  },
  modalContainer: { flex: 1 },
  modalGradient: { flex: 1 },
  modalSafeArea: { flex: 1 },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  modalHeaderCenter: { alignItems: 'center' },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
  },
  modalSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    marginHorizontal: 4,
  },
  activeTab: {
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
  },
  tabIcon: { fontSize: 20, marginBottom: 4 },
  tabText: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  activeTabText: { color: COLORS.white },
  modalContent: { flex: 1, paddingHorizontal: 20 },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    color: 'rgba(255, 255, 255, 0.8)',
    marginTop: 16,
    fontSize: 16,
  },
});