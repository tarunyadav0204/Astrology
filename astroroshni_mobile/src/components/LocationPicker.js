import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Modal } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { COLORS } from '../utils/constants';

export default function LocationPicker({ onLocationSelect, onClose }) {
  const [searchText, setSearchText] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const getTimezoneFromCoordinates = (lat, lng) => {
    if (lat >= 6.0 && lat <= 37.0 && lng >= 68.0 && lng <= 97.0) {
      return 'UTC+5:30';
    }
    const offset = lng / 15.0;
    const hours = Math.floor(Math.abs(offset));
    const minutes = Math.round((Math.abs(offset) - hours) * 60);
    
    if (minutes === 30) {
      return `UTC${offset >= 0 ? '+' : '-'}${hours}:30`;
    } else {
      return `UTC${offset >= 0 ? '+' : '-'}${hours}`;
    }
  };

  const searchPlaces = async (query) => {
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
        { headers: { 'User-Agent': 'AstrologyApp/1.0' } }
      );
      const data = await response.json();
      const places = data.map(item => {
        const lat = parseFloat(item.lat);
        const lng = parseFloat(item.lon);
        return {
          id: item.place_id,
          name: item.display_name,
          latitude: lat,
          longitude: lng,
          timezone: getTimezoneFromCoordinates(lat, lng)
        };
      });
      setSuggestions(places);
    } catch (error) {
      console.error('Location search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTextChange = (text) => {
    setSearchText(text);
    const timeout = setTimeout(() => searchPlaces(text), 300);
    return () => clearTimeout(timeout);
  };

  const selectLocation = (location) => {
    onLocationSelect(location);
  };

  return (
    <Modal visible={true} animationType="slide" onRequestClose={onClose}>
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.container}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="close" size={24} color={COLORS.white} />
            </TouchableOpacity>
            <Text style={styles.title}>Select Location</Text>
            <View style={styles.placeholder} />
          </View>

          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              value={searchText}
              onChangeText={handleTextChange}
              placeholder="Search for city, state, country..."
              placeholderTextColor="rgba(255, 255, 255, 0.5)"
              autoFocus
            />
          </View>

          <View style={styles.suggestionsList}>
            {suggestions.map(suggestion => (
              <TouchableOpacity
                key={suggestion.id}
                style={styles.suggestionItem}
                onPress={() => selectLocation(suggestion)}
              >
                <LinearGradient
                  colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                  style={styles.suggestionGradient}
                >
                  <Icon name="location" size={20} color={COLORS.white} />
                  <Text style={styles.suggestionText} numberOfLines={2}>
                    {suggestion.name}
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </View>
        </SafeAreaView>
      </LinearGradient>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  placeholder: { width: 40 },
  searchContainer: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  searchInput: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 16,
    padding: 16,
    fontSize: 16,
    color: COLORS.white,
  },
  suggestionsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  suggestionItem: {
    marginBottom: 12,
    borderRadius: 16,
    overflow: 'hidden',
  },
  suggestionGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  suggestionText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.white,
    lineHeight: 20,
  },
});