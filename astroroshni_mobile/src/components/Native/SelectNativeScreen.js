import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Alert,
  Animated,
  PanResponder,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { COLORS } from '../../utils/constants';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';

const SwipeableProfileCard = ({ profile, selectedProfile, onSelect, onEdit, onDelete, getZodiacSign }) => {
  const translateX = useRef(new Animated.Value(0)).current;
  const [isRevealed, setIsRevealed] = useState(false);

  const panResponder = PanResponder.create({
    onMoveShouldSetPanResponder: (evt, gestureState) => {
      return Math.abs(gestureState.dx) > 20 && Math.abs(gestureState.dy) < 50;
    },
    onPanResponderMove: (evt, gestureState) => {
      if (gestureState.dx < 0) {
        translateX.setValue(Math.max(gestureState.dx, -120));
      }
    },
    onPanResponderRelease: (evt, gestureState) => {
      if (gestureState.dx < -60) {
        Animated.spring(translateX, {
          toValue: -120,
          useNativeDriver: true,
        }).start();
        setIsRevealed(true);
      } else {
        Animated.spring(translateX, {
          toValue: 0,
          useNativeDriver: true,
        }).start();
        setIsRevealed(false);
      }
    },
  });

  const closeSwipe = () => {
    Animated.spring(translateX, {
      toValue: 0,
      useNativeDriver: true,
    }).start();
    setIsRevealed(false);
  };

  return (
    <View style={styles.profileWrapper}>
      {isRevealed && (
        <View style={styles.swipeActions}>
          <TouchableOpacity 
            style={[styles.actionButton, styles.editButton]}
            onPress={() => { closeSwipe(); onEdit(profile); }}
          >
            <Ionicons name="pencil" size={20} color={COLORS.white} />
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.actionButton, styles.deleteButton]}
            onPress={() => { closeSwipe(); onDelete(profile); }}
          >
            <Ionicons name="trash" size={20} color={COLORS.white} />
          </TouchableOpacity>
        </View>
      )}
      <Animated.View
        {...panResponder.panHandlers}
        style={[styles.profileCard, { transform: [{ translateX }] }]}
      >
        <TouchableOpacity
          style={[
            styles.cardTouchable,
            selectedProfile === profile.name && styles.selectedCard
          ]}
          onPress={() => {
            if (isRevealed) {
              closeSwipe();
            } else {
              onSelect(profile);
            }
          }}
        >
          <LinearGradient
            colors={
              selectedProfile === profile.name
                ? ['rgba(255, 107, 53, 0.3)', 'rgba(255, 107, 53, 0.1)']
                : ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']
            }
            style={styles.cardGradient}
          >
            <View style={styles.profileInfo}>
              <View style={styles.profileLeft}>
                <View style={styles.zodiacIcon}>
                  <Text style={styles.zodiacText}>{getZodiacSign(profile.date)}</Text>
                </View>
                <View style={styles.profileDetails}>
                  <View style={styles.nameRow}>
                    <Text style={styles.profileName}>{profile.name}</Text>
                    {profile.isSelf && (
                      <View style={styles.selfBadge}>
                        <Text style={styles.selfBadgeText}>You</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.profileDate}>
                    {new Date(profile.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })} • {profile.time}
                  </Text>
                  {profile.place && (
                    <Text style={styles.profilePlace}>📍 {profile.place}</Text>
                  )}
                </View>
              </View>
              <View style={styles.profileRight}>
                {selectedProfile === profile.name ? (
                  <Ionicons name="checkmark-circle" size={24} color="#ff6b35" />
                ) : (
                  <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.6)" />
                )}
              </View>
            </View>
          </LinearGradient>
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
};

export default function SelectNativeScreen({ navigation }) {
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);

  useFocusEffect(
    React.useCallback(() => {
      loadProfiles();
    }, [])
  );

  const loadProfiles = async () => {
    try {
      const userData = await storage.getUserData();
      const currentNative = await storage.getBirthDetails();
      
      // Fetch saved charts from API
      const { chartAPI } = require('../../services/api');
      const response = await chartAPI.getExistingCharts();
      const apiCharts = response.data.charts || [];
      
      const profileList = [];
      
      // Add user's own profile if it exists
      if (userData && userData.date && userData.time) {
        profileList.push({
          id: 'self',
          name: userData.name || 'Me',
          date: userData.date,
          time: userData.time,
          place: userData.place,
          latitude: userData.latitude,
          longitude: userData.longitude,
          timezone: userData.timezone,
          isSelf: true
        });
      }
      
      // Add charts from API
      apiCharts.forEach((chart) => {
        profileList.push({
          id: chart.id || chart._id,
          name: chart.name,
          date: chart.date,
          time: chart.time,
          place: chart.place,
          latitude: chart.latitude,
          longitude: chart.longitude,
          timezone: chart.timezone,
          gender: chart.gender,
          isSelf: userData && chart.name === userData.name
        });
      });
      
      // Remove duplicates based on name
      const uniqueProfiles = profileList.filter((profile, index, self) => 
        index === self.findIndex(p => p.name === profile.name)
      );
      
      setProfiles(uniqueProfiles);
      
      if (currentNative) {
        setSelectedProfile(currentNative.name);
      }
    } catch (error) {
      console.error('Error loading profiles:', error);
      // Fallback to local storage if API fails
      const savedProfiles = await storage.getBirthProfiles();
      setProfiles(savedProfiles);
    }
  };

  const selectProfile = async (profile) => {
    try {
      await storage.setBirthDetails(profile);
      setSelectedProfile(profile.name);
      navigation.navigate('Chat');
    } catch (error) {
      console.error('Error selecting profile:', error);
    }
  };

  const handleEdit = (profile) => {
    navigation.navigate('BirthForm', { editProfile: profile });
  };

  const handleDelete = (profile) => {
    Alert.alert(
      'Delete Profile',
      `Are you sure you want to delete ${profile.name}'s profile?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              if (profile.id && profile.id !== 'self') {
                await chartAPI.deleteChart(profile.id);
              }
              await storage.removeBirthProfile(profile.name);
              loadProfiles();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete profile');
            }
          }
        }
      ]
    );
  };

  const getZodiacSign = (date) => {
    if (!date) return '♈';
    const month = new Date(date).getMonth() + 1;
    const day = new Date(date).getDate();
    
    if ((month === 3 && day >= 21) || (month === 4 && day <= 19)) return '♈';
    if ((month === 4 && day >= 20) || (month === 5 && day <= 20)) return '♉';
    if ((month === 5 && day >= 21) || (month === 6 && day <= 20)) return '♊';
    if ((month === 6 && day >= 21) || (month === 7 && day <= 22)) return '♋';
    if ((month === 7 && day >= 23) || (month === 8 && day <= 22)) return '♌';
    if ((month === 8 && day >= 23) || (month === 9 && day <= 22)) return '♍';
    if ((month === 9 && day >= 23) || (month === 10 && day <= 22)) return '♎';
    if ((month === 10 && day >= 23) || (month === 11 && day <= 21)) return '♏';
    if ((month === 11 && day >= 22) || (month === 12 && day <= 21)) return '♐';
    if ((month === 12 && day >= 22) || (month === 1 && day <= 19)) return '♑';
    if ((month === 1 && day >= 20) || (month === 2 && day <= 18)) return '♒';
    return '♓';
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" translucent={false} />
      <LinearGradient
        colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']}
        style={styles.gradient}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.navigate('Chat')} style={styles.backButton}>
              <Ionicons name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Select Native</Text>
            <TouchableOpacity 
              onPress={() => navigation.navigate('BirthForm')} 
              style={styles.addButton}
            >
              <Ionicons name="add" size={24} color={COLORS.white} />
            </TouchableOpacity>
          </View>

          <ScrollView 
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <Text style={styles.subtitle}>Choose a profile for astrological analysis</Text>
            <Text style={styles.instructionText}>👈 Swipe left for options</Text>

            {profiles.map((profile) => (
              <SwipeableProfileCard
                key={profile.id}
                profile={profile}
                selectedProfile={selectedProfile}
                onSelect={selectProfile}
                onEdit={handleEdit}
                onDelete={handleDelete}
                getZodiacSign={getZodiacSign}
              />
            ))}

            {profiles.length === 0 && (
              <View style={styles.emptyState}>
                <Text style={styles.emptyIcon}>👤</Text>
                <Text style={styles.emptyTitle}>No Profiles Found</Text>
                <Text style={styles.emptyText}>Add your birth details to get started</Text>
                <TouchableOpacity 
                  style={styles.addProfileButton}
                  onPress={() => navigation.navigate('BirthForm')}
                >
                  <LinearGradient
                    colors={['#ff6b35', '#ff8c5a']}
                    style={styles.addProfileGradient}
                  >
                    <Text style={styles.addProfileText}>Add Profile</Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>
            )}
          </ScrollView>
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
    paddingVertical: 16 
  },
  backButton: { 
    width: 40, 
    height: 40, 
    borderRadius: 20, 
    backgroundColor: 'rgba(255, 255, 255, 0.1)', 
    alignItems: 'center', 
    justifyContent: 'center' 
  },
  headerTitle: { 
    fontSize: 20, 
    fontWeight: '700', 
    color: COLORS.white 
  },
  addButton: { 
    width: 40, 
    height: 40, 
    borderRadius: 20, 
    backgroundColor: 'rgba(255, 255, 255, 0.1)', 
    alignItems: 'center', 
    justifyContent: 'center' 
  },
  scrollView: { flex: 1 },
  scrollContent: { padding: 20 },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
    marginBottom: 24,
    fontStyle: 'italic',
  },
  profileWrapper: {
    position: 'relative',
    marginBottom: 16,
  },
  profileCard: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  cardTouchable: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  swipeActions: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    flexDirection: 'row',
    alignItems: 'center',
    zIndex: -1,
  },
  actionButton: {
    width: 60,
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  editButton: {
    backgroundColor: '#4CAF50',
  },
  deleteButton: {
    backgroundColor: '#f44336',
  },
  selectedCard: {
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  cardGradient: {
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  profileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  zodiacIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  zodiacText: {
    fontSize: 24,
  },
  profileDetails: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
    marginRight: 8,
  },
  selfBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.3)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  selfBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: COLORS.white,
  },
  profileDate: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 2,
  },
  profilePlace: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  profileRight: {
    marginLeft: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    marginBottom: 24,
  },
  addProfileButton: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  addProfileGradient: {
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  addProfileText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
  },
});